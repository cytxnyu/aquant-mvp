from __future__ import annotations

import numpy as np
import pandas as pd


def cross_sectional_rank(panel: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    ranked = panel.copy()
    for column in columns:
        ranked[f"{column}_rank"] = ranked.groupby(level="date")[column].rank(pct=True)
    return ranked


def cross_sectional_zscore(panel: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    zscored = panel.copy()
    grouped = zscored.groupby(level="date")
    for column in columns:
        mean = grouped[column].transform("mean")
        std = grouped[column].transform("std").replace(0, np.nan)
        zscored[f"{column}_zscore"] = (zscored[column] - mean) / std
    return zscored

