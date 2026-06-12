from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

import numpy as np
import pandas as pd

from aquant_mvp.config import DEFAULT_FACTOR_WEIGHTS
from aquant_mvp.factors import FACTOR_COLUMNS, compute_factor_panel
from aquant_mvp.labels import compute_stock_prediction_labels
from aquant_mvp.modeling.registry import register_model
from aquant_mvp.strategy import score_factors


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
) -> WalkForwardResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    factors = compute_factor_panel(bars_by_symbol)
    labels = compute_stock_prediction_labels(bars_by_symbol, horizons)
    scores = score_factors(factors, DEFAULT_FACTOR_WEIGHTS)
    all_predictions = []
    metric_rows = []
    status = "trusted_candidate" if len(bars_by_symbol) >= min_symbols else "data_insufficient"
    for horizon in horizons:
        pred, metrics = _walk_one_horizon(factors, labels, scores, horizon, model_type, train_years, test_months)
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
                "feature_set": FACTOR_COLUMNS,
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
) -> tuple[pd.DataFrame, dict[str, object]]:
    label_col = f"future_return_{horizon}d"
    direction_col = f"direction_up_{horizon}d"
    dataset = factors[FACTOR_COLUMNS].join(labels[[label_col, direction_col]], how="inner").join(scores[["score"]], how="left")
    dataset = dataset.replace([np.inf, -np.inf], np.nan).dropna(subset=[label_col, direction_col, "score"])
    if dataset.empty:
        return pd.DataFrame(), {"rows": 0, "model_status": "data_insufficient"}
    dates = pd.DatetimeIndex(dataset.index.get_level_values("date").unique()).sort_values()
    start_idx = max(1, min(len(dates) - 1, int(252 * train_years)))
    step = max(21, int(21 * test_months))
    rows = []
    for start in range(start_idx, len(dates), step):
        train_dates = dates[max(0, start - int(252 * train_years)) : start]
        test_dates = dates[start : min(len(dates), start + step)]
        if len(test_dates) == 0:
            continue
        train = dataset[dataset.index.get_level_values("date").isin(train_dates)]
        test = dataset[dataset.index.get_level_values("date").isin(test_dates)]
        if len(train) < 200 or test.empty:
            continue
        pred = _fit_predict(train, test, model_type, label_col, direction_col)
        rows.append(pred)
    predictions = pd.concat(rows) if rows else _baseline_predict(dataset, label_col, direction_col)
    metrics = _metrics(predictions, label_col, direction_col)
    metrics["model_status"] = "ok" if not predictions.empty else "data_insufficient"
    return predictions.reset_index(), metrics


def _fit_predict(train: pd.DataFrame, test: pd.DataFrame, model_type: str, label_col: str, direction_col: str) -> pd.DataFrame:
    features = _select_features(train)
    if model_type in {"lightgbm", "ensemble", "lightgbm_classifier", "lightgbm_regressor", "lightgbm_ranker"} and len(features) >= 5:
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
            out = test[[label_col, direction_col, "score"]].copy()
            out["prob_up"] = prob
            out["predicted_return"] = ret
            out["prediction_method"] = "lightgbm_walk_forward"
            return out
        except Exception:  # noqa: BLE001
            pass
    return _baseline_predict(test, label_col, direction_col, train=train)


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
    return {
        "rows": int(len(predictions)),
        "direction_accuracy": accuracy,
        "baseline_accuracy": baseline_acc,
        "brier": float(((prob - direction) ** 2).mean()),
        "rank_ic": _safe_corr(prob, ret, "spearman"),
        "top_bucket_return": float(top[label_col].mean()) if not top.empty else 0.0,
        "bottom_bucket_return": float(bottom[label_col].mean()) if not bottom.empty else 0.0,
        "beats_baseline": bool(accuracy > baseline_acc or _safe_corr(prob, ret, "spearman") > 0),
    }


def _trust_status(metrics: dict[str, object], data_status: str) -> str:
    if data_status == "data_insufficient":
        return "data_insufficient"
    if metrics.get("model_status") != "ok":
        return "model_failed"
    if bool(metrics.get("beats_baseline", False)):
        return "trusted"
    return "weak"


def _select_features(frame: pd.DataFrame) -> list[str]:
    coverage = frame[FACTOR_COLUMNS].notna().mean()
    return coverage[coverage >= 0.55].index.tolist()


def _safe_corr(left: pd.Series, right: pd.Series, method: str) -> float:
    if left.nunique() < 2 or right.nunique() < 2:
        return 0.0
    value = left.corr(right, method=method)
    if value is None or np.isnan(value):
        return 0.0
    return float(value)
