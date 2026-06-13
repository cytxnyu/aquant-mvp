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
    source_group: str = "market_data"
    implementation_status: str = "implemented"
    access_method: str = "python_adapter"
    impact_domain: str = "price_volume"
    event_types: str = ""
    priority: str = "medium"
    gap_status: str = "usable_with_limitations"
    probe_supported: bool = False


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
            source_group="multi_source_data",
            implementation_status="implemented",
            access_method="akshare_adapter",
            impact_domain="market,sector,capital_flow,news_proxy,commodity",
            event_types="market_data,news_proxy,moneyflow,dragon_tiger,commodity_shock",
            priority="high",
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
            source_group="market_data",
            implementation_status="implemented",
            access_method="baostock_adapter",
            impact_domain="price_volume,financial,index_member",
            event_types="daily_bar,financial,st_flag,index_member",
            priority="high",
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
            source_group="multi_source_data",
            implementation_status="implemented_if_token_ready",
            access_method="tushare_adapter",
            impact_domain="market,financial,margin,index",
            event_types="daily_bar,financial,margin,delist,index_member",
            priority="high",
            gap_status="credential_or_quota_limited",
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
            source_group="announcement",
            implementation_status="implemented_via_public_event_bus",
            access_method="akshare_or_direct_public_endpoint",
            impact_domain="company_announcement,earnings,governance,event_risk",
            event_types="announcement,annual_report,earnings_preannouncement,regulatory_inquiry,mna,lawsuit,repurchase",
            priority="critical",
        ),
        SourceCapability(
            source="cninfo_direct",
            domestic=True,
            installed=True,
            credential_ready=True,
            free_level="public_free",
            tables="announcement_metadata,direct_source_url,announce_date",
            frequencies="event",
            point_in_time="announce_date_available",
            start_year_estimate="varies_by_issuer",
            limitations="direct public endpoint can rate-limit or change schema; PDF body parsing is not yet implemented",
            source_group="announcement",
            implementation_status="implemented_metadata_text_optional",
            access_method="direct_http_public_endpoint",
            impact_domain="company_announcement,earnings,governance,event_risk",
            event_types="announcement_metadata,announcement_text_optional",
            priority="critical",
            probe_supported=True,
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
            source_group="news_capital_flow",
            implementation_status="partial_via_akshare_wrappers",
            access_method="public_page_or_akshare_wrapper",
            impact_domain="moneyflow,sector_heat,concept_heat,stock_news",
            event_types="stock_news,moneyflow,concept_heat,dragon_tiger,northbound_proxy",
            priority="critical",
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
            source_group="broker_readonly",
            implementation_status="readonly_adapter_live_blocked",
            access_method="local_xtquant_client",
            impact_domain="realtime_quote,account,position,reconcile",
            event_types="quote,account_snapshot,position,order_query,trade_query",
            priority="high",
            gap_status="local_client_required",
        ),
        *[
            SourceCapability(
                source=source,
                domestic=True,
                installed=True,
                credential_ready=True,
                free_level="public_free",
                tables=tables,
                frequencies="event,daily",
                point_in_time="published_at_or_announce_date_available",
                start_year_estimate="varies_by_public_site",
                limitations=limitations,
                source_group=group,
                implementation_status=status,
                access_method="direct_public_web_index_adapter"
                if str(status).startswith("implemented_official_index")
                else "direct_public_web_pending_adapter",
                impact_domain=domain,
                event_types=events,
                priority=priority,
                gap_status=gap,
                probe_supported=True,
            )
            for source, group, tables, domain, events, status, priority, gap, limitations in _public_news_policy_sources()
        ],
        *[
            SourceCapability(
                source=source,
                domestic=True,
                installed=True,
                credential_ready=True,
                free_level="public_free",
                tables=tables,
                frequencies="daily,event",
                point_in_time="trade_date_or_published_at_available",
                start_year_estimate="varies_by_exchange",
                limitations=limitations,
                source_group="commodity_exchange",
                implementation_status=status,
                access_method="public_exchange_page_pending_direct_adapter",
                impact_domain=domain,
                event_types=events,
                priority=priority,
                gap_status=gap,
                probe_supported=True,
            )
            for source, tables, domain, events, status, priority, gap, limitations in _public_commodity_sources()
        ],
    ]
    frame = pd.DataFrame([asdict(item) for item in capabilities])
    frame["discovered_at"] = datetime.now().isoformat(timespec="seconds")
    frame["ready_for_event_factor"] = frame["implementation_status"].astype(str).str.contains("implemented|partial", regex=True) & frame["credential_ready"].astype(bool)
    frame["requires_followup"] = ~frame["ready_for_event_factor"] | frame["gap_status"].astype(str).str.contains("limited|pending|required|unavailable", regex=True)
    return frame


def write_source_coverage(output_dir: Path, frame: pd.DataFrame) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "free_source_coverage.csv"
    md_path = output_dir / "free_source_coverage.md"
    gap_csv = output_dir / "source_gap_report.csv"
    gap_md = output_dir / "source_gap_report.md"
    frame.to_csv(csv_path, index=False)
    _source_gap_report(frame).to_csv(gap_csv, index=False)
    rows = [
        "# Free Domestic Source Coverage",
        "",
        "| source | group | status | installed | credential_ready | priority | PIT | ready_for_event_factor | limitations |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in frame.itertuples(index=False):
        rows.append(
            f"| {row.source} | {row.source_group} | {row.implementation_status} | {row.installed} | "
            f"{row.credential_ready} | {row.priority} | {row.point_in_time} | {row.ready_for_event_factor} | "
            f"{row.limitations} |"
        )
    rows.append("")
    rows.append("This report is a capability map, not a guarantee of endpoint availability on a given day.")
    md_path.write_text("\n".join(rows), encoding="utf-8")
    _write_gap_markdown(gap_md, frame)
    return md_path


def _source_gap_report(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["source_group", "sources", "ready_sources", "critical_gaps", "followup_sources"])
    rows = []
    for group, part in frame.groupby("source_group", sort=True):
        ready = part[part["ready_for_event_factor"]]
        followup = part[part["requires_followup"]]
        critical = followup[followup["priority"].isin(["critical", "high"])]
        rows.append(
            {
                "source_group": group,
                "sources": int(len(part)),
                "ready_sources": int(len(ready)),
                "critical_gaps": int(len(critical)),
                "followup_sources": ";".join(critical["source"].astype(str).tolist()[:20]),
                "gap_notes": "; ".join(_unique_notes(critical["limitations"].astype(str).tolist())[:5]),
            }
        )
    return pd.DataFrame(rows).sort_values(["critical_gaps", "source_group"], ascending=[False, True]).reset_index(drop=True)


def _write_gap_markdown(path: Path, frame: pd.DataFrame) -> None:
    gap = _source_gap_report(frame)
    lines = [
        "# Source Gap Report",
        "",
        "This report separates implemented or partially implemented sources from sources that still need direct adapters, credentials, endpoint calibration, or non-free authorization. Missing sources are explicit gaps and must not be fabricated in event factors.",
        "",
        "## Group Summary",
        "",
        "| source_group | sources | ready_sources | critical_gaps | followup_sources |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for row in gap.itertuples(index=False):
        lines.append(
            f"| {row.source_group} | {row.sources} | {row.ready_sources} | {row.critical_gaps} | {row.followup_sources or 'none'} |"
        )
    lines.extend(["", "## Critical Follow-Up Sources", ""])
    followup = frame[(frame["requires_followup"]) & (frame["priority"].isin(["critical", "high"]))]
    if followup.empty:
        lines.append("- No critical follow-up sources in the current matrix.")
    else:
        for row in followup.sort_values(["priority", "source_group", "source"], ascending=[True, True, True]).itertuples(index=False):
            lines.append(
                f"- `{row.source}` ({row.source_group}, {row.implementation_status}): {row.limitations}"
            )
    lines.extend(
        [
            "",
            "## Rule",
            "",
            "A source may influence stock-level event factors only when it has timestamps, source URLs, entity links, and an implemented or explicitly partial adapter. Otherwise it stays in the gap report.",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _unique_notes(values: list[str]) -> list[str]:
    seen = set()
    out = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _public_news_policy_sources() -> list[tuple[str, str, str, str, str, str, str, str, str]]:
    return [
        (
            "sse_public",
            "exchange_regulator",
            "announcement,regulatory_letter,abnormal_trading,public_trade_info",
            "listed_company_event,regulatory_risk,market_microstructure",
            "regulatory_letter,abnormal_volatility,announcement,public_trade_info",
            "implemented_official_index_adapter",
            "critical",
            "index_adapter_limited_body_pagination",
            "official SSE index-page adapter implemented with bounded generic pagination and optional body text audit; site-specific pagination calibration and structured regulatory fields still need expansion",
        ),
        (
            "szse_public",
            "exchange_regulator",
            "announcement,regulatory_letter,abnormal_trading,public_trade_info",
            "listed_company_event,regulatory_risk,market_microstructure",
            "regulatory_letter,abnormal_volatility,announcement,public_trade_info",
            "implemented_official_index_adapter",
            "critical",
            "index_adapter_limited_body_pagination",
            "official SZSE index-page adapter implemented with bounded generic pagination and optional body text audit; site-specific pagination calibration and structured regulatory-letter fields still need expansion",
        ),
        (
            "bse_public",
            "exchange_regulator",
            "announcement,regulatory_letter,abnormal_trading,public_trade_info",
            "listed_company_event,regulatory_risk,market_microstructure",
            "regulatory_letter,announcement,public_trade_info",
            "implemented_official_index_adapter",
            "medium",
            "index_adapter_limited_body_pagination",
            "official BSE index-page adapter implemented with bounded generic pagination and optional body text audit; site-specific pagination calibration still needs expansion",
        ),
        (
            "csrc_public",
            "regulator_policy",
            "regulatory_policy,penalty,ipo_refinancing,market_supervision",
            "regulatory_policy,penalty,capital_market_risk",
            "penalty,regulatory_policy,ipo_refinancing,supervision",
            "implemented_official_index_adapter",
            "critical",
            "index_adapter_limited_body_pagination",
            "official CSRC index-page adapter implemented with bounded generic pagination and optional body text audit; site-specific pagination calibration and penalty/policy field extraction still need expansion",
        ),
        (
            "ndrc_public",
            "macro_policy",
            "industrial_policy,price_policy,energy_policy",
            "industry_policy,commodity_price,energy_chain",
            "industry_policy,price_policy,energy_policy",
            "implemented_official_index_adapter",
            "high",
            "index_adapter_limited_body_pagination",
            "official NDRC index-page adapter implemented with bounded generic pagination and optional body text audit; site-specific pagination calibration and PIT release calendar still need expansion",
        ),
        (
            "miit_public",
            "macro_policy",
            "industrial_policy,technology_policy,manufacturing_policy",
            "semiconductor,robotics,ev,battery,software,manufacturing",
            "industry_policy,production_guidance,technology_policy",
            "implemented_official_index_adapter",
            "high",
            "index_adapter_limited_body_pagination",
            "official MIIT index-page adapter implemented with bounded generic pagination and optional body text audit; site-specific pagination calibration and industry-policy fields still need expansion",
        ),
        (
            "mofcom_public",
            "macro_policy",
            "trade_policy,export_control,consumption_policy",
            "export_chain,trade_risk,consumer_sector",
            "trade_policy,export_control,consumption_policy",
            "implemented_official_index_adapter",
            "high",
            "index_adapter_limited_body_pagination",
            "official MOFCOM index-page adapter implemented with bounded generic pagination and optional body text audit; site-specific pagination calibration and trade-policy fields still need expansion",
        ),
        (
            "pbc_public",
            "macro_policy",
            "monetary_policy,liquidity,rates,credit",
            "market_liquidity,banking,real_estate,valuation_discount_rate",
            "monetary_policy,liquidity_operation,rate_signal,credit_policy",
            "implemented_official_index_adapter",
            "high",
            "index_adapter_limited_body_pagination",
            "official PBC index-page adapter implemented with bounded generic pagination and optional body text audit; site-specific pagination calibration and structured liquidity-operation fields still need expansion",
        ),
        (
            "customs_public",
            "macro_policy",
            "import_export,commodity_trade,sector_trade",
            "export_chain,commodity_supply_demand,metals_energy",
            "import_export,commodity_trade,sector_trade",
            "implemented_official_index_adapter",
            "high",
            "index_adapter_limited_body_pagination",
            "official customs index-page adapter implemented with bounded generic pagination and optional body text audit; site-specific pagination calibration and monthly import/export PIT fields still need expansion",
        ),
        (
            "stats_nbs_public",
            "macro_policy",
            "industrial_output,pmi,cpi,ppi,profit",
            "macro_cycle,industry_profit,commodity_demand",
            "macro_indicator,industry_indicator",
            "implemented_official_index_adapter",
            "medium",
            "index_adapter_limited_body_pagination",
            "official NBS index-page adapter implemented with bounded generic pagination and optional body text audit; site-specific pagination calibration and release-calendar PIT treatment still need expansion",
        ),
        (
            "sina_finance_public",
            "news_capital_flow",
            "stock_news,market_news,quote_proxy",
            "stock_news,sector_sentiment,market_sentiment",
            "stock_news,market_news",
            "candidate_public_page_adapter",
            "medium",
            "pending_direct_adapter",
            "direct Sina news adapter not yet implemented; available through some AKShare wrappers only",
        ),
        (
            "tencent_finance_public",
            "news_capital_flow",
            "stock_news,market_news,quote_proxy",
            "stock_news,sector_sentiment,market_sentiment",
            "stock_news,market_news",
            "candidate_public_page_adapter",
            "medium",
            "pending_direct_adapter",
            "direct Tencent finance adapter not yet implemented",
        ),
        (
            "netease_finance_public",
            "news_capital_flow",
            "stock_news,market_news,quote_proxy",
            "stock_news,sector_sentiment,market_sentiment",
            "stock_news,market_news",
            "candidate_public_page_adapter",
            "medium",
            "pending_direct_adapter",
            "direct NetEase finance adapter not yet implemented",
        ),
    ]


def _public_commodity_sources() -> list[tuple[str, str, str, str, str, str, str, str]]:
    return [
        (
            "shfe_public",
            "futures_price,inventory,warehouse_receipt,notice",
            "copper,aluminum,zinc,nickel,tin,gold,silver,energy_metals",
            "commodity_price,inventory_change,exchange_notice",
            "partial_via_akshare_sina_futures",
            "critical",
            "partial_direct_exchange_gap",
            "futures price shocks are implemented through AKShare/Sina; direct SHFE inventory/notices still need adapter",
        ),
        (
            "ine_public",
            "crude_oil,energy_futures,inventory,notice",
            "oil_gas,chemical,shipping,energy_cost",
            "commodity_price,inventory_change,exchange_notice",
            "partial_via_akshare_sina_futures",
            "high",
            "partial_direct_exchange_gap",
            "energy futures price shocks are partially covered; direct INE inventory/notices still need adapter",
        ),
        (
            "dce_public",
            "industrial_commodity,agriculture_futures,inventory,notice",
            "chemical,coal_proxy,agriculture,materials",
            "commodity_price,inventory_change,exchange_notice",
            "candidate_direct_adapter",
            "medium",
            "pending_direct_adapter",
            "direct DCE adapter not yet implemented",
        ),
        (
            "czce_public",
            "chemical_agriculture_futures,inventory,notice",
            "chemical,agriculture,materials",
            "commodity_price,inventory_change,exchange_notice",
            "candidate_direct_adapter",
            "medium",
            "pending_direct_adapter",
            "direct CZCE adapter not yet implemented",
        ),
        (
            "cffex_public",
            "index_futures,bond_futures,open_interest",
            "market_risk,beta,hedging_pressure",
            "index_futures,bond_futures,open_interest",
            "candidate_direct_adapter",
            "medium",
            "pending_direct_adapter",
            "direct CFFEX adapter not yet implemented",
        ),
        (
            "gfex_public",
            "lithium_silicon_new_energy_futures,notice",
            "battery,solar,new_energy_materials",
            "commodity_price,exchange_notice",
            "partial_via_akshare_sina_futures",
            "high",
            "partial_direct_exchange_gap",
            "lithium/silicon futures shocks are partially covered through AKShare/Sina; direct GFEX notices still need adapter",
        ),
    ]


def _installed(module: str) -> bool:
    return importlib.util.find_spec(module) is not None
