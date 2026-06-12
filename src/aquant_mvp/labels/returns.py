from __future__ import annotations

import pandas as pd


def compute_return_labels(bars_by_symbol: dict[str, pd.DataFrame], horizons: list[int]) -> pd.DataFrame:
    frames = []
    for symbol, bars in bars_by_symbol.items():
        df = bars.sort_values("date")[["date", "close"]].copy()
        df["symbol"] = symbol
        for horizon in horizons:
            df[f"future_return_{horizon}d"] = df["close"].shift(-horizon) / df["close"] - 1
        frames.append(df.drop(columns=["close"]))

    labels = pd.concat(frames, ignore_index=True).set_index(["date", "symbol"]).sort_index()
    for horizon in horizons:
        column = f"future_return_{horizon}d"
        excess_column = f"excess_return_{horizon}d"
        cross_section_mean = labels.groupby(level="date")[column].transform("mean")
        labels[excess_column] = labels[column] - cross_section_mean
    return labels


def compute_stock_prediction_labels(bars_by_symbol: dict[str, pd.DataFrame], horizons: list[int]) -> pd.DataFrame:
    """Build future-return, direction and downside-risk labels for stock forecasts."""
    labels = compute_return_labels(bars_by_symbol, horizons)
    downside_frames = []
    for symbol, bars in bars_by_symbol.items():
        df = bars.sort_values("date")[["date", "close"]].copy()
        df["symbol"] = symbol
        for horizon in horizons:
            future_prices = pd.concat([df["close"].shift(-step) for step in range(1, horizon + 1)], axis=1)
            future_min = future_prices.min(axis=1)
            future_max = future_prices.max(axis=1)
            df[f"future_downside_{horizon}d"] = future_min / df["close"] - 1
            df[f"future_upside_{horizon}d"] = future_max / df["close"] - 1
            df[f"direction_up_{horizon}d"] = (df["close"].shift(-horizon) > df["close"]).astype("float64")
            df.loc[df["close"].shift(-horizon).isna(), f"direction_up_{horizon}d"] = pd.NA
        downside_frames.append(df.drop(columns=["close"]))
    extra = pd.concat(downside_frames, ignore_index=True).set_index(["date", "symbol"]).sort_index()
    return labels.join(extra, how="left")

