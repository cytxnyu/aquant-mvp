from __future__ import annotations

from datetime import datetime
import importlib.util
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
        "requested_model_type": model_type,
        "effective_model_type": model_type,
        "model_base_status": "requested",
        "fallback_reason": "",
    }
    trained_record = _try_train_requested_model(dataset, features, model_type, label_col, direction_col, output_dir, model_id)
    if trained_record is None:
        baseline = _baseline_metrics(scores, labels, horizon)
        metadata["model_family"] = "factor_score_baseline"
        metadata["effective_model_type"] = "factor_score"
        metadata["model_base_status"] = "fallback"
        metadata["fallback_reason"] = _fallback_reason(dataset, features, model_type, direction_col)
        metadata["metrics"] = baseline
        artifact_path.write_text(json.dumps({"model": "factor_score_baseline", "weights": DEFAULT_FACTOR_WEIGHTS}, indent=2), encoding="utf-8")
    else:
        metadata.update(trained_record)
    record = register_model(registry_dir, metadata)
    return record


def _try_train_requested_model(
    dataset: pd.DataFrame,
    features: list[str],
    model_type: str,
    label_col: str,
    direction_col: str,
    output_dir: Path,
    model_id: str,
) -> dict[str, object] | None:
    normalized = model_type.lower().replace("-", "_")
    if len(features) < 5 or len(dataset) < 200:
        return None
    if normalized in {"lightgbm_regressor", "lightgbm_classifier", "lightgbm_ranker", "ensemble", "event_aware_ensemble", "lightgbm"}:
        return _try_train_lightgbm(dataset, features, normalized, label_col, direction_col, output_dir, model_id)
    if normalized in {"xgboost", "xgb"}:
        return _try_train_xgboost(dataset, features, label_col, direction_col, output_dir, model_id)
    if normalized in {"catboost", "cat"}:
        return _try_train_catboost(dataset, features, label_col, direction_col, output_dir, model_id)
    if normalized in {"logistic", "ridge", "linear", "sklearn", "sklearn_linear"}:
        return _try_train_sklearn(dataset, features, normalized, label_col, direction_col, output_dir, model_id)
    return None


def _try_train_lightgbm(
    dataset: pd.DataFrame,
    features: list[str],
    model_type: str,
    label_col: str,
    direction_col: str,
    output_dir: Path,
    model_id: str,
) -> dict[str, object] | None:
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
    return {
        "model_family": "lightgbm",
        "effective_model_type": model_type,
        "model_base_status": "trained",
        "metrics": metrics,
        "artifact_path": str(artifact),
    }


def _try_train_xgboost(
    dataset: pd.DataFrame,
    features: list[str],
    label_col: str,
    direction_col: str,
    output_dir: Path,
    model_id: str,
) -> dict[str, object] | None:
    try:
        from xgboost import XGBClassifier, XGBRegressor  # type: ignore
    except ImportError:
        return None

    train, valid = _time_split(dataset)
    if train.empty:
        return None
    fill_values = train[features].median(numeric_only=True)
    X_train = train[features].fillna(fill_values)
    X_valid = valid[features].fillna(fill_values) if not valid.empty else valid[features]
    artifact = output_dir / f"{model_id}.xgb.json"
    metrics: dict[str, float] = {}
    if train[direction_col].nunique() >= 2:
        clf = XGBClassifier(
            n_estimators=120,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=45,
            eval_metric="logloss",
        )
        clf.fit(X_train, train[direction_col].astype(int))
        if not valid.empty:
            prob = pd.Series(clf.predict_proba(X_valid)[:, 1], index=valid.index)
            metrics["valid_accuracy"] = float(((prob >= 0.5).astype(int) == valid[direction_col].astype(int)).mean())
            metrics["valid_brier"] = float(((prob - valid[direction_col]) ** 2).mean())
    reg = XGBRegressor(
        n_estimators=120,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=46,
    )
    reg.fit(X_train, train[label_col])
    if not valid.empty:
        pred = pd.Series(reg.predict(X_valid), index=valid.index)
        metrics["valid_rank_ic"] = _safe_corr(pred, valid[label_col], "spearman")
        metrics["valid_mae"] = float((pred - valid[label_col]).abs().mean())
    reg.save_model(str(artifact))
    return {
        "model_family": "xgboost",
        "effective_model_type": "xgboost",
        "model_base_status": "trained",
        "metrics": metrics,
        "artifact_path": str(artifact),
    }


def _try_train_catboost(
    dataset: pd.DataFrame,
    features: list[str],
    label_col: str,
    direction_col: str,
    output_dir: Path,
    model_id: str,
) -> dict[str, object] | None:
    try:
        from catboost import CatBoostClassifier, CatBoostRegressor  # type: ignore
    except ImportError:
        return None

    train, valid = _time_split(dataset)
    if train.empty:
        return None
    artifact = output_dir / f"{model_id}.cbm"
    metrics: dict[str, float] = {}
    if train[direction_col].nunique() >= 2:
        clf = CatBoostClassifier(
            iterations=120,
            depth=4,
            learning_rate=0.05,
            loss_function="Logloss",
            verbose=False,
            random_seed=47,
            allow_writing_files=False,
        )
        clf.fit(train[features], train[direction_col].astype(int))
        if not valid.empty:
            prob = pd.Series(clf.predict_proba(valid[features])[:, 1], index=valid.index)
            metrics["valid_accuracy"] = float(((prob >= 0.5).astype(int) == valid[direction_col].astype(int)).mean())
            metrics["valid_brier"] = float(((prob - valid[direction_col]) ** 2).mean())
    reg = CatBoostRegressor(
        iterations=120,
        depth=4,
        learning_rate=0.05,
        loss_function="RMSE",
        verbose=False,
        random_seed=48,
        allow_writing_files=False,
    )
    reg.fit(train[features], train[label_col])
    if not valid.empty:
        pred = pd.Series(reg.predict(valid[features]), index=valid.index)
        metrics["valid_rank_ic"] = _safe_corr(pred, valid[label_col], "spearman")
        metrics["valid_mae"] = float((pred - valid[label_col]).abs().mean())
    reg.save_model(str(artifact))
    return {
        "model_family": "catboost",
        "effective_model_type": "catboost",
        "model_base_status": "trained",
        "metrics": metrics,
        "artifact_path": str(artifact),
    }


def _try_train_sklearn(
    dataset: pd.DataFrame,
    features: list[str],
    model_type: str,
    label_col: str,
    direction_col: str,
    output_dir: Path,
    model_id: str,
) -> dict[str, object] | None:
    try:
        import joblib  # type: ignore
        from sklearn.impute import SimpleImputer  # type: ignore
        from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge  # type: ignore
        from sklearn.pipeline import make_pipeline  # type: ignore
        from sklearn.preprocessing import StandardScaler  # type: ignore
    except ImportError:
        return None

    train, valid = _time_split(dataset)
    if train.empty:
        return None
    artifact = output_dir / f"{model_id}.joblib"
    reg_model = LinearRegression() if model_type == "linear" else Ridge(alpha=1.0)
    reg = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), reg_model)
    reg.fit(train[features], train[label_col])
    metrics: dict[str, float] = {}
    if not valid.empty:
        pred = pd.Series(reg.predict(valid[features]), index=valid.index)
        metrics["valid_rank_ic"] = _safe_corr(pred, valid[label_col], "spearman")
        metrics["valid_mae"] = float((pred - valid[label_col]).abs().mean())
    if train[direction_col].nunique() >= 2:
        clf = make_pipeline(
            SimpleImputer(strategy="median"),
            StandardScaler(),
            LogisticRegression(max_iter=1000, class_weight="balanced"),
        )
        clf.fit(train[features], train[direction_col].astype(int))
        if not valid.empty:
            prob = pd.Series(clf.predict_proba(valid[features])[:, 1], index=valid.index)
            metrics["valid_accuracy"] = float(((prob >= 0.5).astype(int) == valid[direction_col].astype(int)).mean())
            metrics["valid_brier"] = float(((prob - valid[direction_col]) ** 2).mean())
        artifact_payload = {"regressor": reg, "classifier": clf, "features": features}
    else:
        artifact_payload = {"regressor": reg, "classifier": None, "features": features}
    joblib.dump(artifact_payload, artifact)
    return {
        "model_family": "sklearn_linear",
        "effective_model_type": model_type,
        "model_base_status": "trained",
        "metrics": metrics,
        "artifact_path": str(artifact),
    }


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


def _fallback_reason(dataset: pd.DataFrame, features: list[str], model_type: str, direction_col: str) -> str:
    normalized = model_type.lower().replace("-", "_")
    if len(dataset) < 200:
        return "insufficient_training_rows"
    if len(features) < 5:
        return "insufficient_feature_coverage"
    if normalized in {"lightgbm_regressor", "lightgbm_classifier", "lightgbm_ranker", "ensemble", "event_aware_ensemble", "lightgbm"} and importlib.util.find_spec("lightgbm") is None:
        return "lightgbm_not_installed"
    if normalized in {"xgboost", "xgb"} and importlib.util.find_spec("xgboost") is None:
        return "xgboost_not_installed"
    if normalized in {"catboost", "cat"} and importlib.util.find_spec("catboost") is None:
        return "catboost_not_installed"
    if normalized in {"logistic", "ridge", "linear", "sklearn", "sklearn_linear"} and importlib.util.find_spec("sklearn") is None:
        return "sklearn_not_installed"
    if "classifier" in normalized and dataset[direction_col].nunique() < 2:
        return "single_class_direction_label"
    return "requested_model_failed_or_unsupported"


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
