from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

import pandas as pd

from aquant_mvp.backtest import backtest_stock_forecast
from aquant_mvp.broker import PaperBroker, QMTReadOnlyBroker, build_order_plan_from_targets
from aquant_mvp.config import load_config
from aquant_mvp.data import add_source_audit_columns, audit_point_in_time_tables, check_daily_bars, load_daily_bars
from aquant_mvp.data.providers import LoadReport
from aquant_mvp.features import build_point_in_time_feature_store
from aquant_mvp.factors import compute_factor_panel
from aquant_mvp.foundations import discover_foundations, write_foundation_report
from aquant_mvp.modeling import train_model, train_walk_forward
from aquant_mvp.pipeline import run_pipeline
from aquant_mvp.prediction import build_stock_forecast, explain_stock_forecast
from aquant_mvp.risk import TradingRiskConfig, check_order_plan
from aquant_mvp.sources import discover_domestic_sources, write_source_coverage
from aquant_mvp.storage import LocalWarehouse
from aquant_mvp.strategy import build_rebalance_targets, score_factors
from aquant_mvp.tooling import discover_tools, write_tool_report
from aquant_mvp.universe import build_theme_universe, symbol_theme_membership, symbols_for_themes, theme_universe_summary
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
            "backtest-stock",
            "paper-trade",
            "live-trade",
            "discover-sources",
            "discover-foundations",
            "discover-tools",
            "sync-free-all",
            "audit-data",
            "build-feature-store",
            "train-walk-forward",
            "evaluate-models",
            "explain-stock",
            "qmt-readonly-sync",
        ],
    )
    parser.add_argument("--config", default="configs/mvp.json", help="Path to JSON/YAML config.")
    parser.add_argument(
        "--source",
        choices=["sample", "akshare", "auto", "free_real", "research", "baostock", "tushare"],
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
    parser.add_argument("--strict-pit", action="store_true", help="Treat missing point-in-time metadata as audit issues.")
    parser.add_argument("--point-in-time", action="store_true", help="Build PIT feature store with effective dates.")
    parser.add_argument("--trusted-only", action="store_true", help="Require trusted/weak-free prediction metadata when available.")
    parser.add_argument("--by-year", action="store_true", help="Write yearly evaluation slices.")
    parser.add_argument("--by-industry", action="store_true", help="Write industry evaluation placeholder slices.")
    parser.add_argument("--days", type=int, default=1, help="Number of dry-run paper trading days to simulate.")
    parser.add_argument("--no-live", action="store_true", help="Explicitly forbid live trading in paper/QMT workflows.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(args.config)
    source = _effective_source(args)
    output_dir = Path(args.output_dir) if args.output_dir else None

    if args.command == "build-universe":
        return _cmd_build_universe(args, output_dir)

    if args.command == "discover-sources":
        return _cmd_discover_sources(args, output_dir)

    if args.command == "discover-foundations":
        return _cmd_discover_foundations(output_dir)

    if args.command == "discover-tools":
        return _cmd_discover_tools(output_dir)

    if args.command == "sync-free-all":
        return _cmd_sync_free_all(config, args, source, output_dir)

    if args.command == "audit-data":
        return _cmd_audit_data(config, args, output_dir)

    if args.command == "build-feature-store":
        return _cmd_build_feature_store(config, args, source, output_dir)

    if args.command == "train-walk-forward":
        return _cmd_train_walk_forward(config, args, source, output_dir)

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
        bars_by_symbol, load_report = load_daily_bars(data_config)
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
    elif args.command == "backtest":
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


def _cmd_build_universe(args: argparse.Namespace, output_dir: Path | None) -> int:
    themes = args.themes or args.universe or "hot"
    frame = build_theme_universe(themes)
    summary = theme_universe_summary(frame)
    membership = symbol_theme_membership(frame)
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
    duplicate_rows = int(len(frame) - unique_symbols)
    _write_json(
        manifest_path,
        {
            "requested_themes": themes,
            "theme_count": int(frame["theme"].nunique()) if not frame.empty else 0,
            "rows": int(len(frame)),
            "unique_symbols": unique_symbols,
            "duplicate_theme_rows": duplicate_rows,
            "multi_theme_symbols": int((membership["theme_count"] > 1).sum()) if not membership.empty else 0,
            "minimum_symbols_for_trusted_prediction": 200,
            "notes": [
                "This is a curated hot-sector seed universe, not an official industry classifier.",
                "Use --universe all-a for maximum market coverage when free source availability allows it.",
            ],
        },
    )
    print("Hot theme universe generated.")
    print(f"Themes: {frame['theme'].nunique()}; rows: {len(frame)}; unique symbols: {unique_symbols}")
    print(f"Output: {path}")
    print(f"Summary: {summary_path}")
    print(f"Membership: {membership_path}")
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
    loaded: dict[str, pd.DataFrame] = {}
    warnings: list[str] = []
    for idx, symbol in enumerate(symbols, start=1):
        data_config = replace(config.data, source=source, symbols=[symbol], start_date=start_date)
        try:
            bars_by_symbol, report = load_daily_bars(data_config)
        except Exception as exc:  # noqa: BLE001 - large free-source jobs must keep the audit trail moving.
            warnings.append(f"{symbol}: failed to load ({exc})")
            continue
        loaded.update(bars_by_symbol)
        warnings.extend(report.warnings)
        if args.max_symbols and idx >= args.max_symbols:
            break
    return loaded, LoadReport(source=source, symbols_loaded=sorted(loaded), warnings=warnings)


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


def _cmd_build_feature_store(config, args: argparse.Namespace, source: str | None, output_dir: Path | None) -> int:
    data_config = _data_config_with_source(config, args, source)
    bars_by_symbol, load_report = load_daily_bars(data_config)
    horizons = _parse_horizons(args, config.model.horizons)
    result = build_point_in_time_feature_store(bars_by_symbol, horizons, load_report.source)
    warehouse = LocalWarehouse(config.storage.root_dir, config.storage.file_format)
    write_result = warehouse.write_table("feature_store", result.features)
    out_dir = output_dir or Path("reports/feature_store")
    out_dir.mkdir(parents=True, exist_ok=True)
    result.features.head(2000).to_csv(out_dir / "feature_store_preview.csv", index=False)
    _write_json(out_dir / "feature_store_summary.json", result.metadata)
    print("Point-in-time feature store built.")
    print(f"Rows: {len(result.features)}; features: {result.metadata['feature_count']}; version: {result.metadata['feature_version']}")
    print(f"Warehouse: {write_result.path}")
    return 0


def _cmd_train_walk_forward(config, args: argparse.Namespace, source: str | None, output_dir: Path | None) -> int:
    data_config = _data_config_with_source(config, args, source)
    bars_by_symbol, load_report = load_daily_bars(data_config)
    horizons = _parse_horizons(args, config.model.horizons)
    out_dir = output_dir or Path("reports/walk_forward")
    result = train_walk_forward(
        bars_by_symbol,
        args.model or config.model.model_type,
        horizons,
        out_dir,
        config.model.registry_dir,
    )
    print("Walk-forward training finished.")
    print(f"Source: {load_report.source}; symbols: {len(bars_by_symbol)}; rows: {result.summary['rows']}")
    print(result.metrics.to_string(index=False) if not result.metrics.empty else "No metrics generated.")
    print(f"Report: {out_dir}")
    return 0


def _cmd_evaluate_models(config, args: argparse.Namespace, output_dir: Path | None) -> int:
    out_dir = output_dir or Path("reports/model_evaluation")
    out_dir.mkdir(parents=True, exist_ok=True)
    records = _read_model_registry(config.model.registry_dir)
    rows = []
    for record in records:
        metrics = record.get("metrics", {}) if isinstance(record, dict) else {}
        rows.append(
            {
                "model_id": record.get("model_id", ""),
                "model_type": record.get("model_type", ""),
                "horizon_days": record.get("horizon_days", ""),
                "model_family": record.get("model_family", ""),
                "trust_status": metrics.get("trust_status", record.get("trust_status", "")) if isinstance(metrics, dict) else "",
                "rank_ic": metrics.get("rank_ic", metrics.get("valid_rank_ic", "")) if isinstance(metrics, dict) else "",
                "direction_accuracy": metrics.get("direction_accuracy", metrics.get("valid_accuracy", "")) if isinstance(metrics, dict) else "",
                "brier": metrics.get("brier", metrics.get("valid_brier", "")) if isinstance(metrics, dict) else "",
                "beats_baseline": metrics.get("beats_baseline", "") if isinstance(metrics, dict) else "",
            }
        )
    evaluation = pd.DataFrame(rows)
    if evaluation.empty:
        evaluation = pd.DataFrame(columns=["model_id", "model_type", "horizon_days", "model_family", "rank_ic", "direction_accuracy"])
    evaluation.to_csv(out_dir / "model_evaluation.csv", index=False)
    if args.by_year:
        _write_yearly_evaluation(out_dir)
    if args.by_industry:
        pd.DataFrame([{"industry": "industry_data_unavailable_free_mode", "note": "industry history not yet synced"}]).to_csv(
            out_dir / "evaluation_by_industry.csv",
            index=False,
        )
    print("Model evaluation finished.")
    print(f"Records: {len(evaluation)}")
    print(f"Report: {out_dir}")
    return 0


def _cmd_explain_stock(config, args: argparse.Namespace, source: str | None, output_dir: Path | None) -> int:
    if not args.symbol:
        raise ValueError("explain-stock requires --symbol.")
    data_config = _data_config_with_source(config, args, source, ensure_symbol=args.symbol)
    bars_by_symbol, load_report = load_daily_bars(data_config)
    horizons = _parse_horizons(args, config.model.horizons)
    forecast = build_stock_forecast(
        bars_by_symbol,
        args.symbol,
        horizons,
        source=load_report.source,
        model_type=args.model or config.model.model_type,
        embargo_days=config.model.embargo_days,
        allow_sample=args.allow_sample,
    )
    explanation = explain_stock_forecast(bars_by_symbol, forecast, args.symbol, horizons)
    out_dir = output_dir or Path("reports/stock_explain")
    out_dir.mkdir(parents=True, exist_ok=True)
    explanation.report.to_csv(out_dir / "stock_explanation.csv", index=False)
    explanation.similar_history.to_csv(out_dir / "similar_history.csv", index=False)
    (out_dir / "stock_explanation.md").write_text(explanation.markdown, encoding="utf-8")
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
    model_type = args.model or config.model.model_type
    horizons = _parse_horizons(args, config.model.horizons)
    summary = train_model(bars_by_symbol, model_type, horizons, out_dir, config.model.registry_dir)
    print("Model training finished.")
    print(f"Source: {load_report.source}; model: {model_type}; horizons: {horizons}")
    print(f"Registry: {config.model.registry_dir / 'model_registry.json'}")
    print(f"Summary: {out_dir / 'train_summary.json'}")
    return 0


def _cmd_predict_stock(config, args: argparse.Namespace, source: str | None, output_dir: Path | None) -> int:
    if not args.symbol:
        raise ValueError("predict-stock requires --symbol.")
    data_config = _data_config_with_source(config, args, source, ensure_symbol=args.symbol)
    bars_by_symbol, load_report = load_daily_bars(data_config)
    horizons = _parse_horizons(args, config.model.horizons)
    result = build_stock_forecast(
        bars_by_symbol,
        args.symbol,
        horizons,
        source=load_report.source,
        model_type=args.model or config.model.model_type,
        embargo_days=config.model.embargo_days,
        allow_sample=args.allow_sample,
    )
    out_dir = output_dir or Path("reports/stock_forecast")
    out_dir.mkdir(parents=True, exist_ok=True)
    result.forecast.to_csv(out_dir / "stock_forecast.csv", index=False)
    _write_json(out_dir / "stock_forecast.json", result.summary)
    print("Stock forecast finished.")
    print(f"Symbol: {args.symbol.zfill(6)}; source: {load_report.source}; horizons: {horizons}")
    print(
        result.forecast[
            ["horizon_days", "prob_up", "expected_return", "direction", "trend_label", "universe_symbol_count", "trust_status"]
        ].to_string(index=False)
    )
    print(f"Output: {out_dir}")
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
    print("Stock forecast backtest finished.")
    print(f"Symbol: {args.symbol.zfill(6)}; source: {load_report.source}; horizons: {horizons}")
    print(result.metrics.to_string(index=False))
    print(f"Output: {out_dir}")
    return 0


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
    bars_by_symbol = filtered_bars
    latest_target = targets.iloc[-1]
    latest_date = pd.Timestamp(targets.index[-1]).date().isoformat()
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
    )
    decision = check_order_plan(order_plan.orders, risk_config, equity=config.backtest.initial_cash)
    out_dir = output_dir or Path("reports/paper_trade")
    out_dir.mkdir(parents=True, exist_ok=True)
    order_plan.to_frame().to_csv(out_dir / "order_plan.csv", index=False)
    decision.report.to_csv(out_dir / "risk_report.csv", index=False)
    targets.to_csv(out_dir / "rebalance_targets.csv")
    if decision.passed:
        broker = PaperBroker(
            initial_cash=config.backtest.initial_cash,
            fee_rate=config.backtest.fee_rate,
            tax_rate=config.backtest.tax_rate,
            slippage_rate=config.backtest.slippage_rate,
        )
        execution = broker.submit(order_plan)
        broker.save_report(execution, out_dir)
        _write_json(
            out_dir / "paper_summary.json",
            {"passed": True, "requested_days": args.days, "no_live": args.no_live, "metadata": execution.metadata},
        )
    else:
        _write_json(
            out_dir / "paper_summary.json",
            {"passed": False, "requested_days": args.days, "no_live": args.no_live, "reasons": decision.reasons},
        )
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
    if normalized == "all-a":
        symbols = _try_fetch_all_a_symbols()
        return symbols or symbols_for_themes("mega-hot")
    return [item.strip().zfill(6) for item in universe.split(",") if item.strip()]


def _try_fetch_all_a_symbols() -> list[str]:
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
                    return sorted(frame["code"].astype(str).str.replace(".", "", regex=False).str[-6:].unique().tolist())
    except Exception:  # noqa: BLE001
        pass
    try:
        import akshare as ak  # type: ignore

        raw = ak.stock_info_a_code_name()
        code_col = "code" if "code" in raw.columns else _infer_symbol_column(raw)
        if code_col:
            return sorted(raw[code_col].astype(str).str.zfill(6).unique().tolist())
    except Exception:  # noqa: BLE001
        pass
    return []


def _infer_symbol_column(frame: pd.DataFrame) -> str | None:
    for column in frame.columns:
        values = frame[column].astype(str).str.strip()
        if values.str.fullmatch(r"\d{6}").mean() > 0.50:
            return str(column)
    return None


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
    if ensure_symbol:
        normalized = ensure_symbol.zfill(6)
        if normalized not in symbols:
            symbols.append(normalized)
    return replace(config.data, source=data_source, symbols=symbols)


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
