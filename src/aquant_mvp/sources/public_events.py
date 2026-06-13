from __future__ import annotations

from dataclasses import dataclass
import hashlib
from html import unescape
import io
import json
import re
from typing import Callable
from urllib import parse, request

import pandas as pd


CNINFO_QUERY_URL = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
CNINFO_STATIC_BASE = "http://static.cninfo.com.cn/"
RAW_EVENT_COLUMNS = [
    "source",
    "source_url",
    "published_at",
    "symbol",
    "related_symbols",
    "title",
    "summary",
    "source_text_status",
    "source_text_length",
    "source_text_hash",
    "quality_flag",
]


@dataclass(frozen=True)
class PublicEventFetchResult:
    events: pd.DataFrame
    warnings: list[str]


HttpPost = Callable[[str, dict[str, str], dict[str, str], int], dict[str, object]]
HttpGet = Callable[[str, dict[str, str], int], bytes]


def fetch_cninfo_announcements_direct(
    symbols: list[str],
    start_date: str,
    end_date: str,
    *,
    max_events_per_symbol: int = 80,
    fetch_text: bool = False,
    http_post: HttpPost | None = None,
    http_get: HttpGet | None = None,
) -> PublicEventFetchResult:
    """Fetch CNINFO announcement metadata directly from the public query endpoint.

    By default this only fetches metadata. When fetch_text=True, it attempts a
    bounded body download and records explicit extraction status; failures are
    audit signals and never become fake announcement summaries.
    """

    post = http_post or _post_form_json
    get = http_get or _get_bytes
    rows: list[dict[str, object]] = []
    warnings: list[str] = []
    for symbol in [str(item).zfill(6) for item in symbols]:
        payload = _cninfo_payload(symbol, start_date, end_date, max_events_per_symbol)
        try:
            data = post(CNINFO_QUERY_URL, payload, _cninfo_headers(), 20)
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"{symbol}: cninfo_direct failed ({exc})")
            continue
        announcements = data.get("announcements", [])
        if not isinstance(announcements, list):
            warnings.append(f"{symbol}: cninfo_direct unexpected schema")
            continue
        for item in announcements[:max_events_per_symbol]:
            if not isinstance(item, dict):
                continue
            row = _cninfo_announcement_to_event(item, symbol)
            if row:
                if fetch_text:
                    row, body_warning = _attach_announcement_text(row, get)
                    if body_warning:
                        warnings.append(body_warning)
                rows.append(row)
    return PublicEventFetchResult(pd.DataFrame(rows, columns=RAW_EVENT_COLUMNS), warnings)


def _cninfo_payload(symbol: str, start_date: str, end_date: str, page_size: int) -> dict[str, str]:
    return {
        "stock": symbol,
        "searchkey": "",
        "plate": "",
        "category": "",
        "trade": "",
        "column": _cninfo_column(symbol),
        "pageNum": "1",
        "pageSize": str(max(1, min(int(page_size), 100))),
        "tabName": "fulltext",
        "sortName": "",
        "sortType": "",
        "limit": "",
        "seDate": f"{start_date}~{end_date}",
    }


def _cninfo_column(symbol: str) -> str:
    if symbol.startswith("6"):
        return "sse"
    if symbol.startswith(("4", "8", "9")):
        return "bj"
    return "szse"


def _cninfo_headers() -> dict[str, str]:
    return {
        "User-Agent": "Mozilla/5.0 AQuantResearch/0.4",
        "Referer": "http://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=disclosure/list/search",
        "Origin": "http://www.cninfo.com.cn",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }


def _post_form_json(url: str, payload: dict[str, str], headers: dict[str, str], timeout: int) -> dict[str, object]:
    encoded = parse.urlencode(payload).encode("utf-8")
    req = request.Request(url, data=encoded, headers=headers, method="POST")
    with request.urlopen(req, timeout=timeout) as response:  # noqa: S310 - public finance endpoint configured by constant.
        body = response.read().decode("utf-8", errors="replace")
    parsed = json.loads(body)
    return parsed if isinstance(parsed, dict) else {}


def _get_bytes(url: str, headers: dict[str, str], timeout: int) -> bytes:
    req = request.Request(url, headers=headers, method="GET")
    with request.urlopen(req, timeout=timeout) as response:  # noqa: S310 - public finance endpoint configured by source URL.
        return response.read(3_000_000)


def _cninfo_announcement_to_event(item: dict[str, object], fallback_symbol: str) -> dict[str, object] | None:
    symbol = _clean_symbol(item.get("secCode") or item.get("sec_code") or fallback_symbol)
    if not symbol:
        return None
    title = _strip_html(str(item.get("announcementTitle") or item.get("title") or "")).strip()
    if not title:
        return None
    published = _parse_announcement_time(item.get("announcementTime") or item.get("announcementDate"))
    adjunct_url = str(item.get("adjunctUrl") or item.get("announcementUrl") or "").strip()
    source_url = _cninfo_source_url(adjunct_url)
    return {
        "source": "cninfo_direct",
        "source_url": source_url,
        "published_at": published,
        "symbol": symbol,
        "related_symbols": symbol,
        "title": title,
        "summary": title,
        "source_text_status": "not_requested",
        "source_text_length": 0,
        "source_text_hash": "",
        "quality_flag": "direct_cninfo_announcement",
    }


def _attach_announcement_text(row: dict[str, object], http_get: HttpGet) -> tuple[dict[str, object], str | None]:
    url = str(row.get("source_url", "")).strip()
    if not url or url == "http://www.cninfo.com.cn/":
        row.update({"source_text_status": "missing_source_url", "source_text_length": 0, "source_text_hash": ""})
        return row, f"{row.get('symbol')}: cninfo_direct text missing source_url"
    try:
        body = http_get(url, _cninfo_text_headers(), 20)
    except Exception as exc:  # noqa: BLE001
        row.update({"source_text_status": f"download_failed:{type(exc).__name__}", "source_text_length": 0, "source_text_hash": ""})
        return row, f"{row.get('symbol')}: cninfo_direct text download failed ({exc})"
    text, status = _extract_announcement_text(url, body)
    text = _normalize_text(text)
    if text:
        row["summary"] = text[:1200]
    row["source_text_status"] = status
    row["source_text_length"] = len(text)
    row["source_text_hash"] = hashlib.sha1(text.encode("utf-8")).hexdigest() if text else ""
    warning = None if text else f"{row.get('symbol')}: cninfo_direct text {status}"
    return row, warning


def _cninfo_text_headers() -> dict[str, str]:
    return {
        "User-Agent": "Mozilla/5.0 AQuantResearch/0.4",
        "Referer": "http://www.cninfo.com.cn/",
    }


def _extract_announcement_text(url: str, body: bytes) -> tuple[str, str]:
    lower = url.lower()
    if lower.endswith(".pdf") or body[:4] == b"%PDF":
        try:
            from pypdf import PdfReader  # type: ignore
        except Exception:  # noqa: BLE001
            return "", "pdf_parser_unavailable"
        try:
            reader = PdfReader(io.BytesIO(body))
            pages = [(page.extract_text() or "") for page in reader.pages[:20]]
            return "\n".join(pages), "ok_pdf"
        except Exception as exc:  # noqa: BLE001
            return "", f"pdf_parse_failed:{type(exc).__name__}"
    decoded = body.decode("utf-8", errors="replace")
    if "<html" in decoded.lower() or "<body" in decoded.lower() or "<p" in decoded.lower():
        return _strip_html(decoded), "ok_html"
    return decoded, "ok_text"


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", unescape(text or "")).strip()


def _clean_symbol(value: object) -> str:
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    return digits[-6:].zfill(6) if digits else ""


def _parse_announcement_time(value: object) -> pd.Timestamp:
    if isinstance(value, (int, float)) and value > 10_000_000_000:
        return pd.to_datetime(int(value), unit="ms", errors="coerce")
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return pd.Timestamp.now().normalize()
    return pd.Timestamp(parsed)


def _cninfo_source_url(adjunct_url: str) -> str:
    if not adjunct_url:
        return "http://www.cninfo.com.cn/"
    if adjunct_url.startswith(("http://", "https://")):
        return adjunct_url
    return parse.urljoin(CNINFO_STATIC_BASE, adjunct_url)


def _strip_html(value: str) -> str:
    cleaned = value.replace("<em>", "").replace("</em>", "").replace("&nbsp;", " ")
    cleaned = re.sub(r"<script[\s\S]*?</script>", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<style[\s\S]*?</style>", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    return unescape(cleaned)
