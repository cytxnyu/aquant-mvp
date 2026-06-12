from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math

import numpy as np
import pandas as pd

from aquant_mvp.config import DEFAULT_FACTOR_WEIGHTS
from aquant_mvp.factors import FACTOR_COLUMNS, compute_factor_panel
from aquant_mvp.labels import compute_stock_prediction_labels
from aquant_mvp.strategy import score_factors


@dataclass(frozen=True)
class StockForecastResult:
    forecast: pd.DataFrame
    summary: dict[str, object]


def build_stock_forecast(
    bars_by_symbol: dict[str, pd.DataFrame],
    symbol: str,
    horizons: list[int],
    source: str,
    model_type: str = "ensemble",
    embargo_days: int = 5,
    allow_sample: bool = False,
) -> StockForecastResult:
    symbol = symbol.zfill(6)
    if source == "sample" and not allow_sample:
        raise ValueError("predict-stock forbids sample data by default. Use --source research or --allow-sample for demos.")
    if symbol not in bars_by_symbol:
        raise ValueError(f"Symbol {symbol} is not loaded in the current universe.")

    factors = compute_factor_panel(bars_by_symbol)
    labels = compute_stock_prediction_labels(bars_by_symbol, horizons)
    scores = score_factors(factors, DEFAULT_FACTOR_WEIGHTS)
    latest_date = pd.Timestamp(scores.dropna(subset=["score"]).index.get_level_values("date").max())
    data_version = _data_version(bars_by_symbol, source)

    rows: list[dict[str, object]] = []
    diagnostics: dict[str, object] = {}
    for horizon in horizons:
        row, quality = _forecast_one_horizon(
            factors=factors,
            labels=labels,
            scores=scores,
            symbol=symbol,
            horizon=horizon,
            latest_date=latest_date,
            model_type=model_type,
            embargo_days=embargo_days,
        )
        latest_bars = bars_by_symbol[symbol].sort_values("date")
        row["trend_label"] = _trend_label(latest_bars)
        row["risk_flags"] = ";".join(_risk_flags(latest_bars, source))
        row["top_factor_contributors"] = _factor_contributors(factors, symbol, latest_date)
        row["latest_date"] = latest_date.date().isoformat()
        row["symbol"] = symbol
        row["horizon_days"] = horizon
        row["model_type"] = model_type
        row["model_id"] = f"stock_forecast_{model_type}_h{horizon}"
        row["data_version"] = data_version
        row["universe_symbol_count"] = len(bars_by_symbol)
        row["minimum_trusted_symbols"] = 200
        row["sample_oos_accuracy"] = quality.get("valid_accuracy", 0.0)
        row["sample_oos_auc"] = quality.get("valid_auc", 0.0)
        row["sample_oos_brier"] = quality.get("valid_brier", 0.0)
        row["sample_rank_ic"] = quality.get("valid_return_ic", quality.get("valid_rank_ic", 0.0))
        row["trust_status"] = _forecast_trust_status(row, quality, len(bars_by_symbol), source)
        row["note"] = "Research signal only; not investment advice."
        rows.append(row)
        diagnostics[f"horizon_{horizon}d"] = quality

    forecast = pd.DataFrame(rows)
    columns = [
        "latest_date",
        "symbol",
        "horizon_days",
        "prob_up",
        "expected_return",
        "expected_excess_return",
        "direction",
        "trend_label",
        "confidence",
        "return_p10",
        "return_p50",
        "return_p90",
        "risk_flags",
        "top_factor_contributors",
        "prediction_method",
        "sample_oos_accuracy",
        "sample_oos_auc",
        "sample_oos_brier",
        "sample_rank_ic",
        "universe_symbol_count",
        "minimum_trusted_symbols",
        "trust_status",
        "model_type",
        "model_id",
        "data_version",
        "note",
    ]
    forecast = forecast[columns]
    summary = {
        "symbol": symbol,
        "latest_date": latest_date.date().isoformat(),
        "horizons": horizons,
        "source": source,
        "model_type": model_type,
        "data_version": data_version,
        "diagnostics": diagnostics,
        "note": "Predictions are probabilistic research signals, not guaranteed price moves.",
    }
    return StockForecastResult(forecast=forecast, summary=summary)


def _forecast_one_horizon(
    factors: pd.DataFrame,
    labels: pd.DataFrame,
    scores: pd.DataFrame,
    symbol: str,
    horizon: int,
    latest_date: pd.Timestamp,
    model_type: str,
    embargo_days: int,
) -> tuple[dict[str, object], dict[str, object]]:
    future_col = f"future_return_{horizon}d"
    excess_col = f"excess_return_{horizon}d"
    direction_col = f"direction_up_{horizon}d"
    base = factors[FACTOR_COLUMNS].join(labels[[future_col, excess_col, direction_col]], how="inner")
    base = base.replace([np.inf, -np.inf], np.nan).dropna(subset=[future_col, excess_col, direction_col])
    feature_columns = _select_features(base, latest_date)
    model_output = None
    if model_type in {"lightgbm", "ensemble", "lightgbm_classifier", "lightgbm_regressor"}:
        latest_x = factors.loc[(latest_date, symbol), feature_columns] if (latest_date, symbol) in factors.index else None
        model_output = _try_lightgbm_models(base, feature_columns, latest_x, future_col, excess_col, direction_col)

    if model_output is None:
        row, quality = _score_baseline(scores, labels, symbol, latest_date, horizon)
    else:
        row, quality = model_output

    history = labels.xs(symbol, level="symbol", drop_level=False)[future_col].dropna()
    history = history[history.index.get_level_values("date") < latest_date]
    residual_scale = _residual_scale(row["expected_return"], history)
    row["return_p10"] = residual_scale[0]
    row["return_p50"] = residual_scale[1]
    row["return_p90"] = residual_scale[2]
    row["direction"] = _direction_label(float(row["prob_up"]), float(row["expected_return"]))
    row["confidence"] = _confidence(float(row["prob_up"]), quality)
    quality["feature_count"] = len(feature_columns)
    quality["embargo_days"] = embargo_days
    return row, quality


def _try_lightgbm_models(
    base: pd.DataFrame,
    feature_columns: list[str],
    latest_x: pd.Series | None,
    future_col: str,
    excess_col: str,
    direction_col: str,
) -> tuple[dict[str, object], dict[str, object]] | None:
    if len(feature_columns) < 5:
        return None
    try:
        from lightgbm import LGBMClassifier, LGBMRegressor  # type: ignore
    except ImportError:
        return None

    train, valid = _time_split(base)
    if len(train) < 200 or train[direction_col].nunique() < 2:
        return None
    if latest_x is None:
        return None

    classifier = LGBMClassifier(
        n_estimators=180,
        learning_rate=0.04,
        num_leaves=15,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=42,
        verbose=-1,
    )
    regressor = LGBMRegressor(
        n_estimators=180,
        learning_rate=0.04,
        num_leaves=15,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=43,
        verbose=-1,
    )
    excess_regressor = LGBMRegressor(
        n_estimators=140,
        learning_rate=0.05,
        num_leaves=15,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=44,
        verbose=-1,
    )
    classifier.fit(train[feature_columns], train[direction_col].astype(int))
    regressor.fit(train[feature_columns], train[future_col])
    excess_regressor.fit(train[feature_columns], train[excess_col])
    latest_frame = latest_x.to_frame().T
    prob_up = float(classifier.predict_proba(latest_frame)[0, 1])
    expected_return = float(regressor.predict(latest_frame)[0])
    expected_excess = float(excess_regressor.predict(latest_frame)[0])
    quality = {"method": "lightgbm", "train_rows": int(len(train)), "valid_rows": int(len(valid))}
    if not valid.empty and valid[direction_col].nunique() >= 2:
        valid_prob = pd.Series(classifier.predict_proba(valid[feature_columns])[:, 1], index=valid.index)
        valid_pred = pd.Series(regressor.predict(valid[feature_columns]), index=valid.index)
        quality.update(_classification_metrics(valid_prob, valid[direction_col]))
        quality["valid_return_ic"] = _safe_corr(valid_pred, valid[future_col], "spearman")
    return (
        {
            "prob_up": prob_up,
            "expected_return": expected_return,
            "expected_excess_return": expected_excess,
            "prediction_method": "lightgbm",
        },
        quality,
    )


def _score_baseline(
    scores: pd.DataFrame,
    labels: pd.DataFrame,
    symbol: str,
    latest_date: pd.Timestamp,
    horizon: int,
) -> tuple[dict[str, object], dict[str, object]]:
    future_col = f"future_return_{horizon}d"
    excess_col = f"excess_return_{horizon}d"
    direction_col = f"direction_up_{horizon}d"
    history = scores[["score"]].join(labels[[future_col, excess_col, direction_col]], how="inner").dropna()
    history = history[history.index.get_level_values("date") < latest_date].copy()
    history["score_percentile"] = history.groupby(level="date")["score"].rank(pct=True)
    latest_daily = scores.xs(latest_date, level="date")
    latest_percentiles = latest_daily["score"].rank(pct=True)
    latest_pct = float(latest_percentiles.loc[symbol])
    prob_up, prob_quality = _linear_calibrated_prediction(history["score_percentile"], history[direction_col], latest_pct)
    expected_return, ret_quality = _linear_calibrated_prediction(history["score_percentile"], history[future_col], latest_pct)
    expected_excess, excess_quality = _linear_calibrated_prediction(history["score_percentile"], history[excess_col], latest_pct)
    valid = _last_validation_slice(history)
    quality: dict[str, object] = {
        "method": "score_baseline",
        "history_rows": int(len(history)),
        "prob_calibration": prob_quality,
        "return_calibration": ret_quality,
        "excess_calibration": excess_quality,
    }
    if not valid.empty:
        valid_prob = _predict_linear_series(
            history.drop(valid.index, errors="ignore")["score_percentile"],
            history.drop(valid.index, errors="ignore")[direction_col],
            valid["score_percentile"],
            clamp=True,
        )
        quality.update(_classification_metrics(valid_prob, valid[direction_col]))
    return (
        {
            "prob_up": float(np.clip(prob_up, 0.05, 0.95)),
            "expected_return": float(expected_return),
            "expected_excess_return": float(expected_excess),
            "prediction_method": "score_baseline",
        },
        quality,
    )


def _select_features(base: pd.DataFrame, latest_date: pd.Timestamp) -> list[str]:
    history = base[base.index.get_level_values("date") < latest_date]
    if history.empty:
        return []
    coverage = history[FACTOR_COLUMNS].notna().mean()
    return coverage[coverage >= 0.55].index.tolist()


def _time_split(dataset: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    dates = pd.DatetimeIndex(dataset.index.get_level_values("date").unique()).sort_values()
    if len(dates) < 30:
        return dataset, dataset.iloc[0:0]
    split = max(1, int(len(dates) * 0.8))
    train_dates = dates[:split]
    valid_dates = dates[split:]
    train = dataset[dataset.index.get_level_values("date").isin(train_dates)]
    valid = dataset[dataset.index.get_level_values("date").isin(valid_dates)]
    return train, valid


def _linear_calibrated_prediction(x: pd.Series, y: pd.Series, latest_x: float) -> tuple[float, dict[str, object]]:
    clean = pd.concat([x.astype(float), y.astype(float)], axis=1).dropna()
    if len(clean) < 20 or clean.iloc[:, 0].nunique() < 2:
        return float(clean.iloc[:, 1].mean()) if not clean.empty else 0.0, {"mode": "mean", "rows": int(len(clean))}
    xv = clean.iloc[:, 0]
    yv = clean.iloc[:, 1]
    var = float(xv.var(ddof=0))
    beta = float(xv.cov(yv, ddof=0) / var) if var > 0 else 0.0
    alpha = float(yv.mean() - beta * xv.mean())
    return alpha + beta * latest_x, {"mode": "linear_score_percentile", "rows": int(len(clean))}


def _predict_linear_series(x: pd.Series, y: pd.Series, latest_x: pd.Series, clamp: bool) -> pd.Series:
    pred, _quality = _linear_calibrated_prediction(x, y, 0.5)
    clean = pd.concat([x.astype(float), y.astype(float)], axis=1).dropna()
    if len(clean) >= 20 and clean.iloc[:, 0].nunique() >= 2:
        xv = clean.iloc[:, 0]
        yv = clean.iloc[:, 1]
        var = float(xv.var(ddof=0))
        beta = float(xv.cov(yv, ddof=0) / var) if var > 0 else 0.0
        alpha = float(yv.mean() - beta * xv.mean())
        out = alpha + beta * latest_x.astype(float)
    else:
        out = pd.Series(pred, index=latest_x.index)
    return out.clip(0.0, 1.0) if clamp else out


def _last_validation_slice(history: pd.DataFrame) -> pd.DataFrame:
    dates = pd.DatetimeIndex(history.index.get_level_values("date").unique()).sort_values()
    if len(dates) < 20:
        return history.iloc[0:0]
    valid_dates = dates[int(len(dates) * 0.8) :]
    return history[history.index.get_level_values("date").isin(valid_dates)]


def _classification_metrics(prob: pd.Series, target: pd.Series) -> dict[str, float]:
    aligned = pd.concat([prob.astype(float), target.astype(float)], axis=1).dropna()
    if aligned.empty:
        return {"valid_accuracy": 0.0, "valid_brier": 0.0, "valid_auc": 0.0}
    p = aligned.iloc[:, 0].clip(0.0, 1.0)
    y = aligned.iloc[:, 1]
    accuracy = float(((p >= 0.5).astype(int) == y.astype(int)).mean())
    brier = float(((p - y) ** 2).mean())
    return {"valid_accuracy": accuracy, "valid_brier": brier, "valid_auc": _auc(p, y)}


def _auc(prob: pd.Series, target: pd.Series) -> float:
    clean = pd.concat([prob, target], axis=1).dropna()
    y = clean.iloc[:, 1].astype(int)
    scores = clean.iloc[:, 0].astype(float)
    positive_count = int((y == 1).sum())
    negative_count = int((y == 0).sum())
    if positive_count == 0 or negative_count == 0:
        return 0.0
    ranks = scores.rank(method="average")
    positive_rank_sum = float(ranks[y == 1].sum())
    numerator = positive_rank_sum - positive_count * (positive_count + 1) / 2
    return float(numerator / (positive_count * negative_count))


def _residual_scale(expected_return: float, history: pd.Series) -> tuple[float, float, float]:
    if history.empty:
        return expected_return, expected_return, expected_return
    quantiles = history.astype(float).quantile([0.10, 0.50, 0.90])
    median = float(quantiles.loc[0.50])
    shift = expected_return - median
    return (
        float(quantiles.loc[0.10] + shift),
        float(quantiles.loc[0.50] + shift),
        float(quantiles.loc[0.90] + shift),
    )


def _direction_label(prob_up: float, expected_return: float) -> str:
    if prob_up >= 0.70 and expected_return > 0:
        return "强看多"
    if prob_up >= 0.58 and expected_return > -0.005:
        return "看多"
    if prob_up >= 0.53:
        return "震荡偏多"
    if prob_up <= 0.30 and expected_return < 0:
        return "强看空"
    if prob_up <= 0.42 and expected_return < 0.005:
        return "看空"
    if prob_up <= 0.47:
        return "震荡偏弱"
    return "中性"


def _confidence(prob_up: float, quality: dict[str, object]) -> float:
    edge = abs(prob_up - 0.5) * 2
    auc = float(quality.get("valid_auc", 0.5) or 0.5)
    quality_bonus = max(0.0, min(0.25, (auc - 0.5) * 0.5))
    return float(np.clip(edge * 0.75 + quality_bonus, 0.0, 1.0))


def _forecast_trust_status(row: dict[str, object], quality: dict[str, object], symbol_count: int, source: str) -> str:
    if source == "sample":
        return "data_insufficient"
    if symbol_count < 200:
        return "data_insufficient"
    method = str(quality.get("method", ""))
    if method not in {"lightgbm", "score_baseline"}:
        return "model_failed"
    confidence = float(row.get("confidence", 0.0))
    rank_ic = float(row.get("sample_rank_ic", 0.0) or 0.0)
    brier = float(row.get("sample_oos_brier", 1.0) or 1.0)
    if confidence >= 0.55 and (rank_ic > 0 or brier < 0.25):
        return "trusted"
    return "weak"


def _trend_label(bars: pd.DataFrame) -> str:
    df = bars.sort_values("date").copy()
    if len(df) < 60:
        return "无明显形态"
    close = df["close"]
    amount = df["amount"]
    ma20 = close.rolling(20).mean()
    ma60 = close.rolling(60).mean()
    high60 = df["high"].rolling(60).max()
    low60 = df["low"].rolling(60).min()
    ret5 = close.pct_change(5)
    latest_close = float(close.iloc[-1])
    if latest_close >= float(high60.iloc[-1]) * 0.995 and amount.iloc[-5:].mean() > amount.iloc[-20:].mean():
        return "突破"
    if latest_close > float(ma20.iloc[-1]) > float(ma60.iloc[-1]) and float(ret5.iloc[-1]) > 0:
        return "趋势延续"
    if latest_close > float(ma20.iloc[-1]) and float(close.iloc[-6]) <= float(ma20.iloc[-6]):
        return "均线修复"
    if latest_close / float(low60.iloc[-1]) - 1 < 0.04 and float(ret5.iloc[-1]) > 0:
        return "超跌反弹"
    if latest_close <= float(low60.iloc[-1]) * 1.005 or latest_close < float(ma20.iloc[-1]) * 0.94:
        return "破位"
    if latest_close / float(high60.iloc[-1]) > 0.92 and amount.iloc[-5:].mean() > amount.iloc[-60:].mean() * 1.5:
        return "高位拥挤"
    return "无明显形态"


def _risk_flags(bars: pd.DataFrame, source: str) -> list[str]:
    flags: list[str] = []
    df = bars.sort_values("date").copy()
    if len(df) < 180:
        flags.append("short_history")
    ret = df["close"].pct_change()
    if df["amount"].tail(20).fillna(0).le(0).any():
        flags.append("zero_amount")
    if ret.tail(20).abs().max() > 0.115:
        flags.append("abnormal_recent_return")
    vol20 = ret.tail(20).std()
    if not math.isnan(float(vol20)) and vol20 > 0.045:
        flags.append("high_volatility")
    if source in {"research", "auto"}:
        flags.append("may_include_fallback_data")
    return flags or ["none"]


def _factor_contributors(factors: pd.DataFrame, symbol: str, latest_date: pd.Timestamp) -> str:
    if (latest_date, symbol) not in factors.index:
        return ""
    history = factors[FACTOR_COLUMNS].replace([np.inf, -np.inf], np.nan)
    latest = history.loc[(latest_date, symbol)]
    mean = history.mean(numeric_only=True)
    std = history.std(numeric_only=True).replace(0, np.nan)
    z = ((latest - mean) / std).dropna()
    top = z.reindex(z.abs().sort_values(ascending=False).head(5).index)
    return ";".join(f"{name}={value:.3f}" for name, value in top.items())


def _data_version(bars_by_symbol: dict[str, pd.DataFrame], source: str) -> str:
    parts = [source]
    for symbol, bars in sorted(bars_by_symbol.items()):
        dates = pd.to_datetime(bars["date"])
        parts.append(f"{symbol}:{dates.min().date()}:{dates.max().date()}:{len(bars)}")
    digest = hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()
    return digest[:12]


def _safe_corr(left: pd.Series, right: pd.Series, method: str) -> float:
    if left.nunique() < 2 or right.nunique() < 2:
        return 0.0
    value = left.corr(right, method=method)
    if value is None or np.isnan(value):
        return 0.0
    return float(value)
