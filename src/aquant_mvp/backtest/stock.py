from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from aquant_mvp.config import DEFAULT_FACTOR_WEIGHTS
from aquant_mvp.factors import compute_factor_panel
from aquant_mvp.labels import compute_stock_prediction_labels
from aquant_mvp.strategy import score_factors


@dataclass(frozen=True)
class StockBacktestResult:
    predictions: pd.DataFrame
    metrics: pd.DataFrame


def backtest_stock_forecast(
    bars_by_symbol: dict[str, pd.DataFrame],
    symbol: str,
    horizons: list[int],
) -> StockBacktestResult:
    symbol = symbol.zfill(6)
    factors = compute_factor_panel(bars_by_symbol)
    labels = compute_stock_prediction_labels(bars_by_symbol, horizons)
    scores = score_factors(factors, DEFAULT_FACTOR_WEIGHTS)
    rows: list[pd.DataFrame] = []
    metric_rows: list[dict[str, object]] = []
    for horizon in horizons:
        label_col = f"future_return_{horizon}d"
        direction_col = f"direction_up_{horizon}d"
        data = scores[["score"]].join(labels[[label_col, direction_col]], how="inner").dropna()
        if data.empty:
            continue
        data["score_percentile"] = data.groupby(level="date")["score"].rank(pct=True)
        stock = data.xs(symbol, level="symbol", drop_level=False).copy()
        stock["prob_up"] = _expanding_calibrated_prob(data, stock["score_percentile"], direction_col)
        stock["predicted_direction"] = (stock["prob_up"] >= 0.5).astype(int)
        stock["horizon_days"] = horizon
        stock_reset = stock.reset_index()
        stock_reset["symbol"] = symbol
        rows.append(stock_reset)
        metric_rows.append(_metrics(stock_reset, horizon, label_col, direction_col))
    predictions = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    metrics = pd.DataFrame(metric_rows)
    return StockBacktestResult(predictions=predictions, metrics=metrics)


def _expanding_calibrated_prob(history: pd.DataFrame, latest_x: pd.Series, direction_col: str) -> pd.Series:
    out = []
    all_dates = pd.DatetimeIndex(history.index.get_level_values("date"))
    for idx, value in latest_x.items():
        date = pd.Timestamp(idx[0])
        past = history[all_dates < date]
        if len(past) < 80 or past["score_percentile"].nunique() < 2:
            out.append(float(past[direction_col].mean()) if not past.empty else 0.5)
            continue
        x = past["score_percentile"].astype(float)
        y = past[direction_col].astype(float)
        var = float(x.var(ddof=0))
        beta = float(x.cov(y, ddof=0) / var) if var > 0 else 0.0
        alpha = float(y.mean() - beta * x.mean())
        out.append(float(np.clip(alpha + beta * float(value), 0.05, 0.95)))
    return pd.Series(out, index=latest_x.index)


def _metrics(frame: pd.DataFrame, horizon: int, label_col: str, direction_col: str) -> dict[str, object]:
    if frame.empty:
        return {"horizon_days": horizon}
    prob = frame["prob_up"].astype(float)
    direction = frame[direction_col].astype(int)
    ret = frame[label_col].astype(float)
    high_bucket = frame[prob >= prob.quantile(0.8)]
    low_bucket = frame[prob <= prob.quantile(0.2)]
    wealth = (1.0 + ret.clip(lower=-0.999)).cumprod()
    max_forward_drawdown = float((wealth / wealth.cummax() - 1.0).min()) if not wealth.empty else 0.0
    return {
        "horizon_days": horizon,
        "rows": int(len(frame)),
        "direction_accuracy": float(((prob >= 0.5).astype(int) == direction).mean()),
        "brier": float(((prob - direction) ** 2).mean()),
        "return_ic": _safe_corr(prob, ret, "spearman"),
        "top_bucket_return": float(high_bucket[label_col].mean()) if not high_bucket.empty else 0.0,
        "bottom_bucket_return": float(low_bucket[label_col].mean()) if not low_bucket.empty else 0.0,
        "max_forward_drawdown": max_forward_drawdown,
    }


def _safe_corr(left: pd.Series, right: pd.Series, method: str) -> float:
    if left.nunique() < 2 or right.nunique() < 2:
        return 0.0
    value = left.corr(right, method=method)
    if value is None or np.isnan(value):
        return 0.0
    return float(value)
