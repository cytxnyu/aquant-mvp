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


@dataclass(frozen=True)
class OfficialPublicSource:
    source: str
    display_name: str
    seed_urls: tuple[str, ...]
    quality_flag: str
    impact_domain: str
    default_event_type: str = "industry_policy"
    default_impact: float = 0.10
    default_confidence: float = 0.55


OFFICIAL_PUBLIC_SOURCES: dict[str, OfficialPublicSource] = {
    "sse_public": OfficialPublicSource(
        "sse_public",
        "Shanghai Stock Exchange",
        ("https://www.sse.com.cn/disclosure/listedinfo/announcement/", "https://www.sse.com.cn/disclosure/credibility/supervision/inquiries/"),
        "official_public:sse",
        "exchange_regulator",
        "regulatory_inquiry",
        -0.20,
        0.60,
    ),
    "szse_public": OfficialPublicSource(
        "szse_public",
        "Shenzhen Stock Exchange",
        ("https://www.szse.cn/disclosure/listed/notice/index.html", "https://www.szse.cn/disclosure/supervision/inquire/index.html"),
        "official_public:szse",
        "exchange_regulator",
        "regulatory_inquiry",
        -0.20,
        0.60,
    ),
    "bse_public": OfficialPublicSource(
        "bse_public",
        "Beijing Stock Exchange",
        ("https://www.bse.cn/disclosure/announcement.html",),
        "official_public:bse",
        "exchange_regulator",
        "regulatory_inquiry",
        -0.15,
        0.55,
    ),
    "csrc_public": OfficialPublicSource(
        "csrc_public",
        "China Securities Regulatory Commission",
        ("https://www.csrc.gov.cn/csrc/c100028/common_list.shtml", "https://www.csrc.gov.cn/csrc/c100035/common_list.shtml"),
        "official_public:csrc",
        "regulator_policy",
        "industry_policy",
        0.05,
        0.60,
    ),
    "ndrc_public": OfficialPublicSource(
        "ndrc_public",
        "National Development and Reform Commission",
        ("https://www.ndrc.gov.cn/xwdt/xwfb/", "https://www.ndrc.gov.cn/xwdt/tzgg/"),
        "official_public:ndrc",
        "macro_policy",
        "industry_policy",
        0.10,
        0.55,
    ),
    "miit_public": OfficialPublicSource(
        "miit_public",
        "Ministry of Industry and Information Technology",
        ("https://www.miit.gov.cn/xwdt/gxdt/sjdt/index.html", "https://www.miit.gov.cn/zwgk/zcwj/index.html"),
        "official_public:miit",
        "macro_policy",
        "industry_policy",
        0.10,
        0.55,
    ),
    "mofcom_public": OfficialPublicSource(
        "mofcom_public",
        "Ministry of Commerce",
        ("https://www.mofcom.gov.cn/xwfbh/", "https://www.mofcom.gov.cn/zwgk/zcfb/"),
        "official_public:mofcom",
        "macro_policy",
        "industry_policy",
        0.05,
        0.55,
    ),
    "pbc_public": OfficialPublicSource(
        "pbc_public",
        "People's Bank of China",
        ("http://www.pbc.gov.cn/goutongjiaoliu/113456/113469/index.html",),
        "official_public:pbc",
        "macro_policy",
        "industry_policy",
        0.05,
        0.60,
    ),
    "customs_public": OfficialPublicSource(
        "customs_public",
        "General Administration of Customs",
        ("http://www.customs.gov.cn/customs/xwfb34/302425/index.html",),
        "official_public:customs",
        "macro_policy",
        "industry_policy",
        0.05,
        0.55,
    ),
    "stats_nbs_public": OfficialPublicSource(
        "stats_nbs_public",
        "National Bureau of Statistics",
        ("https://www.stats.gov.cn/sj/zxfb/",),
        "official_public:stats_nbs",
        "macro_policy",
        "industry_policy",
        0.05,
        0.55,
    ),
}


def official_public_source_ids() -> set[str]:
    return set(OFFICIAL_PUBLIC_SOURCES)


def fetch_official_public_events(
    symbols: list[str],
    start_date: str,
    end_date: str,
    *,
    source: str,
    max_events_per_source: int = 120,
    fetch_text: bool = False,
    max_text_events: int = 20,
    max_pages_per_seed: int = 1,
    http_get: HttpGet | None = None,
) -> PublicEventFetchResult:
    """Fetch headline-level events from official public web pages.

    This is a conservative index-page adapter. It records URL-backed headlines
    and explicit warnings, but it does not fabricate body text or stock links.
    Entity linking is handled later by the event bus.
    """
    source_id = str(source).lower()
    config = OFFICIAL_PUBLIC_SOURCES.get(source_id)
    if config is None:
        return PublicEventFetchResult(pd.DataFrame(columns=RAW_EVENT_COLUMNS), [f"{source}: official public source not configured"])

    get = http_get or _get_bytes
    rows: list[dict[str, object]] = []
    warnings: list[str] = []
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    wanted_symbols = [str(item).zfill(6) for item in symbols]
    max_pages = max(1, int(max_pages_per_seed or 1))
    for seed_url in config.seed_urls:
        for page_idx, url in enumerate(_official_paginated_urls(seed_url, max_pages), start=1):
            try:
                body = get(url, _official_headers(url), 20)
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"{source_id}: official page fetch failed page={page_idx} {url} ({exc})")
                continue
            page_rows = _official_page_to_events(
                body,
                base_url=url,
                source=config,
                symbols=wanted_symbols,
                start=start,
                end=end,
            )
            for row in page_rows:
                row["quality_flag"] = f"{row.get('quality_flag', config.quality_flag)}:page_{page_idx}"
            rows.extend(page_rows)
            if len(rows) >= max_events_per_source:
                break
        if len(rows) >= max_events_per_source:
            break
    if not rows and not warnings:
        warnings.append(f"{source_id}: no official public events parsed")
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame = frame.drop_duplicates(subset=["source", "source_url", "title"], keep="last").head(max_events_per_source)
        if fetch_text:
            enriched_rows = []
            for idx, row in enumerate(frame.to_dict(orient="records")):
                if idx >= max_text_events:
                    row["source_text_status"] = "official_text_not_requested_limit"
                    row["source_text_length"] = int(row.get("source_text_length", 0) or 0)
                    row["source_text_hash"] = str(row.get("source_text_hash", "") or "")
                    enriched_rows.append(row)
                    continue
                enriched, warning = _attach_official_text(row, get, source_id, set(config.seed_urls))
                if warning:
                    warnings.append(warning)
                enriched_rows.append(enriched)
            frame = pd.DataFrame(enriched_rows)
    return PublicEventFetchResult(frame, warnings)


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


def _official_headers(url: str) -> dict[str, str]:
    parsed = parse.urlparse(url)
    referer = f"{parsed.scheme}://{parsed.netloc}/" if parsed.scheme and parsed.netloc else url
    return {
        "User-Agent": "Mozilla/5.0 AQuantResearch/0.4",
        "Referer": referer,
        "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
    }


def _official_text_headers(url: str) -> dict[str, str]:
    headers = _official_headers(url)
    headers["Accept"] = "text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.8"
    return headers


def _official_paginated_urls(seed_url: str, max_pages: int) -> list[str]:
    urls = [seed_url]
    for page_no in range(1, max(1, int(max_pages or 1))):
        urls.append(_official_page_variant(seed_url, page_no))
    out: list[str] = []
    seen: set[str] = set()
    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        out.append(url)
    return out


def _official_page_variant(seed_url: str, page_no: int) -> str:
    parsed = parse.urlparse(seed_url)
    path = parsed.path or ""
    if not path or path.endswith("/") or "." not in path.rsplit("/", 1)[-1]:
        new_path = f"{path.rstrip('/')}/index_{page_no}.html"
    else:
        head, tail = path.rsplit("/", 1) if "/" in path else ("", path)
        stem, dot, ext = tail.rpartition(".")
        new_tail = f"{stem}_{page_no}.{ext}" if dot else f"{tail}_{page_no}"
        new_path = f"{head}/{new_tail}" if head else new_tail
    return parse.urlunparse(parsed._replace(path=new_path, query=""))


def _official_page_to_events(
    body: bytes,
    *,
    base_url: str,
    source: OfficialPublicSource,
    symbols: list[str],
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> list[dict[str, object]]:
    text = _decode_web_text(body)
    if not text.strip():
        return []
    items = _json_items_to_links(text, base_url) if text.lstrip().startswith(("{", "[")) else []
    if not items:
        items = _html_links_to_items(text, base_url)
    rows = []
    for item in items:
        title = _normalize_text(str(item.get("title", "")))
        if not title or len(title) < 4:
            continue
        context = _normalize_text(f"{item.get('context', '')} {title}")
        published, date_quality = _extract_official_date(context, end)
        if published < start or published > end + pd.Timedelta(days=1):
            continue
        # Keep the index summary scoped to the current anchor. The surrounding
        # HTML context is still used for dates, but can contain neighboring
        # headlines and stock codes that would contaminate entity links.
        summary = _truncate_official_summary(title, 800)
        explicit_symbols = _symbols_in_text(title, symbols) or _symbols_in_text(summary, symbols)
        classification = _classify_official_public_event(title, summary, source)
        row = {
            "source": source.source,
            "source_url": str(item.get("url", base_url)),
            "published_at": published,
            "symbol": "",
            "related_symbols": ";".join(explicit_symbols),
            "title": title,
            "summary": summary or title,
            "source_text_status": "official_index_snippet",
            "source_text_length": len(summary or title),
            "source_text_hash": hashlib.sha1((summary or title).encode("utf-8")).hexdigest(),
            "quality_flag": f"{source.quality_flag}:{date_quality}",
            "event_type": classification["event_type"],
            "sentiment": classification["sentiment"],
            "impact_score": classification["impact_score"],
            "confidence": classification["confidence"],
        }
        rows.append(row)
    return rows


def _attach_official_text(
    row: dict[str, object],
    http_get: HttpGet,
    source_id: str,
    seed_urls: set[str],
) -> tuple[dict[str, object], str | None]:
    url = str(row.get("source_url", "")).strip()
    if not url:
        row.update({"source_text_status": "missing_source_url", "source_text_length": 0, "source_text_hash": ""})
        return row, f"{source_id}: official text missing source_url"
    if url in seed_urls:
        row["source_text_status"] = "official_text_skipped_seed_url"
        row["source_text_length"] = int(row.get("source_text_length", 0) or 0)
        row["source_text_hash"] = str(row.get("source_text_hash", "") or "")
        return row, f"{source_id}: official text skipped seed url {url}"
    try:
        body = http_get(url, _official_text_headers(url), 20)
    except Exception as exc:  # noqa: BLE001
        row.update({"source_text_status": f"official_text_download_failed:{type(exc).__name__}", "source_text_length": 0, "source_text_hash": ""})
        return row, f"{source_id}: official text download failed {url} ({exc})"
    text, status = _extract_announcement_text(url, body)
    text = _normalize_text(text)
    if text:
        row["summary"] = _truncate_official_summary(text, 1200)
    row["source_text_status"] = f"official_text_{status}" if status.startswith("ok_") else f"official_text_{status}"
    row["source_text_length"] = len(text)
    row["source_text_hash"] = hashlib.sha1(text.encode("utf-8")).hexdigest() if text else ""
    warning = None if text else f"{source_id}: official text {status} {url}"
    return row, warning


def _classify_official_public_event(title: str, summary: str, source: OfficialPublicSource) -> dict[str, object]:
    rules = [
        ("regulatory_penalty", ("处罚", "行政处罚", "市场禁入", "罚款", "立案", "调查", "警示函", "纪律处分", "通报批评", "penalty", "sanction"), -0.80, 0.78),
        ("regulatory_inquiry", ("问询", "监管函", "关注函", "异常波动", "风险提示", "监督管理", "inquiry", "supervision"), -0.55, 0.72),
        ("litigation_risk", ("诉讼", "仲裁", "纠纷", "执行", "冻结", "查封", "lawsuit", "arbitration"), -0.60, 0.70),
        ("performance_beat", ("预增", "扭亏", "业绩增长", "超预期", "profit forecast increase", "beat"), 0.65, 0.70),
        ("performance_miss", ("预减", "亏损", "业绩下降", "不及预期", "修正", "miss"), -0.65, 0.70),
        ("shareholder_change", ("减持", "增持", "股东", "解禁", "质押", "pledge", "shareholder"), -0.18, 0.62),
        ("buyback_dividend", ("回购", "分红", "派息", "注销股份", "repurchase", "dividend"), 0.42, 0.66),
        ("ma_restructuring", ("并购", "重组", "收购", "资产注入", "重大资产", "merger", "acquisition"), 0.35, 0.62),
        ("order_contract", ("中标", "合同", "订单", "采购", "合作协议", "contract", "order"), 0.45, 0.62),
        ("capacity_operation", ("投产", "停产", "扩产", "复产", "产能", "检修", "production", "capacity"), 0.20, 0.58),
        ("export_control", ("出口管制", "制裁", "关税", "反倾销", "贸易摩擦", "export control", "tariff"), -0.45, 0.66),
        ("monetary_liquidity", ("公开市场", "逆回购", "降准", "降息", "贷款市场报价利率", "LPR", "流动性"), 0.10, 0.62),
        ("macro_indicator", ("CPI", "PPI", "PMI", "工业增加值", "进出口", "社会融资", "统计数据"), 0.04, 0.56),
        ("industry_policy", ("政策", "规划", "支持", "补贴", "实施方案", "指导意见", "监管", "policy", "guideline"), source.default_impact, source.default_confidence),
    ]
    title_classification = _match_official_event_rules(title, rules)
    if title_classification:
        return title_classification
    summary_classification = _match_official_event_rules(summary, rules)
    if summary_classification:
        return summary_classification
    score = float(source.default_impact)
    return {
        "event_type": source.default_event_type,
        "sentiment": _official_sentiment(score),
        "impact_score": score,
        "confidence": float(source.default_confidence),
    }


def _match_official_event_rules(
    text: str,
    rules: list[tuple[str, tuple[str, ...], float, float]],
) -> dict[str, object] | None:
    normalized = _normalize_text(text).lower()
    if not normalized:
        return None
    for event_type, keywords, score, base_confidence in rules:
        hits = sum(str(keyword).lower() in normalized for keyword in keywords)
        if hits <= 0:
            continue
        confidence = min(0.95, float(base_confidence) + 0.04 * hits)
        return {
            "event_type": event_type,
            "sentiment": _official_sentiment(float(score)),
            "impact_score": float(score),
            "confidence": confidence,
        }
    return None


def _official_sentiment(score: float) -> str:
    if score > 0.15:
        return "positive"
    if score < -0.15:
        return "negative"
    return "neutral"


def _decode_web_text(body: bytes) -> str:
    for encoding in ("utf-8", "gb18030", "gbk"):
        try:
            return body.decode(encoding)
        except UnicodeDecodeError:
            continue
    return body.decode("utf-8", errors="replace")


def _html_links_to_items(text: str, base_url: str) -> list[dict[str, object]]:
    items = []
    for match in re.finditer(r"<a\b[^>]*href=[\"']?([^\"'>\s]+)[\"']?[^>]*>(.*?)</a>", text, flags=re.IGNORECASE | re.DOTALL):
        href = unescape(match.group(1)).strip()
        title = _strip_html(match.group(2))
        if not href or href.lower().startswith(("javascript:", "#")):
            continue
        start = max(0, match.start() - 180)
        end = min(len(text), match.end() + 180)
        context = _strip_html(text[start:end])
        items.append({"title": title, "url": parse.urljoin(base_url, href), "context": context})
    if items:
        return items
    plain = _strip_html(text)
    lines = [line.strip() for line in re.split(r"[\r\n]+", plain) if line.strip()]
    return [{"title": line[:120], "url": base_url, "context": line} for line in lines[:120]]


def _json_items_to_links(text: str, base_url: str) -> list[dict[str, object]]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return []
    items: list[dict[str, object]] = []
    for item in _walk_json_objects(parsed):
        title = item.get("title") or item.get("name") or item.get("bt") or item.get("docTitle")
        if not title:
            continue
        url = item.get("url") or item.get("href") or item.get("link") or item.get("docpuburl") or base_url
        date = item.get("date") or item.get("time") or item.get("publishTime") or item.get("pubDate") or item.get("docreltime") or ""
        summary = item.get("summary") or item.get("content") or item.get("memo") or ""
        items.append({"title": str(title), "url": parse.urljoin(base_url, str(url)), "context": f"{date} {summary} {title}"})
    return items


def _walk_json_objects(value: object) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    if isinstance(value, dict):
        out.append(value)
        for child in value.values():
            out.extend(_walk_json_objects(child))
    elif isinstance(value, list):
        for child in value:
            out.extend(_walk_json_objects(child))
    return out


def _extract_official_date(text: str, fallback: pd.Timestamp) -> tuple[pd.Timestamp, str]:
    patterns = [
        r"(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})",
        r"(20\d{2})年(\d{1,2})月(\d{1,2})日",
        r"(20\d{2})(\d{2})(\d{2})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        parts = match.groups()
        try:
            return pd.Timestamp(year=int(parts[0]), month=int(parts[1]), day=int(parts[2])), "date_from_page"
        except ValueError:
            continue
    return pd.Timestamp(fallback).normalize(), "date_fallback_to_query_end"


def _extract_official_date(text: str, fallback: pd.Timestamp) -> tuple[pd.Timestamp, str]:
    normalized = (
        str(text)
        .replace("\u5e74", "-")
        .replace("\u6708", "-")
        .replace("\u65e5", " ")
    )
    for pattern in (r"(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})", r"(20\d{2})(\d{2})(\d{2})"):
        match = re.search(pattern, normalized)
        if not match:
            continue
        year, month, day = match.groups()
        try:
            return pd.Timestamp(year=int(year), month=int(month), day=int(day)), "date_from_page"
        except ValueError:
            continue
    return pd.Timestamp(fallback).normalize(), "date_fallback_to_query_end"


def _symbols_in_text(text: str, symbols: list[str]) -> list[str]:
    return sorted({symbol for symbol in symbols if symbol and symbol in text})


def _truncate_official_summary(value: str, limit: int) -> str:
    clean = _normalize_text(value)
    return clean if len(clean) <= limit else clean[: max(0, limit - 3)] + "..."


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
