from __future__ import annotations

import pandas as pd

from aquant_mvp.backtest.stock import _metrics
from aquant_mvp.factors import FACTOR_COLUMNS, compute_factor_panel
from aquant_mvp.labels import compute_return_labels
from aquant_mvp.prediction import build_latest_predictions
from aquant_mvp.strategy import score_factors


def _sample_bars(symbol: str, offset: float) -> pd.DataFrame:
    dates = pd.bdate_range("2024-01-01", periods=140)
    close = pd.Series(range(20, 160), dtype="float64") + offset
    return pd.DataFrame(
        {
            "date": dates,
            "symbol": symbol,
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": 100000.0 + offset,
            "amount": close * (100000.0 + offset),
            "turnover": 1.0 + offset / 1000,
        }
    )


def test_latest_predictions_have_rank_and_signal() -> None:
    bars = {
        "000001": _sample_bars("000001", 0),
        "000002": _sample_bars("000002", 10),
        "000003": _sample_bars("000003", 20),
    }
    factors = compute_factor_panel(bars)
    labels = compute_return_labels(bars, [5])
    scores = score_factors(factors, {"momentum_20": 0.5, "volatility_20": -0.2, "amount_mean_20": 0.3})
    result = build_latest_predictions(factors, labels, scores, FACTOR_COLUMNS, horizon=5)
    assert len(result.predictions) == 3
    assert set(result.predictions["signal"]).issubset({"候选", "观察", "回避"})
    assert result.summary["method"] in {"score_proxy", "lightgbm"}


def test_stock_backtest_drawdown_is_bounded() -> None:
    frame = pd.DataFrame(
        {
            "prob_up": [0.8, 0.7, 0.6],
            "direction_up_5d": [0, 0, 0],
            "future_return_5d": [-0.5, -0.5, -0.5],
        }
    )
    metrics = _metrics(frame, 5, "future_return_5d", "direction_up_5d")
    assert -1.0 <= metrics["max_forward_drawdown"] <= 0.0
