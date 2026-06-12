from __future__ import annotations

import numpy as np
import pandas as pd


MOMENTUM_WINDOWS = [1, 2, 3, 5, 10, 20, 40, 60, 120]
REVERSAL_WINDOWS = [1, 2, 3, 5, 10, 20]
RISK_WINDOWS = [5, 10, 20, 40, 60, 120]
MA_WINDOWS = [5, 10, 20, 40, 60, 120]
POSITION_WINDOWS = [20, 40, 60, 120]
LIQUIDITY_WINDOWS = [5, 10, 20, 40, 60]


FACTOR_COLUMNS = [
    *[f"momentum_{window}" for window in MOMENTUM_WINDOWS],
    *[f"reversal_{window}" for window in REVERSAL_WINDOWS],
    *[f"volatility_{window}" for window in RISK_WINDOWS],
    *[f"downside_volatility_{window}" for window in [5, 10, 20, 60, 120]],
    *[f"upside_volatility_{window}" for window in [5, 10, 20, 60]],
    *[f"max_drawdown_{window}" for window in [20, 60, 120]],
    *[f"ma_bias_{window}" for window in MA_WINDOWS],
    *[f"ma_slope_{window}" for window in [5, 10, 20, 60]],
    *[f"price_position_{window}" for window in POSITION_WINDOWS],
    *[f"breakout_high_{window}" for window in POSITION_WINDOWS],
    *[f"breakdown_low_{window}" for window in POSITION_WINDOWS],
    *[f"amount_mean_{window}" for window in LIQUIDITY_WINDOWS],
    *[f"amount_zscore_{window}" for window in [20, 60]],
    *[f"amount_percentile_{window}" for window in [20, 60]],
    *[f"turnover_mean_{window}" for window in LIQUIDITY_WINDOWS],
    *[f"turnover_zscore_{window}" for window in [20, 60]],
    *[f"turnover_percentile_{window}" for window in [20, 60]],
    "volume_ratio_5_20",
    "volume_ratio_10_60",
    "amount_ratio_5_20",
    "amount_ratio_10_60",
    "intraday_return",
    "overnight_return",
    "gap_return",
    "amplitude",
    "close_position",
    "upper_shadow",
    "lower_shadow",
    "body_size",
    "return_skew_20",
    "return_skew_60",
    "return_kurt_20",
    "return_kurt_60",
    "amihud_illiquidity_20",
    "amihud_illiquidity_60",
    "limit_up_count_20",
    "limit_up_count_60",
    "limit_down_count_20",
    "limit_down_count_60",
    "up_day_ratio_20",
    "up_day_ratio_60",
    "down_day_ratio_20",
    "down_day_ratio_60",
    "up_streak",
    "down_streak",
    "new_high_distance_60",
    "new_low_distance_60",
]


def compute_factor_panel(bars_by_symbol: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Build a date/symbol factor panel using only current and historical daily bars."""
    frames = []
    for symbol, bars in bars_by_symbol.items():
        df = bars.sort_values("date").copy()
        df["date"] = pd.to_datetime(df["date"])
        ret = df["close"].pct_change()
        prev_close = df["close"].shift(1)

        for window in MOMENTUM_WINDOWS:
            df[f"momentum_{window}"] = df["close"].pct_change(window)
        for window in REVERSAL_WINDOWS:
            df[f"reversal_{window}"] = -df["close"].pct_change(window)
        for window in RISK_WINDOWS:
            min_periods = _min_periods(window)
            df[f"volatility_{window}"] = ret.rolling(window, min_periods=min_periods).std()
        downside_ret = ret.where(ret < 0, 0.0)
        upside_ret = ret.where(ret > 0, 0.0)
        for window in [5, 10, 20, 60, 120]:
            df[f"downside_volatility_{window}"] = downside_ret.rolling(window, min_periods=_min_periods(window)).std()
        for window in [5, 10, 20, 60]:
            df[f"upside_volatility_{window}"] = upside_ret.rolling(window, min_periods=_min_periods(window)).std()
        for window in [20, 60, 120]:
            df[f"max_drawdown_{window}"] = df["close"].rolling(window, min_periods=_min_periods(window)).apply(
                _window_max_drawdown,
                raw=False,
            )

        moving_averages: dict[int, pd.Series] = {}
        for window in MA_WINDOWS:
            ma = df["close"].rolling(window, min_periods=_min_periods(window)).mean()
            moving_averages[window] = ma
            df[f"ma_bias_{window}"] = df["close"] / ma - 1
        for window in [5, 10, 20, 60]:
            ma = moving_averages[window]
            df[f"ma_slope_{window}"] = ma / ma.shift(window) - 1

        high_roll: dict[int, pd.Series] = {}
        low_roll: dict[int, pd.Series] = {}
        for window in POSITION_WINDOWS:
            high_roll[window] = df["high"].rolling(window, min_periods=_min_periods(window)).max()
            low_roll[window] = df["low"].rolling(window, min_periods=_min_periods(window)).min()
            spread = (high_roll[window] - low_roll[window]).replace(0, np.nan)
            df[f"price_position_{window}"] = (df["close"] - low_roll[window]) / spread
            df[f"breakout_high_{window}"] = df["close"] / high_roll[window] - 1
            df[f"breakdown_low_{window}"] = df["close"] / low_roll[window] - 1

        for window in LIQUIDITY_WINDOWS:
            df[f"amount_mean_{window}"] = df["amount"].rolling(window, min_periods=_min_periods(window)).mean()
            df[f"turnover_mean_{window}"] = df["turnover"].rolling(window, min_periods=_min_periods(window)).mean()
        for window in [20, 60]:
            amount_mean = df["amount"].rolling(window, min_periods=_min_periods(window)).mean()
            amount_std = df["amount"].rolling(window, min_periods=_min_periods(window)).std()
            turnover_mean = df["turnover"].rolling(window, min_periods=_min_periods(window)).mean()
            turnover_std = df["turnover"].rolling(window, min_periods=_min_periods(window)).std()
            df[f"amount_zscore_{window}"] = (df["amount"] - amount_mean) / amount_std.replace(0, np.nan)
            df[f"turnover_zscore_{window}"] = (df["turnover"] - turnover_mean) / turnover_std.replace(0, np.nan)
            df[f"amount_percentile_{window}"] = df["amount"].rolling(window, min_periods=_min_periods(window)).apply(
                _last_percentile,
                raw=False,
            )
            df[f"turnover_percentile_{window}"] = df["turnover"].rolling(window, min_periods=_min_periods(window)).apply(
                _last_percentile,
                raw=False,
            )

        volume_mean_5 = df["volume"].rolling(5, min_periods=5).mean()
        volume_mean_10 = df["volume"].rolling(10, min_periods=8).mean()
        volume_mean_20 = df["volume"].rolling(20, min_periods=15).mean()
        volume_mean_60 = df["volume"].rolling(60, min_periods=40).mean()
        amount_mean_5 = df["amount"].rolling(5, min_periods=5).mean()
        amount_mean_10 = df["amount"].rolling(10, min_periods=8).mean()
        amount_mean_20 = df["amount"].rolling(20, min_periods=15).mean()
        amount_mean_60 = df["amount"].rolling(60, min_periods=40).mean()
        df["volume_ratio_5_20"] = volume_mean_5 / volume_mean_20 - 1
        df["volume_ratio_10_60"] = volume_mean_10 / volume_mean_60 - 1
        df["amount_ratio_5_20"] = amount_mean_5 / amount_mean_20 - 1
        df["amount_ratio_10_60"] = amount_mean_10 / amount_mean_60 - 1

        df["intraday_return"] = df["close"] / df["open"] - 1
        df["overnight_return"] = df["open"] / prev_close - 1
        df["gap_return"] = df["open"] / prev_close - 1
        df["amplitude"] = (df["high"] - df["low"]) / prev_close
        candle_range = (df["high"] - df["low"]).replace(0, np.nan)
        df["close_position"] = (df["close"] - df["low"]) / candle_range
        df["upper_shadow"] = (df["high"] - df[["open", "close"]].max(axis=1)) / candle_range
        df["lower_shadow"] = (df[["open", "close"]].min(axis=1) - df["low"]) / candle_range
        df["body_size"] = (df["close"] - df["open"]).abs() / candle_range

        df["return_skew_20"] = ret.rolling(20, min_periods=15).skew()
        df["return_skew_60"] = ret.rolling(60, min_periods=40).skew()
        df["return_kurt_20"] = ret.rolling(20, min_periods=15).kurt()
        df["return_kurt_60"] = ret.rolling(60, min_periods=40).kurt()
        value_traded = df["amount"].replace(0, np.nan)
        illiquidity = ret.abs() / value_traded
        df["amihud_illiquidity_20"] = illiquidity.rolling(20, min_periods=15).mean()
        df["amihud_illiquidity_60"] = illiquidity.rolling(60, min_periods=40).mean()

        df = df.copy()
        limit_up = (ret >= 0.095).astype(float)
        limit_down = (ret <= -0.095).astype(float)
        up_day = (ret > 0).astype(float)
        down_day = (ret < 0).astype(float)
        df["limit_up_count_20"] = limit_up.rolling(20, min_periods=1).sum()
        df["limit_up_count_60"] = limit_up.rolling(60, min_periods=1).sum()
        df["limit_down_count_20"] = limit_down.rolling(20, min_periods=1).sum()
        df["limit_down_count_60"] = limit_down.rolling(60, min_periods=1).sum()
        df["up_day_ratio_20"] = up_day.rolling(20, min_periods=15).mean()
        df["up_day_ratio_60"] = up_day.rolling(60, min_periods=40).mean()
        df["down_day_ratio_20"] = down_day.rolling(20, min_periods=15).mean()
        df["down_day_ratio_60"] = down_day.rolling(60, min_periods=40).mean()
        df["up_streak"] = _streak(ret > 0)
        df["down_streak"] = _streak(ret < 0)
        df["new_high_distance_60"] = df["close"] / high_roll[60] - 1
        df["new_low_distance_60"] = df["close"] / low_roll[60] - 1

        df["symbol"] = symbol
        frames.append(df[["date", "symbol", "close", "amount", *FACTOR_COLUMNS]])

    if not frames:
        raise ValueError("No bars provided")

    panel = pd.concat(frames, ignore_index=True)
    panel = panel.set_index(["date", "symbol"]).sort_index()
    return panel


def _min_periods(window: int) -> int:
    if window <= 10:
        return max(3, int(window * 0.8))
    return max(10, int(window * 0.67))


def _window_max_drawdown(window: pd.Series) -> float:
    running_max = window.cummax()
    drawdown = window / running_max - 1
    return float(drawdown.min())


def _last_percentile(window: pd.Series) -> float:
    clean = window.dropna()
    if clean.empty:
        return np.nan
    return float(clean.rank(pct=True).iloc[-1])


def _streak(mask: pd.Series) -> pd.Series:
    groups = mask.ne(mask.shift()).cumsum()
    streak = mask.astype(int).groupby(groups).cumsum()
    return streak.where(mask, 0).astype(float)
