from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

import numpy as np
import pandas as pd

from aquant_mvp.config import DEFAULT_FACTOR_WEIGHTS
from aquant_mvp.features import merge_event_factors_into_panel
from aquant_mvp.factors import FACTOR_COLUMNS, compute_factor_panel
from aquant_mvp.labels import compute_stock_prediction_labels
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
) -> WalkForwardResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    factors = compute_factor_panel(bars_by_symbol)
    factors, event_feature_columns = merge_event_factors_into_panel(factors, event_factors)
    selected_feature_columns = feature_columns or [*FACTOR_COLUMNS, *event_feature_columns]
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
        pred["trust_status"] = _trust_status(metrics, status)
        all_predictions.append(pred)
        metrics["horizon_days"] = horizon
        metrics["model_type"] = model_type
        metrics["trust_status"] = pred["trust_status"].iloc[0] if not pred.empty else "data_insufficient"
        metric_rows.append(metrics)
        register_model(
            registry_dir,
            {
                "model_id": f"walk_forward_{model_type}_h{horizon}",
                "model_type": model_type,
                "model_family": "walk_forward_validation",
                "horizon_days": horizon,
                "embargo_days": max(horizon, embargo_days),
                "feature_set": selected_feature_columns,
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
        "base_factor_count": len(FACTOR_COLUMNS),
        "event_feature_count": len(event_feature_columns),
        "event_features": event_feature_columns,
        "rows": int(len(predictions)),
        "trust_note": "trusted requires enough symbols and model metrics better than baseline",
    }
    predictions.to_csv(output_dir / "walk_forward_predictions.csv", index=False)
    metrics_frame.to_csv(output_dir / "walk_forward_metrics.csv", index=False)
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
        pred = _fit_predict(train, test, model_type, label_col, direction_col, available_features)
        rows.append(pred)
    predictions = pd.concat(rows) if rows else _baseline_predict(dataset, label_col, direction_col)
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
) -> pd.DataFrame:
    features = _select_features(train, feature_columns)
    normalized = model_type.lower()
    if normalized in {"factor_score", "factor-score", "baseline", "factor_score_baseline"}:
        return _baseline_predict(test, label_col, direction_col, train=train)
    if normalized == "lightgbm_ranker" and len(features) >= 5:
        try:
            return _fit_lightgbm_ranker(train, test, features, label_col, direction_col)
        except Exception:  # noqa: BLE001
            pass
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
            return _make_prediction_frame(test, label_col, direction_col, prob, ret, "lightgbm_walk_forward")
        except Exception:  # noqa: BLE001
            pass
    if normalized in {"logistic", "ridge", "linear", "sklearn", "sklearn_linear", "ensemble", "event_aware_ensemble", "event-aware-ensemble"} and len(features) >= 5:
        try:
            return _fit_sklearn_linear(train, test, features, label_col, direction_col, normalized)
        except Exception:  # noqa: BLE001
            pass
    if normalized in {"xgboost", "xgb"} and len(features) >= 5:
        try:
            return _fit_xgboost(train, test, features, label_col, direction_col)
        except Exception:  # noqa: BLE001
            pass
    if normalized in {"catboost", "cat"} and len(features) >= 5:
        try:
            return _fit_catboost(train, test, features, label_col, direction_col)
        except Exception:  # noqa: BLE001
            pass
    return _baseline_predict(test, label_col, direction_col, train=train)


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
        clf = CatBoostClassifier(iterations=80, depth=4, learning_rate=0.05, loss_function="Logloss", verbose=False, random_seed=47)
        clf.fit(X_train, train[direction_col].astype(int))
        prob = clf.predict_proba(X_test)[:, 1]
    else:
        prob = np.full(len(test), train[direction_col].mean())
    reg = CatBoostRegressor(iterations=80, depth=4, learning_rate=0.05, loss_function="RMSE", verbose=False, random_seed=48)
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


def _return_to_probability(ret: np.ndarray | pd.Series) -> np.ndarray:
    values = pd.Series(ret).astype(float).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    std = float(values.std(ddof=0) or 1.0)
    z = (values - float(values.mean())) / std
    return (1 / (1 + np.exp(-z))).clip(0.05, 0.95).to_numpy()


def _baseline_predict(test: pd.DataFrame, label_col: str, direction_col: str, train: pd.DataFrame | None = None) -> pd.DataFrame:
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
    return out


def _metrics(predictions: pd.DataFrame, label_col: str, direction_col: str) -> dict[str, object]:
    if predictions.empty:
        return {"rows": 0}
    prob = predictions["prob_up"].astype(float)
    direction = predictions[direction_col].astype(int)
    ret = predictions[label_col].astype(float)
    top = predictions[prob >= prob.quantile(0.8)]
    bottom = predictions[prob <= prob.quantile(0.2)]
    baseline_acc = float((direction == int(direction.mean() >= 0.5)).mean())
    accuracy = float(((prob >= 0.5).astype(int) == direction).mean())
    auc = 0.0
    if direction.nunique() >= 2:
        try:
            from sklearn.metrics import roc_auc_score  # type: ignore

            auc = float(roc_auc_score(direction, prob))
        except Exception:  # noqa: BLE001
            auc = 0.0
    rank_ic = _safe_corr(prob, ret, "spearman")
    top_bucket_return = float(top[label_col].mean()) if not top.empty else 0.0
    bottom_bucket_return = float(bottom[label_col].mean()) if not bottom.empty else 0.0
    top_bottom_spread = top_bucket_return - bottom_bucket_return
    brier = float(((prob - direction) ** 2).mean())
    beats_baseline = bool((accuracy > baseline_acc and auc >= 0.50) or rank_ic > 0.0 or top_bottom_spread > 0.0)
    return {
        "rows": int(len(predictions)),
        "direction_accuracy": accuracy,
        "baseline_accuracy": baseline_acc,
        "auc": auc,
        "brier": brier,
        "rank_ic": rank_ic,
        "top_bucket_return": top_bucket_return,
        "bottom_bucket_return": bottom_bucket_return,
        "top_bottom_spread": float(top_bottom_spread),
        "beats_baseline": beats_baseline,
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
        "rank_ic_positive": float(metrics.get("rank_ic", 0.0) or 0.0) > 0.0,
        "top_bottom_spread_positive": float(metrics.get("top_bottom_spread", 0.0) or 0.0) > 0.0,
    }
    failed = [name for name, passed in checks.items() if not passed]
    return {"passed": not failed, "checks": checks, "failed_reasons": failed}


def _select_features(frame: pd.DataFrame, feature_columns: list[str]) -> list[str]:
    columns = [column for column in feature_columns if column in frame.columns]
    coverage = frame[columns].notna().mean()
    return coverage[coverage >= 0.55].index.tolist()


def _safe_corr(left: pd.Series, right: pd.Series, method: str) -> float:
    if left.nunique() < 2 or right.nunique() < 2:
        return 0.0
    value = left.corr(right, method=method)
    if value is None or np.isnan(value):
        return 0.0
    return float(value)
