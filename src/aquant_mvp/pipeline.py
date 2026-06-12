from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from pathlib import Path

from aquant_mvp.analysis import analyze_factors
from aquant_mvp.backtest import run_backtest
from aquant_mvp.config import AppConfig
from aquant_mvp.data import check_daily_bars, load_daily_bars
from aquant_mvp.factors import FACTOR_COLUMNS, compute_factor_panel
from aquant_mvp.labels import compute_return_labels
from aquant_mvp.prediction import build_latest_predictions
from aquant_mvp.reporting import save_run_outputs
from aquant_mvp.strategy import build_rebalance_targets, score_factors
from aquant_mvp.universe import filter_universe


def run_pipeline(config: AppConfig, source: str | None = None, output_dir: Path | None = None) -> dict[str, object]:
    data_config = config.data if source is None else replace(config.data, source=source)
    bars_by_symbol, load_report = load_daily_bars(data_config)
    data_quality = check_daily_bars(bars_by_symbol)
    filtered_bars, universe_report = filter_universe(bars_by_symbol, config.universe)
    if not filtered_bars:
        raise RuntimeError("Universe filters removed all symbols. Relax universe config and rerun.")

    factor_panel = compute_factor_panel(filtered_bars)
    labels = compute_return_labels(filtered_bars, config.analysis.label_horizons)
    analysis_label = f"excess_return_{config.analysis.label_horizons[0]}d"
    factor_analysis = analyze_factors(
        factor_panel,
        labels,
        FACTOR_COLUMNS,
        analysis_label,
        quantiles=config.analysis.quantiles,
    )
    scores = score_factors(factor_panel, config.strategy.factor_weights)
    predictions = build_latest_predictions(
        factor_panel,
        labels,
        scores,
        FACTOR_COLUMNS,
        horizon=config.analysis.label_horizons[0],
    )
    targets = build_rebalance_targets(scores, config.strategy)
    result = run_backtest(filtered_bars, targets, config.backtest)

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = output_dir or (config.report.output_dir / f"run_{run_id}")
    paths = save_run_outputs(
        run_dir,
        config=config,
        load_report=load_report,
        data_quality=data_quality,
        universe_report=universe_report,
        factors=factor_panel,
        labels=labels,
        factor_analysis=factor_analysis,
        predictions=predictions,
        scores=scores,
        targets=targets,
        result=result,
    )
    return {
        "load_report": load_report,
        "data_quality": data_quality,
        "universe_report": universe_report,
        "bars_by_symbol": filtered_bars,
        "factors": factor_panel,
        "labels": labels,
        "factor_analysis": factor_analysis,
        "predictions": predictions,
        "scores": scores,
        "targets": targets,
        "result": result,
        "paths": paths,
        "run_dir": run_dir,
    }
