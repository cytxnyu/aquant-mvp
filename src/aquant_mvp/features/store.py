from __future__ import annotations

from dataclasses import dataclass
import hashlib

import pandas as pd

from aquant_mvp.factors import FACTOR_COLUMNS, compute_factor_panel
from aquant_mvp.labels import compute_stock_prediction_labels


@dataclass(frozen=True)
class FeatureStoreResult:
    features: pd.DataFrame
    metadata: dict[str, object]


def build_point_in_time_feature_store(
    bars_by_symbol: dict[str, pd.DataFrame],
    horizons: list[int],
    source: str,
) -> FeatureStoreResult:
    factors = compute_factor_panel(bars_by_symbol)
    labels = compute_stock_prediction_labels(bars_by_symbol, horizons)
    frame = factors.join(labels, how="left").reset_index()
    frame["effective_date"] = pd.to_datetime(frame["date"])
    frame["source"] = source
    frame["feature_version"] = _feature_version(FACTOR_COLUMNS, horizons, source)
    frame["pit_ready"] = True
    coverage = frame[FACTOR_COLUMNS].notna().mean().sort_values()
    metadata = {
        "source": source,
        "feature_version": frame["feature_version"].iloc[0] if not frame.empty else "",
        "rows": int(len(frame)),
        "symbols": int(frame["symbol"].nunique()) if not frame.empty else 0,
        "start_date": str(pd.to_datetime(frame["date"]).min().date()) if not frame.empty else "",
        "end_date": str(pd.to_datetime(frame["date"]).max().date()) if not frame.empty else "",
        "feature_count": len(FACTOR_COLUMNS),
        "low_coverage_features": coverage[coverage < 0.60].index.tolist(),
    }
    return FeatureStoreResult(features=frame, metadata=metadata)


def _feature_version(features: list[str], horizons: list[int], source: str) -> str:
    payload = "|".join([source, ",".join(features), ",".join(map(str, horizons))])
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]
