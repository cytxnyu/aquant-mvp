from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path

import numpy as np
import pandas as pd

from aquant_mvp.config import DEFAULT_FACTOR_WEIGHTS
from aquant_mvp.factors import FACTOR_COLUMNS, compute_factor_panel
from aquant_mvp.labels import compute_stock_prediction_labels
from aquant_mvp.modeling.registry import register_model
from aquant_mvp.strategy import score_factors


def train_model(
    bars_by_symbol: dict[str, pd.DataFrame],
    model_type: str,
    horizons: list[int],
    output_dir: Path,
    registry_dir: Path,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    factors = compute_factor_panel(bars_by_symbol)
    labels = compute_stock_prediction_labels(bars_by_symbol, horizons)
    scores = score_factors(factors, DEFAULT_FACTOR_WEIGHTS)
    records = []
    for horizon in horizons:
        record = _train_one_horizon(factors, labels, scores, model_type, horizon, output_dir, registry_dir)
        records.append(record)
    summary = {"model_type": model_type, "horizons": horizons, "records": records}
    (output_dir / "train_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return summary


def _train_one_horizon(
    factors: pd.DataFrame,
    labels: pd.DataFrame,
    scores: pd.DataFrame,
    model_type: str,
    horizon: int,
    output_dir: Path,
    registry_dir: Path,
) -> dict[str, object]:
    label_col = f"future_return_{horizon}d"
    direction_col = f"direction_up_{horizon}d"
    dataset = factors[FACTOR_COLUMNS].join(labels[[label_col, direction_col]], how="inner")
    dataset = dataset.replace([np.inf, -np.inf], np.nan).dropna(subset=[label_col, direction_col])
    features = _select_features(dataset)
    model_id = f"{model_type}_h{horizon}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    artifact_path = output_dir / f"{model_id}.json"
    metadata: dict[str, object] = {
        "model_id": model_id,
        "model_type": model_type,
        "horizon_days": horizon,
        "feature_set": features,
        "label": label_col,
        "direction_label": direction_col,
        "train_rows": int(len(dataset)),
        "artifact_path": str(artifact_path),
    }
    lgbm_record = None
    if model_type in {"lightgbm_regressor", "lightgbm_classifier", "lightgbm_ranker", "ensemble", "lightgbm"}:
        lgbm_record = _try_train_lightgbm(dataset, features, model_type, label_col, direction_col, output_dir, model_id)
    if lgbm_record is None:
        baseline = _baseline_metrics(scores, labels, horizon)
        metadata["model_family"] = "factor_score_baseline"
        metadata["metrics"] = baseline
        artifact_path.write_text(json.dumps({"model": "factor_score_baseline", "weights": DEFAULT_FACTOR_WEIGHTS}, indent=2), encoding="utf-8")
    else:
        metadata.update(lgbm_record)
    record = register_model(registry_dir, metadata)
    return record


def _try_train_lightgbm(
    dataset: pd.DataFrame,
    features: list[str],
    model_type: str,
    label_col: str,
    direction_col: str,
    output_dir: Path,
    model_id: str,
) -> dict[str, object] | None:
    if len(features) < 5 or len(dataset) < 200:
        return None
    try:
        from lightgbm import LGBMClassifier, LGBMRanker, LGBMRegressor  # type: ignore
    except ImportError:
        return None

    train, valid = _time_split(dataset)
    artifact = output_dir / f"{model_id}.txt"
    metrics: dict[str, float] = {}
    if model_type == "lightgbm_classifier":
        if train[direction_col].nunique() < 2:
            return None
        model = LGBMClassifier(n_estimators=160, learning_rate=0.04, num_leaves=15, random_state=42, verbose=-1)
        model.fit(train[features], train[direction_col].astype(int))
        if not valid.empty:
            pred = pd.Series(model.predict_proba(valid[features])[:, 1], index=valid.index)
            metrics["valid_accuracy"] = float(((pred >= 0.5).astype(int) == valid[direction_col].astype(int)).mean())
            metrics["valid_brier"] = float(((pred - valid[direction_col]) ** 2).mean())
    elif model_type == "lightgbm_ranker":
        train_rank = train.copy()
        train_rank["rank_label"] = train_rank.groupby(level="date")[label_col].rank(method="first").astype(int)
        group = train_rank.groupby(level="date").size().to_list()
        model = LGBMRanker(n_estimators=120, learning_rate=0.05, num_leaves=15, random_state=42, verbose=-1)
        model.fit(train_rank[features], train_rank["rank_label"], group=group)
        if not valid.empty:
            pred = pd.Series(model.predict(valid[features]), index=valid.index)
            metrics["valid_rank_ic"] = _safe_corr(pred, valid[label_col], "spearman")
    else:
        model = LGBMRegressor(n_estimators=160, learning_rate=0.04, num_leaves=15, random_state=42, verbose=-1)
        model.fit(train[features], train[label_col])
        if not valid.empty:
            pred = pd.Series(model.predict(valid[features]), index=valid.index)
            metrics["valid_rank_ic"] = _safe_corr(pred, valid[label_col], "spearman")
            metrics["valid_mae"] = float((pred - valid[label_col]).abs().mean())
    model.booster_.save_model(str(artifact))
    return {"model_family": "lightgbm", "metrics": metrics, "artifact_path": str(artifact)}


def _baseline_metrics(scores: pd.DataFrame, labels: pd.DataFrame, horizon: int) -> dict[str, float]:
    label_col = f"future_return_{horizon}d"
    direction_col = f"direction_up_{horizon}d"
    dataset = scores[["score"]].join(labels[[label_col, direction_col]], how="inner").dropna()
    dataset["score_percentile"] = dataset.groupby(level="date")["score"].rank(pct=True)
    return {
        "rank_ic": _safe_corr(dataset["score_percentile"], dataset[label_col], "spearman"),
        "direction_accuracy": float(((dataset["score_percentile"] >= 0.5).astype(int) == dataset[direction_col].astype(int)).mean())
        if not dataset.empty
        else 0.0,
    }


def _select_features(dataset: pd.DataFrame) -> list[str]:
    coverage = dataset[FACTOR_COLUMNS].notna().mean()
    return coverage[coverage >= 0.55].index.tolist()


def _time_split(dataset: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    dates = pd.DatetimeIndex(dataset.index.get_level_values("date").unique()).sort_values()
    if len(dates) < 30:
        return dataset, dataset.iloc[0:0]
    split = int(len(dates) * 0.8)
    train = dataset[dataset.index.get_level_values("date").isin(dates[:split])]
    valid = dataset[dataset.index.get_level_values("date").isin(dates[split:])]
    return train, valid


def _safe_corr(left: pd.Series, right: pd.Series, method: str) -> float:
    if left.nunique() < 2 or right.nunique() < 2:
        return 0.0
    value = left.corr(right, method=method)
    if value is None or np.isnan(value):
        return 0.0
    return float(value)
