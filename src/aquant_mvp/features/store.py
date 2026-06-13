from __future__ import annotations

from dataclasses import dataclass
import hashlib

import pandas as pd

from aquant_mvp.events import EVENT_FACTOR_CONTEXT_COLUMNS, EVENT_FACTOR_NUMERIC_COLUMNS
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
    event_factors: pd.DataFrame | None = None,
) -> FeatureStoreResult:
    factors = compute_factor_panel(bars_by_symbol)
    labels = compute_stock_prediction_labels(bars_by_symbol, horizons)
    frame = factors.join(labels, how="left").reset_index()
    frame, event_feature_columns = merge_event_factors_into_frame(frame, event_factors)
    feature_columns = [*FACTOR_COLUMNS, *event_feature_columns]
    fetched_at = pd.Timestamp.now().isoformat(timespec="seconds")
    frame["effective_date"] = pd.to_datetime(frame["date"])
    frame["source"] = source
    frame["fetched_at"] = fetched_at
    frame["announce_date"] = pd.NaT
    frame["quality_flag"] = "ok"
    frame["feature_version"] = _feature_version(feature_columns, horizons, source)
    frame["pit_ready"] = True
    frame["raw_hash"] = pd.util.hash_pandas_object(frame.astype(str), index=False).astype(str)
    coverage = frame[feature_columns].notna().mean().sort_values() if feature_columns else pd.Series(dtype=float)
    event_feature_quality = audit_event_feature_matrix(frame, event_feature_columns)
    event_quality_counts = (
        event_feature_quality["quality_status"].value_counts().to_dict()
        if not event_feature_quality.empty and "quality_status" in event_feature_quality.columns
        else {}
    )
    metadata = {
        "source": source,
        "feature_version": frame["feature_version"].iloc[0] if not frame.empty else "",
        "rows": int(len(frame)),
        "symbols": int(frame["symbol"].nunique()) if not frame.empty else 0,
        "start_date": str(pd.to_datetime(frame["date"]).min().date()) if not frame.empty else "",
        "end_date": str(pd.to_datetime(frame["date"]).max().date()) if not frame.empty else "",
        "feature_count": len(feature_columns),
        "base_factor_count": len(FACTOR_COLUMNS),
        "event_feature_count": len(event_feature_columns),
        "event_features": event_feature_columns,
        "event_factor_rows": int(len(event_factors)) if event_factors is not None else 0,
        "event_feature_quality_counts": event_quality_counts,
        "event_feature_quality_passed": bool(
            not event_feature_quality.empty
            and event_feature_quality["quality_status"].isin(["approved", "watchlist"]).all()
            and event_feature_quality["quality_status"].eq("approved").mean() >= 0.50
        )
        if event_feature_columns
        else True,
        "low_coverage_features": coverage[coverage < 0.60].index.tolist(),
    }
    return FeatureStoreResult(features=frame, metadata=metadata)


def merge_event_factors_into_frame(
    frame: pd.DataFrame,
    event_factors: pd.DataFrame | None,
) -> tuple[pd.DataFrame, list[str]]:
    if event_factors is None or event_factors.empty or frame.empty:
        return frame, []
    if not {"date", "symbol"}.issubset(event_factors.columns):
        return frame, []

    event_columns = [column for column in EVENT_FACTOR_NUMERIC_COLUMNS if column in event_factors.columns]
    context_columns = [column for column in EVENT_FACTOR_CONTEXT_COLUMNS if column in event_factors.columns]
    if not event_columns and not context_columns:
        return frame, []

    left = frame.copy()
    left["date"] = pd.to_datetime(left["date"]).dt.normalize()
    left["symbol"] = left["symbol"].astype(str).str.zfill(6)

    right = event_factors[["date", "symbol", *event_columns, *context_columns]].copy()
    right["date"] = pd.to_datetime(right["date"], errors="coerce").dt.normalize()
    right["symbol"] = right["symbol"].astype(str).str.zfill(6)
    right = right.dropna(subset=["date"])
    if right.empty:
        return left, []
    right = right.sort_values(["date", "symbol"]).drop_duplicates(["date", "symbol"], keep="last")
    for column in event_columns:
        right[column] = pd.to_numeric(right[column], errors="coerce")

    merged = left.merge(right, on=["date", "symbol"], how="left")
    for column in event_columns:
        merged[column] = merged[column].fillna(0.0)
    for column in context_columns:
        merged[column] = merged[column].fillna("")
    return merged, event_columns


def merge_event_factors_into_panel(
    panel: pd.DataFrame,
    event_factors: pd.DataFrame | None,
) -> tuple[pd.DataFrame, list[str]]:
    if panel.empty:
        return panel, []
    frame = panel.reset_index()
    merged, event_columns = merge_event_factors_into_frame(frame, event_factors)
    if not event_columns:
        return panel, []
    merged = merged.set_index(["date", "symbol"]).sort_index()
    return merged, event_columns


def audit_event_feature_matrix(frame: pd.DataFrame, event_feature_columns: list[str]) -> pd.DataFrame:
    rows = []
    if frame.empty or not event_feature_columns:
        return pd.DataFrame(
            columns=[
                "feature",
                "coverage",
                "nonzero_ratio",
                "mean_abs_value",
                "distinct_values",
                "quality_status",
                "failed_reasons",
                "can_enter_trusted_model",
            ]
        )
    for column in event_feature_columns:
        if column not in frame.columns:
            rows.append(
                {
                    "feature": column,
                    "coverage": 0.0,
                    "nonzero_ratio": 0.0,
                    "mean_abs_value": 0.0,
                    "distinct_values": 0,
                    "quality_status": "quarantine",
                    "failed_reasons": "missing_feature_column",
                    "can_enter_trusted_model": False,
                }
            )
            continue
        values = pd.to_numeric(frame[column], errors="coerce")
        coverage = float(values.notna().mean()) if len(values) else 0.0
        filled = values.fillna(0.0)
        nonzero_ratio = float(filled.abs().gt(1e-12).mean()) if len(filled) else 0.0
        mean_abs_value = float(filled.abs().mean()) if len(filled) else 0.0
        distinct_values = int(values.dropna().nunique())
        failed = []
        if coverage < 0.95:
            failed.append("low_matrix_coverage")
        if nonzero_ratio <= 0.0:
            failed.append("all_zero_event_feature")
        elif nonzero_ratio < 0.01:
            failed.append("sparse_event_signal")
        if distinct_values < 2:
            failed.append("constant_event_feature")
        if not failed:
            status = "approved"
        elif {"all_zero_event_feature", "constant_event_feature"}.intersection(failed):
            status = "quarantine"
        else:
            status = "watchlist"
        rows.append(
            {
                "feature": column,
                "coverage": coverage,
                "nonzero_ratio": nonzero_ratio,
                "mean_abs_value": mean_abs_value,
                "distinct_values": distinct_values,
                "quality_status": status,
                "failed_reasons": ";".join(failed) if failed else "passed",
                "can_enter_trusted_model": status == "approved",
            }
        )
    return pd.DataFrame(rows)


def _feature_version(features: list[str], horizons: list[int], source: str) -> str:
    payload = "|".join([source, ",".join(features), ",".join(map(str, horizons))])
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]
