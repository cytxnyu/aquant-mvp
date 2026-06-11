from __future__ import annotations

import pandas as pd


FACTOR_COLUMNS = [
    "momentum_20",
    "momentum_60",
    "reversal_5",
    "reversal_10",
    "volatility_20",
    "volatility_60",
    "amount_mean_20",
    "amount_mean_60",
    "turnover_mean_20",
    "turnover_mean_60",
    "volume_ratio_5_20",
    "price_position_60",
    "ma_bias_20",
    "max_drawdown_60",
    "downside_volatility_20",
]


def compute_factor_panel(bars_by_symbol: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Build a date/symbol factor panel using only historical daily bars."""
    frames = []
    for symbol, bars in bars_by_symbol.items():
        df = bars.sort_values("date").copy()
        ret = df["close"].pct_change()
        df["momentum_20"] = df["close"].pct_change(20)
        df["momentum_60"] = df["close"].pct_change(60)
        df["reversal_5"] = -df["close"].pct_change(5)
        df["reversal_10"] = -df["close"].pct_change(10)
        df["volatility_20"] = ret.rolling(20, min_periods=15).std()
        df["volatility_60"] = ret.rolling(60, min_periods=40).std()
        df["amount_mean_20"] = df["amount"].rolling(20, min_periods=15).mean()
        df["amount_mean_60"] = df["amount"].rolling(60, min_periods=40).mean()
        df["turnover_mean_20"] = df["turnover"].rolling(20, min_periods=15).mean()
        df["turnover_mean_60"] = df["turnover"].rolling(60, min_periods=40).mean()
        volume_mean_5 = df["volume"].rolling(5, min_periods=5).mean()
        volume_mean_20 = df["volume"].rolling(20, min_periods=15).mean()
        df["volume_ratio_5_20"] = volume_mean_5 / volume_mean_20 - 1
        high_60 = df["high"].rolling(60, min_periods=40).max()
        low_60 = df["low"].rolling(60, min_periods=40).min()
        df["price_position_60"] = (df["close"] - low_60) / (high_60 - low_60)
        ma_20 = df["close"].rolling(20, min_periods=15).mean()
        df["ma_bias_20"] = df["close"] / ma_20 - 1
        df["max_drawdown_60"] = df["close"].rolling(60, min_periods=40).apply(_window_max_drawdown, raw=False)
        downside_ret = ret.where(ret < 0, 0.0)
        df["downside_volatility_20"] = downside_ret.rolling(20, min_periods=15).std()
        df["symbol"] = symbol
        frames.append(df[["date", "symbol", "close", "amount", *FACTOR_COLUMNS]])

    if not frames:
        raise ValueError("No bars provided")

    panel = pd.concat(frames, ignore_index=True)
    panel = panel.set_index(["date", "symbol"]).sort_index()
    return panel


def _window_max_drawdown(window: pd.Series) -> float:
    running_max = window.cummax()
    drawdown = window / running_max - 1
    return float(drawdown.min())
