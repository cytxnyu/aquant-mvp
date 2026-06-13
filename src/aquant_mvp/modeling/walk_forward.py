from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

import numpy as np
import pandas as pd

from aquant_mvp.config import DEFAULT_FACTOR_WEIGHTS
from aquant_mvp.features import audit_event_feature_matrix, merge_event_factors_into_panel
from aquant_mvp.factors import FACTOR_COLUMNS, compute_factor_panel
from aquant_mvp.labels import compute_stock_prediction_labels
from aquant_mvp.modeling.calibration import calibrate_probability_series
from aquant_mvp.modeling.registry import register_model
from aquant_mvp.strategy import score_factors


EVALUATION_DIAGNOSTIC_COLUMNS = [
    "amount_mean_20",
    "amount_mean_60",
    "turnover_mean_20",
    "volatility_20",
    "downside_volatility_20",
    "cs_amount_rank_20",
    "cs_volatility_rank_20",
    "cs_liquidity_risk_score",
    "market_breadth",
    "market_mean_return",
]


@dataclass(frozen=True)
class WalkForwardResult:
    predictions: pd.DataFrame
    metrics: pd.DataFrame
    summary: dict[str, object]


def train_walk_forward(
    bars_by_symbol: dict[str, pd.DataFrame],
    model_type: str,
    horizons: list[int],
    output_dir: Path,
    registry_dir: Path,
    min_symbols: int = 200,
    train_years: int = 4,
    test_months: int = 6,
    embargo_days: int = 5,
    event_factors: pd.DataFrame | None = None,
    feature_columns: list[str] | None = None,
    feature_set_source: str | None = None,
) -> WalkForwardResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    factors = compute_factor_panel(bars_by_symbol)
    factors, event_feature_columns = merge_event_factors_into_panel(factors, event_factors)
    event_feature_quality = audit_event_feature_matrix(factors.reset_index(), event_feature_columns)
    base_feature_columns = list(feature_columns) if feature_columns is not None else list(FACTOR_COLUMNS)
    selected_feature_columns = [*base_feature_columns, *[column for column in event_feature_columns if column not in base_feature_columns]]
    feature_source = feature_set_source or ("explicit" if feature_columns is not None else "all_factor_columns")
    labels = compute_stock_prediction_labels(bars_by_symbol, horizons)
    scores = score_factors(factors, DEFAULT_FACTOR_WEIGHTS)
    all_predictions = []
    metric_rows = []
    status = "trusted_candidate" if len(bars_by_symbol) >= min_symbols else "data_insufficient"
    for horizon in horizons:
        pred, metrics = _walk_one_horizon(
            factors,
            labels,
            scores,
            horizon,
            model_type,
            train_years,
            test_months,
            embargo_days,
            selected_feature_columns,
        )
        pred["horizon_days"] = horizon
        pred["model_type"] = model_type
        metrics["horizon_days"] = horizon
        metrics["model_type"] = model_type
        metrics.update(_event_feature_quality_metrics(event_feature_quality, bool(event_feature_columns)))
        pred["trust_status"] = _trust_status(metrics, status)
        all_predictions.append(pred)
        metrics["trust_status"] = pred["trust_status"].iloc[0] if not pred.empty else "data_insufficient"
        metric_rows.append(metrics)
        effective_model_type = str(metrics.get("effective_model_type", model_type) or model_type)
        model_base_status = str(metrics.get("model_base_status", "") or "")
        fallback_reason = str(metrics.get("fallback_reasons", "") or "")
        register_model(
            registry_dir,
            {
                "model_id": f"walk_forward_{model_type}_h{horizon}",
                "model_type": model_type,
                "requested_model_type": model_type,
                "effective_model_type": effective_model_type,
                "model_base_status": model_base_status,
                "fallback_reason": fallback_reason,
                "prediction_methods": metrics.get("prediction_methods", ""),
                "fallback_rate": metrics.get("fallback_rate", 0.0),
                "model_family": "walk_forward_validation",
                "horizon_days": horizon,
                "embargo_days": max(horizon, embargo_days),
                "feature_set": selected_feature_columns,
                "feature_set_source": feature_source,
                "event_feature_set": event_feature_columns,
                "metrics": metrics,
                "artifact_path": str(output_dir / "walk_forward_predictions.csv"),
            },
        )
    predictions = pd.concat(all_predictions, ignore_index=True) if all_predictions else pd.DataFrame()
    metrics_frame = pd.DataFrame(metric_rows)
    summary = {
        "model_type": model_type,
        "horizons": horizons,
        "symbols": len(bars_by_symbol),
        "min_symbols": min_symbols,
        "embargo_days": embargo_days,
        "feature_count": len(selected_feature_columns),
        "feature_set_source": feature_source,
        "base_factor_count": len(FACTOR_COLUMNS),
        "event_feature_count": len(event_feature_columns),
        "event_features": event_feature_columns,
        "event_feature_quality_counts": event_feature_quality["quality_status"].value_counts().to_dict()
        if not event_feature_quality.empty and "quality_status" in event_feature_quality.columns
        else {},
        "event_feature_quality_passed": _event_feature_quality_metrics(event_feature_quality, bool(event_feature_columns))["event_feature_quality_passed"],
        "rows": int(len(predictions)),
        "trust_note": "trusted requires enough symbols and model metrics better than baseline",
    }
    predictions.to_csv(output_dir / "walk_forward_predictions.csv", index=False)
    metrics_frame.to_csv(output_dir / "walk_forward_metrics.csv", index=False)
    event_feature_quality.to_csv(output_dir / "event_feature_quality.csv", index=False)
    (output_dir / "walk_forward_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return WalkForwardResult(predictions=predictions, metrics=metrics_frame, summary=summary)


def _walk_one_horizon(
    factors: pd.DataFrame,
    labels: pd.DataFrame,
    scores: pd.DataFrame,
    horizon: int,
    model_type: str,
    train_years: int,
    test_months: int,
    embargo_days: int,
    feature_columns: list[str],
) -> tuple[pd.DataFrame, dict[str, object]]:
    label_col = f"future_return_{horizon}d"
    direction_col = f"direction_up_{horizon}d"
    available_features = [column for column in feature_columns if column in factors.columns]
    diagnostic_columns = [column for column in EVALUATION_DIAGNOSTIC_COLUMNS if column in factors.columns and column not in available_features]
    dataset = (
        factors[[*available_features, *diagnostic_columns]]
        .join(labels[[label_col, direction_col]], how="inner")
        .join(scores[["score"]], how="left")
    )
    dataset = dataset.replace([np.inf, -np.inf], np.nan).dropna(subset=[label_col, direction_col, "score"])
    if dataset.empty:
        return pd.DataFrame(), {"rows": 0, "model_status": "data_insufficient"}
    dates = pd.DatetimeIndex(dataset.index.get_level_values("date").unique()).sort_values()
    start_idx = max(1, min(len(dates) - 1, int(252 * train_years)))
    step = max(21, int(21 * test_months))
    rows = []
    embargo = max(int(horizon), int(embargo_days))
    for start in range(start_idx, len(dates), step):
        train_dates = dates[max(0, start - int(252 * train_years)) : start]
        test_dates = dates[start : min(len(dates), start + step)]
        if len(test_dates) == 0:
            continue
        if embargo > 0 and len(train_dates) > embargo:
            train_dates = train_dates[:-embargo]
        train = dataset[dataset.index.get_level_values("date").isin(train_dates)]
        test = dataset[dataset.index.get_level_values("date").isin(test_dates)]
        if len(train) < 200 or test.empty:
            continue
        pred = _fit_predict(
            train,
            test,
            model_type,
            label_col,
            direction_col,
            available_features,
            embargo_days=embargo,
            fold_id=len(rows) + 1,
        )
        rows.append(pred)
    predictions = pd.concat(rows) if rows else _baseline_predict(
        dataset,
        label_col,
        direction_col,
        requested_model_type=model_type,
        model_base_status="fallback",
        fallback_reason="no_walk_forward_folds",
    )
    metrics = _metrics(predictions, label_col, direction_col)
    metrics["model_status"] = "ok" if not predictions.empty else "data_insufficient"
    return predictions.reset_index(), metrics


def _fit_predict(
    train: pd.DataFrame,
    test: pd.DataFrame,
    model_type: str,
    label_col: str,
    direction_col: str,
    feature_columns: list[str],
    *,
    embargo_days: int,
    fold_id: int,
) -> pd.DataFrame:
    model_train, calibration = _split_model_and_calibration_train(train, embargo_days)
    if len(model_train) < 200 or calibration.empty:
        raw_test = _fit_predict_uncalibrated(train, test, model_type, label_col, direction_col, feature_columns)
        empty_calibration = raw_test.iloc[0:0]
        return _apply_fold_probability_calibration(
            raw_test,
            empty_calibration,
            label_col,
            direction_col,
            fold_id,
            model_train=train,
            calibration=calibration,
            test=test,
        )

    calibration_pred = _fit_predict_uncalibrated(model_train, calibration, model_type, label_col, direction_col, feature_columns)
    raw_test = _fit_predict_uncalibrated(model_train, test, model_type, label_col, direction_col, feature_columns)
    return _apply_fold_probability_calibration(
        raw_test,
        calibration_pred,
        label_col,
        direction_col,
        fold_id,
        model_train=model_train,
        calibration=calibration,
        test=test,
    )


def _fit_predict_uncalibrated(
    train: pd.DataFrame,
    test: pd.DataFrame,
    model_type: str,
    label_col: str,
    direction_col: str,
    feature_columns: list[str],
) -> pd.DataFrame:
    features = _select_features(train, feature_columns)
    normalized = model_type.lower().replace("-", "_")
    if normalized in {"factor_score", "factor-score", "baseline", "factor_score_baseline"}:
        return _baseline_predict(
            test,
            label_col,
            direction_col,
            train=train,
            requested_model_type=model_type,
            model_base_status="baseline",
        )
    failures: list[str] = []
    if normalized == "lightgbm_ranker" and len(features) >= 5:
        try:
            return _with_model_audit(
                _fit_lightgbm_ranker(train, test, features, label_col, direction_col),
                requested_model_type=model_type,
                effective_model_type="lightgbm_ranker",
                model_base_status="trained",
            )
        except Exception as exc:  # noqa: BLE001
            failures.append(_failure_reason("lightgbm_ranker", exc))
    if normalized in {
        "lightgbm",
        "ensemble",
        "event_aware_ensemble",
        "event-aware-ensemble",
        "event_aware",
        "lightgbm_classifier",
        "lightgbm_regressor",
        "lightgbm_ranker",
    } and len(features) >= 5:
        try:
            from lightgbm import LGBMClassifier, LGBMRegressor  # type: ignore

            clf = LGBMClassifier(n_estimators=80, learning_rate=0.05, num_leaves=15, random_state=42, verbose=-1)
            reg = LGBMRegressor(n_estimators=80, learning_rate=0.05, num_leaves=15, random_state=43, verbose=-1)
            if train[direction_col].nunique() >= 2:
                clf.fit(train[features], train[direction_col].astype(int))
                prob = clf.predict_proba(test[features])[:, 1]
            else:
                prob = np.full(len(test), train[direction_col].mean())
            reg.fit(train[features], train[label_col])
            ret = reg.predict(test[features])
            return _with_model_audit(
                _make_prediction_frame(test, label_col, direction_col, prob, ret, "lightgbm_walk_forward"),
                requested_model_type=model_type,
                effective_model_type="lightgbm",
                model_base_status="trained",
            )
        except Exception as exc:  # noqa: BLE001
            failures.append(_failure_reason("lightgbm", exc))
    if normalized in {"logistic", "ridge", "linear", "sklearn", "sklearn_linear", "ensemble", "event_aware_ensemble", "event-aware-ensemble"} and len(features) >= 5:
        try:
            return _with_model_audit(
                _fit_sklearn_linear(train, test, features, label_col, direction_col, normalized),
                requested_model_type=model_type,
                effective_model_type=normalized,
                model_base_status="trained",
            )
        except Exception as exc:  # noqa: BLE001
            failures.append(_failure_reason("sklearn_linear", exc))
    if normalized in {"xgboost", "xgb"} and len(features) >= 5:
        try:
            return _with_model_audit(
                _fit_xgboost(train, test, features, label_col, direction_col),
                requested_model_type=model_type,
                effective_model_type="xgboost",
                model_base_status="trained",
            )
        except Exception as exc:  # noqa: BLE001
            failures.append(_failure_reason("xgboost", exc))
    if normalized in {"catboost", "cat"} and len(features) >= 5:
        try:
            return _with_model_audit(
                _fit_catboost(train, test, features, label_col, direction_col),
                requested_model_type=model_type,
                effective_model_type="catboost",
                model_base_status="trained",
            )
        except Exception as exc:  # noqa: BLE001
            failures.append(_failure_reason("catboost", exc))
    return _baseline_predict(
        test,
        label_col,
        direction_col,
        train=train,
        requested_model_type=model_type,
        model_base_status="fallback",
        fallback_reason=_walk_forward_fallback_reason(normalized, features, failures),
    )


def _with_model_audit(
    frame: pd.DataFrame,
    *,
    requested_model_type: str,
    effective_model_type: str,
    model_base_status: str,
    fallback_reason: str = "",
) -> pd.DataFrame:
    out = frame.copy()
    out["requested_model_type"] = requested_model_type
    out["effective_model_type"] = effective_model_type
    out["model_base_status"] = model_base_status
    out["fallback_reason"] = fallback_reason
    return out


def _failure_reason(model_base: str, exc: Exception) -> str:
    message = str(exc).replace("\n", " ").strip()
    if len(message) > 160:
        message = message[:157] + "..."
    return f"{model_base}_failed:{exc.__class__.__name__}:{message}" if message else f"{model_base}_failed:{exc.__class__.__name__}"


def _walk_forward_fallback_reason(normalized_model_type: str, features: list[str], failures: list[str]) -> str:
    if len(features) < 5:
        return "insufficient_feature_coverage"
    if failures:
        return "|".join(failures)
    supported = {
        "factor_score",
        "factor_score_baseline",
        "baseline",
        "lightgbm",
        "lightgbm_classifier",
        "lightgbm_regressor",
        "lightgbm_ranker",
        "ensemble",
        "event_aware_ensemble",
        "event_aware",
        "logistic",
        "ridge",
        "linear",
        "sklearn",
        "sklearn_linear",
        "xgboost",
        "xgb",
        "catboost",
        "cat",
    }
    if normalized_model_type not in supported:
        return "unsupported_model_type"
    return "requested_model_failed_or_unsupported"


def _fit_lightgbm_ranker(train: pd.DataFrame, test: pd.DataFrame, features: list[str], label_col: str, direction_col: str) -> pd.DataFrame:
    from lightgbm import LGBMRanker  # type: ignore

    train_sorted = train.sort_index(level="date")
    test_sorted = test.sort_index(level="date")
    relevance = train_sorted.groupby(level="date")[label_col].rank(pct=True).fillna(0.5)
    relevance = (relevance * 4).round().clip(0, 4).astype(int)
    groups = train_sorted.groupby(level="date").size().astype(int).tolist()
    ranker = LGBMRanker(n_estimators=80, learning_rate=0.05, num_leaves=15, random_state=44, verbose=-1)
    ranker.fit(train_sorted[features], relevance, group=groups)
    rank_score = pd.Series(ranker.predict(test_sorted[features]), index=test_sorted.index)
    prob = rank_score.groupby(level="date").rank(pct=True).fillna(0.5).to_numpy()
    scale = float(train[label_col].std(ddof=0) or 0.0)
    ret = ((prob - 0.5) * 2 * scale)
    return _make_prediction_frame(test_sorted, label_col, direction_col, prob, ret, "lightgbm_ranker_walk_forward")


def _fit_sklearn_linear(
    train: pd.DataFrame,
    test: pd.DataFrame,
    features: list[str],
    label_col: str,
    direction_col: str,
    model_type: str,
) -> pd.DataFrame:
    from sklearn.impute import SimpleImputer  # type: ignore
    from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge  # type: ignore
    from sklearn.pipeline import make_pipeline  # type: ignore
    from sklearn.preprocessing import StandardScaler  # type: ignore

    X_train = train[features]
    X_test = test[features]
    reg_model = LinearRegression() if model_type == "linear" else Ridge(alpha=1.0)
    reg = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), reg_model)
    reg.fit(X_train, train[label_col])
    ret = reg.predict(X_test)
    if train[direction_col].nunique() >= 2:
        clf = make_pipeline(
            SimpleImputer(strategy="median"),
            StandardScaler(),
            LogisticRegression(max_iter=1000, class_weight="balanced"),
        )
        clf.fit(X_train, train[direction_col].astype(int))
        prob = clf.predict_proba(X_test)[:, 1]
    else:
        prob = _return_to_probability(ret)
    return _make_prediction_frame(test, label_col, direction_col, prob, ret, f"{model_type}_walk_forward")


def _fit_xgboost(train: pd.DataFrame, test: pd.DataFrame, features: list[str], label_col: str, direction_col: str) -> pd.DataFrame:
    from xgboost import XGBClassifier, XGBRegressor  # type: ignore

    clf = XGBClassifier(n_estimators=80, max_depth=3, learning_rate=0.05, subsample=0.9, random_state=45, eval_metric="logloss")
    reg = XGBRegressor(n_estimators=80, max_depth=3, learning_rate=0.05, subsample=0.9, random_state=46)
    X_train = train[features].fillna(train[features].median(numeric_only=True))
    X_test = test[features].fillna(train[features].median(numeric_only=True))
    if train[direction_col].nunique() >= 2:
        clf.fit(X_train, train[direction_col].astype(int))
        prob = clf.predict_proba(X_test)[:, 1]
    else:
        prob = np.full(len(test), train[direction_col].mean())
    reg.fit(X_train, train[label_col])
    ret = reg.predict(X_test)
    return _make_prediction_frame(test, label_col, direction_col, prob, ret, "xgboost_walk_forward")


def _fit_catboost(train: pd.DataFrame, test: pd.DataFrame, features: list[str], label_col: str, direction_col: str) -> pd.DataFrame:
    from catboost import CatBoostClassifier, CatBoostRegressor  # type: ignore

    X_train = train[features]
    X_test = test[features]
    if train[direction_col].nunique() >= 2:
        clf = CatBoostClassifier(
            iterations=80,
            depth=4,
            learning_rate=0.05,
            loss_function="Logloss",
            verbose=False,
            random_seed=47,
            allow_writing_files=False,
        )
        clf.fit(X_train, train[direction_col].astype(int))
        prob = clf.predict_proba(X_test)[:, 1]
    else:
        prob = np.full(len(test), train[direction_col].mean())
    reg = CatBoostRegressor(
        iterations=80,
        depth=4,
        learning_rate=0.05,
        loss_function="RMSE",
        verbose=False,
        random_seed=48,
        allow_writing_files=False,
    )
    reg.fit(X_train, train[label_col])
    ret = reg.predict(X_test)
    return _make_prediction_frame(test, label_col, direction_col, prob, ret, "catboost_walk_forward")


def _make_prediction_frame(
    test: pd.DataFrame,
    label_col: str,
    direction_col: str,
    prob: np.ndarray | pd.Series,
    ret: np.ndarray | pd.Series,
    method: str,
) -> pd.DataFrame:
    out = test[[label_col, direction_col, "score"]].copy()
    out["prob_up"] = pd.Series(prob, index=out.index).astype(float).clip(0.01, 0.99)
    out["predicted_return"] = pd.Series(ret, index=out.index).astype(float)
    out["prediction_method"] = method
    for column in EVALUATION_DIAGNOSTIC_COLUMNS:
        if column in test.columns:
            out[column] = test[column]
    return out


def _split_model_and_calibration_train(train: pd.DataFrame, embargo_days: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    dates = pd.DatetimeIndex(train.index.get_level_values("date").unique()).sort_values()
    if len(dates) < 60:
        return train, train.iloc[0:0]
    calibration_date_count = max(20, int(len(dates) * 0.20))
    calibration_start = max(1, len(dates) - calibration_date_count)
    model_end = max(1, calibration_start - max(0, int(embargo_days)))
    model_dates = dates[:model_end]
    calibration_dates = dates[calibration_start:]
    if len(model_dates) < 20 or len(calibration_dates) < 5:
        return train, train.iloc[0:0]
    model_train = train[train.index.get_level_values("date").isin(model_dates)]
    calibration = train[train.index.get_level_values("date").isin(calibration_dates)]
    return model_train, calibration


def _apply_fold_probability_calibration(
    raw_test: pd.DataFrame,
    calibration_pred: pd.DataFrame,
    label_col: str,
    direction_col: str,
    fold_id: int,
    *,
    model_train: pd.DataFrame,
    calibration: pd.DataFrame,
    test: pd.DataFrame,
) -> pd.DataFrame:
    out = raw_test.copy()
    raw_prob = out["prob_up"].astype(float).clip(0.0, 1.0)
    if calibration_pred.empty:
        result = calibrate_probability_series(
            pd.Series(dtype="float64"),
            pd.Series(dtype="float64"),
            raw_prob,
        )
    else:
        result = calibrate_probability_series(
            calibration_pred["prob_up"].astype(float),
            calibration_pred[direction_col].astype(float),
            raw_prob,
        )
    calibrated = result.calibrated_probabilities.reindex(out.index).fillna(raw_prob).astype(float).clip(0.0, 1.0)
    out["raw_prob_up"] = raw_prob
    out["calibrated_prob_up"] = calibrated
    out["prob_up"] = calibrated
    out["probability_calibration_method"] = result.method
    out["probability_calibration_status"] = result.status
    out["probability_calibration_rows"] = result.rows
    out["probability_calibration_train_rows"] = result.train_rows
    out["probability_calibration_eval_rows"] = result.eval_rows
    out["probability_raw_brier"] = result.raw_brier
    out["probability_calibrated_brier"] = result.calibrated_brier
    out["probability_raw_ece"] = result.raw_ece
    out["probability_calibrated_ece"] = result.calibrated_ece
    out["probability_calibration_improvement_brier"] = result.improvement_brier
    out["probability_calibration_improvement_ece"] = result.improvement_ece
    out["probability_calibration_candidate_methods"] = ";".join(result.candidates["method"].astype(str).tolist()) if not result.candidates.empty else ""
    out["fold_id"] = int(fold_id)
    out["model_train_end_date"] = _max_index_date(model_train)
    out["probability_calibration_start_date"] = _min_index_date(calibration)
    out["probability_calibration_end_date"] = _max_index_date(calibration)
    out["test_start_date"] = _min_index_date(test)
    out["test_end_date"] = _max_index_date(test)
    out["probability_calibration_pit_passed"] = _pit_date_before(out["probability_calibration_end_date"].iloc[0], out["test_start_date"].iloc[0])
    return out


def _min_index_date(frame: pd.DataFrame) -> str:
    if frame.empty:
        return ""
    return pd.Timestamp(frame.index.get_level_values("date").min()).date().isoformat()


def _max_index_date(frame: pd.DataFrame) -> str:
    if frame.empty:
        return ""
    return pd.Timestamp(frame.index.get_level_values("date").max()).date().isoformat()


def _pit_date_before(left: object, right: object) -> bool:
    if not str(left).strip() or not str(right).strip():
        return False
    return pd.Timestamp(left) < pd.Timestamp(right)


def _return_to_probability(ret: np.ndarray | pd.Series) -> np.ndarray:
    values = pd.Series(ret).astype(float).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    std = float(values.std(ddof=0) or 1.0)
    z = (values - float(values.mean())) / std
    return (1 / (1 + np.exp(-z))).clip(0.05, 0.95).to_numpy()


def _baseline_predict(
    test: pd.DataFrame,
    label_col: str,
    direction_col: str,
    train: pd.DataFrame | None = None,
    *,
    requested_model_type: str = "factor_score",
    model_base_status: str = "baseline",
    fallback_reason: str = "",
) -> pd.DataFrame:
    reference = train if train is not None and not train.empty else test
    ref = reference.copy()
    ref["score_percentile"] = ref.groupby(level="date")["score"].rank(pct=True)
    base_prob = float(ref[direction_col].mean()) if not ref.empty else 0.5
    out = test[[label_col, direction_col, "score"]].copy()
    out["score_percentile"] = out.groupby(level="date")["score"].rank(pct=True)
    out["prob_up"] = (base_prob + (out["score_percentile"] - 0.5) * 0.20).clip(0.05, 0.95)
    out["predicted_return"] = (out["score_percentile"] - 0.5) * float(ref[label_col].std(ddof=0) if len(ref) else 0.0)
    out["prediction_method"] = "factor_score_baseline"
    for column in EVALUATION_DIAGNOSTIC_COLUMNS:
        if column in test.columns:
            out[column] = test[column]
    return _with_model_audit(
        out,
        requested_model_type=requested_model_type,
        effective_model_type="factor_score",
        model_base_status=model_base_status,
        fallback_reason=fallback_reason,
    )


def _metrics(predictions: pd.DataFrame, label_col: str, direction_col: str) -> dict[str, object]:
    if predictions.empty:
        return {"rows": 0}
    prob = predictions["prob_up"].astype(float)
    raw_prob = predictions["raw_prob_up"].astype(float) if "raw_prob_up" in predictions.columns else prob
    direction = predictions[direction_col].astype(int)
    ret = predictions[label_col].astype(float)
    top = predictions[prob >= prob.quantile(0.8)]
    bottom = predictions[prob <= prob.quantile(0.2)]
    baseline_acc = float((direction == int(direction.mean() >= 0.5)).mean())
    accuracy = float(((prob >= 0.5).astype(int) == direction).mean())
    raw_accuracy = float(((raw_prob >= 0.5).astype(int) == direction).mean())
    auc = 0.0
    raw_auc = 0.0
    if direction.nunique() >= 2:
        try:
            from sklearn.metrics import roc_auc_score  # type: ignore

            auc = float(roc_auc_score(direction, prob))
            raw_auc = float(roc_auc_score(direction, raw_prob))
        except Exception:  # noqa: BLE001
            auc = 0.0
            raw_auc = 0.0
    rank_ic = _safe_corr(prob, ret, "spearman")
    top_bucket_return = float(top[label_col].mean()) if not top.empty else 0.0
    bottom_bucket_return = float(bottom[label_col].mean()) if not bottom.empty else 0.0
    top_bottom_spread = top_bucket_return - bottom_bucket_return
    brier = float(((prob - direction) ** 2).mean())
    raw_brier = float(((raw_prob - direction) ** 2).mean())
    calibration = _calibration_metrics(predictions, prob, raw_prob, direction)
    model_audit = _model_audit_metrics(predictions)
    beats_baseline = bool((accuracy > baseline_acc and auc >= 0.50) or rank_ic > 0.0 or top_bottom_spread > 0.0)
    return {
        "rows": int(len(predictions)),
        "direction_accuracy": accuracy,
        "raw_direction_accuracy": raw_accuracy,
        "baseline_accuracy": baseline_acc,
        "auc": auc,
        "raw_auc": raw_auc,
        "brier": brier,
        "raw_brier": raw_brier,
        "calibrated_ece": calibration["calibrated_ece"],
        "raw_ece": calibration["raw_ece"],
        "probability_calibration_methods": calibration["methods"],
        "probability_calibration_statuses": calibration["statuses"],
        "probability_calibration_ready_ratio": calibration["ready_ratio"],
        "probability_calibration_pit_ratio": calibration["pit_ratio"],
        "probability_calibration_pit_passed": calibration["pit_passed"],
        "probability_calibration_mean_improvement_brier": calibration["mean_improvement_brier"],
        "probability_calibration_mean_improvement_ece": calibration["mean_improvement_ece"],
        "rank_ic": rank_ic,
        "top_bucket_return": top_bucket_return,
        "bottom_bucket_return": bottom_bucket_return,
        "top_bottom_spread": float(top_bottom_spread),
        "beats_baseline": beats_baseline,
        **model_audit,
    }


def _trust_status(metrics: dict[str, object], data_status: str) -> str:
    if data_status == "data_insufficient":
        return "data_insufficient"
    if metrics.get("model_status") != "ok":
        return "model_failed"
    gate = _trust_gate(metrics)
    metrics["trust_gate_passed"] = bool(gate["passed"])
    metrics["trust_gate_reasons"] = ";".join(gate["failed_reasons"]) if gate["failed_reasons"] else "passed"
    if bool(gate["passed"]):
        return "trusted"
    return "weak"


def _trust_gate(metrics: dict[str, object]) -> dict[str, object]:
    checks = {
        "min_oos_rows": int(metrics.get("rows", 0) or 0) >= 5000,
        "beats_baseline": bool(metrics.get("beats_baseline", False)),
        "auc_above_052": float(metrics.get("auc", 0.0) or 0.0) >= 0.52,
        "brier_below_025": float(metrics.get("brier", 1.0) or 1.0) <= 0.25,
        "calibration_ready": float(metrics.get("probability_calibration_ready_ratio", 0.0) or 0.0) >= 0.80,
        "calibration_pit_passed": bool(metrics.get("probability_calibration_pit_passed", False)),
        "calibrated_ece_below_010": float(metrics.get("calibrated_ece", 1.0) or 1.0) <= 0.10,
        "model_base_not_fallback": str(metrics.get("model_base_status", "") or "").lower() not in {"fallback", "mixed_fallback"},
        "event_feature_quality_passed": bool(metrics.get("event_feature_quality_passed", True)),
        "rank_ic_positive": float(metrics.get("rank_ic", 0.0) or 0.0) > 0.0,
        "top_bottom_spread_positive": float(metrics.get("top_bottom_spread", 0.0) or 0.0) > 0.0,
    }
    failed = [name for name, passed in checks.items() if not passed]
    return {"passed": not failed, "checks": checks, "failed_reasons": failed}


def _event_feature_quality_metrics(quality: pd.DataFrame, event_features_enabled: bool) -> dict[str, object]:
    if not event_features_enabled:
        return {
            "event_features_enabled": False,
            "event_feature_quality_passed": True,
            "event_feature_approved_count": 0,
            "event_feature_watchlist_count": 0,
            "event_feature_quarantine_count": 0,
            "event_feature_quality_failed_reasons": "",
        }
    if quality.empty:
        return {
            "event_features_enabled": True,
            "event_feature_quality_passed": False,
            "event_feature_approved_count": 0,
            "event_feature_watchlist_count": 0,
            "event_feature_quarantine_count": 0,
            "event_feature_quality_failed_reasons": "event_feature_quality_missing",
        }
    counts = quality["quality_status"].value_counts().to_dict() if "quality_status" in quality.columns else {}
    approved = int(counts.get("approved", 0))
    quarantine = int(counts.get("quarantine", 0))
    total = int(len(quality))
    failed_reasons = (
        ";".join(sorted(set(";".join(quality["failed_reasons"].dropna().astype(str)).split(";")) - {"", "passed"}))
        if "failed_reasons" in quality.columns
        else ""
    )
    passed = total > 0 and quarantine == 0 and approved / max(1, total) >= 0.50
    return {
        "event_features_enabled": True,
        "event_feature_quality_passed": bool(passed),
        "event_feature_approved_count": approved,
        "event_feature_watchlist_count": int(counts.get("watchlist", 0)),
        "event_feature_quarantine_count": quarantine,
        "event_feature_quality_failed_reasons": failed_reasons,
    }


def _model_audit_metrics(predictions: pd.DataFrame) -> dict[str, object]:
    def joined(column: str) -> str:
        if column not in predictions.columns:
            return ""
        values = sorted(value for value in predictions[column].dropna().astype(str).unique().tolist() if value)
        return ";".join(values)

    statuses = (
        predictions["model_base_status"].dropna().astype(str)
        if "model_base_status" in predictions.columns
        else pd.Series(dtype="object")
    )
    fallback_rate = float(statuses.str.contains("fallback", case=False, regex=False).mean()) if not statuses.empty else 0.0
    status_values = sorted(statuses.unique().tolist()) if not statuses.empty else []
    if not status_values:
        model_base_status = ""
    elif len(status_values) == 1:
        model_base_status = status_values[0]
    elif any("fallback" in value.lower() for value in status_values):
        model_base_status = "mixed_fallback"
    else:
        model_base_status = "mixed"

    effective_types = joined("effective_model_type")
    effective_model_type = effective_types if ";" not in effective_types else f"mixed:{effective_types}"
    return {
        "requested_model_type": joined("requested_model_type"),
        "effective_model_type": effective_model_type,
        "effective_model_types": effective_types,
        "model_base_status": model_base_status,
        "model_base_statuses": joined("model_base_status"),
        "fallback_reason": joined("fallback_reason"),
        "fallback_reasons": joined("fallback_reason"),
        "fallback_rate": fallback_rate,
        "prediction_methods": joined("prediction_method"),
    }


def _select_features(frame: pd.DataFrame, feature_columns: list[str]) -> list[str]:
    columns = [column for column in feature_columns if column in frame.columns]
    coverage = frame[columns].notna().mean()
    return coverage[coverage >= 0.55].index.tolist()


def _calibration_metrics(
    predictions: pd.DataFrame,
    prob: pd.Series,
    raw_prob: pd.Series,
    direction: pd.Series,
) -> dict[str, object]:
    statuses = (
        predictions["probability_calibration_status"].dropna().astype(str)
        if "probability_calibration_status" in predictions.columns
        else pd.Series(dtype="object")
    )
    methods = (
        predictions["probability_calibration_method"].dropna().astype(str)
        if "probability_calibration_method" in predictions.columns
        else pd.Series(dtype="object")
    )
    ready_statuses = {"calibrated", "calibration_watch"}
    ready_ratio = float(statuses.isin(ready_statuses).mean()) if not statuses.empty else 0.0
    if "probability_calibration_pit_passed" in predictions.columns:
        pit_values = predictions["probability_calibration_pit_passed"].astype(bool)
        pit_ratio = float(pit_values.mean()) if len(pit_values) else 0.0
        pit_passed = bool(pit_values.all()) if len(pit_values) else False
    else:
        pit_ratio = 0.0
        pit_passed = False
    return {
        "raw_ece": _ece(raw_prob, direction),
        "calibrated_ece": _ece(prob, direction),
        "methods": ";".join(sorted(methods.unique().tolist())) if not methods.empty else "",
        "statuses": ";".join(sorted(statuses.unique().tolist())) if not statuses.empty else "calibration_missing",
        "ready_ratio": ready_ratio,
        "pit_ratio": pit_ratio,
        "pit_passed": pit_passed,
        "mean_improvement_brier": _mean_column(predictions, "probability_calibration_improvement_brier"),
        "mean_improvement_ece": _mean_column(predictions, "probability_calibration_improvement_ece"),
    }


def _ece(prob: pd.Series, direction: pd.Series, bins: int = 5) -> float:
    clean = pd.concat([prob.astype(float).clip(0.0, 1.0), direction.astype(float)], axis=1).dropna()
    if clean.empty:
        return 1.0
    p = clean.iloc[:, 0]
    y = clean.iloc[:, 1]
    edges = np.linspace(0.0, 1.0, bins + 1)
    ece = 0.0
    for left, right in zip(edges[:-1], edges[1:]):
        mask = (p >= left) & (p <= right) if right >= 1.0 else (p >= left) & (p < right)
        if mask.any():
            ece += float(mask.mean()) * abs(float(p[mask].mean()) - float(y[mask].mean()))
    return float(ece)


def _mean_column(frame: pd.DataFrame, column: str) -> float:
    if column not in frame.columns:
        return 0.0
    values = pd.to_numeric(frame[column], errors="coerce").dropna()
    return float(values.mean()) if not values.empty else 0.0


def _safe_corr(left: pd.Series, right: pd.Series, method: str) -> float:
    if left.nunique() < 2 or right.nunique() < 2:
        return 0.0
    value = left.corr(right, method=method)
    if value is None or np.isnan(value):
        return 0.0
    return float(value)
