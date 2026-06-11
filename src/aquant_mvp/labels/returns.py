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

