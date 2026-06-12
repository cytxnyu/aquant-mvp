from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import importlib.util
import os
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class SourceCapability:
    source: str
    domestic: bool
    installed: bool
    credential_ready: bool
    free_level: str
    tables: str
    frequencies: str
    point_in_time: str
    start_year_estimate: str
    limitations: str


def discover_domestic_sources() -> pd.DataFrame:
    capabilities = [
        SourceCapability(
            source="akshare",
            domestic=True,
            installed=_installed("akshare"),
            credential_ready=True,
            free_level="public_free",
            tables="daily_bar,minute_bar,industry,concept,moneyflow,northbound,dragon_tiger,announcement_proxy",
            frequencies="daily,minute,spot",
            point_in_time="partial",
            start_year_estimate="varies_by_endpoint",
            limitations="public endpoints can fail or change schema; PIT metadata is incomplete",
        ),
        SourceCapability(
            source="baostock",
            domestic=True,
            installed=_installed("baostock"),
            credential_ready=True,
            free_level="public_free",
            tables="daily_bar,adj_factor,st_flag,suspension_proxy,trade_calendar,index_member,financial",
            frequencies="daily",
            point_in_time="partial",
            start_year_estimate="1990s_for_some_daily_data",
            limitations="requires login session; no full announcement text; minute data unavailable",
        ),
        SourceCapability(
            source="tushare_free",
            domestic=True,
            installed=_installed("tushare"),
            credential_ready=bool(os.getenv("TUSHARE_TOKEN", "").strip()),
            free_level="token_free_limited",
            tables="stock_basic,trade_calendar,daily_bar,financial,margin,index_member,delist",
            frequencies="daily",
            point_in_time="partial",
            start_year_estimate="varies_by_permission",
            limitations="free quota and fields vary by token score; token required",
        ),
        SourceCapability(
            source="cninfo",
            domestic=True,
            installed=True,
            credential_ready=True,
            free_level="public_free",
            tables="announcement,annual_report,financial_report_pdf",
            frequencies="event",
            point_in_time="announce_date_available",
            start_year_estimate="varies_by_issuer",
            limitations="PDF/HTML parsing is noisy; structured fields need extraction",
        ),
        SourceCapability(
            source="eastmoney_public",
            domestic=True,
            installed=True,
            credential_ready=True,
            free_level="public_free",
            tables="moneyflow,concept,sector,valuation_proxy,northbound_proxy",
            frequencies="daily,spot",
            point_in_time="partial",
            start_year_estimate="varies_by_endpoint",
            limitations="unofficial endpoints can change; historical depth varies",
        ),
        SourceCapability(
            source="qmt_readonly",
            domestic=True,
            installed=_installed("xtquant"),
            credential_ready=_installed("xtquant"),
            free_level="local_client_required",
            tables="quote,account,position,order,trade,reconcile",
            frequencies="realtime,account_snapshot",
            point_in_time="runtime_snapshot",
            start_year_estimate="local_cache_or_broker",
            limitations="requires local MiniQMT/XtQuant and broker account; no live submit in this project",
        ),
    ]
    frame = pd.DataFrame([asdict(item) for item in capabilities])
    frame["discovered_at"] = datetime.now().isoformat(timespec="seconds")
    return frame


def write_source_coverage(output_dir: Path, frame: pd.DataFrame) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "free_source_coverage.csv"
    md_path = output_dir / "free_source_coverage.md"
    frame.to_csv(csv_path, index=False)
    rows = [
        "# Free Domestic Source Coverage",
        "",
        "| source | installed | credential_ready | tables | PIT | limitations |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in frame.itertuples(index=False):
        rows.append(
            f"| {row.source} | {row.installed} | {row.credential_ready} | {row.tables} | "
            f"{row.point_in_time} | {row.limitations} |"
        )
    rows.append("")
    rows.append("This report is a capability map, not a guarantee of endpoint availability on a given day.")
    md_path.write_text("\n".join(rows), encoding="utf-8")
    return md_path


def _installed(module: str) -> bool:
    return importlib.util.find_spec(module) is not None
