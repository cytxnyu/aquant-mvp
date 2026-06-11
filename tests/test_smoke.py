from __future__ import annotations

from pathlib import Path

from aquant_mvp.config import BacktestConfig, DataConfig, ReportConfig, StrategyConfig, AppConfig
from aquant_mvp.pipeline import run_pipeline


def test_sample_pipeline_runs(tmp_path: Path) -> None:
    config = AppConfig(
        data=DataConfig(
            source="sample",
            symbols=["000001", "600519", "300750"],
            start_date="2023-01-01",
            end_date="2023-12-31",
            cache_dir=tmp_path / "cache",
        ),
        strategy=StrategyConfig(top_n=2),
        backtest=BacktestConfig(initial_cash=100000),
        report=ReportConfig(output_dir=tmp_path / "reports"),
    )
    payload = run_pipeline(config)
    result = payload["result"]
    assert not result.equity_curve.empty
    assert not result.rebalances.empty
    assert result.metrics["final_equity"] > 0
    assert (payload["run_dir"] / "metrics.json").exists()
    assert (payload["run_dir"] / "manifest.json").exists()
    assert (payload["run_dir"] / "summary.md").exists()
    assert (payload["run_dir"] / "factor_ic_summary.csv").exists()
    assert (payload["run_dir"] / "factor_analysis.json").exists()
    assert (payload["run_dir"] / "equity_curve.png").exists()
    assert (payload["run_dir"] / "drawdown.png").exists()
