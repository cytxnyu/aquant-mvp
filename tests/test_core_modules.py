from __future__ import annotations

from pathlib import Path

import pandas as pd

from aquant_mvp.backtest import run_backtest
from aquant_mvp.config import BacktestConfig
from aquant_mvp.data.quality import check_daily_bars
from aquant_mvp.factors import compute_factor_panel
from aquant_mvp.labels import compute_return_labels


def _bars(symbol: str = "000001", periods: int = 90) -> pd.DataFrame:
    dates = pd.bdate_range("2024-01-01", periods=periods)
    close = pd.Series(range(10, 10 + periods), dtype="float64")
    return pd.DataFrame(
        {
            "date": dates,
            "symbol": symbol,
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": 100000.0,
            "amount": close * 100000,
            "turnover": 1.0,
        }
    )


def test_return_labels_use_future_close() -> None:
    bars = {"000001": _bars(periods=12)}
    labels = compute_return_labels(bars, [5])
    first_date = pd.Timestamp("2024-01-01")
    assert labels.loc[(first_date, "000001"), "future_return_5d"] == 5 / 10
    assert pd.isna(labels.iloc[-1]["future_return_5d"])


def test_factor_values_do_not_change_when_future_price_changes() -> None:
    original = _bars(periods=100)
    changed_future = original.copy()
    changed_future.loc[90:, "close"] = changed_future.loc[90:, "close"] * 100
    factor_date = original.loc[70, "date"]

    factors_original = compute_factor_panel({"000001": original})
    factors_changed = compute_factor_panel({"000001": changed_future})

    left = factors_original.loc[(factor_date, "000001"), "momentum_20"]
    right = factors_changed.loc[(factor_date, "000001"), "momentum_20"]
    assert left == right


def test_backtest_executes_next_day_and_uses_lot_size() -> None:
    dates = pd.bdate_range("2024-01-01", periods=4)
    bars = pd.DataFrame(
        {
            "date": dates,
            "symbol": "000001",
            "open": [10.0, 10.0, 12.0, 12.0],
            "high": [10.0, 10.0, 12.0, 12.0],
            "low": [10.0, 10.0, 12.0, 12.0],
            "close": [10.0, 10.0, 12.0, 12.0],
            "volume": [100000.0] * 4,
            "amount": [1000000.0] * 4,
            "turnover": [1.0] * 4,
        }
    )
    targets = pd.DataFrame({"000001": [1.0, 0.0]}, index=[dates[0], dates[1]])
    result = run_backtest(
        {"000001": bars},
        targets,
        BacktestConfig(initial_cash=10000, fee_rate=0, tax_rate=0, slippage_rate=0, lot_size=100),
    )
    assert list(result.trades["side"]) == ["BUY", "SELL"]
    assert list(pd.to_datetime(result.trades["date"])) == [dates[1], dates[2]]
    assert all(result.trades["shares"] % 100 == 0)


def test_data_quality_flags_bad_rows() -> None:
    bars = _bars(periods=5)
    bars.loc[2, "close"] = -1
    bars = pd.concat([bars, bars.iloc[[0]]], ignore_index=True)
    report = check_daily_bars({"000001": bars})
    assert report.issue_count >= 2
    assert set(report.issues["issue"]).issuperset({"duplicate_dates", "non_positive_price"})
