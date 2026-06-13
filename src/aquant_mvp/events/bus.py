from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

import numpy as np
import pandas as pd

from aquant_mvp.sources import fetch_cninfo_announcements_direct, fetch_official_public_events, official_public_source_ids


REQUIRED_EVENT_COLUMNS = [
    "event_id",
    "source",
    "source_url",
    "published_at",
    "fetched_at",
    "related_symbols",
    "symbol",
    "title",
    "summary",
    "entity_link_method",
    "entity_link_confidence",
    "entity_link_keywords",
    "event_type",
    "sentiment",
    "impact_score",
    "confidence",
    "source_category",
    "source_reliability",
    "weighted_impact_score",
    "source_text_status",
    "source_text_length",
    "source_text_hash",
    "effective_date",
    "raw_hash",
    "quality_flag",
]

EVENT_FACTOR_NUMERIC_COLUMNS = [
    "event_count_3d",
    "event_count_20d",
    "positive_event_count",
    "negative_event_count",
    "event_risk_count",
    "event_impact_score",
    "event_weighted_impact_score",
    "event_confidence_mean",
    "event_reliability_mean",
    "event_high_reliability_count",
    "event_entity_link_confidence_mean",
    "latest_event_source_reliability",
    "latest_entity_link_confidence",
]

EVENT_FACTOR_CONTEXT_COLUMNS = [
    "latest_event_type",
    "latest_event_title",
    "latest_event_source",
    "latest_event_source_category",
    "latest_entity_link_method",
    "latest_entity_link_keywords",
]

EVENT_FACTOR_COLUMNS = EVENT_FACTOR_NUMERIC_COLUMNS + EVENT_FACTOR_CONTEXT_COLUMNS

EVENT_RISK_TYPES = {
    "regulatory_inquiry",
    "regulatory_penalty",
    "public_opinion_risk",
    "performance_miss",
    "litigation_risk",
    "export_control",
}


COMMODITY_CONTRACTS: dict[str, dict[str, object]] = {
    "copper": {"contract": "CU0", "name": "沪铜主连", "keywords": ["copper", "铜"]},
    "aluminum": {"contract": "AL0", "name": "沪铝主连", "keywords": ["aluminum", "铝"]},
    "gold": {"contract": "AU0", "name": "沪金主连", "keywords": ["gold", "黄金"]},
    "silver": {"contract": "AG0", "name": "沪银主连", "keywords": ["silver", "白银", "silver tin"]},
    "zinc": {"contract": "ZN0", "name": "沪锌主连", "keywords": ["zinc", "锌"]},
    "nickel": {"contract": "NI0", "name": "沪镍主连", "keywords": ["nickel", "镍"]},
    "tin": {"contract": "SN0", "name": "沪锡主连", "keywords": ["tin", "锡"]},
    "lithium": {"contract": "LC0", "name": "碳酸锂主连", "keywords": ["lithium", "锂", "battery"]},
    "silicon": {"contract": "SI0", "name": "工业硅主连", "keywords": ["silicon", "硅"]},
    "iron_ore": {"contract": "I0", "name": "铁矿石主连", "keywords": ["iron", "steel", "铁矿"]},
    "crude_oil": {"contract": "SC0", "name": "原油主连", "keywords": ["oil", "crude", "油气", "石油"]},
}

COMMODITY_PROXY_MAP: dict[str, list[str]] = {
    "rare_earth": ["copper", "aluminum"],
    "cobalt": ["nickel", "lithium"],
}

THEME_ENTITY_KEYWORDS: dict[str, list[str]] = {
    "ai_semiconductor": ["AI", "artificial intelligence", "算力", "半导体", "芯片", "先进封装", "光模块", "数据中心", "CPO"],
    "robotics_manufacturing": ["机器人", "人形机器人", "高端制造", "工业母机", "数控", "自动化", "激光"],
    "metals_energy": ["有色", "金属", "铜", "铝", "锌", "镍", "锡", "黄金", "白银", "稀土", "锂", "钴", "矿"],
    "power_battery": ["电力设备", "固态电池", "新能源", "储能", "光伏", "风电", "特高压", "电网", "锂电"],
    "defense_ship": ["军工", "航海", "船舶", "海工", "卫星", "商业航天", "低空经济", "无人机"],
    "medical_drug": ["创新药", "医药", "医疗器械", "CXO", "生物医药", "IVD", "临床", "医保"],
    "software_data": ["信创", "软件", "数据要素", "网络安全", "金融科技", "AI应用", "游戏", "传媒"],
    "consumer_export": ["消费电子", "家电", "出口", "PCB", "手机", "汽车电子"],
    "macro_trade": ["进出口", "关税", "出口管制", "汇率", "外贸", "商务部", "海关"],
}


@dataclass(frozen=True)
class EventBuildResult:
    raw_events: pd.DataFrame
    event_store: pd.DataFrame
    event_factors: pd.DataFrame
    evidence_markdown: str
    warnings: list[str]


def sync_public_events(
    symbols: list[str],
    start_date: str,
    end_date: str,
    source: str = "akshare",
    max_events_per_symbol: int = 80,
    fetch_announcement_text: bool = False,
    max_pages: int = 1,
) -> tuple[pd.DataFrame, list[str]]:
    normalized = [str(symbol).zfill(6) for symbol in symbols]
    warnings: list[str] = []
    if source == "sample":
        return _sample_events(normalized, start_date, end_date), warnings
    if source in {"cninfo_direct", "direct_cninfo", "cninfo"}:
        result = fetch_cninfo_announcements_direct(
            normalized,
            start_date,
            end_date,
            max_events_per_symbol=max_events_per_symbol,
            fetch_text=fetch_announcement_text,
        )
        return result.events, result.warnings
    if source in official_public_source_ids():
        result = fetch_official_public_events(
            normalized,
            start_date,
            end_date,
            source=source,
            max_events_per_source=max_events_per_symbol,
            fetch_text=fetch_announcement_text,
            max_pages_per_seed=max_pages,
        )
        return result.events, result.warnings
    events: list[dict[str, object]] = []
    try:
        import akshare as ak  # type: ignore
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"akshare unavailable: {exc}; using deterministic sample event fallback")
        return _sample_events(normalized, start_date, end_date), warnings

    for symbol in normalized:
        for loader_name, loader in [
            ("eastmoney_stock_news", lambda: ak.stock_news_em(symbol=symbol)),
            (
                "cninfo_disclosure",
                lambda: ak.stock_zh_a_disclosure_report_cninfo(
                    symbol=symbol,
                    market="沪深京",
                    start_date=_compact_date(start_date),
                    end_date=_compact_date(end_date),
                ),
            ),
        ]:
            try:
                raw = loader()
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"{symbol}: {loader_name} failed ({exc})")
                continue
            normalized_rows = _normalize_raw_events(raw, symbol, loader_name, start_date, end_date)
            events.extend(normalized_rows[:max_events_per_symbol])
    try:
        macro = ak.news_cctv(date=_compact_date(end_date))
        events.extend(_normalize_raw_events(macro, "", "cctv_macro", start_date, end_date)[:120])
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"macro cctv news failed ({exc})")
    commodity_events, commodity_warnings = sync_commodity_events(
        normalized,
        start_date,
        end_date,
        max_events_per_symbol=max_events_per_symbol,
        ak_module=ak,
    )
    events.extend(commodity_events.to_dict(orient="records"))
    warnings.extend(commodity_warnings)
    if not events:
        warnings.append("no public events fetched; using deterministic sample event fallback")
        return _sample_events(normalized, start_date, end_date), warnings
    frame = pd.DataFrame(events)
    return frame, warnings


def sync_commodity_events(
    symbols: list[str],
    start_date: str,
    end_date: str,
    shock_threshold: float = 0.03,
    max_events_per_symbol: int = 80,
    ak_module: object | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    """Build stock-linked commodity shock events from domestic futures data."""
    normalized = [str(symbol).zfill(6) for symbol in symbols]
    if not normalized:
        return pd.DataFrame(columns=["source", "source_url", "published_at", "symbol", "related_symbols", "title", "summary", "quality_flag"]), []
    warnings: list[str] = []
    try:
        ak = ak_module
        if ak is None:
            import akshare as ak  # type: ignore
    except Exception as exc:  # noqa: BLE001
        return pd.DataFrame(), [f"akshare unavailable for commodity events: {exc}"]

    symbol_map = commodity_symbol_map(normalized)
    symbol_map = {symbol: _expand_commodity_proxies(commodities) for symbol, commodities in symbol_map.items()}
    wanted_commodities = sorted({commodity for commodities in symbol_map.values() for commodity in commodities})
    rows: list[dict[str, object]] = []
    for commodity in wanted_commodities:
        meta = COMMODITY_CONTRACTS.get(commodity, {})
        contract = str(meta.get("contract", ""))
        if not contract:
            continue
        try:
            raw = ak.futures_main_sina(symbol=contract, start_date=_compact_date(start_date), end_date=_compact_date(end_date))
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"commodity {commodity}/{contract} failed ({exc})")
            continue
        shocks = _commodity_shock_rows(raw, commodity, contract, str(meta.get("name", commodity)), shock_threshold)
        if shocks.empty:
            continue
        linked_symbols = [symbol for symbol, commodities in symbol_map.items() if commodity in commodities]
        for symbol in linked_symbols:
            symbol_shocks = shocks.tail(max_events_per_symbol)
            for shock in symbol_shocks.to_dict(orient="records"):
                rows.append({**shock, "symbol": symbol, "related_symbols": symbol})
    return pd.DataFrame(rows), warnings


def _expand_commodity_proxies(commodities: list[str]) -> list[str]:
    expanded: set[str] = set()
    for commodity in commodities:
        if commodity in COMMODITY_CONTRACTS:
            expanded.add(commodity)
        expanded.update(COMMODITY_PROXY_MAP.get(commodity, []))
    return sorted(expanded)


def commodity_symbol_map(symbols: list[str]) -> dict[str, list[str]]:
    from aquant_mvp.universe import build_theme_universe

    normalized = [str(symbol).zfill(6) for symbol in symbols]
    try:
        universe = build_theme_universe("hot")
    except Exception:  # noqa: BLE001
        universe = pd.DataFrame()
    reason_by_symbol: dict[str, str] = {}
    if not universe.empty:
        temp = universe.copy()
        temp["symbol"] = temp["symbol"].astype(str).str.zfill(6)
        grouped = temp.groupby("symbol").agg(
            text=("reason", lambda values: " ".join(str(value) for value in values)),
            themes=("theme", lambda values: " ".join(str(value) for value in values)),
            names=("name", lambda values: " ".join(str(value) for value in values)),
        )
        reason_by_symbol = {
            symbol: f"{row.text} {row.themes} {row.names}".lower()
            for symbol, row in grouped.iterrows()
        }
    fallback = _fallback_symbol_commodity_map()
    out: dict[str, list[str]] = {}
    for symbol in normalized:
        text = reason_by_symbol.get(symbol, "")
        commodities = set(fallback.get(symbol, []))
        for commodity, meta in COMMODITY_CONTRACTS.items():
            for keyword in meta.get("keywords", []):
                if str(keyword).lower() in text:
                    commodities.add(commodity)
        if not commodities and any(key in text for key in ["metals", "有色", "mining", "rare_earth"]):
            commodities.update(["copper", "gold", "aluminum"])
        out[symbol] = sorted(commodities)
    return out


def build_event_store(raw_events: pd.DataFrame, symbols: list[str] | None = None) -> EventBuildResult:
    symbols = [str(symbol).zfill(6) for symbol in symbols or []]
    frame = raw_events.copy()
    if frame.empty:
        frame = pd.DataFrame(columns=REQUIRED_EVENT_COLUMNS)
    normalized = _complete_event_columns(frame, symbols)
    normalized = normalized.drop_duplicates(subset=["raw_hash", "symbol"], keep="last").reset_index(drop=True)
    event_factors = _build_event_factors(normalized)
    evidence = build_news_evidence_report(normalized, event_factors)
    warnings = [] if not normalized.empty else ["event_store_empty"]
    return EventBuildResult(
        raw_events=raw_events,
        event_store=normalized[REQUIRED_EVENT_COLUMNS],
        event_factors=event_factors,
        evidence_markdown=evidence,
        warnings=warnings,
    )


def write_event_outputs(result: EventBuildResult, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "raw_events": output_dir / "raw_events.csv",
        "event_store": output_dir / "event_store.csv",
        "event_factors": output_dir / "event_factors.csv",
        "news_evidence": output_dir / "news_evidence.md",
        "event_warnings": output_dir / "event_warnings.json",
    }
    result.raw_events.to_csv(paths["raw_events"], index=False)
    result.event_store.to_csv(paths["event_store"], index=False)
    result.event_factors.to_csv(paths["event_factors"], index=False)
    paths["news_evidence"].write_text(result.evidence_markdown, encoding="utf-8")
    paths["event_warnings"].write_text(json.dumps({"warnings": result.warnings}, ensure_ascii=False, indent=2), encoding="utf-8")
    return paths


def audit_event_coverage(event_store: pd.DataFrame, event_factors: pd.DataFrame, symbols: list[str]) -> pd.DataFrame:
    normalized = [str(symbol).zfill(6) for symbol in symbols]
    events = event_store.copy()
    factors = event_factors.copy()
    rows = []
    for symbol in normalized:
        symbol_events = events[events["symbol"].astype(str).str.zfill(6) == symbol] if not events.empty and "symbol" in events.columns else pd.DataFrame()
        symbol_factors = factors[factors["symbol"].astype(str).str.zfill(6) == symbol] if not factors.empty and "symbol" in factors.columns else pd.DataFrame()
        event_rows = int(len(symbol_events))
        factor_rows = int(len(symbol_factors))
        first_event = ""
        last_event = ""
        event_types = ""
        positive = 0
        negative = 0
        risk = 0
        avg_reliability = 0.0
        high_reliability = 0
        avg_link_confidence = 0.0
        link_methods = ""
        if not symbol_events.empty:
            dates = pd.to_datetime(symbol_events["published_at"], errors="coerce")
            first_event = str(dates.min().date()) if dates.notna().any() else ""
            last_event = str(dates.max().date()) if dates.notna().any() else ""
            event_types = ",".join(sorted(symbol_events["event_type"].astype(str).unique().tolist()))
            positive = int((symbol_events["sentiment"].astype(str) == "positive").sum())
            negative = int((symbol_events["sentiment"].astype(str) == "negative").sum())
            risk = int(symbol_events["event_type"].isin(EVENT_RISK_TYPES).sum())
            if "source_reliability" in symbol_events.columns:
                reliability = pd.to_numeric(symbol_events["source_reliability"], errors="coerce").fillna(0.0)
                avg_reliability = float(reliability.mean())
                high_reliability = int(reliability.ge(0.80).sum())
            if "entity_link_confidence" in symbol_events.columns:
                link_conf = pd.to_numeric(symbol_events["entity_link_confidence"], errors="coerce").fillna(0.0)
                avg_link_confidence = float(link_conf.mean())
            if "entity_link_method" in symbol_events.columns:
                link_methods = ",".join(sorted(symbol_events["entity_link_method"].astype(str).unique().tolist()))
        status = "ok"
        if event_rows == 0:
            status = "no_linked_news"
        elif event_rows < 3 or factor_rows == 0:
            status = "sparse"
        rows.append(
            {
                "symbol": symbol,
                "event_rows": event_rows,
                "event_factor_rows": factor_rows,
                "first_event": first_event,
                "last_event": last_event,
                "event_types": event_types,
                "positive_events": positive,
                "negative_events": negative,
                "risk_events": risk,
                "avg_source_reliability": avg_reliability,
                "high_reliability_events": high_reliability,
                "avg_entity_link_confidence": avg_link_confidence,
                "entity_link_methods": link_methods,
                "coverage_status": status,
            }
        )
    return pd.DataFrame(rows)


def build_news_evidence_report(event_store: pd.DataFrame, event_factors: pd.DataFrame, symbol: str | None = None) -> str:
    frame = event_store.copy()
    if symbol:
        frame = frame[frame["symbol"].astype(str).str.zfill(6) == str(symbol).zfill(6)]
    lines = [
        "# News And Event Evidence Report",
        "",
        "## Summary",
        "",
        f"- Events: {len(frame)}",
        f"- Symbols: {frame['symbol'].nunique() if 'symbol' in frame.columns and not frame.empty else 0}",
        "- Event factors are structured research inputs, not direct trading advice.",
        "",
    ]
    if not event_factors.empty:
        factors = event_factors.copy()
        if symbol:
            factors = factors[factors["symbol"].astype(str).str.zfill(6) == str(symbol).zfill(6)]
        latest = factors.sort_values("date").groupby("symbol").tail(1)
        lines.extend(["## Latest Event Factor Snapshot", ""])
        for row in latest.head(30).itertuples(index=False):
            lines.append(
                f"- `{row.symbol}` {row.date}: impact={row.event_impact_score:.3f}, "
                f"weighted={getattr(row, 'event_weighted_impact_score', 0.0):.3f}, "
                f"reliability={getattr(row, 'event_reliability_mean', 0.0):.2f}, "
                f"link={getattr(row, 'event_entity_link_confidence_mean', 0.0):.2f}, "
                f"positive={row.positive_event_count}, negative={row.negative_event_count}, risk={row.event_risk_count}"
            )
        lines.append("")
    if not frame.empty:
        announcement_mask = (
            frame["source"].astype(str).str.contains("cninfo|announcement|disclosure|notice", case=False, regex=True, na=False)
            | frame["event_type"].astype(str).str.contains("performance|regulatory|buyback|dividend|shareholder|ma_restructuring", case=False, regex=True, na=False)
        )
        announcements = frame[announcement_mask].sort_values("published_at", ascending=False).head(20)
        if not announcements.empty:
            lines.extend(["## Recent Major Announcement Summary", ""])
            for row in announcements.itertuples(index=False):
                summary = _truncate_text(str(getattr(row, "summary", "") or getattr(row, "title", "")), 180)
                lines.append(
                    f"- `{row.symbol}` {row.published_at} [{row.source}] {row.event_type}: "
                    f"link={getattr(row, 'entity_link_method', 'unknown')}/"
                    f"{float(getattr(row, 'entity_link_confidence', 0.0) or 0.0):.2f}; "
                    f"text={getattr(row, 'source_text_status', 'not_available')}/"
                    f"{int(float(getattr(row, 'source_text_length', 0) or 0))}; {summary}"
                )
            lines.append("")
    lines.extend(["## Evidence Items", ""])
    if frame.empty:
        lines.append("- No event evidence available.")
    else:
        for row in frame.sort_values("published_at", ascending=False).head(80).itertuples(index=False):
            lines.append(
                f"- `{row.symbol}` {row.published_at} [{row.source}] {row.event_type}/{row.sentiment} "
                f"impact={row.impact_score:.2f}, reliability={getattr(row, 'source_reliability', 0.0):.2f}: "
                f"link={getattr(row, 'entity_link_method', 'unknown')}/"
                f"{float(getattr(row, 'entity_link_confidence', 0.0) or 0.0):.2f} "
                f"{row.title} "
                f"text={getattr(row, 'source_text_status', 'not_available')}/"
                f"{int(float(getattr(row, 'source_text_length', 0) or 0))} "
                f"({row.source_url or 'no_url'})"
            )
    lines.extend(["", "## Guardrails", "", "- Unlinked news is excluded from individual-stock event factors.", "- Source failures must be written as warnings, not silently filled with fake events."])
    return "\n".join(lines)


def _truncate_text(value: str, limit: int) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    return value if len(value) <= limit else value[: max(0, limit - 3)] + "..."


def _normalize_raw_events(raw: pd.DataFrame, symbol: str, source: str, start_date: str, end_date: str) -> list[dict[str, object]]:
    if raw is None or raw.empty:
        return []
    frame = raw.copy()
    title_col = _first_matching_column(frame, ["标题", "title", "公告标题", "新闻标题", "内容", "summary"])
    time_col = _first_matching_column(frame, ["发布时间", "publish", "time", "日期", "公告时间", "date", "披露时间"])
    url_col = _first_matching_column(frame, ["链接", "url", "公告链接", "网址"])
    summary_col = _first_matching_column(frame, ["内容", "摘要", "summary", "新闻内容"])
    rows = []
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    for item in frame.to_dict(orient="records"):
        title = str(item.get(title_col, "") if title_col else "").strip()
        summary = str(item.get(summary_col, "") if summary_col else title).strip()
        if not title and summary:
            title = summary[:80]
        if not title:
            continue
        published = _parse_timestamp(item.get(time_col) if time_col else None, fallback=end)
        if published < start or published > end + pd.Timedelta(days=1):
            continue
        rows.append(
            {
                "source": source,
                "source_url": str(item.get(url_col, "") if url_col else ""),
                "published_at": published,
                "symbol": str(symbol).zfill(6) if symbol else "",
                "related_symbols": str(symbol).zfill(6) if symbol else "",
                "title": title,
                "summary": summary or title,
                "quality_flag": "ok",
            }
        )
    return rows


def _complete_event_columns(frame: pd.DataFrame, symbols: list[str]) -> pd.DataFrame:
    out = frame.copy()
    fetched_at = pd.Timestamp.now().isoformat(timespec="seconds")
    for column in [
        "source",
        "source_url",
        "title",
        "summary",
        "quality_flag",
        "source_text_status",
        "source_text_hash",
        "entity_link_method",
        "entity_link_keywords",
    ]:
        if column not in out.columns:
            out[column] = ""
    if "entity_link_confidence" not in out.columns:
        out["entity_link_confidence"] = 0.0
    out["entity_link_confidence"] = pd.to_numeric(out["entity_link_confidence"], errors="coerce").fillna(0.0)
    if "source_text_length" not in out.columns:
        out["source_text_length"] = 0
    out["source_text_length"] = pd.to_numeric(out["source_text_length"], errors="coerce").fillna(0).astype(int)
    out["source_text_status"] = out["source_text_status"].replace("", "not_available")
    if "published_at" not in out.columns:
        out["published_at"] = pd.Timestamp.now()
    out["published_at"] = pd.to_datetime(out["published_at"], errors="coerce").fillna(pd.Timestamp.now())
    out["fetched_at"] = fetched_at
    if "symbol" not in out.columns:
        out["symbol"] = ""
    if "related_symbols" not in out.columns:
        out["related_symbols"] = out["symbol"]
    out = _expand_entity_links(out, symbols)
    out = out[out["symbol"].astype(str).str.fullmatch(r"\d{6}", na=False)].copy()
    if out.empty:
        for column in REQUIRED_EVENT_COLUMNS:
            if column not in out.columns:
                out[column] = pd.Series(dtype="object")
        return out[REQUIRED_EVENT_COLUMNS]
    classified = out.apply(lambda row: _classify_event(str(row.get("title", "")), str(row.get("summary", ""))), axis=1)
    for column in ["event_type", "sentiment", "impact_score", "confidence"]:
        if column not in out.columns:
            out[column] = pd.NA
    out["event_type"] = out["event_type"].fillna(pd.Series([item["event_type"] for item in classified], index=out.index))
    out["sentiment"] = out["sentiment"].fillna(pd.Series([item["sentiment"] for item in classified], index=out.index))
    out["impact_score"] = pd.to_numeric(out["impact_score"], errors="coerce").fillna(
        pd.Series([item["impact_score"] for item in classified], index=out.index)
    )
    out["confidence"] = pd.to_numeric(out["confidence"], errors="coerce").fillna(
        pd.Series([item["confidence"] for item in classified], index=out.index)
    )
    source_meta = out.apply(_source_reliability_meta, axis=1)
    out["source_category"] = [item["source_category"] for item in source_meta]
    if "source_reliability" not in out.columns:
        out["source_reliability"] = pd.NA
    computed_reliability = pd.Series([item["source_reliability"] for item in source_meta], index=out.index)
    out["source_reliability"] = pd.to_numeric(out["source_reliability"], errors="coerce").fillna(computed_reliability).clip(0.05, 1.0)
    out["weighted_impact_score"] = (
        pd.to_numeric(out["impact_score"], errors="coerce").fillna(0.0)
        * pd.to_numeric(out["confidence"], errors="coerce").fillna(0.0)
        * pd.to_numeric(out["source_reliability"], errors="coerce").fillna(0.0)
    )
    out["effective_date"] = out["published_at"].dt.normalize()
    out["raw_hash"] = out.apply(_event_hash, axis=1)
    out["event_id"] = out["raw_hash"].str[:16]
    out["quality_flag"] = out["quality_flag"].replace("", "ok")
    return out


def _expand_entity_links(frame: pd.DataFrame, symbols: list[str]) -> pd.DataFrame:
    if frame.empty:
        return frame
    normalized_symbols = [str(symbol).zfill(6) for symbol in symbols]
    profiles = _symbol_entity_profiles(normalized_symbols)
    rows: list[pd.Series] = []
    for _idx, row in frame.iterrows():
        links = _entity_links_for_event(row, normalized_symbols, profiles)
        if not links:
            continue
        related = ";".join(sorted({link["symbol"] for link in links}))
        for link in links:
            item = row.copy()
            item["symbol"] = link["symbol"]
            item["related_symbols"] = related
            item["entity_link_method"] = link["method"]
            item["entity_link_confidence"] = link["confidence"]
            item["entity_link_keywords"] = link["keywords"]
            rows.append(item)
    return pd.DataFrame(rows).reset_index(drop=True) if rows else frame.iloc[0:0].copy()


def _entity_links_for_event(
    row: pd.Series,
    symbols: list[str],
    profiles: dict[str, dict[str, object]],
    max_links: int = 120,
) -> list[dict[str, object]]:
    text = _event_link_text(row)
    links: dict[str, dict[str, object]] = {}
    existing = _linked_symbol(row, symbols)
    if existing:
        links[existing] = {"symbol": existing, "method": "explicit_symbol", "confidence": 1.0, "keywords": existing}
    for symbol in _extract_related_symbol_list(str(row.get("related_symbols", "")), symbols):
        links.setdefault(symbol, {"symbol": symbol, "method": "provided_related_symbols", "confidence": 0.95, "keywords": symbol})
    for symbol in symbols:
        if symbol in text:
            links.setdefault(symbol, {"symbol": symbol, "method": "code_mention", "confidence": 0.95, "keywords": symbol})
        profile = profiles.get(symbol, {})
        name = str(profile.get("name", "")).strip().lower()
        if name and len(name) >= 3 and name in text.lower():
            links.setdefault(symbol, {"symbol": symbol, "method": "name_mention", "confidence": 0.85, "keywords": name})
    if not links:
        for symbol, profile in profiles.items():
            hits = _keyword_hits(text, profile.get("keywords", []))
            if not hits:
                continue
            confidence = min(0.78, 0.50 + 0.07 * len(hits))
            links[symbol] = {
                "symbol": symbol,
                "method": "theme_keyword",
                "confidence": confidence,
                "keywords": ",".join(hits[:8]),
            }
    return sorted(links.values(), key=lambda item: (-float(item["confidence"]), str(item["symbol"])))[:max_links]


def _linked_symbol(row: pd.Series, symbols: list[str]) -> str:
    existing = str(row.get("symbol", "")).strip().replace(".", "")[-6:]
    if re.fullmatch(r"\d{6}", existing):
        return existing.zfill(6)
    text = _event_link_text(row)
    for symbol in symbols:
        if symbol in text:
            return symbol
    return ""


def _event_link_text(row: pd.Series) -> str:
    return f"{row.get('title', '')} {row.get('summary', '')} {row.get('source', '')} {row.get('quality_flag', '')}"


def _extract_related_symbol_list(value: str, symbols: list[str]) -> list[str]:
    wanted = set(symbols)
    out = []
    for item in re.findall(r"\d{6}", value or ""):
        symbol = item.zfill(6)
        if symbol in wanted:
            out.append(symbol)
    return sorted(set(out))


def _symbol_entity_profiles(symbols: list[str]) -> dict[str, dict[str, object]]:
    try:
        from aquant_mvp.universe import build_theme_universe

        universe = build_theme_universe("hot")
    except Exception:  # noqa: BLE001
        universe = pd.DataFrame()
    profiles: dict[str, dict[str, object]] = {symbol: {"name": "", "keywords": []} for symbol in symbols}
    if universe.empty:
        return profiles
    frame = universe.copy()
    frame["symbol"] = frame["symbol"].astype(str).str.zfill(6)
    frame = frame[frame["symbol"].isin(symbols)]
    if frame.empty:
        return profiles
    grouped = frame.groupby("symbol", sort=False).agg(
        name=("name", lambda values: str(next(iter(values), ""))),
        text=("reason", lambda values: " ".join(str(value) for value in values)),
        themes=("theme", lambda values: " ".join(str(value) for value in values)),
    )
    for symbol, row in grouped.iterrows():
        source_text = f"{row.name} {row.text} {row.themes}"
        profiles[str(symbol).zfill(6)] = {"name": str(row.name), "keywords": _profile_keywords(source_text)}
    return profiles


def _profile_keywords(text: str) -> list[str]:
    lower = text.lower()
    keywords: set[str] = set()
    for bucket, terms in THEME_ENTITY_KEYWORDS.items():
        bucket_key = bucket.replace("_", " ")
        if bucket in lower or bucket_key in lower or any(str(term).lower() in lower for term in terms):
            keywords.update(str(term) for term in terms)
    for token in re.split(r"[^A-Za-z0-9]+", lower):
        if len(token) >= 5:
            keywords.add(token)
    return sorted(keywords)


def _keyword_hits(text: str, keywords: object) -> list[str]:
    lowered = text.lower()
    hits = []
    for keyword in keywords if isinstance(keywords, list) else []:
        key = str(keyword).strip()
        if key and key.lower() in lowered:
            hits.append(key)
    return sorted(set(hits))


def _classify_event(title: str, summary: str) -> dict[str, object]:
    text = f"{title} {summary}"
    event_rules = [
        ("performance_beat", ["预增", "增长", "扭亏", "超预期", "大增", "净利润增加"], 0.75),
        ("performance_miss", ["预减", "亏损", "下降", "不及预期", "大幅减少"], -0.75),
        ("order_contract", ["中标", "合同", "订单", "采购", "合作协议"], 0.55),
        ("ma_restructuring", ["并购", "重组", "收购", "注入资产"], 0.45),
        ("shareholder_change", ["减持", "增持", "股东", "解禁"], -0.15),
        ("buyback_dividend", ["回购", "分红", "派息", "注销股份"], 0.45),
        ("regulatory_inquiry", ["问询", "监管函", "处罚", "立案", "调查", "警示"], -0.70),
        ("capacity_operation", ["投产", "停产", "扩产", "复产", "产能"], 0.25),
        ("commodity_shock", ["铜", "黄金", "锂", "稀土", "煤", "油", "期货", "库存", "价格"], 0.20),
        ("industry_policy", ["政策", "补贴", "规划", "监管", "出口管制"], 0.10),
        ("fund_flow", ["龙虎榜", "北向", "融资", "主力资金", "大单"], 0.15),
        ("public_opinion_risk", ["舆情", "事故", "诉讼", "纠纷", "风险提示"], -0.55),
    ]
    for event_type, keywords, score in event_rules:
        if any(keyword in text for keyword in keywords):
            confidence = min(0.95, 0.55 + 0.08 * sum(keyword in text for keyword in keywords))
            return {"event_type": event_type, "sentiment": _sentiment(score), "impact_score": float(score), "confidence": float(confidence)}
    positive = ["上涨", "突破", "创新高", "利好", "改善"]
    negative = ["下跌", "破位", "利空", "风险", "承压"]
    score = 0.1 * sum(word in text for word in positive) - 0.1 * sum(word in text for word in negative)
    return {"event_type": "general_news", "sentiment": _sentiment(score), "impact_score": float(np.clip(score, -0.35, 0.35)), "confidence": 0.35}


def _source_reliability_meta(row: pd.Series) -> dict[str, object]:
    source = str(row.get("source", "")).lower()
    flag = str(row.get("quality_flag", "")).lower()
    url = str(row.get("source_url", "")).lower()
    text = " ".join([source, flag, url])
    if "sample" in text:
        return {"source_category": "sample_demo", "source_reliability": 0.40}
    if any(key in text for key in ["cninfo", "disclosure", "announcement", "notice", "sse", "szse", "bse", "csrc", "exchange", "regulator"]):
        return {"source_category": "official_disclosure", "source_reliability": 0.95}
    if any(key in text for key in ["pbc", "pboc", "ndrc", "miit", "mofcom", "customs", "gov.cn"]):
        return {"source_category": "official_policy_macro", "source_reliability": 0.90}
    if any(key in text for key in ["futures", "sina", "commodity_shock", "market_data"]):
        return {"source_category": "market_data", "source_reliability": 0.75}
    if any(key in text for key in ["cctv", "xinhua", "official_media"]):
        return {"source_category": "official_media", "source_reliability": 0.80}
    if any(key in text for key in ["eastmoney", "stock_news", "netease", "qq", "tencent", "finance_news"]):
        return {"source_category": "public_finance_media", "source_reliability": 0.65}
    if url:
        return {"source_category": "public_web", "source_reliability": 0.55}
    return {"source_category": "unknown", "source_reliability": 0.45}


def _sentiment(score: float) -> str:
    if score > 0.15:
        return "positive"
    if score < -0.15:
        return "negative"
    return "neutral"


def _commodity_shock_rows(
    raw: pd.DataFrame,
    commodity: str,
    contract: str,
    display_name: str,
    shock_threshold: float,
) -> pd.DataFrame:
    if raw is None or raw.empty:
        return pd.DataFrame()
    frame = raw.copy()
    date_col = _first_matching_column(frame, ["日期", "date"])
    close_col = _first_matching_column(frame, ["收盘价", "close"])
    volume_col = _first_matching_column(frame, ["成交量", "volume"])
    if date_col is None or close_col is None:
        return pd.DataFrame()
    frame["date"] = pd.to_datetime(frame[date_col], errors="coerce")
    frame["close"] = pd.to_numeric(frame[close_col], errors="coerce")
    frame["volume"] = pd.to_numeric(frame[volume_col], errors="coerce") if volume_col else 0.0
    frame = frame.dropna(subset=["date", "close"]).sort_values("date")
    if frame.empty:
        return pd.DataFrame()
    frame["return_1d"] = frame["close"].pct_change()
    frame["return_5d"] = frame["close"].pct_change(5)
    shock = frame[(frame["return_1d"].abs() >= shock_threshold) | (frame["return_5d"].abs() >= shock_threshold * 1.8)].copy()
    rows: list[dict[str, object]] = []
    for row in shock.itertuples(index=False):
        ret1 = float(getattr(row, "return_1d", 0.0) or 0.0)
        ret5 = float(getattr(row, "return_5d", 0.0) or 0.0)
        dominant = ret1 if abs(ret1) >= abs(ret5) else ret5
        impact = float(np.clip(dominant * 8.0, -0.85, 0.85))
        direction = "上涨" if dominant >= 0 else "下跌"
        date = pd.Timestamp(getattr(row, "date"))
        close = float(getattr(row, "close"))
        title = f"{display_name}价格{direction}触发商品冲击"
        summary = (
            f"{display_name}({contract}) {date.date()} 收盘 {close:.4g}; "
            f"1日涨跌 {ret1:.2%}, 5日涨跌 {ret5:.2%}. "
            "该事件按产业链映射进入相关股票的事件因子。"
        )
        rows.append(
            {
                "source": "akshare_futures_main_sina",
                "source_url": "https://vip.stock.finance.sina.com.cn/quotes_service/view/qihuohangqing.html",
                "published_at": date,
                "title": title,
                "summary": summary,
                "event_type": "commodity_shock",
                "sentiment": _sentiment(impact),
                "impact_score": impact,
                "confidence": 0.70,
                "quality_flag": f"commodity_shock:{commodity}:{contract}",
            }
        )
    return pd.DataFrame(rows)


def _fallback_symbol_commodity_map() -> dict[str, list[str]]:
    return {
        "000630": ["copper", "gold", "silver"],
        "000737": ["copper"],
        "000807": ["aluminum"],
        "000831": ["rare_earth"],
        "000878": ["copper"],
        "000933": ["aluminum"],
        "000960": ["tin", "zinc"],
        "000975": ["gold", "silver"],
        "002155": ["gold", "silver"],
        "002203": ["copper"],
        "002237": ["gold", "silver"],
        "002460": ["lithium"],
        "002466": ["lithium"],
        "002497": ["lithium"],
        "002532": ["aluminum"],
        "002738": ["lithium"],
        "002756": ["lithium"],
        "300390": ["lithium"],
        "300618": ["cobalt", "nickel"],
        "300697": ["copper"],
        "301219": ["copper", "cobalt"],
        "600111": ["rare_earth"],
        "600219": ["aluminum"],
        "600362": ["copper", "gold", "silver"],
        "600489": ["gold"],
        "600497": ["zinc"],
        "600547": ["gold"],
        "600988": ["gold"],
        "601168": ["copper", "zinc"],
        "601600": ["aluminum"],
        "601609": ["copper"],
        "601899": ["copper", "gold", "lithium"],
        "603799": ["cobalt", "nickel", "lithium"],
        "603993": ["copper", "cobalt"],
    }


def _build_event_factors(event_store: pd.DataFrame) -> pd.DataFrame:
    if event_store.empty:
        return pd.DataFrame(
            columns=[
                "date",
                "symbol",
                "event_count_3d",
                "event_count_20d",
                "positive_event_count",
                "negative_event_count",
                "event_risk_count",
                "event_impact_score",
                "event_weighted_impact_score",
                "event_confidence_mean",
                "event_reliability_mean",
                "event_high_reliability_count",
                "event_entity_link_confidence_mean",
                "latest_event_source_reliability",
                "latest_entity_link_confidence",
                "latest_event_type",
                "latest_event_title",
                "latest_event_source",
                "latest_event_source_category",
                "latest_entity_link_method",
                "latest_entity_link_keywords",
            ]
        )
    frame = event_store.copy()
    frame["date"] = pd.to_datetime(frame["effective_date"]).dt.normalize()
    rows = []
    for symbol, part in frame.groupby("symbol", sort=True):
        dates = pd.date_range(part["date"].min(), part["date"].max(), freq="B")
        for date in dates:
            trailing20 = part[(part["date"] <= date) & (part["date"] >= date - pd.Timedelta(days=30))]
            trailing3 = part[(part["date"] <= date) & (part["date"] >= date - pd.Timedelta(days=5))]
            if trailing20.empty:
                continue
            latest = trailing20.sort_values("published_at").iloc[-1]
            decay_days = (date - pd.to_datetime(trailing20["date"])).dt.days.clip(lower=0)
            weights = np.exp(-decay_days / 7.0)
            confidence = pd.to_numeric(trailing20["confidence"], errors="coerce").fillna(0.0).clip(0.0, 1.0)
            reliability_raw = (
                trailing20["source_reliability"]
                if "source_reliability" in trailing20.columns
                else pd.Series(0.45, index=trailing20.index)
            )
            reliability = pd.to_numeric(reliability_raw, errors="coerce").fillna(0.45).clip(0.05, 1.0)
            impact_series = pd.to_numeric(trailing20["impact_score"], errors="coerce").fillna(0.0)
            weighted_raw = (
                trailing20["weighted_impact_score"]
                if "weighted_impact_score" in trailing20.columns
                else impact_series * confidence * reliability
            )
            weighted_impact_series = pd.to_numeric(
                weighted_raw,
                errors="coerce",
            ).fillna(0.0)
            impact = float(np.average(impact_series, weights=weights))
            weighted_event_impact = float(np.average(weighted_impact_series, weights=weights))
            reliability_mean = float(np.average(reliability, weights=weights))
            link_confidence_raw = (
                trailing20["entity_link_confidence"]
                if "entity_link_confidence" in trailing20.columns
                else pd.Series(0.0, index=trailing20.index)
            )
            link_confidence = pd.to_numeric(link_confidence_raw, errors="coerce").fillna(0.0).clip(0.0, 1.0)
            link_confidence_mean = float(np.average(link_confidence, weights=weights))
            rows.append(
                {
                    "date": date,
                    "symbol": symbol,
                    "event_count_3d": int(len(trailing3)),
                    "event_count_20d": int(len(trailing20)),
                    "positive_event_count": int((trailing20["sentiment"] == "positive").sum()),
                    "negative_event_count": int((trailing20["sentiment"] == "negative").sum()),
                    "event_risk_count": int(trailing20["event_type"].isin(EVENT_RISK_TYPES).sum()),
                    "event_impact_score": impact,
                    "event_weighted_impact_score": weighted_event_impact,
                    "event_confidence_mean": float(confidence.mean()),
                    "event_reliability_mean": reliability_mean,
                    "event_high_reliability_count": int(reliability.ge(0.80).sum()),
                    "event_entity_link_confidence_mean": link_confidence_mean,
                    "latest_event_source_reliability": float(latest.get("source_reliability", 0.0) or 0.0),
                    "latest_entity_link_confidence": float(latest.get("entity_link_confidence", 0.0) or 0.0),
                    "latest_event_type": str(latest["event_type"]),
                    "latest_event_title": str(latest["title"])[:160],
                    "latest_event_source": str(latest.get("source", "")),
                    "latest_event_source_category": str(latest.get("source_category", "")),
                    "latest_entity_link_method": str(latest.get("entity_link_method", "")),
                    "latest_entity_link_keywords": str(latest.get("entity_link_keywords", ""))[:160],
                }
            )
    return pd.DataFrame(rows)


def _sample_events(symbols: list[str], start_date: str, end_date: str) -> pd.DataFrame:
    end = pd.Timestamp(end_date)
    rows = []
    templates = [
        ("公告", "{symbol} 发布经营进展公告，订单合同和产能信息需要继续跟踪。", "sample_announcement"),
        ("行业", "有色金属与新能源产业链价格波动，对相关股票形成商品价格冲击。", "sample_industry_news"),
        ("风险", "{symbol} 出现舆情风险提示，需降低事件置信度。", "sample_risk_news"),
    ]
    for idx, symbol in enumerate(symbols):
        for offset, (prefix, template, source) in enumerate(templates):
            published = end - pd.Timedelta(days=idx + offset * 3)
            rows.append(
                {
                    "source": source,
                    "source_url": "",
                    "published_at": published,
                    "symbol": symbol,
                    "related_symbols": symbol,
                    "title": f"{prefix}: " + template.format(symbol=symbol),
                    "summary": template.format(symbol=symbol),
                    "quality_flag": "sample_fallback",
                }
            )
    policy_templates = [
        (
            "sample_policy_news",
            "政策支持AI算力、半导体、先进封装、数据中心和光模块产业链。",
            "AI compute and semiconductor policy event without explicit stock code.",
        ),
        (
            "sample_policy_news",
            "有色金属、铜、黄金、锂和稀土资源产业链价格与供给政策受到关注。",
            "Metals and energy-materials policy event without explicit stock code.",
        ),
    ]
    for offset, (source, title, summary) in enumerate(policy_templates, start=1):
        rows.append(
            {
                "source": source,
                "source_url": "",
                "published_at": end - pd.Timedelta(days=offset),
                "symbol": "",
                "related_symbols": "",
                "title": title,
                "summary": summary,
                "quality_flag": "sample_macro_policy_unlinked",
            }
        )
    return pd.DataFrame(rows)


def _first_matching_column(frame: pd.DataFrame, names: list[str]) -> str | None:
    lowered = {str(column).lower(): column for column in frame.columns}
    for name in names:
        lower = name.lower()
        for key, column in lowered.items():
            if lower in key:
                return str(column)
    return None


def _parse_timestamp(value: object, fallback: pd.Timestamp) -> pd.Timestamp:
    if value is None or str(value).strip() == "":
        return fallback
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return fallback
    return pd.Timestamp(parsed)


def _event_hash(row: pd.Series) -> str:
    payload = "|".join(str(row.get(column, "")) for column in ["source", "symbol", "published_at", "title", "source_url"])
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def _compact_date(value: str) -> str:
    return str(value).replace("-", "")
