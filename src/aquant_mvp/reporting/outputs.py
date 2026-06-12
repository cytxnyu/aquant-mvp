from __future__ import annotations

import json
from pathlib import Path
from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import Any

import pandas as pd

from aquant_mvp.analysis import FactorAnalysisResult
from aquant_mvp.backtest import BacktestResult
from aquant_mvp.config import AppConfig
from aquant_mvp.data import DataQualityReport
from aquant_mvp.data.providers import LoadReport
from aquant_mvp.prediction import PredictionResult
from aquant_mvp.universe import UniverseReport


def save_run_outputs(
    output_dir: Path,
    config: AppConfig,
    load_report: LoadReport,
    data_quality: DataQualityReport,
    universe_report: UniverseReport,
    factors: pd.DataFrame,
    labels: pd.DataFrame,
    factor_analysis: FactorAnalysisResult,
    predictions: PredictionResult,
    scores: pd.DataFrame,
    targets: pd.DataFrame,
    result: BacktestResult,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "equity_curve": output_dir / "equity_curve.csv",
        "trades": output_dir / "trades.csv",
        "holdings": output_dir / "holdings.csv",
        "rebalances": output_dir / "rebalances.csv",
        "metrics": output_dir / "metrics.json",
        "manifest": output_dir / "manifest.json",
        "config": output_dir / "config.json",
        "load_report": output_dir / "load_report.json",
        "data_quality_summary": output_dir / "data_quality_summary.csv",
        "data_quality_issues": output_dir / "data_quality_issues.csv",
        "universe": output_dir / "universe.csv",
        "factors": output_dir / "factors.csv",
        "labels": output_dir / "labels.csv",
        "factor_ic_summary": output_dir / "factor_ic_summary.csv",
        "factor_ic_series": output_dir / "factor_ic_series.csv",
        "factor_quantile_returns": output_dir / "factor_quantile_returns.csv",
        "factor_coverage": output_dir / "factor_coverage.csv",
        "factor_analysis_json": output_dir / "factor_analysis.json",
        "predictions": output_dir / "predictions.csv",
        "prediction_summary": output_dir / "prediction_summary.json",
        "scores": output_dir / "scores.csv",
        "targets": output_dir / "rebalance_targets.csv",
        "equity_plot": output_dir / "equity_curve.png",
        "drawdown_plot": output_dir / "drawdown.png",
        "factor_ic_plot": output_dir / "factor_ic.png",
        "quantile_returns_plot": output_dir / "quantile_returns.png",
        "summary": output_dir / "summary.md",
    }

    result.equity_curve.to_csv(paths["equity_curve"], index=False)
    result.trades.to_csv(paths["trades"], index=False)
    result.holdings.to_csv(paths["holdings"], index=False)
    result.rebalances.to_csv(paths["rebalances"], index=False)
    data_quality.summary.to_csv(paths["data_quality_summary"], index=False)
    data_quality.issues.to_csv(paths["data_quality_issues"], index=False)
    universe_report.detail.to_csv(paths["universe"], index=False)
    factors.reset_index().to_csv(paths["factors"], index=False)
    labels.reset_index().to_csv(paths["labels"], index=False)
    factor_analysis.ic_summary.to_csv(paths["factor_ic_summary"], index=False)
    factor_analysis.ic_series.to_csv(paths["factor_ic_series"], index=False)
    factor_analysis.quantile_returns.to_csv(paths["factor_quantile_returns"], index=False)
    factor_analysis.coverage.to_csv(paths["factor_coverage"], index=False)
    paths["factor_analysis_json"].write_text(
        json.dumps(
            {
                "ic_summary": factor_analysis.ic_summary.to_dict(orient="records"),
                "coverage": factor_analysis.coverage.to_dict(orient="records"),
                "quantile_return_rows": int(len(factor_analysis.quantile_returns)),
                "ic_series_rows": int(len(factor_analysis.ic_series)),
            },
            ensure_ascii=False,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    predictions.predictions.to_csv(paths["predictions"], index=False)
    paths["prediction_summary"].write_text(
        json.dumps(predictions.summary, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    scores.reset_index().to_csv(paths["scores"], index=False)
    targets.to_csv(paths["targets"])

    metrics = dict(result.metrics)
    paths["metrics"].write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    paths["config"].write_text(json.dumps(_jsonable(config), ensure_ascii=False, indent=2), encoding="utf-8")
    paths["load_report"].write_text(json.dumps(_jsonable(load_report), ensure_ascii=False, indent=2), encoding="utf-8")
    _save_equity_plot(result.equity_curve, paths["equity_plot"])
    _save_drawdown_plot(result.equity_curve, paths["drawdown_plot"])
    _save_factor_ic_plot(factor_analysis.ic_summary, paths["factor_ic_plot"])
    _save_quantile_returns_plot(factor_analysis.quantile_returns, paths["quantile_returns_plot"])
    _write_summary(paths["summary"], config, load_report, universe_report, data_quality, metrics, predictions, paths)
    _write_manifest(
        paths["manifest"],
        output_dir,
        config,
        load_report,
        universe_report,
        data_quality,
        metrics,
        predictions,
        paths,
    )

    return paths


def _save_equity_plot(equity_curve: pd.DataFrame, path: Path) -> None:
    plt = _get_pyplot()
    if plt is None:
        return

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(pd.to_datetime(equity_curve["date"]), equity_curve["equity"], linewidth=1.6)
    ax.set_title("A-share MVP Equity Curve")
    ax.set_xlabel("Date")
    ax.set_ylabel("Equity")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _save_drawdown_plot(equity_curve: pd.DataFrame, path: Path) -> None:
    plt = _get_pyplot()
    if plt is None:
        return
    if "drawdown" not in equity_curve.columns:
        return
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.fill_between(pd.to_datetime(equity_curve["date"]), equity_curve["drawdown"], 0, alpha=0.35)
    ax.set_title("Drawdown")
    ax.set_xlabel("Date")
    ax.set_ylabel("Drawdown")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _save_factor_ic_plot(ic_summary: pd.DataFrame, path: Path) -> None:
    plt = _get_pyplot()
    if plt is None:
        return
    if ic_summary.empty:
        return
    plot_frame = ic_summary.sort_values("rank_ic_mean")
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.barh(plot_frame["factor"], plot_frame["rank_ic_mean"])
    ax.set_title("Factor RankIC Mean")
    ax.set_xlabel("RankIC")
    ax.grid(True, axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _save_quantile_returns_plot(quantile_returns: pd.DataFrame, path: Path) -> None:
    plt = _get_pyplot()
    if plt is None:
        return
    if quantile_returns.empty:
        return
    grouped = quantile_returns.groupby("quantile")["mean_forward_return"].mean()
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.bar(grouped.index.astype(str), grouped.values)
    ax.set_title("Average Forward Return by Factor Quantile")
    ax.set_xlabel("Quantile")
    ax.set_ylabel("Mean forward return")
    ax.grid(True, axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _get_pyplot():
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt
    except Exception:
        return None
    return plt


def _write_summary(
    path: Path,
    config: AppConfig,
    load_report: LoadReport,
    universe_report: UniverseReport,
    data_quality: DataQualityReport,
    metrics: dict[str, float],
    predictions: PredictionResult,
    paths: dict[str, Path],
) -> None:
    metric_lines = "\n".join(f"- `{key}`: {value:.6f}" for key, value in metrics.items())
    output_lines = "\n".join(f"- `{key}`: `{value.name}`" for key, value in paths.items() if key != "summary")
    prediction_lines = "\n".join(
        f"- `{row.symbol}`: rank {int(row.prediction_rank)}, signal {row.signal}, predicted excess {row.predicted_excess_return:.4%}"
        for row in predictions.predictions.head(5).itertuples()
    )
    text = f"""# AQuant Run Summary

## Run Config

- Data source: `{load_report.source}`
- Date range: `{config.data.start_date}` to `{config.data.end_date}`
- Loaded symbols: {len(load_report.symbols_loaded)}
- Selected universe: {len(universe_report.selected_symbols)}
- Rebalance: `{config.strategy.rebalance}`
- Top N: {config.strategy.top_n}

## Data Quality

- Issue count: {data_quality.issue_count}
- Universe filters reserve ST, suspension, limit-up/down, delisting and industry hooks for the next data upgrade.

## Metrics

{metric_lines}

## Latest Predictions

- Method: `{predictions.summary.get('method')}`
- Horizon: {predictions.summary.get('horizon_days')} trading days

{prediction_lines}

## Outputs

{output_lines}

## Notes

Sample data is only for workflow verification. Real strategy research must use point-in-time A-share data and handle survivorship bias, announcement dates, suspensions, ST flags and limit-up/down constraints.
"""
    path.write_text(text, encoding="utf-8")


def _write_manifest(
    path: Path,
    output_dir: Path,
    config: AppConfig,
    load_report: LoadReport,
    universe_report: UniverseReport,
    data_quality: DataQualityReport,
    metrics: dict[str, float],
    predictions: PredictionResult,
    paths: dict[str, Path],
) -> None:
    files = []
    for key, value in sorted(paths.items()):
        if key == "manifest":
            continue
        if value.exists():
            files.append({"key": key, "file": value.name, "bytes": value.stat().st_size})
        else:
            files.append({"key": key, "file": value.name, "bytes": 0, "missing": True})
    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project": "aquant-mvp",
        "run_dir": str(output_dir),
        "data_source": load_report.source,
        "date_range": {"start": config.data.start_date, "end": config.data.end_date},
        "loaded_symbols": load_report.symbols_loaded,
        "selected_symbols": universe_report.selected_symbols,
        "data_quality_issue_count": data_quality.issue_count,
        "metrics": metrics,
        "prediction_summary": predictions.summary,
        "config": _jsonable(config),
        "files": files,
    }
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value
