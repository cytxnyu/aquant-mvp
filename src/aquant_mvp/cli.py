from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

from aquant_mvp.config import load_config
from aquant_mvp.data import check_daily_bars, load_daily_bars
from aquant_mvp.pipeline import run_pipeline
from aquant_mvp.universe import filter_universe


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the A-share quant research MVP.")
    parser.add_argument("command", nargs="?", default="run", choices=["run", "run-demo", "check-data", "analyze-factors"])
    parser.add_argument("--config", default="configs/mvp.json", help="Path to JSON/YAML config.")
    parser.add_argument("--source", choices=["sample", "akshare", "auto"], default=None, help="Override data source.")
    parser.add_argument("--output-dir", default=None, help="Optional report output directory.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(args.config)
    source = "sample" if args.command == "run-demo" and args.source is None else args.source
    output_dir = Path(args.output_dir) if args.output_dir else None

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
    print(f"Report dir: {payload['run_dir']}")
    print(f"Metrics: {paths['metrics']}")
    print(f"Summary: {paths['summary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
