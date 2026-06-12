from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PredictionResult:
    predictions: pd.DataFrame
    summary: dict[str, object]


def build_latest_predictions(
    factors: pd.DataFrame,
    labels: pd.DataFrame,
    scores: pd.DataFrame,
    factor_columns: list[str],
    horizon: int = 5,
) -> PredictionResult:
    """Create a latest-date prediction table for the current stock pool.

    If LightGBM is installed, the function trains a small cross-sectional model
    on historical factor/label rows. Otherwise it falls back to a calibrated
    factor-score proxy, which is transparent and dependency-light.
    """
    label_column = f"excess_return_{horizon}d"
    if label_column not in labels.columns:
        raise ValueError(f"Missing label column: {label_column}")

    latest_date = _latest_scored_date(scores)
    latest_scores = scores.xs(latest_date, level="date").copy()
    latest_factors = factors.xs(latest_date, level="date").copy()
    latest = latest_scores.join(latest_factors[factor_columns], how="left", rsuffix="_factor")

    model_output = _try_lightgbm_prediction(factors, labels, latest_factors, factor_columns, label_column)
    if model_output is None:
        predictions, method_summary = _score_proxy_prediction(scores, labels, latest, latest_date, label_column)
    else:
        predictions, method_summary = model_output
        predictions = latest[["score", "close", "amount"]].join(predictions, how="left")

    predictions = _add_ranks_and_signals(predictions)
    predictions["latest_date"] = latest_date
    predictions["horizon_days"] = horizon
    predictions["top_factor_contributors"] = _factor_contributors(latest, factor_columns)
    predictions = predictions.reset_index().rename(columns={"index": "symbol"})
    predictions = predictions.sort_values("prediction_rank").reset_index(drop=True)

    summary = {
        "latest_date": str(pd.Timestamp(latest_date).date()),
        "horizon_days": horizon,
        "method": method_summary["method"],
        "model_quality": method_summary.get("model_quality", {}),
        "top_symbols": predictions.head(5)[["symbol", "prediction_rank", "signal"]].to_dict(orient="records"),
        "note": "Predictions are research signals, not investment advice.",
    }
    return PredictionResult(predictions=predictions, summary=summary)


def _latest_scored_date(scores: pd.DataFrame) -> pd.Timestamp:
    valid = scores.dropna(subset=["score"])
    if valid.empty:
        raise ValueError("No valid score rows for prediction")
    return pd.Timestamp(valid.index.get_level_values("date").max())


def _try_lightgbm_prediction(
    factors: pd.DataFrame,
    labels: pd.DataFrame,
    latest_factors: pd.DataFrame,
    factor_columns: list[str],
    label_column: str,
) -> tuple[pd.DataFrame, dict[str, object]] | None:
    try:
        from lightgbm import LGBMRegressor  # type: ignore
    except ImportError:
        return None

    dataset = factors[factor_columns].join(labels[[label_column]], how="inner").dropna()
    if len(dataset) < 200 or dataset.index.get_level_values("date").nunique() < 30:
        return None

    unique_dates = pd.DatetimeIndex(dataset.index.get_level_values("date").unique()).sort_values()
    split = max(1, int(len(unique_dates) * 0.8))
    train_dates = unique_dates[:split]
    valid_dates = unique_dates[split:]
    train = dataset[dataset.index.get_level_values("date").isin(train_dates)]
    valid = dataset[dataset.index.get_level_values("date").isin(valid_dates)]

    model = LGBMRegressor(
        n_estimators=160,
        learning_rate=0.04,
        num_leaves=15,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=42,
        verbose=-1,
    )
    model.fit(train[factor_columns], train[label_column])
    quality: dict[str, object] = {"train_rows": int(len(train)), "valid_rows": int(len(valid))}
    if not valid.empty:
        valid_pred = pd.Series(model.predict(valid[factor_columns]), index=valid.index)
        quality["valid_rank_ic"] = _safe_corr(valid_pred, valid[label_column], method="spearman")
        quality["valid_mae"] = float((valid_pred - valid[label_column]).abs().mean())

    latest_x = latest_factors[factor_columns].dropna()
    prediction = pd.Series(model.predict(latest_x), index=latest_x.index, name="predicted_excess_return")
    frame = pd.DataFrame({"predicted_excess_return": prediction})
    frame["prediction_method"] = "lightgbm"
    return frame, {"method": "lightgbm", "model_quality": quality}


def _score_proxy_prediction(
    scores: pd.DataFrame,
    labels: pd.DataFrame,
    latest: pd.DataFrame,
    latest_date: pd.Timestamp,
    label_column: str,
) -> tuple[pd.DataFrame, dict[str, object]]:
    history = scores[["score"]].join(labels[[label_column]], how="inner").dropna()
    history = history[history.index.get_level_values("date") < latest_date]
    if history.empty:
        latest_rank = latest["score"].rank(pct=True)
        predicted = latest_rank * 0.0
        quality = {"history_rows": 0, "calibration": "flat"}
    else:
        history = history.copy()
        history["score_percentile"] = history.groupby(level="date")["score"].rank(pct=True)
        x = history["score_percentile"].astype(float)
        y = history[label_column].astype(float)
        var = float(x.var(ddof=0))
        beta = float(x.cov(y, ddof=0) / var) if var > 0 else 0.0
        alpha = float(y.mean() - beta * x.mean())
        latest_rank = latest["score"].rank(pct=True)
        predicted = alpha + beta * latest_rank
        quality = {
            "history_rows": int(len(history)),
            "calibration": "linear_score_percentile",
            "score_label_rank_ic": _safe_corr(x, y, method="spearman"),
        }

    frame = latest[["score", "close", "amount"]].copy()
    frame["score_percentile"] = latest_rank
    frame["predicted_excess_return"] = predicted
    frame["prediction_method"] = "score_proxy"
    return frame, {"method": "score_proxy", "model_quality": quality}


def _add_ranks_and_signals(predictions: pd.DataFrame) -> pd.DataFrame:
    out = predictions.copy()
    out["prediction_rank"] = out["predicted_excess_return"].rank(ascending=False, method="first").astype(int)
    count = max(1, len(out))
    out["prediction_percentile"] = 1 - (out["prediction_rank"] - 1) / count
    out["signal"] = out["prediction_percentile"].map(_signal_from_percentile)
    out["confidence"] = (out["prediction_percentile"] - 0.5).abs().mul(2).clip(0, 1)
    return out


def _signal_from_percentile(value: float) -> str:
    if value >= 0.80:
        return "\u5019\u9009"
    if value >= 0.50:
        return "\u89c2\u5bdf"
    return "\u56de\u907f"


def _factor_contributors(latest: pd.DataFrame, factor_columns: list[str]) -> pd.Series:
    contributors = {}
    for symbol, row in latest.iterrows():
        values = []
        for factor in factor_columns:
            value = row.get(factor)
            if value is None or (isinstance(value, float) and math.isnan(value)):
                continue
            values.append((factor, float(value)))
        ranked = sorted(values, key=lambda item: abs(item[1]), reverse=True)[:3]
        contributors[symbol] = ";".join(f"{name}={value:.4g}" for name, value in ranked)
    return pd.Series(contributors)


def _safe_corr(left: pd.Series, right: pd.Series, method: str) -> float:
    if left.nunique() < 2 or right.nunique() < 2:
        return 0.0
    value = left.corr(right, method=method)
    if value is None or np.isnan(value):
        return 0.0
    return float(value)
