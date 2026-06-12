from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from aquant_mvp.factors import FACTOR_COLUMNS, compute_factor_panel
from aquant_mvp.labels import compute_stock_prediction_labels
from aquant_mvp.prediction.stock import StockForecastResult


@dataclass(frozen=True)
class StockExplanation:
    report: pd.DataFrame
    similar_history: pd.DataFrame
    markdown: str


def explain_stock_forecast(
    bars_by_symbol: dict[str, pd.DataFrame],
    forecast: StockForecastResult,
    symbol: str,
    horizons: list[int],
    trust_floor: str = "weak",
) -> StockExplanation:
    symbol = symbol.zfill(6)
    factors = compute_factor_panel(bars_by_symbol)
    labels = compute_stock_prediction_labels(bars_by_symbol, horizons)
    latest_date = pd.Timestamp(forecast.forecast["latest_date"].iloc[0])
    current_vector = factors.loc[(latest_date, symbol), FACTOR_COLUMNS].replace([np.inf, -np.inf], np.nan)
    z = _factor_zscores(factors, current_vector)
    similar = _similar_history(factors, labels, symbol, latest_date, current_vector, horizons)
    report = forecast.forecast.copy()
    report["trust_status"] = report.apply(_trust_status, axis=1)
    report["industry_relative_rank"] = "industry_data_unavailable_free_mode"
    report["similar_history_rows"] = len(similar)
    report["similar_history_mean_return"] = float(similar["future_return"].mean()) if not similar.empty else 0.0
    report["explanation"] = report.apply(lambda row: _row_explanation(row, z), axis=1)
    markdown = _markdown(symbol, report, similar, z, trust_floor)
    return StockExplanation(report=report, similar_history=similar, markdown=markdown)


def _factor_zscores(factors: pd.DataFrame, current_vector: pd.Series) -> pd.Series:
    history = factors[FACTOR_COLUMNS].replace([np.inf, -np.inf], np.nan)
    mean = history.mean(numeric_only=True)
    std = history.std(numeric_only=True).replace(0, np.nan)
    z = ((current_vector - mean) / std).dropna()
    return z.reindex(z.abs().sort_values(ascending=False).head(8).index)


def _similar_history(
    factors: pd.DataFrame,
    labels: pd.DataFrame,
    symbol: str,
    latest_date: pd.Timestamp,
    current_vector: pd.Series,
    horizons: list[int],
) -> pd.DataFrame:
    history = factors.xs(symbol, level="symbol", drop_level=False)[FACTOR_COLUMNS].replace([np.inf, -np.inf], np.nan)
    history = history[history.index.get_level_values("date") < latest_date]
    usable = current_vector.dropna().index.intersection(history.columns)
    if len(usable) < 5 or history.empty:
        return pd.DataFrame(columns=["date", "distance", "horizon_days", "future_return"])
    normalized = (history[usable] - history[usable].mean()) / history[usable].std().replace(0, np.nan)
    current = ((current_vector[usable] - history[usable].mean()) / history[usable].std().replace(0, np.nan)).fillna(0)
    distance = ((normalized.fillna(0) - current) ** 2).sum(axis=1).pow(0.5).sort_values().head(20)
    rows = []
    for idx, value in distance.items():
        for horizon in horizons:
            label = f"future_return_{horizon}d"
            future_return = labels.loc[idx, label] if idx in labels.index and label in labels.columns else np.nan
            rows.append(
                {
                    "date": idx[0],
                    "symbol": idx[1],
                    "distance": float(value),
                    "horizon_days": horizon,
                    "future_return": future_return,
                }
            )
    return pd.DataFrame(rows).dropna(subset=["future_return"])


def _trust_status(row: pd.Series) -> str:
    existing = str(row.get("trust_status", "")).strip()
    if existing in {"data_insufficient", "model_failed", "trusted", "weak"}:
        return existing
    confidence = float(row.get("confidence", 0.0))
    flags = str(row.get("risk_flags", ""))
    if "short_history" in flags or "may_include_fallback_data" in flags:
        return "data_insufficient"
    if confidence >= 0.55 and "high_volatility" not in flags:
        return "trusted"
    if confidence >= 0.25:
        return "weak"
    return "weak"


def _row_explanation(row: pd.Series, z: pd.Series) -> str:
    contributors = ", ".join(f"{name}={value:.2f}" for name, value in z.head(4).items())
    return (
        f"{row['horizon_days']}d {row['direction']} with prob_up={float(row['prob_up']):.3f}; "
        f"trend={row['trend_label']}; key_factors={contributors or 'insufficient_factor_signal'}; "
        f"risk={row['risk_flags']}"
    )


def _markdown(symbol: str, report: pd.DataFrame, similar: pd.DataFrame, z: pd.Series, trust_floor: str) -> str:
    lines = [f"# Stock Explanation: {symbol}", ""]
    lines.append("## Forecast")
    for row in report.itertuples(index=False):
        lines.append(
            f"- {row.horizon_days}d: {row.direction}, prob_up={row.prob_up:.3f}, "
            f"expected_return={row.expected_return:.3%}, trust={row.trust_status}"
        )
    lines.append("")
    lines.append("## Key Factors")
    if z.empty:
        lines.append("- No stable factor contributor available.")
    else:
        for name, value in z.items():
            lines.append(f"- `{name}`: z={value:.3f}")
    lines.append("")
    lines.append("## Similar History")
    if similar.empty:
        lines.append("- No enough similar historical states.")
    else:
        grouped = similar.groupby("horizon_days")["future_return"].agg(["mean", "count"]).reset_index()
        for row in grouped.itertuples(index=False):
            lines.append(f"- {row.horizon_days}d: mean_return={row.mean:.3%}, samples={int(row.count)}")
    lines.append("")
    lines.append(f"Trust floor requested: `{trust_floor}`. Signals are probabilistic research outputs, not investment advice.")
    return "\n".join(lines)
