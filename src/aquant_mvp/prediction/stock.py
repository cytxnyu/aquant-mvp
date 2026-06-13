from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from aquant_mvp.config import DEFAULT_FACTOR_WEIGHTS
from aquant_mvp.features import merge_event_factors_into_panel
from aquant_mvp.factors import FACTOR_COLUMNS, compute_factor_panel
from aquant_mvp.labels import compute_stock_prediction_labels
from aquant_mvp.modeling.calibration import calibrate_probability, calibration_result_to_metrics
from aquant_mvp.strategy import score_factors


_TRUST_GATE_COLUMNS = [
    "latest_date",
    "symbol",
    "horizon_days",
    "trust_status",
    "gate",
    "passed",
    "severity",
    "reason",
    "model_id",
    "data_version",
]


@dataclass(frozen=True)
class StockForecastResult:
    forecast: pd.DataFrame
    summary: dict[str, object]


@dataclass(frozen=True)
class StockTrustGateReport:
    gates: pd.DataFrame
    summary: dict[str, object]
    markdown: str


def build_stock_forecast(
    bars_by_symbol: dict[str, pd.DataFrame],
    symbol: str,
    horizons: list[int],
    source: str,
    model_type: str = "ensemble",
    embargo_days: int = 5,
    allow_sample: bool = False,
    event_factors: pd.DataFrame | None = None,
    model_registry_dir: Path | None = None,
) -> StockForecastResult:
    symbol = symbol.zfill(6)
    if source == "sample" and not allow_sample:
        raise ValueError("predict-stock forbids sample data by default. Use --source research or --allow-sample for demos.")
    if symbol not in bars_by_symbol:
        raise ValueError(f"Symbol {symbol} is not loaded in the current universe.")

    factors = compute_factor_panel(bars_by_symbol)
    factors, event_feature_columns = merge_event_factors_into_panel(factors, event_factors)
    model_feature_columns = [*FACTOR_COLUMNS, *event_feature_columns]
    labels = compute_stock_prediction_labels(bars_by_symbol, horizons)
    scores = score_factors(factors, DEFAULT_FACTOR_WEIGHTS)
    latest_date = pd.Timestamp(scores.dropna(subset=["score"]).index.get_level_values("date").max())
    data_version = _data_version(bars_by_symbol, source)
    walk_forward_evidence = _load_walk_forward_evidence(model_registry_dir)

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
            feature_columns=model_feature_columns,
        )
        latest_bars = bars_by_symbol[symbol].sort_values("date")
        row["trend_label"] = _trend_label(latest_bars)
        row["risk_flags"] = ";".join(_risk_flags(latest_bars, source))
        row["top_factor_contributors"] = _factor_contributors(factors, symbol, latest_date, model_feature_columns)
        row["latest_date"] = latest_date.date().isoformat()
        row["symbol"] = symbol
        row["horizon_days"] = horizon
        row["model_type"] = model_type
        row["model_id"] = f"stock_forecast_{model_type}_h{horizon}"
        row["data_version"] = data_version
        row["universe_symbol_count"] = len(bars_by_symbol)
        row["minimum_trusted_symbols"] = 200
        row["event_feature_count"] = len(event_feature_columns)
        rel_rank = _relative_rank(scores, symbol, latest_date)
        row["same_theme_rank"] = rel_rank["rank"]
        row["same_theme_percentile"] = rel_rank["percentile"]
        row["same_theme_rank_note"] = "free mode uses loaded universe/theme pool as same-theme proxy"
        row["sample_oos_accuracy"] = quality.get("valid_accuracy", 0.0)
        row["sample_oos_auc"] = quality.get("valid_auc", 0.0)
        row["sample_oos_brier"] = quality.get("valid_brier", 0.0)
        row["sample_rank_ic"] = quality.get("valid_return_ic", quality.get("valid_rank_ic", 0.0))
        row["raw_prob_up"] = quality.get("raw_prob_up", row.get("prob_up", 0.5))
        row["calibrated_prob_up"] = quality.get("calibrated_prob_up", row.get("prob_up", 0.5))
        row["probability_calibration_method"] = quality.get("probability_calibration_method", "identity_missing")
        row["probability_calibration_status"] = quality.get("probability_calibration_status", quality.get("calibration_status", "calibration_missing"))
        row["probability_raw_brier"] = quality.get("probability_raw_brier", quality.get("valid_brier", 1.0))
        row["probability_calibrated_brier"] = quality.get("probability_calibrated_brier", quality.get("valid_brier", 1.0))
        row["probability_raw_ece"] = quality.get("probability_raw_ece", quality.get("calibration_ece", 1.0))
        row["probability_calibrated_ece"] = quality.get("probability_calibrated_ece", quality.get("calibration_ece", 1.0))
        row["probability_calibration_improvement_brier"] = quality.get("probability_calibration_improvement_brier", 0.0)
        row["probability_calibration_improvement_ece"] = quality.get("probability_calibration_improvement_ece", 0.0)
        row["calibration_rows"] = quality.get("calibration_rows", 0)
        row["calibration_bins"] = quality.get("calibration_bins", 0)
        row["calibration_ece"] = quality.get("calibration_ece", 1.0)
        row["calibration_status"] = quality.get("calibration_status", "calibration_missing")
        evidence = _match_walk_forward_evidence(walk_forward_evidence, model_type, horizon)
        row["walk_forward_model_id"] = evidence.get("model_id", "")
        row["walk_forward_status"] = evidence.get("trust_status", "missing")
        row["walk_forward_rows"] = evidence.get("rows", 0)
        row["walk_forward_auc"] = evidence.get("auc", 0.0)
        row["walk_forward_brier"] = evidence.get("brier", 0.0)
        row["walk_forward_rank_ic"] = evidence.get("rank_ic", 0.0)
        row["walk_forward_gate_reasons"] = evidence.get("trust_gate_reasons", "walk_forward_evidence_missing")
        row["trust_status"] = _forecast_trust_status(row, quality, len(bars_by_symbol), source, evidence)
        row["note"] = "Research signal only; not investment advice."
        rows.append(row)
        diagnostics[f"horizon_{horizon}d"] = quality

    forecast = pd.DataFrame(rows)
    columns = [
        "latest_date",
        "symbol",
        "horizon_days",
        "prob_up",
        "raw_prob_up",
        "calibrated_prob_up",
        "expected_return",
        "expected_excess_return",
        "direction",
        "trend_label",
        "confidence",
        "return_p10",
        "return_p50",
        "return_p90",
        "conformal_method",
        "conformal_rows",
        "conformal_alpha",
        "conformal_target_coverage",
        "conformal_interval_half_width",
        "conformal_status",
        "risk_flags",
        "top_factor_contributors",
        "prediction_method",
        "sample_oos_accuracy",
        "sample_oos_auc",
        "sample_oos_brier",
        "sample_rank_ic",
        "probability_calibration_method",
        "probability_calibration_status",
        "probability_raw_brier",
        "probability_calibrated_brier",
        "probability_raw_ece",
        "probability_calibrated_ece",
        "probability_calibration_improvement_brier",
        "probability_calibration_improvement_ece",
        "calibration_rows",
        "calibration_bins",
        "calibration_ece",
        "calibration_status",
        "walk_forward_model_id",
        "walk_forward_status",
        "walk_forward_rows",
        "walk_forward_auc",
        "walk_forward_brier",
        "walk_forward_rank_ic",
        "walk_forward_gate_reasons",
        "same_theme_rank",
        "same_theme_percentile",
        "same_theme_rank_note",
        "universe_symbol_count",
        "minimum_trusted_symbols",
        "event_feature_count",
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
        "event_feature_count": len(event_feature_columns),
        "event_features": event_feature_columns,
        "walk_forward_evidence_count": len(walk_forward_evidence),
        "diagnostics": diagnostics,
        "note": "Predictions are probabilistic research signals, not guaranteed price moves.",
    }
    return StockForecastResult(forecast=forecast, summary=summary)


def build_stock_trust_gate_report(
    forecast: pd.DataFrame,
    *,
    source: str = "",
    news_summary: dict[str, object] | None = None,
) -> StockTrustGateReport:
    """Build a horizon-by-horizon trust gate report for stock forecasts."""
    rows: list[dict[str, object]] = []
    if forecast.empty:
        summary = {
            "horizons": 0,
            "final_status_set": [],
            "blocking_gate_count": 0,
            "note": "No forecast rows were available for trust-gate evaluation.",
        }
        return StockTrustGateReport(pd.DataFrame(columns=_TRUST_GATE_COLUMNS), summary, _trust_gate_markdown(pd.DataFrame(), summary))

    news = news_summary or {}
    for row in forecast.to_dict(orient="records"):
        rows.extend(_trust_gate_rows(row, source=source, news_summary=news))
    gates = pd.DataFrame(rows, columns=_TRUST_GATE_COLUMNS)
    blocking = gates[(~gates["passed"].astype(bool)) & (gates["severity"] == "block")]
    by_horizon = {}
    for horizon, part in gates.groupby("horizon_days", sort=True):
        failed = part[(~part["passed"].astype(bool)) & (part["severity"] == "block")]
        by_horizon[str(int(horizon))] = {
            "trust_status": str(part["trust_status"].iloc[0]),
            "blocking_gates": failed["gate"].astype(str).tolist(),
            "blocking_reasons": failed["reason"].astype(str).tolist(),
        }
    summary = {
        "symbol": str(forecast["symbol"].iloc[0]).zfill(6) if "symbol" in forecast.columns else "",
        "latest_date": str(forecast["latest_date"].iloc[0]) if "latest_date" in forecast.columns else "",
        "source": source,
        "horizons": int(forecast["horizon_days"].nunique()) if "horizon_days" in forecast.columns else int(len(forecast)),
        "final_status_set": sorted(forecast["trust_status"].dropna().astype(str).unique().tolist()) if "trust_status" in forecast.columns else [],
        "gate_rows": int(len(gates)),
        "blocking_gate_count": int(len(blocking)),
        "blocking_gate_names": sorted(blocking["gate"].dropna().astype(str).unique().tolist()),
        "by_horizon": by_horizon,
        "news_summary": news,
        "note": "Trust gates explain why a probabilistic research forecast is trusted, weak, data_insufficient, or model_failed. They are not investment advice.",
    }
    return StockTrustGateReport(gates, summary, _trust_gate_markdown(gates, summary))


def write_stock_trust_gate_outputs(
    output_dir: Path,
    report: StockTrustGateReport,
    *,
    prefix: str = "stock_trust_gates",
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "csv": output_dir / f"{prefix}.csv",
        "json": output_dir / f"{prefix}.json",
        "md": output_dir / f"{prefix}.md",
    }
    report.gates.to_csv(paths["csv"], index=False)
    paths["json"].write_text(json.dumps(report.summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    paths["md"].write_text(report.markdown, encoding="utf-8")
    return paths


def _forecast_one_horizon(
    factors: pd.DataFrame,
    labels: pd.DataFrame,
    scores: pd.DataFrame,
    symbol: str,
    horizon: int,
    latest_date: pd.Timestamp,
    model_type: str,
    embargo_days: int,
    feature_columns: list[str],
) -> tuple[dict[str, object], dict[str, object]]:
    future_col = f"future_return_{horizon}d"
    excess_col = f"excess_return_{horizon}d"
    direction_col = f"direction_up_{horizon}d"
    available_features = [column for column in feature_columns if column in factors.columns]
    base = factors[available_features].join(labels[[future_col, excess_col, direction_col]], how="inner")
    base = base.replace([np.inf, -np.inf], np.nan).dropna(subset=[future_col, excess_col, direction_col])
    feature_columns = _select_features(base, latest_date, available_features)
    model_output = None
    if model_type in {"lightgbm", "ensemble", "event_aware_ensemble", "event-aware-ensemble", "lightgbm_classifier", "lightgbm_regressor"}:
        latest_x = factors.loc[(latest_date, symbol), feature_columns] if (latest_date, symbol) in factors.index else None
        model_output = _try_lightgbm_models(base, feature_columns, latest_x, future_col, excess_col, direction_col)

    if model_output is None:
        row, quality = _score_baseline(scores, labels, symbol, latest_date, horizon)
    else:
        row, quality = model_output

    history = labels.xs(symbol, level="symbol", drop_level=False)[future_col].dropna()
    history = history[history.index.get_level_values("date") < latest_date]
    interval, interval_quality = _conformal_return_interval(float(row["expected_return"]), history)
    row["return_p10"] = interval[0]
    row["return_p50"] = interval[1]
    row["return_p90"] = interval[2]
    row["conformal_method"] = interval_quality["conformal_method"]
    row["conformal_rows"] = interval_quality["conformal_rows"]
    row["conformal_alpha"] = interval_quality["conformal_alpha"]
    row["conformal_target_coverage"] = interval_quality["conformal_target_coverage"]
    row["conformal_interval_half_width"] = interval_quality["conformal_interval_half_width"]
    row["conformal_status"] = interval_quality["conformal_status"]
    row["direction"] = _direction_label(float(row["prob_up"]), float(row["expected_return"]))
    row["confidence"] = _confidence(float(row["prob_up"]), quality)
    quality["feature_count"] = len(feature_columns)
    quality["embargo_days"] = embargo_days
    quality.update(interval_quality)
    return row, quality


def _relative_rank(scores: pd.DataFrame, symbol: str, latest_date: pd.Timestamp) -> dict[str, object]:
    try:
        daily = scores.xs(latest_date, level="date").dropna(subset=["score"]).copy()
        daily["rank"] = daily["score"].rank(ascending=False, method="min")
        total = int(len(daily))
        rank = int(daily.loc[symbol, "rank"]) if symbol in daily.index else 0
        percentile = float(1 - (rank - 1) / max(1, total)) if rank else 0.0
        return {"rank": rank, "percentile": percentile}
    except Exception:  # noqa: BLE001
        return {"rank": 0, "percentile": 0.0}


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
    raw_prob_up = prob_up
    if not valid.empty and valid[direction_col].nunique() >= 2:
        valid_prob = pd.Series(classifier.predict_proba(valid[feature_columns])[:, 1], index=valid.index)
        valid_pred = pd.Series(regressor.predict(valid[feature_columns]), index=valid.index)
        quality.update(_classification_metrics(valid_prob, valid[direction_col]))
        prob_up = _apply_probability_calibration(valid_prob, valid[direction_col], raw_prob_up, quality)
        quality["valid_return_ic"] = _safe_corr(valid_pred, valid[future_col], "spearman")
    return (
        {
            "prob_up": prob_up,
            "raw_prob_up": raw_prob_up,
            "calibrated_prob_up": prob_up,
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
        raw_prob_up = float(np.clip(prob_up, 0.05, 0.95))
        prob_up = _apply_probability_calibration(valid_prob, valid[direction_col], raw_prob_up, quality)
    else:
        raw_prob_up = float(np.clip(prob_up, 0.05, 0.95))
    return (
        {
            "prob_up": float(np.clip(prob_up, 0.05, 0.95)),
            "raw_prob_up": raw_prob_up,
            "calibrated_prob_up": float(np.clip(prob_up, 0.05, 0.95)),
            "expected_return": float(expected_return),
            "expected_excess_return": float(expected_excess),
            "prediction_method": "score_baseline",
        },
        quality,
    )


def _select_features(base: pd.DataFrame, latest_date: pd.Timestamp, feature_columns: list[str]) -> list[str]:
    history = base[base.index.get_level_values("date") < latest_date]
    if history.empty:
        return []
    columns = [column for column in feature_columns if column in history.columns]
    coverage = history[columns].notna().mean()
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


def _apply_probability_calibration(
    prob: pd.Series,
    target: pd.Series,
    latest_prob: float,
    quality: dict[str, object],
) -> float:
    result = calibrate_probability(prob, target, latest_prob)
    metrics = calibration_result_to_metrics(result)
    quality.update(metrics)
    quality["raw_valid_brier"] = quality.get("valid_brier", result.raw_brier)
    quality["raw_calibration_ece"] = quality.get("calibration_ece", result.raw_ece)
    quality["valid_brier"] = result.calibrated_brier
    quality["calibration_rows"] = result.rows
    quality["calibration_bins"] = quality.get("calibration_bins", 0)
    quality["calibration_ece"] = result.calibrated_ece
    quality["calibration_status"] = result.status
    return result.calibrated_latest_prob


def _classification_metrics(prob: pd.Series, target: pd.Series) -> dict[str, float | int | str]:
    aligned = pd.concat([prob.astype(float), target.astype(float)], axis=1).dropna()
    if aligned.empty:
        return {
            "valid_accuracy": 0.0,
            "valid_brier": 1.0,
            "valid_auc": 0.0,
            "calibration_rows": 0,
            "calibration_bins": 0,
            "calibration_ece": 1.0,
            "calibration_status": "calibration_missing",
        }
    p = aligned.iloc[:, 0].clip(0.0, 1.0)
    y = aligned.iloc[:, 1]
    accuracy = float(((p >= 0.5).astype(int) == y.astype(int)).mean())
    brier = float(((p - y) ** 2).mean())
    reliability = _probability_reliability(p, y)
    return {
        "valid_accuracy": accuracy,
        "valid_brier": brier,
        "valid_auc": _auc(p, y),
        **reliability,
    }


def _probability_reliability(prob: pd.Series, target: pd.Series, bins: int = 5) -> dict[str, float | int | str]:
    clean = pd.concat([prob.astype(float).clip(0.0, 1.0), target.astype(float)], axis=1).dropna()
    if clean.empty:
        return {"calibration_rows": 0, "calibration_bins": 0, "calibration_ece": 1.0, "calibration_status": "calibration_missing"}
    p = clean.iloc[:, 0]
    y = clean.iloc[:, 1]
    edges = np.linspace(0.0, 1.0, bins + 1)
    total = len(clean)
    ece = 0.0
    used_bins = 0
    for left, right in zip(edges[:-1], edges[1:]):
        if right >= 1.0:
            mask = (p >= left) & (p <= right)
        else:
            mask = (p >= left) & (p < right)
        if not mask.any():
            continue
        used_bins += 1
        bin_prob = float(p[mask].mean())
        bin_rate = float(y[mask].mean())
        ece += float(mask.mean()) * abs(bin_prob - bin_rate)
    if total < 200:
        status = "calibration_sparse"
    elif used_bins < 3:
        status = "calibration_low_coverage"
    elif ece <= 0.05:
        status = "calibrated"
    elif ece <= 0.10:
        status = "calibration_watch"
    else:
        status = "calibration_failed"
    return {
        "calibration_rows": int(total),
        "calibration_bins": int(used_bins),
        "calibration_ece": float(ece),
        "calibration_status": status,
    }


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


def _conformal_return_interval(
    expected_return: float,
    history: pd.Series,
    alpha: float = 0.20,
    min_rows: int = 80,
) -> tuple[tuple[float, float, float], dict[str, object]]:
    clean = history.astype(float).replace([np.inf, -np.inf], np.nan).dropna()
    if len(clean) < min_rows:
        interval = _residual_scale(expected_return, clean)
        half_width = float(max(abs(interval[1] - interval[0]), abs(interval[2] - interval[1])))
        return interval, {
            "conformal_method": "historical_shifted_quantile_fallback",
            "conformal_rows": int(len(clean)),
            "conformal_alpha": float(alpha),
            "conformal_target_coverage": float(1.0 - alpha),
            "conformal_interval_half_width": half_width,
            "conformal_status": "conformal_sparse",
        }
    center = float(clean.median())
    residual = (clean - center).abs().sort_values()
    rank = int(math.ceil((len(residual) + 1) * (1.0 - alpha)))
    rank = min(max(rank, 1), len(residual))
    half_width = float(residual.iloc[rank - 1])
    return (
        float(expected_return - half_width),
        float(expected_return),
        float(expected_return + half_width),
    ), {
        "conformal_method": "split_conformal_historical_residual_proxy",
        "conformal_rows": int(len(clean)),
        "conformal_alpha": float(alpha),
        "conformal_target_coverage": float(1.0 - alpha),
        "conformal_interval_half_width": half_width,
        "conformal_status": "conformal_ready",
    }


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


def _forecast_trust_status(
    row: dict[str, object],
    quality: dict[str, object],
    symbol_count: int,
    source: str,
    walk_forward_evidence: dict[str, object],
) -> str:
    if source == "sample":
        return "data_insufficient"
    if symbol_count < 200:
        return "data_insufficient"
    if not walk_forward_evidence:
        row["walk_forward_gate_reasons"] = "walk_forward_evidence_missing"
        return "model_failed"
    if str(walk_forward_evidence.get("trust_status", "")) == "data_insufficient":
        return "data_insufficient"
    if str(walk_forward_evidence.get("trust_status", "")) == "model_failed":
        return "model_failed"
    if str(walk_forward_evidence.get("trust_status", "")) != "trusted":
        return "weak"
    method = str(quality.get("method", ""))
    if method not in {"lightgbm", "score_baseline"}:
        return "model_failed"
    confidence = float(row.get("confidence", 0.0))
    rank_ic = float(row.get("sample_rank_ic", 0.0) or 0.0)
    brier = float(row.get("sample_oos_brier", 1.0) or 1.0)
    calibration_status = str(row.get("probability_calibration_status", row.get("calibration_status", "calibration_missing")))
    calibration_ece = float(row.get("probability_calibrated_ece", row.get("calibration_ece", 1.0)) or 1.0)
    if calibration_status in {"calibration_missing", "calibration_sparse", "calibration_low_coverage"}:
        return "weak"
    if calibration_status == "calibration_failed" or calibration_ece > 0.10:
        return "model_failed"
    if str(row.get("conformal_status", "conformal_missing")) in {"conformal_missing", "conformal_sparse"}:
        return "weak"
    if confidence >= 0.55 and (rank_ic > 0 or brier < 0.25):
        return "trusted"
    return "weak"


def _trust_gate_rows(row: dict[str, object], *, source: str, news_summary: dict[str, object]) -> list[dict[str, object]]:
    horizon = int(row.get("horizon_days", 0) or 0)
    status = str(row.get("trust_status", ""))
    symbol = str(row.get("symbol", "")).zfill(6)
    gates = [
        _gate_row(row, horizon, symbol, status, "sample_data_block", source != "sample", "block", "sample_source_cannot_be_trusted"),
        _gate_row(
            row,
            horizon,
            symbol,
            status,
            "minimum_universe_size",
            int(row.get("universe_symbol_count", 0) or 0) >= int(row.get("minimum_trusted_symbols", 200) or 200),
            "block",
            f"universe_symbols={row.get('universe_symbol_count', 0)}, minimum={row.get('minimum_trusted_symbols', 200)}",
        ),
        _gate_row(
            row,
            horizon,
            symbol,
            status,
            "walk_forward_evidence_present",
            bool(str(row.get("walk_forward_model_id", "")).strip()),
            "block",
            str(row.get("walk_forward_gate_reasons", "walk_forward_evidence_missing")),
        ),
        _gate_row(
            row,
            horizon,
            symbol,
            status,
            "walk_forward_trusted",
            str(row.get("walk_forward_status", "")) == "trusted",
            "block",
            f"walk_forward_status={row.get('walk_forward_status', 'missing')}; reasons={row.get('walk_forward_gate_reasons', '')}",
        ),
        _gate_row(
            row,
            horizon,
            symbol,
            status,
            "walk_forward_rows",
            int(float(row.get("walk_forward_rows", 0) or 0)) >= 5000,
            "block",
            f"walk_forward_rows={row.get('walk_forward_rows', 0)}",
        ),
        _gate_row(
            row,
            horizon,
            symbol,
            status,
            "probability_calibration",
            str(row.get("probability_calibration_status", row.get("calibration_status", ""))) in {"calibrated", "calibration_watch"},
            "block",
            f"calibration_status={row.get('probability_calibration_status', row.get('calibration_status', ''))}; ece={_safe_float(row.get('probability_calibrated_ece', row.get('calibration_ece', 1.0))):.4f}; rows={row.get('calibration_rows', 0)}; method={row.get('probability_calibration_method', '')}",
        ),
        _gate_row(
            row,
            horizon,
            symbol,
            status,
            "probability_error",
            _safe_float(row.get("sample_oos_brier", 1.0)) <= 0.25,
            "block",
            f"sample_oos_brier={_safe_float(row.get('sample_oos_brier', 1.0)):.4f}",
        ),
        _gate_row(
            row,
            horizon,
            symbol,
            status,
            "conformal_interval_ready",
            str(row.get("conformal_status", "")) == "conformal_ready",
            "block",
            f"conformal_status={row.get('conformal_status', '')}; rows={row.get('conformal_rows', 0)}",
        ),
        _gate_row(
            row,
            horizon,
            symbol,
            status,
            "local_signal_quality",
            _safe_float(row.get("confidence", 0.0)) >= 0.55
            and (_safe_float(row.get("sample_rank_ic", 0.0)) > 0 or _safe_float(row.get("sample_oos_brier", 1.0)) < 0.25),
            "block",
            f"confidence={_safe_float(row.get('confidence', 0.0)):.4f}; sample_rank_ic={_safe_float(row.get('sample_rank_ic', 0.0)):.4f}",
        ),
        _gate_row(
            row,
            horizon,
            symbol,
            status,
            "risk_flags_clear",
            _risk_flags_pass(str(row.get("risk_flags", ""))),
            "warn",
            f"risk_flags={row.get('risk_flags', '')}",
        ),
        _gate_row(
            row,
            horizon,
            symbol,
            status,
            "news_evidence_available",
            int(news_summary.get("event_rows", 0) or 0) > 0 if news_summary.get("with_news") else False,
            "warn",
            f"with_news={news_summary.get('with_news', False)}; event_rows={news_summary.get('event_rows', 0)}; event_factor_rows={news_summary.get('event_factor_rows', 0)}",
        ),
    ]
    return gates


def _gate_row(
    row: dict[str, object],
    horizon: int,
    symbol: str,
    trust_status: str,
    gate: str,
    passed: bool,
    severity: str,
    reason: str,
) -> dict[str, object]:
    if trust_status == "trusted" and severity == "block" and not passed:
        reason = f"INCONSISTENT_TRUSTED_STATUS:{reason}"
    return {
        "latest_date": row.get("latest_date", ""),
        "symbol": symbol,
        "horizon_days": horizon,
        "trust_status": trust_status,
        "gate": gate,
        "passed": bool(passed),
        "severity": severity,
        "reason": reason if not passed else "passed",
        "model_id": row.get("model_id", ""),
        "data_version": row.get("data_version", ""),
    }


def _risk_flags_pass(flags: str) -> bool:
    normalized = (flags or "none").strip().lower()
    if normalized in {"", "none", "nan"}:
        return True
    hard_flags = {"short_history", "may_include_fallback_data", "high_volatility", "data_gap"}
    return not any(flag in normalized for flag in hard_flags)


def _safe_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _trust_gate_markdown(gates: pd.DataFrame, summary: dict[str, object]) -> str:
    lines = [
        f"# Stock Trust Gate Report: {summary.get('symbol', '')}",
        "",
        "This report explains why each probabilistic forecast is or is not trusted. A failed block gate prevents `trusted`; warning gates are evidence gaps or risk notes. This is not investment advice.",
        "",
        "## Summary",
        "",
        f"- Source: `{summary.get('source', '')}`",
        f"- Horizons: `{summary.get('horizons', 0)}`",
        f"- Final status set: `{', '.join(summary.get('final_status_set', [])) if summary.get('final_status_set') else 'none'}`",
        f"- Blocking gate count: `{summary.get('blocking_gate_count', 0)}`",
        f"- Blocking gates: `{', '.join(summary.get('blocking_gate_names', [])) if summary.get('blocking_gate_names') else 'none'}`",
        "",
    ]
    if gates.empty:
        lines.append("- No gate rows were generated.")
        return "\n".join(lines)
    lines.extend(["## Horizon Gates", ""])
    for horizon, part in gates.groupby("horizon_days", sort=True):
        status = str(part["trust_status"].iloc[0])
        failed = part[(~part["passed"].astype(bool)) & (part["severity"] == "block")]
        warnings = part[(~part["passed"].astype(bool)) & (part["severity"] == "warn")]
        lines.append(f"### {int(horizon)}d - `{status}`")
        if failed.empty:
            lines.append("- Block gates: passed")
        else:
            for row in failed.itertuples(index=False):
                lines.append(f"- Block `{row.gate}`: {row.reason}")
        if not warnings.empty:
            for row in warnings.itertuples(index=False):
                lines.append(f"- Warn `{row.gate}`: {row.reason}")
        lines.append("")
    return "\n".join(lines).rstrip()


def _load_walk_forward_evidence(registry_dir: Path | None) -> list[dict[str, object]]:
    if registry_dir is None:
        return []
    path = Path(registry_dir) / "model_registry.json"
    if not path.exists():
        return []
    try:
        import json

        records = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return []
    if not isinstance(records, list):
        return []
    out: list[dict[str, object]] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        if record.get("model_family") != "walk_forward_validation":
            continue
        metrics = record.get("metrics", {})
        if not isinstance(metrics, dict):
            metrics = {}
        evidence = {
            "model_id": record.get("model_id", ""),
            "model_type": record.get("model_type", ""),
            "horizon_days": int(record.get("horizon_days", metrics.get("horizon_days", 0)) or 0),
            "registered_at": record.get("registered_at", ""),
            "trust_status": metrics.get("trust_status", record.get("trust_status", "")),
            "trust_gate_reasons": metrics.get("trust_gate_reasons", ""),
            "rows": metrics.get("rows", 0),
            "auc": metrics.get("auc", 0.0),
            "brier": metrics.get("brier", 0.0),
            "rank_ic": metrics.get("rank_ic", 0.0),
        }
        out.append(evidence)
    return out


def _match_walk_forward_evidence(records: list[dict[str, object]], model_type: str, horizon: int) -> dict[str, object]:
    normalized = str(model_type).lower().replace("-", "_")
    candidates = [
        record
        for record in records
        if int(record.get("horizon_days", 0) or 0) == int(horizon)
        and str(record.get("model_type", "")).lower().replace("-", "_") == normalized
    ]
    if not candidates:
        return {}
    return sorted(candidates, key=lambda item: str(item.get("registered_at", "")))[-1]


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


def _factor_contributors(factors: pd.DataFrame, symbol: str, latest_date: pd.Timestamp, feature_columns: list[str] | None = None) -> str:
    if (latest_date, symbol) not in factors.index:
        return ""
    columns = [column for column in (feature_columns or FACTOR_COLUMNS) if column in factors.columns]
    history = factors[columns].replace([np.inf, -np.inf], np.nan)
    latest = history.loc[(latest_date, symbol)]
    mean = history.mean(numeric_only=True)
    std = history.std(numeric_only=True).replace(0, np.nan)
    z = ((latest - mean) / std).dropna()
    top = z.reindex(z.abs().sort_values(ascending=False).head(5).index)
    parts = [f"z:{name}={value:.3f}" for name, value in top.items()]
    event_columns = [
        column
        for column in columns
        if column.startswith("event_") or column in {"positive_event_count", "negative_event_count"}
    ]
    for column in event_columns:
        value = latest.get(column, np.nan)
        if pd.notna(value) and abs(float(value)) > 1e-12:
            parts.append(f"latest:{column}={float(value):.3f}")
    return ";".join(parts[:10])


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
