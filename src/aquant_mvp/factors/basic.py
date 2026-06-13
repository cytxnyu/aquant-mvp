from __future__ import annotations

import warnings

import numpy as np
import pandas as pd


warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)

MOMENTUM_WINDOWS = [1, 2, 3, 5, 10, 20, 40, 60, 120, 240]
REVERSAL_WINDOWS = [1, 2, 3, 5, 10, 20]
RISK_WINDOWS = [5, 10, 20, 40, 60, 120, 240]
MA_WINDOWS = [5, 10, 20, 40, 60, 120, 240]
EMA_WINDOWS = [5, 10, 12, 20, 26, 60, 120]
POSITION_WINDOWS = [20, 40, 60, 120, 240]
LIQUIDITY_WINDOWS = [5, 10, 20, 40, 60, 120]
RSI_WINDOWS = [6, 14, 24]
ATR_WINDOWS = [5, 10, 20, 60]
BB_WINDOWS = [20, 60]
CROWDING_WINDOWS = [20, 60]
OSCILLATOR_WINDOWS = [9, 14, 20]
FLOW_WINDOWS = [14, 20]
CROSS_SECTIONAL_FACTORS = [
    "cs_momentum_rank_20",
    "cs_momentum_rank_60",
    "cs_momentum_rank_120",
    "cs_reversal_rank_5",
    "cs_volatility_rank_20",
    "cs_volatility_rank_60",
    "cs_amount_rank_20",
    "cs_amount_rank_60",
    "cs_turnover_rank_20",
    "cs_turnover_rank_60",
    "cs_liquidity_risk_score",
    "market_breadth",
    "market_mean_return",
]


FACTOR_COLUMNS = [
    *[f"momentum_{window}" for window in MOMENTUM_WINDOWS],
    *[f"reversal_{window}" for window in REVERSAL_WINDOWS],
    *[f"volatility_{window}" for window in RISK_WINDOWS],
    *[f"downside_volatility_{window}" for window in [5, 10, 20, 60, 120]],
    *[f"upside_volatility_{window}" for window in [5, 10, 20, 60]],
    *[f"max_drawdown_{window}" for window in [20, 60, 120]],
    *[f"ma_bias_{window}" for window in MA_WINDOWS],
    *[f"ma_slope_{window}" for window in [5, 10, 20, 60]],
    *[f"ema_bias_{window}" for window in EMA_WINDOWS],
    *[f"ema_slope_{window}" for window in [12, 26, 60]],
    "macd_diff",
    "macd_signal",
    "macd_hist",
    *[f"rsi_{window}" for window in RSI_WINDOWS],
    "kdj_k_9",
    "kdj_d_9",
    "kdj_j_9",
    *[f"cci_{window}" for window in [14, 20]],
    *[f"williams_r_{window}" for window in [14, 20]],
    *[f"money_flow_index_{window}" for window in FLOW_WINDOWS],
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
    *[f"vwap_bias_{window}" for window in [5, 20, 60]],
    *[f"obv_slope_{window}" for window in [20, 60]],
    *[f"volume_price_corr_{window}" for window in [20, 60]],
    *[f"return_amount_corr_{window}" for window in [20, 60]],
    *[f"amount_shock_count_{window}" for window in [20, 60]],
    *[f"signed_volume_flow_{window}" for window in [20, 60]],
    *[f"price_volume_trend_{window}" for window in [20, 60]],
    "intraday_return",
    "overnight_return",
    "gap_return",
    "amplitude",
    *[f"atr_pct_{window}" for window in ATR_WINDOWS],
    *[f"amplitude_mean_{window}" for window in ATR_WINDOWS],
    *[f"amplitude_zscore_{window}" for window in [20, 60]],
    *[f"bollinger_zscore_{window}" for window in BB_WINDOWS],
    *[f"bollinger_width_{window}" for window in BB_WINDOWS],
    *[f"bollinger_breakout_count_{window}" for window in [20, 60]],
    "close_position",
    "upper_shadow",
    "lower_shadow",
    "body_size",
    *[f"close_to_high_{window}" for window in [20, 60, 120]],
    *[f"close_to_low_{window}" for window in [20, 60, 120]],
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
    "limit_up_near_5",
    "limit_down_near_5",
    *[f"gap_up_count_{window}" for window in [20, 60]],
    *[f"gap_down_count_{window}" for window in [20, 60]],
    *[f"long_upper_shadow_count_{window}" for window in [20, 60]],
    *[f"long_lower_shadow_count_{window}" for window in [20, 60]],
    "up_day_ratio_20",
    "up_day_ratio_60",
    "down_day_ratio_20",
    "down_day_ratio_60",
    *[f"positive_body_ratio_{window}" for window in [20, 60]],
    *[f"return_autocorr_{window}" for window in [20, 60]],
    *[f"downside_tail_return_{window}" for window in [20, 60]],
    *[f"upside_tail_return_{window}" for window in [20, 60]],
    *[f"return_abs_mean_{window}" for window in [20, 60]],
    *[f"price_efficiency_{window}" for window in [20, 60, 120]],
    *[f"trend_strength_{window}" for window in [20, 60, 120]],
    *[f"close_above_ma_ratio_{window}" for window in [20, 60]],
    "ma_alignment_score",
    "ema_alignment_score",
    *[f"volume_cv_{window}" for window in [20, 60]],
    *[f"amount_cv_{window}" for window in [20, 60]],
    *[f"turnover_cv_{window}" for window in [20, 60]],
    *[f"amount_crowding_{window}" for window in CROWDING_WINDOWS],
    *[f"turnover_crowding_{window}" for window in CROWDING_WINDOWS],
    *[f"shrinkage_breakout_{window}" for window in [20, 60]],
    *[f"stalled_up_volume_{window}" for window in [20, 60]],
    *[f"low_volume_pullback_{window}" for window in [20, 60]],
    *[f"volatility_contraction_{window}" for window in [20, 60]],
    "atr_contraction_20_60",
    *[f"range_compression_{window}" for window in [20, 60]],
    "up_streak",
    "down_streak",
    "new_high_distance_60",
    "new_low_distance_60",
    *CROSS_SECTIONAL_FACTORS,
]

PER_SYMBOL_FACTOR_COLUMNS = [factor for factor in FACTOR_COLUMNS if factor not in CROSS_SECTIONAL_FACTORS]


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

        ema_values: dict[int, pd.Series] = {}
        for window in EMA_WINDOWS:
            ema = df["close"].ewm(span=window, adjust=False, min_periods=_min_periods(window)).mean()
            ema_values[window] = ema
            df[f"ema_bias_{window}"] = df["close"] / ema - 1
        for window in [12, 26, 60]:
            ema = ema_values[window]
            df[f"ema_slope_{window}"] = ema / ema.shift(window) - 1
        macd_diff = ema_values[12] - ema_values[26]
        macd_signal = macd_diff.ewm(span=9, adjust=False, min_periods=6).mean()
        df["macd_diff"] = macd_diff / df["close"].replace(0, np.nan)
        df["macd_signal"] = macd_signal / df["close"].replace(0, np.nan)
        df["macd_hist"] = (macd_diff - macd_signal) / df["close"].replace(0, np.nan)
        for window in RSI_WINDOWS:
            df[f"rsi_{window}"] = _rsi(ret, window)

        high_roll: dict[int, pd.Series] = {}
        low_roll: dict[int, pd.Series] = {}
        for window in POSITION_WINDOWS:
            high_roll[window] = df["high"].rolling(window, min_periods=_min_periods(window)).max()
            low_roll[window] = df["low"].rolling(window, min_periods=_min_periods(window)).min()
            spread = (high_roll[window] - low_roll[window]).replace(0, np.nan)
            df[f"price_position_{window}"] = (df["close"] - low_roll[window]) / spread
            df[f"breakout_high_{window}"] = df["close"] / high_roll[window] - 1
            df[f"breakdown_low_{window}"] = df["close"] / low_roll[window] - 1

        rsv = (df["close"] - low_roll[20]) / (high_roll[20] - low_roll[20]).replace(0, np.nan) * 100
        df["kdj_k_9"] = rsv.ewm(alpha=1 / 3, adjust=False, min_periods=6).mean()
        df["kdj_d_9"] = df["kdj_k_9"].ewm(alpha=1 / 3, adjust=False, min_periods=6).mean()
        df["kdj_j_9"] = 3 * df["kdj_k_9"] - 2 * df["kdj_d_9"]
        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        for window in [14, 20]:
            tp_mean = typical_price.rolling(window, min_periods=_min_periods(window)).mean()
            mean_dev = (typical_price - tp_mean).abs().rolling(window, min_periods=_min_periods(window)).mean()
            df[f"cci_{window}"] = (typical_price - tp_mean) / (0.015 * mean_dev.replace(0, np.nan))
            hh = df["high"].rolling(window, min_periods=_min_periods(window)).max()
            ll = df["low"].rolling(window, min_periods=_min_periods(window)).min()
            df[f"williams_r_{window}"] = -100 * (hh - df["close"]) / (hh - ll).replace(0, np.nan)
        raw_money_flow = typical_price * df["volume"]
        positive_flow = raw_money_flow.where(typical_price.diff() > 0, 0.0)
        negative_flow = raw_money_flow.where(typical_price.diff() < 0, 0.0)
        for window in FLOW_WINDOWS:
            pos_sum = positive_flow.rolling(window, min_periods=_min_periods(window)).sum()
            neg_sum = negative_flow.rolling(window, min_periods=_min_periods(window)).sum()
            money_ratio = pos_sum / neg_sum.replace(0, np.nan)
            df[f"money_flow_index_{window}"] = 100 - 100 / (1 + money_ratio)

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
        for window in [5, 20, 60]:
            value_sum = df["amount"].rolling(window, min_periods=_min_periods(window)).sum()
            volume_sum = df["volume"].rolling(window, min_periods=_min_periods(window)).sum()
            vwap = value_sum / volume_sum.replace(0, np.nan)
            df[f"vwap_bias_{window}"] = df["close"] / vwap.replace(0, np.nan) - 1
        obv = (np.sign(ret.fillna(0.0)) * df["volume"]).cumsum()
        amount_change = df["amount"].pct_change()
        for window in [20, 60]:
            df[f"obv_slope_{window}"] = obv / obv.shift(window).replace(0, np.nan) - 1
            df[f"volume_price_corr_{window}"] = df["volume"].rolling(window, min_periods=_min_periods(window)).corr(df["close"])
            df[f"return_amount_corr_{window}"] = ret.rolling(window, min_periods=_min_periods(window)).corr(amount_change)
            shock = (df[f"amount_zscore_{20 if window == 20 else 60}"] > 1.5).astype(float)
            df[f"amount_shock_count_{window}"] = shock.rolling(window, min_periods=_min_periods(window)).sum()
            signed_flow = (np.sign(ret.fillna(0.0)) * df["amount"]).rolling(window, min_periods=_min_periods(window)).sum()
            df[f"signed_volume_flow_{window}"] = signed_flow / df["amount"].rolling(window, min_periods=_min_periods(window)).sum().replace(0, np.nan)
            pvt = (ret.fillna(0.0) * df["volume"]).cumsum()
            df[f"price_volume_trend_{window}"] = pvt / pvt.shift(window).replace(0, np.nan) - 1

        df["intraday_return"] = df["close"] / df["open"] - 1
        df["overnight_return"] = df["open"] / prev_close - 1
        df["gap_return"] = df["open"] / prev_close - 1
        df["amplitude"] = (df["high"] - df["low"]) / prev_close
        true_range = pd.concat(
            [
                df["high"] - df["low"],
                (df["high"] - prev_close).abs(),
                (df["low"] - prev_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        for window in ATR_WINDOWS:
            atr = true_range.rolling(window, min_periods=_min_periods(window)).mean()
            amp_mean = df["amplitude"].rolling(window, min_periods=_min_periods(window)).mean()
            df[f"atr_pct_{window}"] = atr / df["close"].replace(0, np.nan)
            df[f"amplitude_mean_{window}"] = amp_mean
        for window in [20, 60]:
            amp_mean = df["amplitude"].rolling(window, min_periods=_min_periods(window)).mean()
            amp_std = df["amplitude"].rolling(window, min_periods=_min_periods(window)).std()
            df[f"amplitude_zscore_{window}"] = (df["amplitude"] - amp_mean) / amp_std.replace(0, np.nan)
        for window in BB_WINDOWS:
            ma = moving_averages[window]
            std = df["close"].rolling(window, min_periods=_min_periods(window)).std()
            df[f"bollinger_zscore_{window}"] = (df["close"] - ma) / std.replace(0, np.nan)
            df[f"bollinger_width_{window}"] = (4 * std) / ma.replace(0, np.nan)
            df[f"bollinger_breakout_count_{window}"] = (df[f"bollinger_zscore_{window}"] > 2).astype(float).rolling(
                window,
                min_periods=_min_periods(window),
            ).sum()
        candle_range = (df["high"] - df["low"]).replace(0, np.nan)
        df["close_position"] = (df["close"] - df["low"]) / candle_range
        df["upper_shadow"] = (df["high"] - df[["open", "close"]].max(axis=1)) / candle_range
        df["lower_shadow"] = (df[["open", "close"]].min(axis=1) - df["low"]) / candle_range
        df["body_size"] = (df["close"] - df["open"]).abs() / candle_range
        for window in [20, 60, 120]:
            df[f"close_to_high_{window}"] = df["close"] / high_roll[window] - 1
            df[f"close_to_low_{window}"] = df["close"] / low_roll[window] - 1

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
        df["limit_up_near_5"] = (ret >= 0.075).astype(float).rolling(5, min_periods=1).sum()
        df["limit_down_near_5"] = (ret <= -0.075).astype(float).rolling(5, min_periods=1).sum()
        gap_up = (df["gap_return"] > 0.02).astype(float)
        gap_down = (df["gap_return"] < -0.02).astype(float)
        long_upper = (df["upper_shadow"] > 0.55).astype(float)
        long_lower = (df["lower_shadow"] > 0.55).astype(float)
        for window in [20, 60]:
            df[f"gap_up_count_{window}"] = gap_up.rolling(window, min_periods=_min_periods(window)).sum()
            df[f"gap_down_count_{window}"] = gap_down.rolling(window, min_periods=_min_periods(window)).sum()
            df[f"long_upper_shadow_count_{window}"] = long_upper.rolling(window, min_periods=_min_periods(window)).sum()
            df[f"long_lower_shadow_count_{window}"] = long_lower.rolling(window, min_periods=_min_periods(window)).sum()
        df["up_day_ratio_20"] = up_day.rolling(20, min_periods=15).mean()
        df["up_day_ratio_60"] = up_day.rolling(60, min_periods=40).mean()
        df["down_day_ratio_20"] = down_day.rolling(20, min_periods=15).mean()
        df["down_day_ratio_60"] = down_day.rolling(60, min_periods=40).mean()
        positive_body = (df["close"] > df["open"]).astype(float)
        for window in [20, 60]:
            df[f"positive_body_ratio_{window}"] = positive_body.rolling(window, min_periods=_min_periods(window)).mean()
            df[f"return_autocorr_{window}"] = ret.rolling(window, min_periods=_min_periods(window)).apply(_last_autocorr, raw=False)
            df[f"downside_tail_return_{window}"] = ret.rolling(window, min_periods=_min_periods(window)).quantile(0.10)
            df[f"upside_tail_return_{window}"] = ret.rolling(window, min_periods=_min_periods(window)).quantile(0.90)
            df[f"return_abs_mean_{window}"] = ret.abs().rolling(window, min_periods=_min_periods(window)).mean()
            volume_mean = df["volume"].rolling(window, min_periods=_min_periods(window)).mean()
            amount_mean = df["amount"].rolling(window, min_periods=_min_periods(window)).mean()
            turnover_mean = df["turnover"].rolling(window, min_periods=_min_periods(window)).mean()
            df[f"volume_cv_{window}"] = df["volume"].rolling(window, min_periods=_min_periods(window)).std() / volume_mean.replace(0, np.nan)
            df[f"amount_cv_{window}"] = df["amount"].rolling(window, min_periods=_min_periods(window)).std() / amount_mean.replace(0, np.nan)
            df[f"turnover_cv_{window}"] = df["turnover"].rolling(window, min_periods=_min_periods(window)).std() / turnover_mean.replace(0, np.nan)
            df[f"amount_crowding_{window}"] = df[f"amount_percentile_{window}"] * df[f"volatility_{window}"]
            df[f"turnover_crowding_{window}"] = df[f"turnover_percentile_{window}"] * df[f"volatility_{window}"]
            df[f"close_above_ma_ratio_{window}"] = (df["close"] > moving_averages[window]).astype(float).rolling(
                window,
                min_periods=_min_periods(window),
            ).mean()
            df[f"shrinkage_breakout_{window}"] = (df[f"breakout_high_{window}"] > -0.01).astype(float) * (
                df[f"volume_cv_{window}"] < df[f"volume_cv_{window}"].rolling(window, min_periods=_min_periods(window)).median()
            ).astype(float)
            stalled = ((ret > 0) & (ret < 0.01) & (df[f"amount_zscore_{window}"] > 1.0)).astype(float)
            df[f"stalled_up_volume_{window}"] = stalled.rolling(window, min_periods=_min_periods(window)).sum()
            pullback = ((ret < 0) & (df[f"amount_zscore_{window}"] < -0.5)).astype(float)
            df[f"low_volume_pullback_{window}"] = pullback.rolling(window, min_periods=_min_periods(window)).sum()
            df[f"volatility_contraction_{window}"] = df[f"volatility_{window}"] / df["volatility_120"].replace(0, np.nan)
            df[f"range_compression_{window}"] = df[f"amplitude_mean_{window}"] / df["amplitude_mean_60"].replace(0, np.nan)
        df["ma_alignment_score"] = (
            (moving_averages[5] > moving_averages[10]).astype(float)
            + (moving_averages[10] > moving_averages[20]).astype(float)
            + (moving_averages[20] > moving_averages[60]).astype(float)
        ) / 3
        df["ema_alignment_score"] = (
            (ema_values[5] > ema_values[10]).astype(float)
            + (ema_values[10] > ema_values[20]).astype(float)
            + (ema_values[20] > ema_values[60]).astype(float)
        ) / 3
        df["atr_contraction_20_60"] = df["atr_pct_20"] / df["atr_pct_60"].replace(0, np.nan)
        for window in [20, 60, 120]:
            net_move = df["close"].pct_change(window).abs()
            path_move = ret.abs().rolling(window, min_periods=_min_periods(window)).sum()
            df[f"price_efficiency_{window}"] = net_move / path_move.replace(0, np.nan)
            df[f"trend_strength_{window}"] = net_move / df[f"volatility_{window}"].replace(0, np.nan)
        df["up_streak"] = _streak(ret > 0)
        df["down_streak"] = _streak(ret < 0)
        df["new_high_distance_60"] = df["close"] / high_roll[60] - 1
        df["new_low_distance_60"] = df["close"] / low_roll[60] - 1

        df["symbol"] = symbol
        frames.append(df[["date", "symbol", "close", "amount", *PER_SYMBOL_FACTOR_COLUMNS]])

    if not frames:
        raise ValueError("No bars provided")

    panel = pd.concat(frames, ignore_index=True)
    panel = panel.set_index(["date", "symbol"]).sort_index()
    panel = _add_cross_sectional_factors(panel)
    return panel[["close", "amount", *FACTOR_COLUMNS]]


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


def _rsi(ret: pd.Series, window: int) -> pd.Series:
    gain = ret.clip(lower=0).rolling(window, min_periods=_min_periods(window)).mean()
    loss = (-ret.clip(upper=0)).rolling(window, min_periods=_min_periods(window)).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def _last_autocorr(window: pd.Series) -> float:
    clean = window.dropna()
    if len(clean) < 5 or clean.nunique() < 2:
        return np.nan
    return float(clean.autocorr(lag=1))


def _add_cross_sectional_factors(panel: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy()
    date_level = out.index.get_level_values("date")
    by_date = out.groupby(level="date", sort=False)
    rank_specs = {
        "cs_momentum_rank_20": "momentum_20",
        "cs_momentum_rank_60": "momentum_60",
        "cs_momentum_rank_120": "momentum_120",
        "cs_reversal_rank_5": "reversal_5",
        "cs_volatility_rank_20": "volatility_20",
        "cs_volatility_rank_60": "volatility_60",
        "cs_amount_rank_20": "amount_mean_20",
        "cs_amount_rank_60": "amount_mean_60",
        "cs_turnover_rank_20": "turnover_mean_20",
        "cs_turnover_rank_60": "turnover_mean_60",
    }
    for factor, source in rank_specs.items():
        out[factor] = by_date[source].rank(pct=True)
    out["cs_liquidity_risk_score"] = out[["cs_volatility_rank_20", "cs_turnover_rank_20", "cs_amount_rank_20"]].mean(axis=1)
    symbol_returns = out.groupby(level="symbol", sort=False)["close"].pct_change()
    market = pd.DataFrame({"date": date_level, "ret": symbol_returns.to_numpy()})
    breadth = market.groupby("date")["ret"].apply(lambda values: float((values > 0).mean()))
    mean_return = market.groupby("date")["ret"].mean()
    out["market_breadth"] = date_level.map(breadth)
    out["market_mean_return"] = date_level.map(mean_return)
    return out
