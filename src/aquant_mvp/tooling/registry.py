from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class ToolCapability:
    tool_id: str
    command: str
    category: str
    maturity: str
    primary_module: str
    output_artifacts: str
    live_trading_allowed: bool
    risk_level: str
    notes: str


TOOL_REGISTRY: tuple[ToolCapability, ...] = (
    ToolCapability(
        "source_discovery",
        "python run_mvp.py discover-sources --domestic-only",
        "data",
        "implemented",
        "aquant_mvp.sources.discovery",
        "free_source_coverage.md, source_coverage.csv",
        False,
        "low",
        "Domestic/free source capability scan.",
    ),
    ToolCapability(
        "foundation_registry",
        "python run_mvp.py discover-foundations",
        "foundation",
        "implemented",
        "aquant_mvp.foundations.registry",
        "foundation_registry.csv, foundation_registry.md",
        False,
        "low",
        "External quant/model/data/broker base availability scan.",
    ),
    ToolCapability(
        "tool_registry",
        "python run_mvp.py discover-tools",
        "tooling",
        "implemented",
        "aquant_mvp.tooling.registry",
        "tool_registry.csv, tool_registry.md",
        False,
        "low",
        "Current CLI and module capability catalog.",
    ),
    ToolCapability(
        "mega_hot_universe",
        "python run_mvp.py build-universe --themes mega-hot",
        "universe",
        "implemented",
        "aquant_mvp.universe.themes",
        "theme_universe.csv, theme_universe_summary.csv, symbol_theme_membership.csv",
        False,
        "low",
        "Expanded hot and professional theme seed universe.",
    ),
    ToolCapability(
        "free_max_sync",
        "python run_mvp.py sync-free-all --universe mega-hot",
        "data",
        "implemented",
        "aquant_mvp.data.providers",
        "daily_bar warehouse table, source_audit, data_quality reports",
        False,
        "medium",
        "Free-source sync with per-symbol failure audit.",
    ),
    ToolCapability(
        "pit_audit",
        "python run_mvp.py audit-data --strict-pit",
        "data_quality",
        "implemented",
        "aquant_mvp.data.audit",
        "data_audit_summary.csv, data_audit_issues.csv",
        False,
        "low",
        "Point-in-time metadata and daily bar quality audit.",
    ),
    ToolCapability(
        "feature_store",
        "python run_mvp.py build-feature-store --point-in-time",
        "features",
        "implemented",
        "aquant_mvp.features.store",
        "feature_store warehouse table, feature_store_summary.json",
        False,
        "medium",
        "PIT feature store builder with labels for selected horizons.",
    ),
    ToolCapability(
        "walk_forward_training",
        "python run_mvp.py train-walk-forward --model ensemble",
        "model",
        "implemented",
        "aquant_mvp.modeling.walk_forward",
        "walk_forward_predictions.csv, walk_forward_metrics.csv, model_registry.json",
        False,
        "medium",
        "Rolling sample-out validation and model registry.",
    ),
    ToolCapability(
        "model_evaluation",
        "python run_mvp.py evaluate-models --by-year --by-industry",
        "model",
        "implemented",
        "aquant_mvp.cli",
        "model_evaluation.csv, evaluation_by_year.csv",
        False,
        "low",
        "Registry-level model evaluation summaries.",
    ),
    ToolCapability(
        "stock_forecast",
        "python run_mvp.py predict-stock --symbol 601899 --universe mega-hot",
        "prediction",
        "implemented",
        "aquant_mvp.prediction.stock",
        "stock_forecast.csv, stock_forecast.json",
        False,
        "medium",
        "Probabilistic single-stock forecast with trust gating.",
    ),
    ToolCapability(
        "stock_explain",
        "python run_mvp.py explain-stock --symbol 601899",
        "explainability",
        "implemented",
        "aquant_mvp.prediction.explain",
        "stock_explanation.csv, similar_history.csv, stock_explanation.md",
        False,
        "low",
        "Factor, trend, risk and similar-history explanation.",
    ),
    ToolCapability(
        "stock_backtest",
        "python run_mvp.py backtest-stock --symbol 601899",
        "backtest",
        "implemented",
        "aquant_mvp.backtest.stock",
        "stock_forecast_backtest.csv, stock_forecast_metrics.csv",
        False,
        "medium",
        "Single-stock forecast backtest.",
    ),
    ToolCapability(
        "paper_trade",
        "python run_mvp.py paper-trade --days 20 --no-live",
        "broker",
        "implemented",
        "aquant_mvp.broker.paper",
        "order_plan.csv, risk_report.csv, paper_summary.json",
        False,
        "medium",
        "Paper trading and risk-check path.",
    ),
    ToolCapability(
        "qmt_readonly",
        "python run_mvp.py qmt-readonly-sync",
        "broker",
        "implemented_readonly",
        "aquant_mvp.broker.qmt",
        "qmt_readonly_status.csv, qmt_reconcile.csv",
        False,
        "medium",
        "QMT/XtQuant read-only status and reconcile path.",
    ),
    ToolCapability(
        "live_trade_blocker",
        "python run_mvp.py live-trade --confirm",
        "broker",
        "safety_block",
        "aquant_mvp.cli",
        "no order artifact; exits non-zero",
        False,
        "high",
        "Live trading is intentionally blocked.",
    ),
)


def discover_tools() -> pd.DataFrame:
    return pd.DataFrame([asdict(item) for item in TOOL_REGISTRY]).sort_values(["category", "tool_id"]).reset_index(drop=True)


def write_tool_report(output_dir: Path, frame: pd.DataFrame | None = None) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    data = discover_tools() if frame is None else frame
    csv_path = output_dir / "tool_registry.csv"
    md_path = output_dir / "tool_registry.md"
    data.to_csv(csv_path, index=False)
    lines = [
        "# Tool Registry",
        "",
        "This registry records which AQuant tools are currently exposed as runnable commands.",
        "",
        f"- total: {len(data)}",
        f"- live trading allowed tools: {int(data['live_trading_allowed'].sum()) if not data.empty else 0}",
        "",
        "| tool | category | maturity | live | command |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in data.itertuples():
        lines.append(f"| {row.tool_id} | {row.category} | {row.maturity} | {row.live_trading_allowed} | `{row.command}` |")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return md_path
