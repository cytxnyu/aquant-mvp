from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

import pandas as pd

from aquant_mvp.backtest import backtest_stock_forecast, run_backtest
from aquant_mvp.broker import PaperBroker, QMTReadOnlyBroker, build_order_plan_from_targets
from aquant_mvp.config import load_config
from aquant_mvp.data import add_source_audit_columns, audit_point_in_time_tables, check_daily_bars, load_daily_bars, load_daily_bars_resilient
from aquant_mvp.data.providers import LoadReport
from aquant_mvp.events import (
    analyze_event_impact,
    audit_event_coverage,
    build_event_store,
    build_news_evidence_report,
    build_similar_event_report,
    discover_text_intelligence,
    sync_public_events,
    write_event_outputs,
    write_event_impact_outputs,
    write_similar_event_outputs,
    write_text_intelligence_report,
)
from aquant_mvp.features import build_point_in_time_feature_store
from aquant_mvp.factors import FACTOR_COLUMNS, analyze_factor_trust, compute_factor_panel, write_factor_trust_report
from aquant_mvp.foundations import discover_foundations, write_foundation_report
from aquant_mvp.labels import compute_return_labels
from aquant_mvp.analysis import (
    analyze_factors,
    attribute_portfolio_events,
    evaluate_walk_forward_slices,
    load_walk_forward_prediction_artifacts,
    summarize_model_registry,
    validate_paper_trade,
    validate_portfolio_backtest,
    write_paper_trade_validation_outputs,
    write_portfolio_validation_outputs,
)
from aquant_mvp.modeling import discover_model_bases, train_model, train_walk_forward, write_model_base_report
from aquant_mvp.pipeline import run_pipeline
from aquant_mvp.prediction import (
    audit_stock_forecast_evidence,
    build_kline_forecast,
    build_stock_forecast,
    build_stock_trust_gate_report,
    explain_stock_forecast,
    save_kline_forecast_outputs,
    StockForecastResult,
    write_stock_evidence_audit_outputs,
    write_stock_trust_gate_outputs,
)
from aquant_mvp.risk import EventRiskConfig, TradingRiskConfig, apply_event_risk_guard, check_order_plan, event_context_by_symbol
from aquant_mvp.sources import discover_domestic_sources, official_public_source_ids, write_source_coverage
from aquant_mvp.storage import LocalWarehouse
from aquant_mvp.strategy import (
    apply_portfolio_constraints,
    build_rebalance_targets,
    score_factors,
    write_portfolio_constraint_outputs,
)
from aquant_mvp.tooling import discover_tools, write_tool_report
from aquant_mvp.universe import (
    audit_theme_universe_coverage,
    build_theme_universe,
    symbol_theme_membership,
    symbols_for_themes,
    theme_universe_summary,
    write_theme_coverage_audit,
)
from aquant_mvp.universe import filter_universe


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the A-share quant research MVP.")
    parser.add_argument(
        "command",
        nargs="?",
        default="run",
        choices=[
            "run",
            "run-demo",
            "check-data",
            "analyze-factors",
            "predict",
            "sync-data",
            "build-universe",
            "train-model",
            "backtest",
            "predict-stock",
            "predict-kline",
            "plot-kline",
            "report-stock",
            "backtest-stock",
            "paper-trade",
            "live-trade",
            "discover-sources",
            "discover-foundations",
            "discover-text-intelligence",
            "discover-tools",
            "sync-free-all",
            "audit-data",
            "analyze-factor-trust",
            "sync-news",
            "sync-announcements",
            "build-event-store",
            "audit-news",
            "analyze-event-impact",
            "build-feature-store",
            "train-walk-forward",
            "backtest-portfolio",
            "evaluate-models",
            "explain-stock",
            "qmt-readonly-sync",
        ],
    )
    parser.add_argument("--config", default="configs/mvp.json", help="Path to JSON/YAML config.")
    parser.add_argument(
        "--source",
        choices=[
            "sample",
            "akshare",
            "auto",
            "free_real",
            "research",
            "baostock",
            "tushare",
            "cninfo",
            "cninfo_direct",
            "direct_cninfo",
            "sse_public",
            "szse_public",
            "bse_public",
            "csrc_public",
            "ndrc_public",
            "miit_public",
            "mofcom_public",
            "pbc_public",
            "customs_public",
            "stats_nbs_public",
        ],
        default=None,
        help="Override data source.",
    )
    parser.add_argument("--output-dir", default=None, help="Optional report output directory.")
    parser.add_argument("--symbol", default=None, help="Optional symbol to highlight in predict output, e.g. 601899.")
    parser.add_argument("--vendor", default=None, help="Free data vendor: akshare, baostock, tushare, or free_real.")
    parser.add_argument("--themes", default=None, help="Theme set for build-universe, e.g. hot, mega-hot, professional, core-hot.")
    parser.add_argument("--horizons", default=None, help="Comma-separated horizons, e.g. 1,5,20.")
    parser.add_argument("--model", default=None, help="Model type: factor_score, lightgbm_regressor, lightgbm_ranker, ensemble.")
    parser.add_argument("--broker", default="paper", choices=["paper", "qmt"], help="Broker mode for paper/live commands.")
    parser.add_argument("--date", default=None, help="Optional trade or prediction date.")
    parser.add_argument("--allow-sample", action="store_true", help="Allow sample data for predict-stock demos/tests.")
    parser.add_argument("--confirm", action="store_true", help="Required for any future live order path; live remains disabled.")
    parser.add_argument("--domestic-only", action="store_true", help="Limit source discovery to domestic/free A-share sources.")
    parser.add_argument("--start", default=None, help="Override start date for sync-free-all.")
    parser.add_argument("--universe", default=None, help="Universe name: all-a, hot, mega-hot, professional, core-hot, config, or comma-separated symbols.")
    parser.add_argument("--max-symbols", type=int, default=0, help="Optional safety limit for large free sync jobs.")
    parser.add_argument("--max-pages", type=int, default=1, help="Optional max official public index pages per seed URL.")
    parser.add_argument("--min-symbols", type=int, default=0, help="Minimum universe size required before walk-forward can emit trusted candidates.")
    parser.add_argument("--min-prior-rows", type=int, default=20, help="Minimum prior event outcomes required before an event cohort is PIT-ready.")
    parser.add_argument(
        "--max-event-impact-symbols",
        type=int,
        default=80,
        help="Maximum symbols used by stock report news event-impact diagnostics; 0 means no cap.",
    )
    parser.add_argument(
        "--max-event-impact-events",
        type=int,
        default=1500,
        help="Maximum events used by stock report news event-impact diagnostics; 0 means no cap.",
    )
    parser.add_argument("--train-years", type=int, default=0, help="Override walk-forward rolling train window in years.")
    parser.add_argument("--test-months", type=int, default=0, help="Override walk-forward rolling test step in months.")
    parser.add_argument("--strict-pit", action="store_true", help="Treat missing point-in-time metadata as audit issues.")
    parser.add_argument("--point-in-time", action="store_true", help="Build PIT feature store with effective dates.")
    parser.add_argument("--trusted-only", action="store_true", help="Require trusted/weak-free prediction metadata when available.")
    parser.add_argument("--by-year", action="store_true", help="Write yearly evaluation slices.")
    parser.add_argument("--by-industry", action="store_true", help="Write industry evaluation placeholder slices.")
    parser.add_argument(
        "--walk-forward-artifact",
        default=None,
        help="Optional comma-separated walk_forward_predictions.csv path(s) to slice instead of registry artifacts.",
    )
    parser.add_argument("--days", type=int, default=20, help="Forecast/paper-trading days.")
    parser.add_argument("--history-days", type=int, default=120, help="Historical K-line days to include in forecast charts.")
    parser.add_argument("--with-kline", action="store_true", help="Include predicted K-line artifacts in report-stock.")
    parser.add_argument("--with-news", action="store_true", help="Include news/event evidence and event factors where supported.")
    parser.add_argument("--fetch-announcement-text", action="store_true", help="Fetch and parse direct announcement body text where supported.")
    parser.add_argument("--factor-trust-audit", default=None, help="Optional factor_trust_audit.csv path used to restrict walk-forward features.")
    parser.add_argument("--factor-trust-status", default="approved", help="Comma-separated factor trust statuses allowed when --factor-trust-audit is set.")
    parser.add_argument("--no-live", action="store_true", help="Explicitly forbid live trading in paper/QMT workflows.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(args.config)
    source = _effective_source(args)
    output_dir = Path(args.output_dir) if args.output_dir else None

    if args.command == "build-universe":
        return _cmd_build_universe(config, args, output_dir)

    if args.command == "discover-sources":
        return _cmd_discover_sources(args, output_dir)

    if args.command == "discover-foundations":
        return _cmd_discover_foundations(output_dir)

    if args.command == "discover-text-intelligence":
        return _cmd_discover_text_intelligence(output_dir)

    if args.command == "discover-tools":
        return _cmd_discover_tools(output_dir)

    if args.command == "sync-free-all":
        return _cmd_sync_free_all(config, args, source, output_dir)

    if args.command == "audit-data":
        return _cmd_audit_data(config, args, output_dir)

    if args.command == "analyze-factor-trust":
        return _cmd_analyze_factor_trust(config, args, source, output_dir)

    if args.command == "sync-news":
        return _cmd_sync_events(config, args, source, output_dir, mode="news")

    if args.command == "sync-announcements":
        return _cmd_sync_events(config, args, source, output_dir, mode="announcements")

    if args.command == "build-event-store":
        return _cmd_build_event_store(config, args, source, output_dir)

    if args.command == "audit-news":
        return _cmd_audit_news(config, args, source, output_dir)

    if args.command == "analyze-event-impact":
        return _cmd_analyze_event_impact(config, args, source, output_dir)

    if args.command == "build-feature-store":
        return _cmd_build_feature_store(config, args, source, output_dir)

    if args.command == "train-walk-forward":
        return _cmd_train_walk_forward(config, args, source, output_dir)

    if args.command == "backtest-portfolio":
        return _cmd_backtest_portfolio(config, args, source, output_dir)

    if args.command == "evaluate-models":
        return _cmd_evaluate_models(config, args, output_dir)

    if args.command == "explain-stock":
        return _cmd_explain_stock(config, args, source, output_dir)

    if args.command == "qmt-readonly-sync":
        return _cmd_qmt_readonly_sync(config, output_dir)

    if args.command == "sync-data":
        return _cmd_sync_data(config, args, source, output_dir)

    if args.command == "train-model":
        return _cmd_train_model(config, args, source, output_dir)

    if args.command == "predict-stock":
        return _cmd_predict_stock(config, args, source, output_dir)

    if args.command == "predict-kline":
        return _cmd_predict_kline(config, args, source, output_dir)

    if args.command == "plot-kline":
        return _cmd_predict_kline(config, args, source, output_dir)

    if args.command == "report-stock":
        return _cmd_report_stock(config, args, source, output_dir)

    if args.command == "backtest-stock":
        return _cmd_backtest_stock(config, args, source, output_dir)

    if args.command == "paper-trade":
        return _cmd_paper_trade(config, args, source, output_dir)

    if args.command == "live-trade":
        print("Live trading is disabled in this project. QMT order submission is intentionally blocked.")
        if not args.confirm:
            print("Missing --confirm; no live action was attempted.")
        return 1

    if args.command == "check-data":
        data_config = config.data if source is None else replace(config.data, source=source)
        bars_by_symbol, load_report = _load_command_bars(data_config)
        quality = check_daily_bars(bars_by_symbol)
        filtered, universe_report = filter_universe(bars_by_symbol, config.universe)
        print("A-share data check finished.")
        print(f"Data source: {load_report.source}")
        print(f"Date range: {config.data.start_date} to {config.data.end_date}")
        print(f"Loaded symbols: {len(load_report.symbols_loaded)}")
        print(f"Selected universe: {len(filtered)}")
        print(f"Data quality issues: {quality.issue_count}")
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            quality.summary.to_csv(output_dir / "data_quality_summary.csv", index=False)
            quality.issues.to_csv(output_dir / "data_quality_issues.csv", index=False)
            universe_report.detail.to_csv(output_dir / "universe.csv", index=False)
            print(f"Data check report dir: {output_dir}")
        return 0

    payload = run_pipeline(config, source=source, output_dir=output_dir)
    result = payload["result"]
    paths = payload["paths"]
    load_report = payload["load_report"]
    universe_report = payload["universe_report"]
    data_quality = payload["data_quality"]

    if args.command == "analyze-factors":
        print("A-share factor analysis finished.")
    elif args.command == "predict":
        print("A-share latest prediction finished.")
    elif args.command in {"backtest", "backtest-portfolio"}:
        print("A-share backtest finished.")
    else:
        print("A-share quant platform run finished.")
    print(f"Data source: {load_report.source}; symbols: {', '.join(load_report.symbols_loaded)}")
    print(f"Date range: {config.data.start_date} to {config.data.end_date}")
    print(f"Selected universe: {len(universe_report.selected_symbols)} symbols")
    print(f"Data quality issues: {data_quality.issue_count}")
    if load_report.warnings:
        print("Warnings:")
        for note in load_report.warnings:
            print(f"  - {note}")
    for key, value in result.metrics.items():
        print(f"{key}: {value:.6f}")
    if args.command == "predict":
        predictions = payload["predictions"].predictions
        if args.symbol:
            symbol = str(args.symbol).zfill(6)
            selected = predictions[predictions["symbol"] == symbol]
            if selected.empty:
                print(f"Prediction: symbol {symbol} not found in current universe.")
            else:
                row = selected.iloc[0]
                print(
                    "Prediction: "
                    f"{symbol} rank={int(row['prediction_rank'])}, "
                    f"signal={row['signal']}, "
                    f"predicted_excess_return={row['predicted_excess_return']:.4%}"
                )
        print("Top predictions:")
        for row in predictions.head(10).itertuples():
            print(f"  {row.symbol} rank={int(row.prediction_rank)} signal={row.signal} pred={row.predicted_excess_return:.4%}")
    print(f"Report dir: {payload['run_dir']}")
    print(f"Metrics: {paths['metrics']}")
    print(f"Summary: {paths['summary']}")
    return 0


def _effective_source(args: argparse.Namespace) -> str | None:
    if args.command == "run-demo" and args.source is None:
        return "sample"
    if args.source:
        return args.source
    if args.vendor:
        vendor = args.vendor.lower()
        if vendor in {"free", "free_real"}:
            return "free_real"
        return vendor
    return None


def _parse_horizons(args: argparse.Namespace, default: list[int]) -> list[int]:
    if not args.horizons:
        return default
    return [int(item.strip()) for item in args.horizons.split(",") if item.strip()]


def _load_command_bars(data_config) -> tuple[dict[str, pd.DataFrame], LoadReport]:
    if data_config.source.lower() in {"free_real", "research", "baostock", "tushare", "akshare"} and len(data_config.symbols) > 1:
        return load_daily_bars_resilient(data_config)
    return load_daily_bars(data_config)


def _cmd_build_universe(config, args: argparse.Namespace, output_dir: Path | None) -> int:
    themes = args.themes or args.universe or "hot"
    normalized = themes.strip().lower().replace("_", "-")
    if normalized in {"all-a", "all-a-free", "all-free"}:
        frame = _try_fetch_all_a_universe_frame()
        if frame.empty:
            frame = _curated_universe_as_all_a_fallback()
    else:
        frame = build_theme_universe(themes)
        if normalized in {"hot", "mega-hot", "all-hot"}:
            frame = _augment_hot_universe_with_free_market(frame, minimum_symbols=900, target_symbols=1200)
    frame = _normalize_universe_output_columns(frame)
    summary = theme_universe_summary(frame)
    membership = symbol_theme_membership(frame)
    coverage_audit = audit_theme_universe_coverage(frame)
    out_dir = output_dir or Path("reports/hot_universe")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "theme_universe.csv"
    frame.to_csv(path, index=False)
    summary_path = out_dir / "theme_universe_summary.csv"
    membership_path = out_dir / "symbol_theme_membership.csv"
    manifest_path = out_dir / "theme_universe_manifest.json"
    summary.to_csv(summary_path, index=False)
    membership.to_csv(membership_path, index=False)
    unique_symbols = int(frame["symbol"].nunique()) if not frame.empty else 0
    coverage_paths = write_theme_coverage_audit(
        out_dir,
        coverage_audit,
        requested_themes=themes,
        total_unique_symbols=unique_symbols,
    )
    duplicate_rows = int(len(frame) - unique_symbols)
    warehouse_write = None
    try:
        warehouse_frame = add_source_audit_columns(frame, "free_universe" if normalized in {"all-a", "all-a-free", "all-free"} else "curated_plus_free_universe")
        warehouse_write = LocalWarehouse(config.storage.root_dir, config.storage.file_format).write_table("universe", warehouse_frame)
    except Exception as exc:  # noqa: BLE001
        warehouse_write = {"error": str(exc)}
    _write_json(
        manifest_path,
        {
            "requested_themes": themes,
            "universe_mode": "all_a_free" if normalized in {"all-a", "all-a-free", "all-free"} else "theme_seed",
            "theme_count": int(frame["theme"].nunique()) if not frame.empty else 0,
            "rows": int(len(frame)),
            "unique_symbols": unique_symbols,
            "duplicate_theme_rows": duplicate_rows,
            "multi_theme_symbols": int((membership["theme_count"] > 1).sum()) if not membership.empty else 0,
            "minimum_symbols_for_trusted_prediction": 200,
            "coverage_audit": {key: str(value) for key, value in coverage_paths.items()},
            "coverage_status_counts": coverage_audit["coverage_status"].value_counts().to_dict() if not coverage_audit.empty else {},
            "themes_supporting_trusted_evidence_after_other_gates": int(coverage_audit["can_support_trusted_evidence"].sum()) if not coverage_audit.empty else 0,
            "thin_or_blocked_themes": coverage_audit.loc[
                ~coverage_audit["can_support_trusted_evidence"].astype(bool), "theme"
            ].head(50).tolist()
            if not coverage_audit.empty
            else [],
            "warehouse_universe": warehouse_write,
            "notes": [
                "This is a curated hot-sector seed universe, not an official industry classifier.",
                "mega-hot is augmented with free all-A names when domestic sources are available to support large-sample modeling.",
                "Use --universe all-a for maximum market coverage when free source availability allows it.",
            ],
        },
    )
    print("Hot theme universe generated.")
    print(f"Themes: {frame['theme'].nunique()}; rows: {len(frame)}; unique symbols: {unique_symbols}")
    print(f"Output: {path}")
    print(f"Summary: {summary_path}")
    print(f"Membership: {membership_path}")
    print(f"Coverage audit: {coverage_paths['theme_coverage_audit_md']}")
    return 0


def _cmd_discover_sources(args: argparse.Namespace, output_dir: Path | None) -> int:
    frame = discover_domestic_sources()
    if args.domestic_only:
        frame = frame[frame["domestic"]]
    out_dir = output_dir or Path("reports/source_discovery")
    md_path = write_source_coverage(out_dir, frame)
    print("Free domestic source discovery finished.")
    print(f"Sources: {len(frame)}; installed: {int(frame['installed'].sum())}; credential ready: {int(frame['credential_ready'].sum())}")
    print(f"Coverage report: {md_path}")
    return 0


def _cmd_discover_foundations(output_dir: Path | None) -> int:
    frame = discover_foundations()
    out_dir = output_dir or Path("reports/foundations")
    md_path = write_foundation_report(out_dir, frame)
    print("Foundation discovery finished.")
    print(f"Foundations: {len(frame)}; installed: {int(frame['installed'].sum())}; native supported: {int(frame['integration_status'].astype(str).str.contains('native_supported').sum())}")
    print(f"Report: {md_path}")
    return 0


def _cmd_discover_text_intelligence(output_dir: Path | None) -> int:
    frame = discover_text_intelligence()
    out_dir = output_dir or Path("reports/text_intelligence")
    paths = write_text_intelligence_report(out_dir, frame)
    print("Text intelligence discovery finished.")
    print(f"Capabilities: {len(frame)}; installed and ready: {int(frame['installed'].sum()) if not frame.empty else 0}")
    print(f"Report: {paths['md']}")
    return 0


def _cmd_discover_tools(output_dir: Path | None) -> int:
    frame = discover_tools()
    out_dir = output_dir or Path("reports/tools")
    md_path = write_tool_report(out_dir, frame)
    live_allowed = int(frame["live_trading_allowed"].sum()) if not frame.empty else 0
    print("Tool discovery finished.")
    print(f"Tools: {len(frame)}; live trading allowed tools: {live_allowed}")
    print(f"Report: {md_path}")
    return 0


def _cmd_sync_free_all(config, args: argparse.Namespace, source: str | None, output_dir: Path | None) -> int:
    symbols = _symbols_for_universe_arg(args, config)
    if args.max_symbols and args.max_symbols > 0:
        symbols = symbols[: args.max_symbols]
    if not symbols:
        raise RuntimeError("No symbols resolved for sync-free-all.")
    start_date = args.start or config.data.start_date
    data_source = source or "free_real"
    bars_by_symbol, load_report = _load_symbols_resilient(config, args, symbols, data_source, start_date)
    quality = check_daily_bars(bars_by_symbol)
    frame = pd.concat(bars_by_symbol.values(), ignore_index=True) if bars_by_symbol else pd.DataFrame()
    audited = add_source_audit_columns(frame, load_report.source)
    source_audit = pd.DataFrame(
        [
            {
                "symbol": symbol,
                "source": load_report.source,
                "loaded": symbol in load_report.symbols_loaded,
                "warning_count": sum(1 for item in load_report.warnings if symbol in item),
                "notes": "; ".join(item for item in load_report.warnings if symbol in item)[:1000],
            }
            for symbol in symbols
        ]
    )
    source_audit = add_source_audit_columns(source_audit, load_report.source)
    warehouse = LocalWarehouse(config.storage.root_dir, config.storage.file_format)
    daily_write = warehouse.write_table("daily_bar", audited)
    audit_write = warehouse.write_table("source_audit", source_audit)
    out_dir = output_dir or Path("reports/free_max_sync")
    out_dir.mkdir(parents=True, exist_ok=True)
    quality.summary.to_csv(out_dir / "data_quality_summary.csv", index=False)
    quality.issues.to_csv(out_dir / "data_quality_issues.csv", index=False)
    _write_json(
        out_dir / "sync_free_all_summary.json",
        {
            "source": load_report.source,
            "requested_symbols": len(symbols),
            "loaded_symbols": len(load_report.symbols_loaded),
            "failed_symbols": len(symbols) - len(load_report.symbols_loaded),
            "daily_bar": daily_write,
            "source_audit": audit_write,
            "warnings": load_report.warnings,
        },
    )
    print("Free max sync finished.")
    print(f"Source: {load_report.source}; requested: {len(symbols)}; loaded: {len(load_report.symbols_loaded)}; rows: {len(audited)}")
    print(f"Warehouse daily_bar: {daily_write.path}")
    print(f"Report: {out_dir}")
    return 0


def _load_symbols_resilient(config, args: argparse.Namespace, symbols: list[str], source: str, start_date: str) -> tuple[dict[str, pd.DataFrame], LoadReport]:
    selected = symbols[: args.max_symbols] if args.max_symbols and args.max_symbols > 0 else symbols
    data_config = replace(config.data, source=source, symbols=selected, start_date=start_date)
    return load_daily_bars_resilient(data_config)


def _cmd_audit_data(config, args: argparse.Namespace, output_dir: Path | None) -> int:
    warehouse = LocalWarehouse(config.storage.root_dir, config.storage.file_format)
    tables: dict[str, pd.DataFrame] = {}
    for table in ["daily_bar", "feature_store", "source_audit"]:
        try:
            tables[table] = warehouse.read_table(table)
        except FileNotFoundError:
            continue
    if not tables:
        data_config = _data_config_with_source(config, args, args.source or config.data.source)
        bars_by_symbol, load_report = load_daily_bars(data_config)
        frame = pd.concat(bars_by_symbol.values(), ignore_index=True) if bars_by_symbol else pd.DataFrame()
        tables["daily_bar"] = add_source_audit_columns(frame, load_report.source)
    result = audit_point_in_time_tables(tables, strict_pit=args.strict_pit)
    out_dir = output_dir or Path("reports/data_audit")
    out_dir.mkdir(parents=True, exist_ok=True)
    result.summary.to_csv(out_dir / "data_audit_summary.csv", index=False)
    result.issues.to_csv(out_dir / "data_audit_issues.csv", index=False)
    result.cross_source_diff.to_csv(out_dir / "cross_source_diff_report.csv", index=False)
    print("Data audit finished.")
    print(f"Tables: {len(result.summary)}; issues: {len(result.issues)}")
    print(f"Report: {out_dir}")
    return 0


def _cmd_analyze_factor_trust(config, args: argparse.Namespace, source: str | None, output_dir: Path | None) -> int:
    data_config = _data_config_with_source(config, args, source)
    bars_by_symbol, load_report = _load_command_bars(data_config)
    factors = compute_factor_panel(bars_by_symbol)
    horizons = _parse_horizons(args, [5])
    labels = compute_return_labels(bars_by_symbol, horizons)
    label_column = f"future_return_{horizons[0]}d"
    analysis = analyze_factors(factors, labels, FACTOR_COLUMNS, label_column, config.analysis.quantiles)
    result = analyze_factor_trust(factors, analysis, FACTOR_COLUMNS, labels=labels, label_column=label_column)
    out_dir = output_dir or Path("reports/factor_trust")
    paths = write_factor_trust_report(result, out_dir)
    _write_json(
        out_dir / "factor_trust_load_manifest.json",
        {
            "source": load_report.source,
            "requested_symbols": len(data_config.symbols),
            "loaded_symbols": len(bars_by_symbol),
            "requested_symbol_sample": list(data_config.symbols)[:20],
            "loaded_symbol_sample": list(bars_by_symbol)[:20],
            "start_date": data_config.start_date,
            "end_date": data_config.end_date,
            "horizons": horizons,
            "label_column": label_column,
            "factor_count": int(len(result.registry)),
            "audit_rows": int(len(result.audit)),
            "trust_counts": result.audit["trust_status"].value_counts().to_dict() if not result.audit.empty else {},
            "warnings": load_report.warnings[:2000],
            "note": "Factor trust audit uses PIT labels and resilient free-source loading when multiple domestic/free symbols are requested.",
        },
    )
    try:
        warehouse = LocalWarehouse(config.storage.root_dir, config.storage.file_format)
        warehouse.write_table("factor_registry", add_source_audit_columns(result.registry, "factor_registry_v04"))
        warehouse.write_table("factor_trust_audit", add_source_audit_columns(result.audit, load_report.source))
    except Exception:  # noqa: BLE001
        pass
    counts = result.audit["trust_status"].value_counts().to_dict() if not result.audit.empty else {}
    print("Factor trust analysis finished.")
    print(f"Source: {load_report.source}; factors: {len(result.registry)}; counts: {counts}")
    print(f"Registry: {paths['factor_registry']}")
    print(f"Audit: {paths['factor_trust_audit']}")
    print(f"Report: {paths['factor_trust_report']}")
    return 0


def _cmd_sync_events(config, args: argparse.Namespace, source: str | None, output_dir: Path | None, mode: str) -> int:
    symbols = _symbols_for_universe_arg(args, config)
    if args.max_symbols and args.max_symbols > 0:
        symbols = symbols[: args.max_symbols]
    if args.symbol:
        symbol = args.symbol.zfill(6)
        if symbol not in symbols:
            symbols.append(symbol)
    event_source = _event_source_from_data_source(config, args, source)
    raw, warnings = sync_public_events(
        symbols,
        args.start or config.data.start_date,
        config.data.end_date,
        source=event_source,
        fetch_announcement_text=bool(getattr(args, "fetch_announcement_text", False)),
        max_pages=int(getattr(args, "max_pages", 1) or 1),
    )
    if mode == "announcements" and "source" in raw.columns:
        raw = raw[raw["source"].astype(str).str.contains("cninfo|notice|announcement|sample_announcement", case=False, regex=True)].copy()
    out_dir = output_dir or Path(f"reports/{mode}")
    out_dir.mkdir(parents=True, exist_ok=True)
    raw.to_csv(out_dir / "raw_events.csv", index=False)
    _write_json(
        out_dir / f"{mode}_summary.json",
        {"mode": mode, "source": event_source, "symbols": len(symbols), "rows": len(raw), "warnings": warnings},
    )
    _write_json(out_dir / "event_warnings.json", {"warnings": warnings})
    if event_source != "sample":
        try:
            LocalWarehouse(config.storage.root_dir, config.storage.file_format).write_table(
                "raw_events",
                add_source_audit_columns(raw, event_source, quality_flag="raw_event"),
            )
        except Exception:  # noqa: BLE001
            pass
    print(f"{mode} sync finished.")
    print(f"Source: {event_source}; symbols: {len(symbols)}; rows: {len(raw)}; warnings: {len(warnings)}")
    print(f"Output: {out_dir}")
    return 0


def _cmd_build_event_store(config, args: argparse.Namespace, source: str | None, output_dir: Path | None) -> int:
    symbols = _symbols_for_universe_arg(args, config)
    if args.max_symbols and args.max_symbols > 0:
        symbols = symbols[: args.max_symbols]
    if args.symbol:
        symbol = args.symbol.zfill(6)
        if symbol not in symbols:
            symbols.append(symbol)
    raw, source_warnings = _load_or_sync_events_with_warnings(config, args, source, symbols)
    result = build_event_store(raw, symbols)
    if source_warnings:
        result = replace(result, warnings=[*source_warnings, *result.warnings])
    out_dir = output_dir or Path("reports/event_store")
    paths = write_event_outputs(result, out_dir, symbols=symbols)
    text_intelligence_paths = write_text_intelligence_report(out_dir, discover_text_intelligence())
    similar_event_result = build_similar_event_report(
        result.event_store,
        symbol=args.symbol.zfill(6) if args.symbol else None,
    )
    similar_event_paths = write_similar_event_outputs(out_dir, similar_event_result)
    if not _uses_sample_events(config, args, source):
        try:
            warehouse = LocalWarehouse(config.storage.root_dir, config.storage.file_format)
            warehouse.write_table("event_store", add_source_audit_columns(result.event_store, "event_store_v04"))
            warehouse.write_table("event_factor", add_source_audit_columns(result.event_factors, "event_factor_v04"))
        except Exception:  # noqa: BLE001
            pass
    print("Event store built.")
    print(f"Events: {len(result.event_store)}; event factor rows: {len(result.event_factors)}; warnings: {len(result.warnings)}")
    print(f"Event store: {paths['event_store']}")
    print(f"Event factors: {paths['event_factors']}")
    print(f"Evidence: {paths['news_evidence']}")
    print(f"Text intelligence: {text_intelligence_paths['md']}")
    print(f"Similar events: {similar_event_paths['md']}")
    return 0


def _cmd_audit_news(config, args: argparse.Namespace, source: str | None, output_dir: Path | None) -> int:
    symbols = _symbols_for_universe_arg(args, config)
    if args.max_symbols and args.max_symbols > 0:
        symbols = symbols[: args.max_symbols]
    if args.symbol:
        symbol = args.symbol.zfill(6)
        if symbol not in symbols:
            symbols.append(symbol)
    raw, source_warnings = _load_or_sync_events_with_warnings(config, args, source, symbols)
    result = build_event_store(raw, symbols)
    if source_warnings:
        result = replace(result, warnings=[*source_warnings, *result.warnings])
    audit = audit_event_coverage(result.event_store, result.event_factors, symbols)
    out_dir = output_dir or Path("reports/news_audit")
    paths = write_event_outputs(result, out_dir, symbols=symbols)
    audit_path = out_dir / "news_coverage_audit.csv"
    audit.to_csv(audit_path, index=False)
    _write_json(
        out_dir / "news_coverage_summary.json",
        {
            "symbols": len(symbols),
            "event_rows": int(len(result.event_store)),
            "event_factor_rows": int(len(result.event_factors)),
            "coverage_counts": audit["coverage_status"].value_counts().to_dict() if not audit.empty else {},
            "warnings": result.warnings,
            "event_store": str(paths["event_store"]),
            "event_factors": str(paths["event_factors"]),
        },
    )
    print("News coverage audit finished.")
    print(f"Symbols: {len(symbols)}; events: {len(result.event_store)}; event factor rows: {len(result.event_factors)}")
    print(audit["coverage_status"].value_counts().to_string() if not audit.empty else "No symbols audited.")
    print(f"Audit: {audit_path}")
    return 0


def _cmd_analyze_event_impact(config, args: argparse.Namespace, source: str | None, output_dir: Path | None) -> int:
    data_config = _data_config_with_source(config, args, source, ensure_symbol=args.symbol if args.symbol else None)
    bars_by_symbol, load_report = _load_command_bars(data_config)
    symbols = list(bars_by_symbol)
    if args.symbol:
        symbol = args.symbol.zfill(6)
        if symbol not in symbols:
            symbols.append(symbol)
    raw, source_warnings = _load_or_sync_events_with_warnings(config, args, source, symbols)
    event_result = build_event_store(raw, symbols)
    if source_warnings:
        event_result = replace(event_result, warnings=[*source_warnings, *event_result.warnings])
    horizons = tuple(_parse_horizons(args, [1, 5, 20, 60]))
    impact = analyze_event_impact(
        event_result.event_store,
        bars_by_symbol,
        horizons=horizons,
        min_prior_rows=int(args.min_prior_rows or 20),
    )
    out_dir = output_dir or Path("reports/event_impact_study")
    out_dir.mkdir(parents=True, exist_ok=True)
    event_paths = write_event_outputs(event_result, out_dir, symbols=symbols)
    impact_paths = write_event_impact_outputs(out_dir, impact)
    similar = build_similar_event_report(
        event_result.event_store,
        bars_by_symbol=bars_by_symbol,
        symbol=args.symbol.zfill(6) if args.symbol else None,
        horizons=horizons,
    )
    similar_paths = write_similar_event_outputs(out_dir, similar)
    _write_json(
        out_dir / "event_impact_manifest.json",
        {
            "source": load_report.source,
            "event_source": _event_source_from_data_source(config, args, source),
            "symbols": len(symbols),
            "horizons": list(horizons),
            "warnings": event_result.warnings,
            "impact_summary": impact.summary,
            "event_files": {key: str(value) for key, value in event_paths.items()},
            "impact_files": {key: str(value) for key, value in impact_paths.items()},
            "similar_event_files": {key: str(value) for key, value in similar_paths.items()},
            "note": "Event impact statistics are audit evidence only, not investment advice.",
        },
    )
    if not _uses_sample_events(config, args, source):
        try:
            warehouse = LocalWarehouse(config.storage.root_dir, config.storage.file_format)
            warehouse.write_table("event_impact_return", add_source_audit_columns(impact.event_returns, "event_impact_study"))
            warehouse.write_table("event_impact_cohort", add_source_audit_columns(impact.cohorts, "event_impact_study"))
            warehouse.write_table("event_impact_pit_prior", add_source_audit_columns(impact.pit_priors, "event_impact_study"))
        except Exception:  # noqa: BLE001
            pass
    print("Event impact study finished.")
    print(f"Source: {load_report.source}; symbols: {len(symbols)}; horizons: {list(horizons)}")
    print(
        f"Event-return rows: {impact.summary.get('event_return_rows', 0)}; "
        f"available: {impact.summary.get('available_return_rows', 0)}; "
        f"cohorts: {impact.summary.get('cohort_rows', 0)}; "
        f"PIT-ready priors: {impact.summary.get('pit_ready_rows', 0)}"
    )
    print(f"Report: {impact_paths['md']}")
    return 0


def _cmd_build_feature_store(config, args: argparse.Namespace, source: str | None, output_dir: Path | None) -> int:
    data_config = _data_config_with_source(config, args, source)
    bars_by_symbol, load_report = _load_command_bars(data_config)
    horizons = _parse_horizons(args, config.model.horizons)
    out_dir = output_dir or Path("reports/feature_store")
    out_dir.mkdir(parents=True, exist_ok=True)
    event_factors = _load_or_build_event_factors(config, args, source, list(bars_by_symbol), out_dir) if args.with_news else None
    result = build_point_in_time_feature_store(bars_by_symbol, horizons, load_report.source, event_factors=event_factors)
    warehouse = LocalWarehouse(config.storage.root_dir, config.storage.file_format)
    write_result = warehouse.write_table("feature_store", result.features)
    result.features.head(2000).to_csv(out_dir / "feature_store_preview.csv", index=False)
    _write_json(out_dir / "feature_store_summary.json", result.metadata)
    print("Point-in-time feature store built.")
    print(
        f"Rows: {len(result.features)}; features: {result.metadata['feature_count']}; "
        f"event features: {result.metadata.get('event_feature_count', 0)}; version: {result.metadata['feature_version']}"
    )
    print(f"Warehouse: {write_result.path}")
    return 0


def _feature_columns_from_factor_trust(args: argparse.Namespace, output_dir: Path) -> tuple[list[str] | None, dict[str, object]]:
    audit_arg = getattr(args, "factor_trust_audit", None)
    if not audit_arg:
        return None, {}
    audit_path = Path(audit_arg)
    if not audit_path.exists():
        raise FileNotFoundError(f"factor trust audit not found: {audit_path}")
    audit = pd.read_csv(audit_path)
    factor_column = "factor_id" if "factor_id" in audit.columns else "factor" if "factor" in audit.columns else ""
    status_column = "trust_status" if "trust_status" in audit.columns else "status" if "status" in audit.columns else ""
    if not factor_column or not status_column:
        raise ValueError("factor trust audit must contain factor_id/factor and trust_status/status columns")
    allowed_statuses = {
        status.strip()
        for status in str(getattr(args, "factor_trust_status", "approved") or "approved").split(",")
        if status.strip()
    }
    if not allowed_statuses:
        allowed_statuses = {"approved"}
    eligible = audit[audit[status_column].astype(str).isin(allowed_statuses)].copy()
    eligible_factors = set(eligible[factor_column].dropna().astype(str))
    columns = [factor for factor in FACTOR_COLUMNS if factor in eligible_factors]
    if not columns:
        raise ValueError(
            f"factor trust audit {audit_path} produced no usable FACTOR_COLUMNS for statuses {sorted(allowed_statuses)}"
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    feature_frame = pd.DataFrame({"factor_id": columns, "feature_order": range(1, len(columns) + 1)})
    feature_frame.to_csv(output_dir / "factor_trust_feature_set.csv", index=False)
    metadata = {
        "factor_trust_audit_path": str(audit_path),
        "allowed_statuses": sorted(allowed_statuses),
        "audit_rows": int(len(audit)),
        "eligible_rows": int(len(eligible)),
        "selected_feature_count": int(len(columns)),
        "available_factor_columns": int(len(FACTOR_COLUMNS)),
        "feature_set_source": f"factor_trust_audit:{audit_path}:statuses={','.join(sorted(allowed_statuses))}",
        "note": "Only selected factor ids are used as base factors; event factors are appended separately when --with-news/event-aware is enabled.",
    }
    _write_json(output_dir / "factor_trust_feature_set.json", metadata)
    return columns, metadata


def _cmd_train_walk_forward(config, args: argparse.Namespace, source: str | None, output_dir: Path | None) -> int:
    data_config = _data_config_with_source(config, args, source)
    if args.max_symbols and args.max_symbols > 0:
        data_config = replace(data_config, symbols=list(data_config.symbols)[: args.max_symbols])
    if data_config.source.lower() in {"free_real", "research", "baostock", "tushare", "akshare"} and len(data_config.symbols) > 1:
        bars_by_symbol, load_report = load_daily_bars_resilient(data_config)
    else:
        bars_by_symbol, load_report = load_daily_bars(data_config)
    horizons = _parse_horizons(args, config.model.horizons)
    out_dir = output_dir or Path("reports/walk_forward")
    model_type = args.model or config.model.model_type
    use_events = args.with_news or "event" in str(model_type).lower()
    event_factors = _load_or_build_event_factors(config, args, source, list(bars_by_symbol), out_dir) if use_events else None
    feature_columns, feature_metadata = _feature_columns_from_factor_trust(args, out_dir)
    result = train_walk_forward(
        bars_by_symbol,
        model_type,
        horizons,
        out_dir,
        config.model.registry_dir,
        min_symbols=args.min_symbols if args.min_symbols > 0 else 200,
        train_years=args.train_years if args.train_years > 0 else 4,
        test_months=args.test_months if args.test_months > 0 else 6,
        embargo_days=config.model.embargo_days,
        event_factors=event_factors,
        feature_columns=feature_columns,
        feature_set_source=feature_metadata.get("feature_set_source") if feature_metadata else None,
    )
    try:
        registry_rows = pd.DataFrame(_read_model_registry(config.model.registry_dir))
        if not registry_rows.empty:
            LocalWarehouse(config.storage.root_dir, config.storage.file_format).write_table(
                "model_registry",
                add_source_audit_columns(registry_rows, "model_registry"),
            )
    except Exception:  # noqa: BLE001
        pass
    print("Walk-forward training finished.")
    print(
        f"Source: {load_report.source}; symbols: {len(bars_by_symbol)}; rows: {result.summary['rows']}; "
        f"event features: {result.summary.get('event_feature_count', 0)}; feature source: {result.summary.get('feature_set_source', '')}"
    )
    _write_json(
        out_dir / "walk_forward_load_manifest.json",
        {
            "source": load_report.source,
            "requested_symbols": len(data_config.symbols),
            "loaded_symbols": len(bars_by_symbol),
            "min_symbols": args.min_symbols if args.min_symbols > 0 else 200,
            "feature_set": feature_metadata,
            "warnings": load_report.warnings[:2000],
            "note": "Large free-source walk-forward uses resilient per-symbol loading; failed symbols remain audited.",
        },
    )
    print(result.metrics.to_string(index=False) if not result.metrics.empty else "No metrics generated.")
    print(f"Report: {out_dir}")
    return 0


def _cmd_backtest_portfolio(config, args: argparse.Namespace, source: str | None, output_dir: Path | None) -> int:
    data_config = _data_config_with_source(config, args, source)
    portfolio_config = replace(config, data=data_config)
    payload = run_pipeline(portfolio_config, source=None, output_dir=output_dir)
    result = payload["result"]
    load_report = payload["load_report"]
    universe_report = payload["universe_report"]
    out_dir = payload["run_dir"]
    event_attribution = None
    event_guard = None
    event_guarded_metrics: dict[str, float] | None = None
    event_attribution_daily = None
    out_path = Path(out_dir)
    constraint = apply_portfolio_constraints(
        payload["targets"],
        bars_by_symbol=payload["bars_by_symbol"],
        strategy_config=config.strategy,
        risk_config=config.risk,
        theme_membership=_theme_membership_for_symbols(payload["targets"].columns),
        equity_curve=result.equity_curve,
    )
    write_portfolio_constraint_outputs(out_path, constraint)
    constrained_result = run_backtest(payload["bars_by_symbol"], constraint.adjusted_targets, config.backtest)
    constrained_result.equity_curve.to_csv(out_path / "portfolio_constraint_equity_curve.csv", index=False)
    constrained_result.trades.to_csv(out_path / "portfolio_constraint_trades.csv", index=False)
    constrained_result.holdings.to_csv(out_path / "portfolio_constraint_holdings.csv", index=False)
    constrained_result.rebalances.to_csv(out_path / "portfolio_constraint_rebalances.csv", index=False)
    _write_json(out_path / "portfolio_constraint_metrics.json", constrained_result.metrics)
    if args.with_news:
        event_factors = _load_or_build_event_factors(config, args, source, list(data_config.symbols), out_path)
        event_attribution = attribute_portfolio_events(constrained_result.holdings, event_factors)
        event_attribution_daily = event_attribution.daily
        event_attribution.daily.to_csv(out_path / "portfolio_event_attribution_daily.csv", index=False)
        event_attribution.symbol.to_csv(out_path / "portfolio_event_attribution_symbol.csv", index=False)
        (out_path / "portfolio_event_attribution.md").write_text(event_attribution.markdown, encoding="utf-8")
        event_guard = apply_event_risk_guard(constraint.adjusted_targets, event_factors, _event_risk_config(config))
        event_guard.adjusted_targets.to_csv(out_path / "event_guarded_rebalance_targets.csv")
        event_guard.report.to_csv(out_path / "event_risk_guard_report.csv", index=False)
        (out_path / "event_risk_guard_report.md").write_text(event_guard.markdown, encoding="utf-8")
        _write_json(out_path / "event_risk_guard_summary.json", event_guard.metadata)
        guarded_result = run_backtest(payload["bars_by_symbol"], event_guard.adjusted_targets, config.backtest)
        guarded_result.equity_curve.to_csv(out_path / "event_guarded_equity_curve.csv", index=False)
        guarded_result.trades.to_csv(out_path / "event_guarded_trades.csv", index=False)
        guarded_result.holdings.to_csv(out_path / "event_guarded_holdings.csv", index=False)
        guarded_result.rebalances.to_csv(out_path / "event_guarded_rebalances.csv", index=False)
        _write_json(out_path / "event_guarded_metrics.json", guarded_result.metrics)
        event_guarded_metrics = guarded_result.metrics
        guarded_attribution = attribute_portfolio_events(guarded_result.holdings, event_factors)
        guarded_attribution.daily.to_csv(out_path / "event_guarded_portfolio_event_attribution_daily.csv", index=False)
        guarded_attribution.symbol.to_csv(out_path / "event_guarded_portfolio_event_attribution_symbol.csv", index=False)
        (out_path / "event_guarded_portfolio_event_attribution.md").write_text(guarded_attribution.markdown, encoding="utf-8")
    validation = validate_portfolio_backtest(
        result.equity_curve,
        result.trades,
        result.rebalances,
        result.metrics,
        constrained_equity_curve=constrained_result.equity_curve,
        constrained_trades=constrained_result.trades,
        constrained_rebalances=constrained_result.rebalances,
        constrained_metrics=constrained_result.metrics,
        constraint_report=constraint.report,
        constraint_daily=constraint.daily_summary,
        event_attribution_daily=event_attribution_daily,
        event_guard_metadata=event_guard.metadata if event_guard is not None else None,
        event_attribution_required=bool(args.with_news),
        backtest_config=config.backtest,
        strategy_config=config.strategy,
        risk_config=config.risk,
    )
    validation_paths = write_portfolio_validation_outputs(out_path, validation)
    _write_json(
        out_path / "portfolio_backtest_manifest.json",
        {
            "command": "backtest-portfolio",
            "source": load_report.source,
            "requested_universe": args.universe or "config",
            "loaded_symbols": load_report.symbols_loaded,
            "selected_symbols": universe_report.selected_symbols,
            "metrics": result.metrics,
            "portfolio_constraints": constraint.metadata,
            "constraint_adjusted_metrics": constrained_result.metrics,
            "with_news": bool(args.with_news),
            "event_attribution_rows": int(len(event_attribution.daily)) if event_attribution is not None else 0,
            "event_risk_guard": event_guard.metadata if event_guard is not None else {"enabled": False},
            "event_guarded_metrics": event_guarded_metrics or {},
            "portfolio_validation": validation.summary,
            "portfolio_validation_report": str(validation_paths["markdown"]),
            "note": "Portfolio research backtest only; live trading remains disabled.",
        },
    )
    print("Portfolio backtest finished.")
    print(f"Source: {load_report.source}; loaded symbols: {len(load_report.symbols_loaded)}; selected: {len(universe_report.selected_symbols)}")
    print("Base metrics:")
    for key, value in result.metrics.items():
        print(f"{key}: {value:.6f}")
    print("Constraint-adjusted metrics:")
    for key, value in constrained_result.metrics.items():
        print(f"{key}: {value:.6f}")
    print(f"Report: {out_dir}")
    return 0


def _cmd_evaluate_models(config, args: argparse.Namespace, output_dir: Path | None) -> int:
    out_dir = output_dir or Path("reports/model_evaluation")
    out_dir.mkdir(parents=True, exist_ok=True)
    model_base_paths = write_model_base_report(out_dir, discover_model_bases())
    records = _read_model_registry(config.model.registry_dir)
    evaluation = summarize_model_registry(records)
    evaluation.to_csv(out_dir / "model_evaluation.csv", index=False)
    explicit_artifacts = [
        Path(item.strip())
        for item in str(getattr(args, "walk_forward_artifact", "") or "").split(",")
        if item.strip()
    ]
    predictions, artifacts = load_walk_forward_prediction_artifacts(records, out_dir, extra_candidates=explicit_artifacts)
    if explicit_artifacts and not predictions.empty and "source_artifact" in predictions.columns:
        selected = {str(path) for path in explicit_artifacts}
        predictions = predictions[predictions["source_artifact"].astype(str).isin(selected)].copy()
        artifacts = [artifact for artifact in artifacts if artifact in selected]
    slices = evaluate_walk_forward_slices(predictions)
    if args.by_year or not args.by_industry:
        slices["year"].to_csv(out_dir / "evaluation_by_year.csv", index=False)
    if args.by_industry:
        slices["industry"].to_csv(out_dir / "evaluation_by_industry.csv", index=False)
    else:
        slices["industry"].to_csv(out_dir / "evaluation_by_industry.csv", index=False)
    slices["theme"].to_csv(out_dir / "evaluation_by_theme.csv", index=False)
    slices["size"].to_csv(out_dir / "evaluation_by_size.csv", index=False)
    slices["regime"].to_csv(out_dir / "evaluation_by_regime.csv", index=False)
    _write_json(
        out_dir / "model_evaluation_manifest.json",
        {
            "registry_dir": config.model.registry_dir,
            "registry_records": len(records),
            "explicit_walk_forward_artifacts": [str(path) for path in explicit_artifacts],
            "walk_forward_prediction_rows": int(len(predictions)),
            "walk_forward_artifacts": artifacts,
            "slice_reports": [
                "evaluation_by_year.csv",
                "evaluation_by_industry.csv",
                "evaluation_by_theme.csv",
                "evaluation_by_size.csv",
                "evaluation_by_regime.csv",
            ],
            "model_base_availability": {key: str(value) for key, value in model_base_paths.items()},
            "notes": [
                "industry is a curated hot-theme proxy unless historical industry data has been synced",
                "size uses market_cap when available, otherwise PIT liquidity proxy or unavailable",
                "regime uses PIT market breadth/mean return when present; older artifacts fall back to ex-post OOS diagnostics",
            ],
        },
    )
    print("Model evaluation finished.")
    print(f"Records: {len(evaluation)}")
    print(f"Walk-forward rows: {len(predictions)}")
    print(f"Report: {out_dir}")
    return 0


def _cmd_explain_stock(config, args: argparse.Namespace, source: str | None, output_dir: Path | None) -> int:
    if not args.symbol:
        raise ValueError("explain-stock requires --symbol.")
    data_config = _data_config_with_source(config, args, source, ensure_symbol=args.symbol)
    bars_by_symbol, load_report = _load_command_bars(data_config)
    horizons = _parse_horizons(args, config.model.horizons)
    out_dir = output_dir or Path("reports/stock_explain")
    out_dir.mkdir(parents=True, exist_ok=True)
    event_factors = None
    news_summary: dict[str, object] = {"with_news": bool(args.with_news)}
    if args.with_news:
        event_factors, _news_paths, news_summary = _build_stock_news_context(
            config,
            args,
            source,
            list(bars_by_symbol),
            args.symbol,
            out_dir,
            bars_by_symbol=bars_by_symbol,
        )
    forecast = build_stock_forecast(
        bars_by_symbol,
        args.symbol,
        horizons,
        source=load_report.source,
        model_type=args.model or config.model.model_type,
        embargo_days=config.model.embargo_days,
        allow_sample=args.allow_sample,
        event_factors=event_factors,
        model_registry_dir=config.model.registry_dir,
    )
    explanation = explain_stock_forecast(bars_by_symbol, forecast, args.symbol, horizons)
    explanation.report.to_csv(out_dir / "stock_explanation.csv", index=False)
    explanation.similar_history.to_csv(out_dir / "similar_history.csv", index=False)
    (out_dir / "stock_explanation.md").write_text(explanation.markdown, encoding="utf-8")
    _write_json(out_dir / "stock_explain_manifest.json", {"symbol": args.symbol.zfill(6), "news_summary": news_summary})
    trusted = explanation.report["trust_status"].isin(["trusted"]).any() if not explanation.report.empty else False
    print("Stock explanation finished.")
    print(f"Symbol: {args.symbol.zfill(6)}; source: {load_report.source}; trusted_any: {trusted}")
    print(f"Report: {out_dir}")
    if args.trusted_only and not trusted:
        print("trusted-only requested, but no trusted signal was produced.")
        return 2
    return 0


def _cmd_qmt_readonly_sync(config, output_dir: Path | None) -> int:
    broker = QMTReadOnlyBroker(account_id=config.broker.account_id, qmt_path=str(config.broker.qmt_path))
    out_dir = output_dir or Path("reports/qmt_readonly")
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = [{"broker": "qmt_readonly", "xtquant_available": broker.available(), "live_submit_enabled": False}]
    if broker.available():
        try:
            reconcile = broker.reconcile()
        except Exception as exc:  # noqa: BLE001
            reconcile = pd.DataFrame([{"error": str(exc)}])
    else:
        reconcile = pd.DataFrame([{"error": "xtquant is not installed; QMT read-only sync skipped"}])
    pd.DataFrame(rows).to_csv(out_dir / "qmt_readonly_status.csv", index=False)
    reconcile.to_csv(out_dir / "qmt_reconcile.csv", index=False)
    print("QMT read-only sync finished.")
    print(f"xtquant available: {broker.available()}; live submit enabled: False")
    print(f"Report: {out_dir}")
    return 0


def _cmd_sync_data(config, args: argparse.Namespace, source: str | None, output_dir: Path | None) -> int:
    data_config = _data_config_with_source(config, args, source)
    bars_by_symbol, load_report = load_daily_bars(data_config)
    quality = check_daily_bars(bars_by_symbol)
    frame = pd.concat(bars_by_symbol.values(), ignore_index=True) if bars_by_symbol else pd.DataFrame()
    warehouse = LocalWarehouse(config.storage.root_dir, config.storage.file_format)
    write_result = warehouse.write_table("daily_bar", frame)
    out_dir = output_dir or Path("reports/sync_data")
    out_dir.mkdir(parents=True, exist_ok=True)
    quality.summary.to_csv(out_dir / "data_quality_summary.csv", index=False)
    quality.issues.to_csv(out_dir / "data_quality_issues.csv", index=False)
    _write_json(out_dir / "sync_summary.json", {"load_report": load_report, "warehouse": write_result, "issue_count": quality.issue_count})
    print("Data sync finished.")
    print(f"Source: {load_report.source}; symbols: {len(load_report.symbols_loaded)}; rows: {len(frame)}")
    print(f"Warehouse: {write_result.path}")
    print(f"Quality report: {out_dir}")
    return 0


def _cmd_train_model(config, args: argparse.Namespace, source: str | None, output_dir: Path | None) -> int:
    data_config = _data_config_with_source(config, args, source)
    bars_by_symbol, load_report = load_daily_bars(data_config)
    out_dir = output_dir or Path("reports/model_train")
    out_dir.mkdir(parents=True, exist_ok=True)
    write_model_base_report(out_dir, discover_model_bases())
    model_type = args.model or config.model.model_type
    horizons = _parse_horizons(args, config.model.horizons)
    summary = train_model(bars_by_symbol, model_type, horizons, out_dir, config.model.registry_dir)
    try:
        registry_rows = pd.DataFrame(_read_model_registry(config.model.registry_dir))
        if not registry_rows.empty:
            LocalWarehouse(config.storage.root_dir, config.storage.file_format).write_table(
                "model_registry",
                add_source_audit_columns(registry_rows, "model_registry"),
            )
    except Exception:  # noqa: BLE001
        pass
    print("Model training finished.")
    print(f"Source: {load_report.source}; model: {model_type}; horizons: {horizons}")
    print(f"Registry: {config.model.registry_dir / 'model_registry.json'}")
    print(f"Summary: {out_dir / 'train_summary.json'}")
    return 0


def _cmd_predict_stock(config, args: argparse.Namespace, source: str | None, output_dir: Path | None) -> int:
    if not args.symbol:
        raise ValueError("predict-stock requires --symbol.")
    data_config = _data_config_with_source(config, args, source, ensure_symbol=args.symbol)
    bars_by_symbol, load_report = _load_command_bars(data_config)
    horizons = _parse_horizons(args, config.model.horizons)
    out_dir = output_dir or Path("reports/stock_forecast")
    out_dir.mkdir(parents=True, exist_ok=True)
    event_factors = None
    news_paths: dict[str, Path] = {}
    news_summary: dict[str, object] = {"with_news": bool(args.with_news)}
    if args.with_news:
        event_factors, news_paths, news_summary = _build_stock_news_context(
            config,
            args,
            source,
            list(bars_by_symbol),
            args.symbol,
            out_dir,
            bars_by_symbol=bars_by_symbol,
        )
    result = build_stock_forecast(
        bars_by_symbol,
        args.symbol,
        horizons,
        source=load_report.source,
        model_type=args.model or config.model.model_type,
        embargo_days=config.model.embargo_days,
        allow_sample=args.allow_sample,
        event_factors=event_factors,
        model_registry_dir=config.model.registry_dir,
    )
    result.forecast.to_csv(out_dir / "stock_forecast.csv", index=False)
    summary = dict(result.summary)
    summary["news_summary"] = news_summary
    summary["news_files"] = {key: str(value) for key, value in news_paths.items()}
    _write_json(out_dir / "stock_forecast.json", summary)
    trust_gates = build_stock_trust_gate_report(result.forecast, source=load_report.source, news_summary=news_summary)
    trust_gate_paths = write_stock_trust_gate_outputs(out_dir, trust_gates)
    evidence_audit = audit_stock_forecast_evidence(result.forecast, source=load_report.source, news_summary=news_summary)
    evidence_paths = write_stock_evidence_audit_outputs(out_dir, evidence_audit)
    summary["trust_gates"] = trust_gates.summary
    summary["trust_gate_files"] = {key: str(value) for key, value in trust_gate_paths.items()}
    summary["evidence_audit"] = evidence_audit.summary
    summary["evidence_audit_files"] = {key: str(value) for key, value in evidence_paths.items()}
    _write_json(out_dir / "stock_forecast.json", summary)
    _write_json(out_dir / "stock_forecast_trust_summary.json", summary)
    try:
        LocalWarehouse(config.storage.root_dir, config.storage.file_format).write_table(
            "stock_forecast",
            add_source_audit_columns(result.forecast, load_report.source),
        )
    except Exception:  # noqa: BLE001
        pass
    print("Stock forecast finished.")
    print(f"Symbol: {args.symbol.zfill(6)}; source: {load_report.source}; horizons: {horizons}")
    print(
        result.forecast[
            ["horizon_days", "prob_up", "expected_return", "direction", "trend_label", "universe_symbol_count", "trust_status"]
        ].to_string(index=False)
    )
    print(f"Trust gates: {trust_gate_paths['md']}")
    print(f"Evidence audit: {evidence_paths['md']}")
    print(f"Output: {out_dir}")
    if args.trusted_only and not result.forecast["trust_status"].isin(["trusted"]).any():
        print("trusted-only requested, but no trusted signal was produced.")
        return 2
    return 0


def _cmd_predict_kline(config, args: argparse.Namespace, source: str | None, output_dir: Path | None) -> int:
    if not args.symbol:
        raise ValueError(f"{args.command} requires --symbol.")
    data_config = _data_config_with_source(config, args, source, ensure_symbol=args.symbol)
    bars_by_symbol, load_report = _load_command_bars(data_config)
    horizons = _parse_horizons(args, [1, 5, 20, 60])
    out_dir = output_dir or Path("reports/stock_kline")
    out_dir.mkdir(parents=True, exist_ok=True)
    event_factors = None
    news_summary: dict[str, object] = {"with_news": bool(args.with_news)}
    if args.with_news:
        event_factors, _news_paths, news_summary = _build_stock_news_context(
            config,
            args,
            source,
            list(bars_by_symbol),
            args.symbol,
            out_dir,
            bars_by_symbol=bars_by_symbol,
        )
    result = build_kline_forecast(
        bars_by_symbol,
        args.symbol,
        horizons,
        source=load_report.source,
        model_type=args.model or config.model.model_type,
        days=args.days,
        history_days=args.history_days,
        embargo_days=config.model.embargo_days,
        allow_sample=args.allow_sample,
        event_factors=event_factors,
        model_registry_dir=config.model.registry_dir,
    )
    paths = save_kline_forecast_outputs(result, out_dir, source=load_report.source, news_summary=news_summary)
    try:
        LocalWarehouse(config.storage.root_dir, config.storage.file_format).write_table(
            "forecast_kline",
            add_source_audit_columns(result.forecast, load_report.source),
        )
        LocalWarehouse(config.storage.root_dir, config.storage.file_format).write_table(
            "intraday_kline",
            add_source_audit_columns(result.intraday_forecast, load_report.source),
        )
        LocalWarehouse(config.storage.root_dir, config.storage.file_format).write_table(
            "horizon_kline_summary",
            add_source_audit_columns(result.horizon_summary, load_report.source),
        )
    except Exception:  # noqa: BLE001
        pass
    base = result.forecast[result.forecast["scenario"] == "base"]
    last = base.iloc[-1] if not base.empty else None
    print("Predicted K-line forecast finished.")
    print(
        f"Symbol: {args.symbol.zfill(6)}; source: {load_report.source}; "
        f"requested_days: {result.summary.get('requested_days')}; generated_days: {result.summary.get('days')}; horizons: {horizons}"
    )
    if last is not None:
        print(
            "Base path: "
            f"close={float(last['close']):.4f}, "
            f"p10/p50/p90={float(last['p10_close']):.4f}/{float(last['p50_close']):.4f}/{float(last['p90_close']):.4f}, "
            f"prob_up={float(last['prob_up']):.3f}, trust={last['trust_status']}"
        )
    print(f"PNG: {paths['forecast_kline_png']}")
    print(f"Intraday PNG: {paths['intraday_kline_png']}")
    print(f"Intraday CSV: {paths['intraday_kline']}")
    print(f"1/5/20 summary: {paths['horizon_kline_summary']}")
    print(f"HTML: {paths['forecast_kline_html']}")
    print(f"Report: {paths['stock_prediction_report']}")
    print(f"Evidence audit: {paths['stock_evidence_audit_md']}")
    if args.trusted_only and not result.forecast["trust_status"].isin(["trusted"]).any():
        print("trusted-only requested, but no trusted signal was produced.")
        return 2
    return 0


def _cmd_backtest_stock(config, args: argparse.Namespace, source: str | None, output_dir: Path | None) -> int:
    if not args.symbol:
        raise ValueError("backtest-stock requires --symbol.")
    data_config = _data_config_with_source(config, args, source, ensure_symbol=args.symbol)
    bars_by_symbol, load_report = load_daily_bars(data_config)
    horizons = _parse_horizons(args, config.model.horizons)
    result = backtest_stock_forecast(bars_by_symbol, args.symbol, horizons)
    out_dir = output_dir or Path("reports/stock_backtest")
    out_dir.mkdir(parents=True, exist_ok=True)
    result.predictions.to_csv(out_dir / "stock_forecast_backtest.csv", index=False)
    result.metrics.to_csv(out_dir / "stock_forecast_metrics.csv", index=False)
    try:
        metrics = result.metrics.copy()
        metrics["symbol"] = args.symbol.zfill(6)
        metrics["result_type"] = "stock_forecast_metrics"
        LocalWarehouse(config.storage.root_dir, config.storage.file_format).write_table(
            "backtest_result",
            add_source_audit_columns(metrics, load_report.source),
        )
    except Exception:  # noqa: BLE001
        pass
    print("Stock forecast backtest finished.")
    print(f"Symbol: {args.symbol.zfill(6)}; source: {load_report.source}; horizons: {horizons}")
    print(result.metrics.to_string(index=False))
    print(f"Output: {out_dir}")
    return 0


def _cmd_report_stock(config, args: argparse.Namespace, source: str | None, output_dir: Path | None) -> int:
    if not args.symbol:
        raise ValueError("report-stock requires --symbol.")
    symbol = args.symbol.zfill(6)
    data_config = _data_config_with_source(config, args, source, ensure_symbol=symbol)
    bars_by_symbol, load_report = load_daily_bars(data_config)
    horizons = _parse_horizons(args, [1, 5, 20, 60])
    out_dir = output_dir or Path("reports/stock_report") / symbol
    out_dir.mkdir(parents=True, exist_ok=True)
    news_paths: dict[str, Path] = {}
    news_summary: dict[str, object] = {"with_news": bool(args.with_news)}
    event_factors = None
    if args.with_news:
        event_factors, news_paths, news_summary = _build_stock_news_context(
            config,
            args,
            source,
            list(bars_by_symbol),
            symbol,
            out_dir,
            bars_by_symbol=bars_by_symbol,
        )

    forecast_horizons = horizons
    if args.with_kline:
        forecast_horizons = sorted({1, 5, 20, 60, int(args.days or 0), *[int(item) for item in horizons if int(item) > 0]} - {0})
    full_forecast = build_stock_forecast(
        bars_by_symbol,
        symbol,
        forecast_horizons,
        source=load_report.source,
        model_type=args.model or config.model.model_type,
        embargo_days=config.model.embargo_days,
        allow_sample=args.allow_sample,
        event_factors=event_factors,
        model_registry_dir=config.model.registry_dir,
    )
    forecast = _stock_forecast_for_horizons(full_forecast, horizons)
    forecast.forecast.to_csv(out_dir / "stock_forecast.csv", index=False)
    forecast_summary = dict(forecast.summary)
    forecast_summary["news_summary"] = news_summary
    _write_json(out_dir / "stock_forecast.json", forecast_summary)
    trust_gates = build_stock_trust_gate_report(forecast.forecast, source=load_report.source, news_summary=news_summary)
    trust_gate_paths = write_stock_trust_gate_outputs(out_dir, trust_gates)
    evidence_audit = audit_stock_forecast_evidence(forecast.forecast, source=load_report.source, news_summary=news_summary)
    evidence_paths = write_stock_evidence_audit_outputs(out_dir, evidence_audit)
    forecast_summary["trust_gates"] = trust_gates.summary
    forecast_summary["trust_gate_files"] = {key: str(value) for key, value in trust_gate_paths.items()}
    forecast_summary["evidence_audit"] = evidence_audit.summary
    forecast_summary["evidence_audit_files"] = {key: str(value) for key, value in evidence_paths.items()}
    _write_json(out_dir / "stock_forecast.json", forecast_summary)

    explanation = explain_stock_forecast(bars_by_symbol, forecast, symbol, horizons)
    explanation.report.to_csv(out_dir / "stock_explanation.csv", index=False)
    explanation.similar_history.to_csv(out_dir / "similar_history.csv", index=False)
    (out_dir / "stock_explanation.md").write_text(explanation.markdown, encoding="utf-8")

    backtest = backtest_stock_forecast(bars_by_symbol, symbol, horizons)
    backtest.predictions.to_csv(out_dir / "stock_forecast_backtest.csv", index=False)
    backtest.metrics.to_csv(out_dir / "stock_forecast_metrics.csv", index=False)

    kline_paths: dict[str, Path] = {}
    if args.with_kline:
        kline = build_kline_forecast(
            bars_by_symbol,
            symbol,
            horizons,
            source=load_report.source,
            model_type=args.model or config.model.model_type,
            days=args.days,
            history_days=args.history_days,
            embargo_days=config.model.embargo_days,
            allow_sample=args.allow_sample,
            event_factors=event_factors,
            model_registry_dir=config.model.registry_dir,
            stock_forecast_override=full_forecast,
        )
        kline_paths = save_kline_forecast_outputs(
            kline,
            out_dir,
            source=load_report.source,
            news_summary=news_summary,
            evidence_prefix="kline_stock_evidence_audit",
        )
        kline.stock_forecast.forecast.to_csv(out_dir / "kline_stock_forecast.csv", index=False)
        _write_json(out_dir / "kline_stock_forecast.json", kline.stock_forecast.summary)
        kline_paths["kline_stock_forecast"] = out_dir / "kline_stock_forecast.csv"
        kline_paths["kline_stock_forecast_json"] = out_dir / "kline_stock_forecast.json"
        forecast.forecast.to_csv(out_dir / "stock_forecast.csv", index=False)
        _write_json(out_dir / "stock_forecast.json", forecast_summary)
        try:
            LocalWarehouse(config.storage.root_dir, config.storage.file_format).write_table(
                "forecast_kline",
                add_source_audit_columns(kline.forecast, load_report.source),
            )
            LocalWarehouse(config.storage.root_dir, config.storage.file_format).write_table(
                "intraday_kline",
                add_source_audit_columns(kline.intraday_forecast, load_report.source),
            )
            LocalWarehouse(config.storage.root_dir, config.storage.file_format).write_table(
                "horizon_kline_summary",
                add_source_audit_columns(kline.horizon_summary, load_report.source),
            )
        except Exception:  # noqa: BLE001
            pass

    manifest = {
        "symbol": symbol,
        "source": load_report.source,
        "horizons": horizons,
        "with_kline": bool(args.with_kline),
        "with_news": bool(args.with_news),
        "news_summary": news_summary,
        "forecast_rows": int(len(forecast.forecast)),
        "explanation_rows": int(len(explanation.report)),
        "similar_history_rows": int(len(explanation.similar_history)),
        "backtest_rows": int(len(backtest.predictions)),
        "backtest_metric_rows": int(len(backtest.metrics)),
        "trust_status_set": sorted(forecast.forecast["trust_status"].astype(str).unique().tolist()),
        "files": sorted(path.name for path in out_dir.iterdir() if path.is_file()),
        "kline_files": {key: str(value) for key, value in kline_paths.items()},
        "news_files": {key: str(value) for key, value in news_paths.items()},
        "trust_gate_files": {key: str(value) for key, value in trust_gate_paths.items()},
        "trust_gate_summary": trust_gates.summary,
        "evidence_audit_files": {key: str(value) for key, value in evidence_paths.items()},
        "evidence_audit_summary": evidence_audit.summary,
        "note": "Research reports only; not investment advice. Live trading remains disabled.",
    }
    _write_json(out_dir / "stock_report_manifest.json", manifest)
    try:
        LocalWarehouse(config.storage.root_dir, config.storage.file_format).write_table(
            "stock_forecast",
            add_source_audit_columns(forecast.forecast, load_report.source),
        )
        if not backtest.metrics.empty:
            metrics = backtest.metrics.copy()
            metrics["symbol"] = symbol
            metrics["result_type"] = "stock_forecast_metrics"
            LocalWarehouse(config.storage.root_dir, config.storage.file_format).write_table(
                "backtest_result",
                add_source_audit_columns(metrics, load_report.source),
            )
    except Exception:  # noqa: BLE001
        pass

    print("Full stock report finished.")
    print(f"Symbol: {symbol}; source: {load_report.source}; horizons: {horizons}; with_kline: {args.with_kline}; with_news: {args.with_news}")
    print(f"Report: {out_dir}")
    if args.trusted_only and not forecast.forecast["trust_status"].isin(["trusted"]).any():
        print("trusted-only requested, but no trusted signal was produced.")
        return 2
    return 0


def _stock_forecast_for_horizons(result: StockForecastResult, horizons: list[int]) -> StockForecastResult:
    requested = [int(item) for item in horizons]
    forecast = result.forecast[result.forecast["horizon_days"].astype(int).isin(requested)].copy()
    forecast = forecast.sort_values("horizon_days").reset_index(drop=True)
    summary = dict(result.summary)
    summary["horizons"] = requested
    summary["internal_horizons_available"] = [int(item) for item in result.forecast["horizon_days"].astype(int).tolist()]
    diagnostics = summary.get("diagnostics")
    if isinstance(diagnostics, dict):
        summary["diagnostics"] = {f"horizon_{h}d": diagnostics.get(f"horizon_{h}d", {}) for h in requested}
    summary["note"] = (
        f"{summary.get('note', '')} Requested report horizons are preserved; "
        "extra internal horizons may be computed for K-line charting."
    ).strip()
    return StockForecastResult(forecast=forecast, summary=summary)


def _cmd_paper_trade(config, args: argparse.Namespace, source: str | None, output_dir: Path | None) -> int:
    if args.broker == "qmt":
        qmt = QMTReadOnlyBroker(account_id=config.broker.account_id, qmt_path=str(config.broker.qmt_path))
        print("QMT read-only requested. Live order submission is disabled.")
        print(f"xtquant available: {qmt.available()}")
        return 0
    data_config = _data_config_with_source(config, args, source)
    bars_by_symbol, load_report = load_daily_bars(data_config)
    filtered_bars, universe_report = filter_universe(bars_by_symbol, config.universe)
    if not filtered_bars:
        raise RuntimeError("Universe filters removed all symbols. Relax universe config and rerun.")
    factors = compute_factor_panel(filtered_bars)
    scores = score_factors(factors, config.strategy.factor_weights)
    targets = build_rebalance_targets(scores, config.strategy)
    event_guard = None
    event_context: dict[str, dict[str, object]] = {}
    out_dir = output_dir or Path("reports/paper_trade")
    out_dir.mkdir(parents=True, exist_ok=True)
    constraint = apply_portfolio_constraints(
        targets,
        bars_by_symbol=filtered_bars,
        strategy_config=config.strategy,
        risk_config=config.risk,
        theme_membership=_theme_membership_for_symbols(targets.columns),
    )
    write_portfolio_constraint_outputs(out_dir, constraint)
    targets = constraint.adjusted_targets
    if args.with_news:
        event_factors = _load_or_build_event_factors(config, args, source, list(filtered_bars), out_dir)
        event_guard = apply_event_risk_guard(targets, event_factors, _event_risk_config(config))
        event_guard.adjusted_targets.to_csv(out_dir / "event_guarded_rebalance_targets.csv")
        event_guard.report.to_csv(out_dir / "event_risk_guard_report.csv", index=False)
        (out_dir / "event_risk_guard_report.md").write_text(event_guard.markdown, encoding="utf-8")
        _write_json(out_dir / "event_risk_guard_summary.json", event_guard.metadata)
        targets = event_guard.adjusted_targets
    bars_by_symbol = filtered_bars
    latest_target = targets.iloc[-1]
    latest_date = pd.Timestamp(targets.index[-1]).date().isoformat()
    if args.with_news:
        event_context = event_context_by_symbol(event_factors, latest_date)
    latest_prices = pd.Series({symbol: bars.sort_values("date")["close"].iloc[-1] for symbol, bars in bars_by_symbol.items()})
    order_plan = build_order_plan_from_targets(
        latest_target,
        latest_prices,
        equity=config.backtest.initial_cash,
        trade_date=args.date or latest_date,
        lot_size=config.backtest.lot_size,
    )
    risk_config = TradingRiskConfig(
        max_capital=config.risk.max_capital,
        max_single_weight=config.risk.max_single_weight,
        max_order_value=config.risk.max_order_value,
        max_daily_loss=config.risk.max_daily_loss,
        max_drawdown=config.risk.max_drawdown,
        blacklist=tuple(config.risk.blacklist),
        max_event_risk_count=config.risk.event_risk_max_count if args.with_news else None,
        min_event_impact_score=config.risk.event_risk_min_negative_impact if args.with_news else None,
        min_event_confidence=config.risk.event_risk_min_confidence,
    )
    decision = check_order_plan(
        order_plan.orders,
        risk_config,
        equity=config.backtest.initial_cash,
        event_context=event_context,
    )
    order_frame = order_plan.to_frame()
    order_frame.to_csv(out_dir / "order_plan.csv", index=False)
    decision.report.to_csv(out_dir / "risk_report.csv", index=False)
    targets.to_csv(out_dir / "rebalance_targets.csv")
    execution = None
    paper_summary: dict[str, object]
    try:
        paper_frame = order_frame.copy()
        paper_frame["risk_passed"] = decision.passed
        paper_frame["risk_reasons"] = ";".join(decision.reasons)
        LocalWarehouse(config.storage.root_dir, config.storage.file_format).write_table(
            "paper_trade",
            add_source_audit_columns(paper_frame, load_report.source),
        )
    except Exception:  # noqa: BLE001
        pass
    if decision.passed:
        broker = PaperBroker(
            initial_cash=config.backtest.initial_cash,
            fee_rate=config.backtest.fee_rate,
            tax_rate=config.backtest.tax_rate,
            slippage_rate=config.backtest.slippage_rate,
        )
        execution = broker.submit(order_plan)
        broker.save_report(execution, out_dir)
        paper_summary = {
            "passed": True,
            "requested_days": args.days,
            "no_live": args.no_live,
            "with_news": bool(args.with_news),
            "portfolio_constraints": constraint.metadata,
            "event_risk_guard": event_guard.metadata if event_guard is not None else {"enabled": False},
            "metadata": execution.metadata,
        }
        _write_json(
            out_dir / "paper_summary.json",
            paper_summary,
        )
    else:
        paper_summary = {
            "passed": False,
            "requested_days": args.days,
            "no_live": args.no_live,
            "with_news": bool(args.with_news),
            "portfolio_constraints": constraint.metadata,
            "event_risk_guard": event_guard.metadata if event_guard is not None else {"enabled": False},
            "reasons": decision.reasons,
        }
        _write_json(
            out_dir / "paper_summary.json",
            paper_summary,
        )
    paper_validation = validate_paper_trade(
        order_frame,
        decision.report,
        paper_summary,
        executions=execution.executions if execution is not None else None,
        positions=execution.positions if execution is not None else None,
        requested_days=max(1, int(args.days or 20)),
        no_live_required=True,
    )
    write_paper_trade_validation_outputs(out_dir, paper_validation)
    print("Paper trade dry-run finished.")
    print(f"Source: {load_report.source}; selected universe: {len(universe_report.selected_symbols)}")
    print(f"Risk passed: {decision.passed}; orders: {len(order_plan.orders)}; requested days: {args.days}; no-live: {args.no_live}")
    print(f"Output: {out_dir}")
    return 0


def _symbols_for_universe_arg(args: argparse.Namespace, config) -> list[str]:
    universe = (args.universe or "config").strip()
    normalized = universe.lower().replace("_", "-")
    if normalized == "config":
        return list(config.data.symbols)
    if normalized in {"hot", "mega-hot", "all-hot", "core-hot", "professional", "professional-hot", "pro-hot"}:
        return symbols_for_themes(normalized)
    if normalized in {"all-a", "all-a-free", "all-free"}:
        symbols = _try_fetch_all_a_symbols()
        return symbols or symbols_for_themes("mega-hot")
    return [item.strip().zfill(6) for item in universe.split(",") if item.strip()]


def _theme_membership_for_symbols(symbols) -> pd.DataFrame:
    wanted = {str(symbol).zfill(6) for symbol in symbols}
    if not wanted:
        return pd.DataFrame()
    try:
        membership = symbol_theme_membership(build_theme_universe("hot"))
    except Exception:  # noqa: BLE001
        return pd.DataFrame()
    if membership.empty or "symbol" not in membership.columns:
        return pd.DataFrame()
    return membership[membership["symbol"].astype(str).str.zfill(6).isin(wanted)].reset_index(drop=True)


def _event_risk_config(config) -> EventRiskConfig:
    return EventRiskConfig(
        enabled=config.risk.event_risk_enabled,
        max_event_risk_count=config.risk.event_risk_max_count,
        min_negative_impact=config.risk.event_risk_min_negative_impact,
        min_confidence=config.risk.event_risk_min_confidence,
        weight_multiplier=config.risk.event_risk_weight_multiplier,
        block_new_buy=config.risk.event_risk_block_new_buy,
        max_event_age_days=config.risk.event_risk_max_age_days,
    )


def _load_or_sync_events(config, args: argparse.Namespace, source: str | None, symbols: list[str]) -> pd.DataFrame:
    raw, _warnings = _load_or_sync_events_with_warnings(config, args, source, symbols)
    return raw


def _load_or_sync_events_with_warnings(config, args: argparse.Namespace, source: str | None, symbols: list[str]) -> tuple[pd.DataFrame, list[str]]:
    event_source = _event_source_from_data_source(config, args, source)
    warehouse = LocalWarehouse(config.storage.root_dir, config.storage.file_format)
    try:
        raw = warehouse.read_table("raw_events")
        if not raw.empty:
            wanted = set(str(symbol).zfill(6) for symbol in symbols)
            symbol_col = raw["symbol"].astype(str).str.zfill(6) if "symbol" in raw.columns else pd.Series([], dtype=str)
            source_mask = _event_source_mask(raw, event_source)
            filtered = raw[symbol_col.isin(wanted) & source_mask].copy()
            if not filtered.empty:
                covered = set(filtered["symbol"].astype(str).str.zfill(6)) if "symbol" in filtered.columns else set()
                missing = sorted(wanted - covered)
                if not missing:
                    return filtered, []
                fetched, warnings = sync_public_events(
                    missing,
                    args.start or config.data.start_date,
                    config.data.end_date,
                    source=event_source,
                    fetch_announcement_text=bool(getattr(args, "fetch_announcement_text", False)),
                    max_pages=int(getattr(args, "max_pages", 1) or 1),
                )
                combined = pd.concat([filtered, fetched], ignore_index=True, sort=False) if not fetched.empty else filtered
                if event_source != "sample" and not fetched.empty:
                    try:
                        warehouse.write_table("raw_events", add_source_audit_columns(combined, event_source, quality_flag="raw_event"))
                    except Exception:  # noqa: BLE001
                        pass
                return combined, warnings
    except Exception:  # noqa: BLE001
        pass
    raw, warnings = sync_public_events(
        symbols,
        args.start or config.data.start_date,
        config.data.end_date,
        source=event_source,
        fetch_announcement_text=bool(getattr(args, "fetch_announcement_text", False)),
        max_pages=int(getattr(args, "max_pages", 1) or 1),
    )
    if event_source != "sample":
        try:
            warehouse.write_table("raw_events", add_source_audit_columns(raw, event_source, quality_flag="raw_event"))
        except Exception:  # noqa: BLE001
            pass
    return raw, warnings


def _load_or_build_event_factors(
    config,
    args: argparse.Namespace,
    source: str | None,
    symbols: list[str],
    output_dir: Path | None = None,
) -> pd.DataFrame:
    wanted = set(str(symbol).zfill(6) for symbol in symbols)
    warehouse = LocalWarehouse(config.storage.root_dir, config.storage.file_format)
    raw, source_warnings = _load_or_sync_events_with_warnings(config, args, source, symbols)
    result = build_event_store(raw, symbols)
    if source_warnings:
        result = replace(result, warnings=[*source_warnings, *result.warnings])
    if output_dir is not None:
        event_dir = output_dir / "event_inputs"
        write_event_outputs(result, event_dir, symbols=symbols)
    if not _uses_sample_events(config, args, source):
        try:
            warehouse.write_table("event_store", add_source_audit_columns(result.event_store, "event_store_v04"))
            warehouse.write_table("event_factor", add_source_audit_columns(result.event_factors, "event_factor_v04"))
        except Exception:  # noqa: BLE001
            pass
    if result.event_factors.empty or "symbol" not in result.event_factors.columns:
        return result.event_factors
    return result.event_factors[result.event_factors["symbol"].astype(str).str.zfill(6).isin(wanted)].copy()


def _event_source_mask(frame: pd.DataFrame, event_source: str) -> pd.Series:
    if "source" not in frame.columns:
        return pd.Series(True, index=frame.index)
    source_text = frame["source"].astype(str).str.lower()
    sample_like = source_text.str.contains("sample", na=False)
    if event_source == "sample":
        return sample_like | source_text.eq("sample")
    if event_source in {"cninfo", "cninfo_direct", "direct_cninfo"}:
        return source_text.str.contains("cninfo_direct|direct_cninfo", na=False)
    if event_source in official_public_source_ids():
        return source_text.eq(event_source)
    return ~sample_like


def _event_source_from_data_source(config, args: argparse.Namespace, source: str | None) -> str:
    if _uses_sample_events(config, args, source):
        return "sample"
    data_source = str(source or config.data.source or "akshare").lower()
    if data_source in {"cninfo", "cninfo_direct", "direct_cninfo"}:
        return "cninfo_direct"
    if data_source in official_public_source_ids():
        return data_source
    return "akshare"


def _uses_sample_events(config, args: argparse.Namespace, source: str | None) -> bool:
    return (source or config.data.source) == "sample" or bool(args.allow_sample)


def _build_stock_news_context(
    config,
    args: argparse.Namespace,
    source: str | None,
    symbols: list[str],
    symbol: str,
    output_dir: Path,
    bars_by_symbol: dict[str, pd.DataFrame] | None = None,
) -> tuple[pd.DataFrame | None, dict[str, Path], dict[str, object]]:
    symbol = symbol.zfill(6)
    event_symbols = [str(item).zfill(6) for item in symbols]
    if symbol not in event_symbols:
        event_symbols.append(symbol)
    raw_events, source_warnings = _load_or_sync_events_with_warnings(config, args, source, event_symbols)
    event_result = build_event_store(raw_events, event_symbols)
    if source_warnings:
        event_result = replace(event_result, warnings=[*source_warnings, *event_result.warnings])
    news_paths = write_event_outputs(event_result, output_dir, symbols=event_symbols)
    symbol_evidence = build_news_evidence_report(event_result.event_store, event_result.event_factors, symbol=symbol)
    (output_dir / "stock_news_evidence.md").write_text(symbol_evidence, encoding="utf-8")
    symbol_events = event_result.event_store[event_result.event_store["symbol"].astype(str).str.zfill(6) == symbol]
    symbol_factors = event_result.event_factors[event_result.event_factors["symbol"].astype(str).str.zfill(6) == symbol]
    symbol_events.to_csv(output_dir / "stock_event_store.csv", index=False)
    symbol_factors.to_csv(output_dir / "stock_event_factors.csv", index=False)
    similar_events = build_similar_event_report(
        event_result.event_store,
        bars_by_symbol=bars_by_symbol or {},
        symbol=symbol,
        horizons=tuple(_parse_horizons(args, [1, 5, 20])),
    )
    similar_paths = write_similar_event_outputs(output_dir, similar_events, prefix="stock_similar_events")
    impact_horizons = tuple(_parse_horizons(args, [1, 5, 20, 60]))
    impact_event_store, impact_bars, impact_limit_summary = _limit_event_impact_scope(
        event_result.event_store,
        bars_by_symbol or {},
        symbol,
        int(getattr(args, "max_event_impact_symbols", 80) or 0),
        int(getattr(args, "max_event_impact_events", 1500) or 0),
    )
    impact_result = analyze_event_impact(
        impact_event_store,
        impact_bars,
        horizons=impact_horizons,
        min_prior_rows=int(getattr(args, "min_prior_rows", 20) or 20),
    )
    impact_paths = write_event_impact_outputs(output_dir, impact_result, prefix="stock_event_impact_study")
    symbol_impact_returns = impact_result.event_returns[
        impact_result.event_returns["symbol"].astype(str).str.zfill(6) == symbol
    ] if not impact_result.event_returns.empty and "symbol" in impact_result.event_returns.columns else pd.DataFrame()
    symbol_pit_priors = impact_result.pit_priors[
        impact_result.pit_priors["symbol"].astype(str).str.zfill(6) == symbol
    ] if not impact_result.pit_priors.empty and "symbol" in impact_result.pit_priors.columns else pd.DataFrame()
    symbol_impact_returns.to_csv(output_dir / "stock_event_impact_returns.csv", index=False)
    symbol_pit_priors.to_csv(output_dir / "stock_event_impact_pit_priors.csv", index=False)
    if not _uses_sample_events(config, args, source):
        try:
            warehouse = LocalWarehouse(config.storage.root_dir, config.storage.file_format)
            warehouse.write_table("event_store", add_source_audit_columns(event_result.event_store, "event_store_v04"))
            warehouse.write_table("event_factor", add_source_audit_columns(event_result.event_factors, "event_factor_v04"))
        except Exception:  # noqa: BLE001
            pass
    news_summary = {
        "with_news": True,
        "event_rows": int(len(symbol_events)),
        "event_factor_rows": int(len(symbol_factors)),
        "event_types": sorted(symbol_events["event_type"].astype(str).unique().tolist()) if not symbol_events.empty else [],
        "latest_event_title": str(symbol_events.sort_values("published_at")["title"].iloc[-1]) if not symbol_events.empty else "",
        "similar_event_rows": int(len(similar_events.matches)),
        "similar_event_known_return_rows_5d": int(similar_events.summary.get("known_return_rows_5d", 0) or 0),
        "similar_event_positive_rate_5d": float(similar_events.summary.get("positive_rate_5d", 0.0) or 0.0),
        "similar_event_summary": similar_events.summary,
        "event_impact_rows": int(len(symbol_impact_returns)),
        "event_impact_pit_prior_rows": int(len(symbol_pit_priors)),
        "event_impact_pit_ready_rows": int(symbol_pit_priors["pit_ready"].astype(bool).sum()) if not symbol_pit_priors.empty and "pit_ready" in symbol_pit_priors.columns else 0,
        "event_impact_summary": impact_result.summary,
        "event_impact_scope": impact_limit_summary,
    }
    news_paths.update({f"similar_{key}": value for key, value in similar_paths.items()})
    news_paths.update({f"impact_{key}": value for key, value in impact_paths.items()})
    news_paths["stock_event_impact_returns"] = output_dir / "stock_event_impact_returns.csv"
    news_paths["stock_event_impact_pit_priors"] = output_dir / "stock_event_impact_pit_priors.csv"
    return event_result.event_factors, news_paths, news_summary


def _limit_event_impact_scope(
    event_store: pd.DataFrame,
    bars_by_symbol: dict[str, pd.DataFrame],
    symbol: str,
    max_symbols: int,
    max_events: int,
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame], dict[str, object]]:
    symbol = symbol.zfill(6)
    if event_store is None or event_store.empty:
        return pd.DataFrame(), {}, {
            "limited": False,
            "reason": "empty_event_store",
            "input_symbols": len(bars_by_symbol),
            "used_symbols": 0,
            "input_events": 0,
            "used_events": 0,
            "max_symbols": int(max_symbols),
            "max_events": int(max_events),
        }
    events = event_store.copy()
    events["symbol"] = events["symbol"].astype(str).str.replace(r"\D", "", regex=True).str[-6:].str.zfill(6)
    selected_symbols = _rank_event_impact_symbols(events, bars_by_symbol, symbol, max_symbols)
    scoped_events = events[events["symbol"].isin(selected_symbols)].copy()
    input_event_rows = int(len(scoped_events))
    if max_events > 0 and len(scoped_events) > max_events:
        scoped_events = _rank_event_rows_for_impact(scoped_events, symbol).head(max_events).sort_values(["published_at", "symbol"])
    scoped_bars = {code: bars for code, bars in bars_by_symbol.items() if str(code).zfill(6) in set(scoped_events["symbol"].astype(str).str.zfill(6))}
    if symbol in bars_by_symbol and symbol not in scoped_bars:
        scoped_bars[symbol] = bars_by_symbol[symbol]
    summary = {
        "limited": bool(len(selected_symbols) < len(bars_by_symbol) or len(scoped_events) < input_event_rows),
        "input_symbols": int(len(bars_by_symbol)),
        "used_symbols": int(len(scoped_bars)),
        "input_events": int(len(event_store)),
        "candidate_events_after_symbol_limit": input_event_rows,
        "used_events": int(len(scoped_events)),
        "max_symbols": int(max_symbols),
        "max_events": int(max_events),
        "target_symbol_forced": bool(symbol in scoped_bars),
        "reason": "bounded_stock_report_event_impact_runtime;event_factors_still_use_full_event_store",
    }
    return scoped_events, scoped_bars, summary


def _rank_event_impact_symbols(
    events: pd.DataFrame,
    bars_by_symbol: dict[str, pd.DataFrame],
    symbol: str,
    max_symbols: int,
) -> list[str]:
    symbol = symbol.zfill(6)
    available = {str(item).zfill(6) for item in bars_by_symbol}
    if not available:
        available = set(events["symbol"].astype(str).str.zfill(6).unique().tolist())
    counts = events[events["symbol"].isin(available)]["symbol"].value_counts()
    ranked = [symbol]
    for code in counts.index.astype(str).str.zfill(6).tolist():
        if code != symbol:
            ranked.append(code)
    for code in sorted(available):
        if code not in ranked:
            ranked.append(code)
    if max_symbols > 0:
        ranked = ranked[:max_symbols]
    return ranked


def _rank_event_rows_for_impact(events: pd.DataFrame, symbol: str) -> pd.DataFrame:
    frame = events.copy()
    symbol = symbol.zfill(6)
    frame["published_at_ts"] = pd.to_datetime(frame.get("published_at", ""), errors="coerce")
    frame["is_target_symbol"] = frame["symbol"].astype(str).str.zfill(6).eq(symbol).astype(int)
    if "source_reliability" not in frame.columns:
        frame["source_reliability"] = 0.0
    if "entity_link_confidence" not in frame.columns:
        frame["entity_link_confidence"] = 0.0
    if "weighted_impact_score" not in frame.columns:
        frame["weighted_impact_score"] = frame.get("impact_score", 0.0)
    frame["_source_reliability_num"] = pd.to_numeric(frame["source_reliability"], errors="coerce").fillna(0.0)
    frame["_entity_link_confidence_num"] = pd.to_numeric(frame["entity_link_confidence"], errors="coerce").fillna(0.0)
    frame["_impact_abs"] = pd.to_numeric(frame["weighted_impact_score"], errors="coerce").fillna(0.0).abs()
    return frame.sort_values(
        ["is_target_symbol", "_source_reliability_num", "_entity_link_confidence_num", "_impact_abs", "published_at_ts"],
        ascending=[False, False, False, False, False],
    )


def _try_fetch_all_a_symbols() -> list[str]:
    frame = _try_fetch_all_a_universe_frame()
    if not frame.empty:
        return sorted(frame["symbol"].astype(str).str.zfill(6).unique().tolist())
    return []


def _try_fetch_all_a_universe_frame() -> pd.DataFrame:
    for loader in (_fetch_akshare_all_a_universe, _fetch_baostock_all_a_universe):
        try:
            frame = loader()
        except Exception:  # noqa: BLE001
            continue
        if not frame.empty:
            return _normalize_universe_output_columns(frame)
    return pd.DataFrame(
        columns=["theme", "theme_group", "symbol", "name", "reason", "seed_rank", "seed_weight", "source_note", "source", "notes"]
    )


def _fetch_akshare_all_a_universe() -> pd.DataFrame:
    import akshare as ak  # type: ignore

    raw = ak.stock_info_a_code_name()
    symbol_col = _infer_symbol_column(raw)
    name_col = _infer_name_column(raw, symbol_col)
    if symbol_col is None:
        return pd.DataFrame()
    out = pd.DataFrame()
    out["symbol"] = raw[symbol_col].astype(str).str.replace(r"\D", "", regex=True).str[-6:].str.zfill(6)
    out["name"] = raw[name_col].astype(str).str.strip() if name_col else out["symbol"].map(lambda value: f"A-share {value}")
    return _all_a_rows_from_names(out, "akshare_stock_info_a_code_name")


def _fetch_baostock_all_a_universe() -> pd.DataFrame:
    try:
        import baostock as bs  # type: ignore

        login = bs.login()
        if getattr(login, "error_code", "0") == "0":
            query = bs.query_all_stock()
            rows = []
            while query.next():
                rows.append(query.get_row_data())
            bs.logout()
            if rows:
                frame = pd.DataFrame(rows, columns=query.fields)
                if "code" in frame.columns:
                    out = pd.DataFrame()
                    out["symbol"] = frame["code"].astype(str).str.replace(".", "", regex=False).str[-6:].str.zfill(6)
                    name_col = "code_name" if "code_name" in frame.columns else _infer_name_column(frame, "code")
                    out["name"] = frame[name_col].astype(str).str.strip() if name_col else out["symbol"].map(lambda value: f"A-share {value}")
                    return _all_a_rows_from_names(out, "baostock_query_all_stock")
    except Exception:  # noqa: BLE001
        return pd.DataFrame()
    return pd.DataFrame()


def _all_a_rows_from_names(frame: pd.DataFrame, source_note: str) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    clean = frame.copy()
    clean["symbol"] = clean["symbol"].astype(str).str.zfill(6)
    clean = clean[clean["symbol"].str.fullmatch(r"\d{6}", na=False)]
    clean = clean.drop_duplicates("symbol").sort_values("symbol").reset_index(drop=True)
    curated_theme = _curated_primary_theme_by_symbol()
    clean["theme"] = [
        curated_theme.get(symbol) or _classify_free_theme(name)
        for symbol, name in zip(clean["symbol"].astype(str), clean["name"].astype(str), strict=False)
    ]
    clean["theme_group"] = "all_a_free"
    clean["reason"] = "free all-A stock list; theme inferred from public name keywords"
    clean["seed_rank"] = clean.index + 1
    clean["seed_weight"] = 1.0 / clean["seed_rank"]
    clean["source_note"] = source_note
    return clean[["theme", "theme_group", "symbol", "name", "reason", "seed_rank", "seed_weight", "source_note"]]


def _augment_hot_universe_with_free_market(frame: pd.DataFrame, minimum_symbols: int, target_symbols: int) -> pd.DataFrame:
    if frame.empty or int(frame["symbol"].nunique()) >= minimum_symbols:
        return frame
    all_a = _try_fetch_all_a_universe_frame()
    if all_a.empty:
        return frame
    existing = set(frame["symbol"].astype(str).str.zfill(6))
    needed = max(0, target_symbols - len(existing))
    extension = all_a[~all_a["symbol"].astype(str).str.zfill(6).isin(existing)].head(needed).copy()
    if extension.empty:
        return frame
    extension["theme_group"] = "free_market_extension"
    extension["reason"] = "free all-A extension added to make mega-hot large enough for cross-sectional validation"
    extension["source_note"] = extension["source_note"].astype(str) + ";mega_hot_extension"
    extension["seed_rank"] = range(1, len(extension) + 1)
    extension["seed_weight"] = 1.0 / extension["seed_rank"].astype(float)
    return pd.concat([frame, extension[frame.columns]], ignore_index=True, sort=False)


def _curated_universe_as_all_a_fallback() -> pd.DataFrame:
    frame = build_theme_universe("mega-hot").copy()
    frame["theme_group"] = "all_a_free_fallback"
    frame["source_note"] = frame["source_note"].astype(str) + ";all_a_free_fetch_failed"
    frame["reason"] = frame["reason"].astype(str) + "; all-a free fetch failed"
    return frame


def _normalize_universe_output_columns(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    if out.empty:
        return out
    out["symbol"] = out["symbol"].astype(str).str.zfill(6)
    if "source" not in out.columns:
        out["source"] = out.get("source_note", "curated_public_hot_seed")
    if "notes" not in out.columns:
        out["notes"] = out.get("reason", "")
    return out.reset_index(drop=True)


def _infer_symbol_column(frame: pd.DataFrame) -> str | None:
    for column in frame.columns:
        values = frame[column].astype(str).str.strip()
        if values.str.fullmatch(r"\d{6}").mean() > 0.50:
            return str(column)
    return None


def _infer_name_column(frame: pd.DataFrame, symbol_col: str | None) -> str | None:
    preferred = {"name", "名称", "股票简称", "code_name", "证券简称"}
    for column in frame.columns:
        if str(column) in preferred:
            return str(column)
    for column in frame.columns:
        if symbol_col is not None and str(column) == str(symbol_col):
            continue
        values = frame[column].astype(str).str.strip()
        if values.str.len().between(2, 12).mean() > 0.50 and values.str.fullmatch(r"\d{6}").mean() < 0.10:
            return str(column)
    return None


def _curated_primary_theme_by_symbol() -> dict[str, str]:
    try:
        curated = build_theme_universe("hot")
    except Exception:  # noqa: BLE001
        return {}
    if curated.empty:
        return {}
    priority = {"professional_hot": 0, "core_hot": 1, "expanded_hot": 2}
    ranked = curated.copy()
    ranked["theme_priority"] = ranked["theme_group"].map(priority).fillna(9).astype(int)
    ranked = ranked.sort_values(["symbol", "theme_priority", "seed_rank", "theme"])
    return ranked.drop_duplicates("symbol").set_index("symbol")["theme"].astype(str).to_dict()


def _classify_free_theme_keywords(name: object) -> str:
    text = str(name)
    buckets = [
        ("ai_compute_semiconductor", ["半导体", "芯片", "微电", "光电", "算力", "服务器", "浪潮", "曙光", "集成", "电子科技", "中芯"]),
        ("datacenter_optical_liquid_cooling", ["光模块", "光通信", "数据中心", "液冷", "光迅", "中际", "新易盛", "胜宏", "沪电"]),
        ("robotics_highend_manufacturing", ["机器人", "机床", "自动化", "精密", "机械", "数控", "激光", "电机", "伺服"]),
        ("metals_energy_metals", ["铜", "铝", "锌", "锡", "钨", "钼", "锂", "黄金", "稀土", "有色", "矿", "钴", "镍"]),
        ("power_solid_state_battery", ["电池", "锂电", "新能源", "储能", "电力", "光伏", "风电", "电气", "固态"]),
        ("defense_ship_equipment", ["航天", "航空", "船", "卫星", "军", "兵", "中船", "中国船", "北斗", "无人机"]),
        ("innovative_drug_medical_device", ["药", "医", "生物", "医疗", "制药", "器械", "基因", "疫苗", "诊断"]),
        ("consumer_electronics_pcb", ["电子", "消费", "视源", "歌尔", "立讯", "鹏鼎", "沪电", "PCB", "面板", "显示"]),
        ("data_element_fintech_ai_app", ["数据", "传媒", "互联", "金融", "证券", "银行", "保险", "信安", "安全", "软件", "云"]),
        ("central_soe_high_dividend", ["中国", "中远", "中粮", "中交", "中煤", "中石", "国电", "华能", "大唐", "长江电力"]),
        ("agriculture_food_beverage", ["食品", "酒", "乳", "农", "牧", "饮料", "消费", "种业", "饲料"]),
        ("chemical_new_materials", ["化工", "材料", "新材", "硅", "氟", "碳纤", "石化", "化学"]),
        ("coal_power_oil_gas", ["煤", "电力", "石油", "油气", "能源", "燃气", "核电"]),
        ("shipping_ports_logistics", ["航运", "港", "物流", "快递", "中远海", "招商港"]),
        ("home_appliance_export", ["家电", "美的", "海尔", "格力", "电器", "照明"]),
        ("real_estate_chain", ["地产", "置业", "建筑", "水泥", "工程", "建材", "家居"]),
        ("tourism_retail_services", ["旅游", "酒店", "免税", "零售", "百货", "餐饮"]),
        ("environmental_water_gas", ["环保", "水务", "燃气", "节能", "环卫"]),
    ]
    for theme, keywords in buckets:
        if any(keyword in text for keyword in keywords):
            return theme
    return "mega_hot_free_market_extension"


def _classify_free_theme(name: object) -> str:
    return _classify_free_theme_keywords(name)
    text = str(name)
    buckets = [
        ("ai_compute_semiconductor", ["半导体", "芯片", "微电", "光电", "光迅", "中际", "浪潮", "曙光", "软件", "科技"]),
        ("robotics_highend_manufacturing", ["机器人", "机床", "自动", "精密", "机械", "数控", "激光", "电机"]),
        ("metals_energy_metals", ["铜", "铝", "锂", "钴", "镍", "锡", "锌", "黄金", "稀土", "有色", "矿", "钨", "钛"]),
        ("power_solid_state_battery", ["电池", "锂电", "新能源", "储能", "电力", "光伏", "风电", "能源", "电气"]),
        ("defense_ship_equipment", ["航天", "航空", "船", "卫星", "军", "兵", "中航", "中国船"]),
        ("innovative_drug_medical_device", ["药", "医", "生物", "医疗", "制药", "器械", "基因"]),
        ("consumer_electronics_pcb", ["电子", "消费", "视源", "歌尔", "立讯", "鹏鼎", "沪电"]),
        ("data_element_fintech_ai_app", ["数据", "传媒", "互联", "金融", "证券", "银行", "保险", "信安", "安全"]),
        ("central_soe_high_dividend", ["中国", "中远", "中铁", "中交", "中煤", "中石", "国电", "华能", "大唐", "银行"]),
        ("agriculture_food_beverage", ["食品", "酒", "乳", "农", "牧", "饮料", "消费"]),
        ("construction_infrastructure", ["建", "路桥", "水泥", "工程", "地产", "基建"]),
        ("environmental_water_gas", ["环保", "水务", "燃气", "节能", "环卫"]),
    ]
    for theme, keywords in buckets:
        if any(keyword in text for keyword in keywords):
            return theme
    return "mega_hot_free_market_extension"


def _read_model_registry(registry_dir: Path) -> list[dict[str, object]]:
    path = registry_dir / "model_registry.json"
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _write_yearly_evaluation(out_dir: Path) -> None:
    candidates = [
        out_dir / "walk_forward_predictions.csv",
        Path("reports/walk_forward/walk_forward_predictions.csv"),
    ]
    for path in candidates:
        if path.exists():
            frame = pd.read_csv(path)
            if "date" in frame.columns and "prob_up" in frame.columns:
                frame["year"] = pd.to_datetime(frame["date"]).dt.year
                direction_col = next((name for name in frame.columns if name.startswith("direction_up_")), None)
                ret_col = next((name for name in frame.columns if name.startswith("future_return_")), None)
                grouped = frame.groupby("year").apply(
                    lambda part: pd.Series(
                        {
                            "rows": len(part),
                            "direction_accuracy": float(((part["prob_up"] >= 0.5).astype(int) == part[direction_col].astype(int)).mean())
                            if direction_col
                            else 0.0,
                            "mean_forward_return": float(part[ret_col].mean()) if ret_col else 0.0,
                        }
                    ),
                    include_groups=False,
                )
                grouped.reset_index().to_csv(out_dir / "evaluation_by_year.csv", index=False)
                return
    pd.DataFrame([{"year": "", "note": "walk_forward_predictions.csv not found"}]).to_csv(out_dir / "evaluation_by_year.csv", index=False)


def _data_config_with_source(config, args: argparse.Namespace, source: str | None, ensure_symbol: str | None = None):
    data_source = source or config.data.source
    if args.universe:
        symbols = _symbols_for_universe_arg(args, config)
    else:
        symbols = list(config.data.symbols)
    if args.themes:
        symbols = symbols_for_themes(args.themes)
    if not symbols:
        symbols = symbols_for_themes("core-hot")
    if getattr(args, "max_symbols", 0) and args.max_symbols > 0 and len(symbols) > args.max_symbols:
        symbols = list(symbols)[: args.max_symbols]
    if ensure_symbol:
        normalized = ensure_symbol.zfill(6)
        if normalized not in symbols:
            symbols.append(normalized)
    return replace(config.data, source=data_source, symbols=symbols, start_date=args.start or config.data.start_date)


def _write_json(path: Path, value: object) -> None:
    def default(item: object) -> object:
        if hasattr(item, "__dict__"):
            return {key: default(val) for key, val in vars(item).items()}
        if isinstance(item, Path):
            return str(item)
        return str(item)

    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=default), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
