from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from aquant_mvp.universe import build_theme_universe, symbol_theme_membership


def summarize_model_registry(records: list[dict[str, object]]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for record in records:
        metrics = record.get("metrics", {}) if isinstance(record, dict) else {}
        metrics = metrics if isinstance(metrics, dict) else {}
        rows.append(
            {
                "model_id": record.get("model_id", ""),
                "model_type": record.get("model_type", ""),
                "requested_model_type": record.get("requested_model_type", record.get("model_type", "")),
                "effective_model_type": record.get("effective_model_type", record.get("model_type", "")),
                "effective_model_types": record.get("effective_model_types", metrics.get("effective_model_types", "")),
                "model_base_status": record.get("model_base_status", ""),
                "model_base_statuses": record.get("model_base_statuses", metrics.get("model_base_statuses", "")),
                "fallback_reason": record.get("fallback_reason", ""),
                "fallback_rate": record.get("fallback_rate", metrics.get("fallback_rate", "")),
                "prediction_methods": record.get("prediction_methods", metrics.get("prediction_methods", "")),
                "horizon_days": record.get("horizon_days", ""),
                "model_family": record.get("model_family", ""),
                "trust_status": metrics.get("trust_status", record.get("trust_status", "")),
                "trust_gate_passed": metrics.get("trust_gate_passed", ""),
                "trust_gate_reasons": metrics.get("trust_gate_reasons", ""),
                "rows": metrics.get("rows", record.get("train_rows", "")),
                "rank_ic": metrics.get("rank_ic", metrics.get("valid_rank_ic", "")),
                "direction_accuracy": metrics.get("direction_accuracy", metrics.get("valid_accuracy", "")),
                "auc": metrics.get("auc", metrics.get("valid_auc", "")),
                "raw_auc": metrics.get("raw_auc", ""),
                "brier": metrics.get("brier", metrics.get("valid_brier", "")),
                "raw_brier": metrics.get("raw_brier", ""),
                "calibrated_ece": metrics.get("calibrated_ece", ""),
                "raw_ece": metrics.get("raw_ece", ""),
                "probability_calibration_statuses": metrics.get("probability_calibration_statuses", ""),
                "probability_calibration_methods": metrics.get("probability_calibration_methods", ""),
                "probability_calibration_ready_ratio": metrics.get("probability_calibration_ready_ratio", ""),
                "probability_calibration_pit_passed": metrics.get("probability_calibration_pit_passed", ""),
                "top_bottom_spread": metrics.get("top_bottom_spread", ""),
                "beats_baseline": metrics.get("beats_baseline", ""),
                "artifact_path": record.get("artifact_path", ""),
                "registered_at": record.get("registered_at", ""),
            }
        )
    columns = [
        "model_id",
        "model_type",
        "requested_model_type",
        "effective_model_type",
        "effective_model_types",
        "model_base_status",
        "model_base_statuses",
        "fallback_reason",
        "fallback_rate",
        "prediction_methods",
        "horizon_days",
        "model_family",
        "trust_status",
        "trust_gate_passed",
        "trust_gate_reasons",
        "rows",
        "rank_ic",
        "direction_accuracy",
        "auc",
        "raw_auc",
        "brier",
        "raw_brier",
        "calibrated_ece",
        "raw_ece",
        "probability_calibration_statuses",
        "probability_calibration_methods",
        "probability_calibration_ready_ratio",
        "probability_calibration_pit_passed",
        "top_bottom_spread",
        "beats_baseline",
        "artifact_path",
        "registered_at",
    ]
    if not rows:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows)[columns]


def load_walk_forward_prediction_artifacts(
    records: list[dict[str, object]],
    output_dir: Path | None = None,
    extra_candidates: Iterable[Path] | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    candidates: list[Path] = []
    for record in records:
        if record.get("model_family") != "walk_forward_validation":
            continue
        artifact = str(record.get("artifact_path", "") or "")
        if not artifact:
            continue
        path = Path(artifact)
        if path.suffix.lower() == ".csv":
            candidates.append(path)
    if output_dir is not None:
        candidates.append(output_dir / "walk_forward_predictions.csv")
    candidates.append(Path("reports/walk_forward/walk_forward_predictions.csv"))
    candidates.extend(extra_candidates or [])

    frames: list[pd.DataFrame] = []
    used: list[str] = []
    seen: set[str] = set()
    for path in candidates:
        normalized = str(path)
        if normalized in seen or not path.exists():
            continue
        seen.add(normalized)
        try:
            frame = pd.read_csv(path)
        except Exception:  # noqa: BLE001
            continue
        if frame.empty or "prob_up" not in frame.columns:
            continue
        frame["source_artifact"] = normalized
        frames.append(frame)
        used.append(normalized)
    if not frames:
        return pd.DataFrame(), used
    return pd.concat(frames, ignore_index=True, sort=False), used


def evaluate_walk_forward_slices(predictions: pd.DataFrame) -> dict[str, pd.DataFrame]:
    if predictions.empty:
        note = pd.DataFrame([{"note": "walk_forward_predictions.csv not found or empty"}])
        return {
            "year": note.copy(),
            "industry": note.copy(),
            "theme": note.copy(),
            "size": note.copy(),
            "regime": note.copy(),
        }

    frame = predictions.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce") if "date" in frame.columns else pd.NaT
    frame["symbol"] = frame["symbol"].astype(str).str.zfill(6) if "symbol" in frame.columns else ""
    frame = frame.dropna(subset=["date"])
    if frame.empty:
        note = pd.DataFrame([{"note": "walk_forward_predictions.csv has no usable date column"}])
        return {
            "year": note.copy(),
            "industry": note.copy(),
            "theme": note.copy(),
            "size": note.copy(),
            "regime": note.copy(),
        }

    themed = _attach_theme_proxy(frame)
    sized = _attach_size_bucket(frame)
    regime = _attach_regime(frame)

    return {
        "year": _evaluate_grouped(frame.assign(year=frame["date"].dt.year), ["model_type", "horizon_days", "year"]),
        "industry": _evaluate_grouped(
            themed.assign(industry=themed["theme"].map(lambda value: f"theme_proxy:{value}")),
            ["model_type", "horizon_days", "industry"],
            extra_static={"industry_source": "curated_hot_theme_proxy_not_historical_industry"},
        ),
        "theme": _evaluate_grouped(
            themed,
            ["model_type", "horizon_days", "theme"],
            extra_static={"theme_source": "curated_hot_theme_seed"},
        ),
        "size": _evaluate_grouped(
            sized,
            ["model_type", "horizon_days", "size_source", "size_bucket"],
        ),
        "regime": _evaluate_grouped(
            regime,
            ["model_type", "horizon_days", "regime_source", "market_regime"],
        ),
    }


def _evaluate_grouped(frame: pd.DataFrame, group_columns: list[str], extra_static: dict[str, object] | None = None) -> pd.DataFrame:
    missing = [column for column in group_columns if column not in frame.columns]
    if missing:
        return pd.DataFrame([{"note": f"missing slice columns: {','.join(missing)}"}])
    rows: list[dict[str, object]] = []
    for keys, part in frame.groupby(group_columns, dropna=False, sort=True):
        key_values = keys if isinstance(keys, tuple) else (keys,)
        row = {column: value for column, value in zip(group_columns, key_values)}
        row.update(_prediction_metrics(part))
        if extra_static:
            row.update(extra_static)
        rows.append(row)
    if not rows:
        return pd.DataFrame([{"note": "no rows available for slice evaluation"}])
    return pd.DataFrame(rows).sort_values(group_columns).reset_index(drop=True)


def _prediction_metrics(frame: pd.DataFrame) -> dict[str, object]:
    ret_col, direction_col = _prediction_label_columns(frame)
    if not ret_col or not direction_col:
        return {
            "rows": int(len(frame)),
            "symbols": int(frame["symbol"].nunique()) if "symbol" in frame.columns else 0,
            "slice_status": "missing_label_columns",
        }
    optional_columns = [
        column
        for column in [
            "raw_prob_up",
            "probability_calibration_status",
            "probability_calibration_method",
            "probability_calibration_pit_passed",
        ]
        if column in frame.columns
    ]
    work = frame[["symbol", "prob_up", ret_col, direction_col, *optional_columns]].copy()
    work["prob_up"] = pd.to_numeric(work["prob_up"], errors="coerce")
    if "raw_prob_up" in work.columns:
        work["raw_prob_up"] = pd.to_numeric(work["raw_prob_up"], errors="coerce")
    work[ret_col] = pd.to_numeric(work[ret_col], errors="coerce")
    work[direction_col] = pd.to_numeric(work[direction_col], errors="coerce")
    work = work.dropna(subset=["prob_up", ret_col, direction_col])
    if work.empty:
        return {"rows": 0, "symbols": 0, "slice_status": "empty_after_label_filter"}
    prob = work["prob_up"].astype(float).clip(0.0, 1.0)
    raw_prob = work["raw_prob_up"].astype(float).fillna(prob).clip(0.0, 1.0) if "raw_prob_up" in work.columns else prob
    direction = work[direction_col].astype(int)
    ret = work[ret_col].astype(float)
    top = work[prob >= prob.quantile(0.8)] if len(work) >= 5 else work.iloc[0:0]
    bottom = work[prob <= prob.quantile(0.2)] if len(work) >= 5 else work.iloc[0:0]
    baseline = int(direction.mean() >= 0.5)
    direction_accuracy = float(((prob >= 0.5).astype(int) == direction).mean())
    baseline_accuracy = float((direction == baseline).mean())
    top_return = float(top[ret_col].mean()) if not top.empty else 0.0
    bottom_return = float(bottom[ret_col].mean()) if not bottom.empty else 0.0
    rank_ic = _safe_corr(prob, ret, "spearman")
    top_bottom_spread = top_return - bottom_return
    if len(work) < 50:
        status = "data_sparse"
    elif direction_accuracy <= baseline_accuracy and rank_ic <= 0.0 and top_bottom_spread <= 0.0:
        status = "weak_or_failed"
    else:
        status = "ok"
    return {
        "rows": int(len(work)),
        "symbols": int(work["symbol"].nunique()),
        "direction_accuracy": direction_accuracy,
        "baseline_accuracy": baseline_accuracy,
        "auc": _auc(prob, direction),
        "raw_auc": _auc(raw_prob, direction),
        "brier": float(((prob - direction) ** 2).mean()),
        "raw_brier": float(((raw_prob - direction) ** 2).mean()),
        "calibrated_ece": _ece(prob, direction),
        "raw_ece": _ece(raw_prob, direction),
        "probability_calibration_statuses": _joined_values(work, "probability_calibration_status"),
        "probability_calibration_methods": _joined_values(work, "probability_calibration_method"),
        "probability_calibration_ready_ratio": _ready_ratio(work),
        "probability_calibration_pit_ratio": _pit_ratio(work),
        "rank_ic": rank_ic,
        "mean_forward_return": float(ret.mean()),
        "top_bucket_return": top_return,
        "bottom_bucket_return": bottom_return,
        "top_bottom_spread": float(top_bottom_spread),
        "slice_status": status,
    }


def _prediction_label_columns(frame: pd.DataFrame) -> tuple[str | None, str | None]:
    horizon = None
    if "horizon_days" in frame.columns and frame["horizon_days"].notna().any():
        horizon = int(float(frame["horizon_days"].dropna().iloc[0]))
    if horizon is not None:
        ret_col = f"future_return_{horizon}d"
        direction_col = f"direction_up_{horizon}d"
        if ret_col in frame.columns and direction_col in frame.columns:
            return ret_col, direction_col
    ret_col = next((column for column in frame.columns if column.startswith("future_return_")), None)
    direction_col = next((column for column in frame.columns if column.startswith("direction_up_")), None)
    return ret_col, direction_col


def _attach_theme_proxy(frame: pd.DataFrame) -> pd.DataFrame:
    membership = symbol_theme_membership(build_theme_universe("hot"))
    theme_map = {
        str(row.symbol).zfill(6): str(row.themes).split(";")[0]
        for row in membership.itertuples(index=False)
        if str(row.themes)
    }
    out = frame.copy()
    out["theme"] = out["symbol"].map(theme_map).fillna("unmapped_theme")
    return out


def _attach_size_bucket(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["size_source"] = "market_cap_unavailable"
    out["size_bucket"] = "market_cap_unavailable"
    if "market_cap" in out.columns:
        values = pd.to_numeric(out["market_cap"], errors="coerce")
        mask = values.notna()
        out.loc[mask, "size_bucket"] = _quantile_bucket(values[mask], ["small_cap", "mid_cap", "large_cap"])
        out.loc[mask, "size_source"] = "market_cap"
    if "cs_amount_rank_20" in out.columns:
        values = pd.to_numeric(out["cs_amount_rank_20"], errors="coerce")
        mask = out["size_source"].eq("market_cap_unavailable") & values.notna()
        out.loc[mask, "size_bucket"] = _rank_bucket(values[mask], ["low_liquidity_proxy", "mid_liquidity_proxy", "high_liquidity_proxy"])
        out.loc[mask, "size_source"] = "cs_amount_rank_20_liquidity_proxy"
    if "amount_mean_20" in out.columns:
        values = pd.to_numeric(out["amount_mean_20"], errors="coerce")
        mask = out["size_source"].eq("market_cap_unavailable") & values.notna()
        out.loc[mask, "size_bucket"] = _quantile_bucket(values[mask], ["low_liquidity_proxy", "mid_liquidity_proxy", "high_liquidity_proxy"])
        out.loc[mask, "size_source"] = "amount_mean_20_liquidity_proxy"
    return out


def _attach_regime(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy().reset_index(drop=True)
    out["market_regime"] = "regime_unavailable"
    out["regime_source"] = "regime_unavailable"
    if {"market_mean_return", "market_breadth"}.issubset(out.columns):
        pit_regime = _regime_from_pit_market_features(out)
        mask = pit_regime.ne("regime_unavailable")
        out.loc[mask, "market_regime"] = pit_regime[mask]
        out.loc[mask, "regime_source"] = "pit_market_mean_return_and_breadth"
        if mask.all():
            return out
    if "horizon_days" not in out.columns:
        ret_col, _direction_col = _prediction_label_columns(out)
        if ret_col:
            fallback = _regime_for_part(out, ret_col)
            mask = out["regime_source"].eq("regime_unavailable") & fallback.ne("regime_unavailable")
            out.loc[mask, "market_regime"] = fallback[mask]
            out.loc[mask, "regime_source"] = "ex_post_oos_forward_return_for_evaluation_only"
        return out
    for _horizon, index in out.groupby("horizon_days", dropna=False).groups.items():
        part = out.loc[index]
        ret_col, _direction_col = _prediction_label_columns(part)
        if not ret_col:
            continue
        fallback = _regime_for_part(part, ret_col)
        mask = out.loc[index, "regime_source"].eq("regime_unavailable") & fallback.ne("regime_unavailable")
        out.loc[fallback.index[mask], "market_regime"] = fallback[mask]
        out.loc[fallback.index[mask], "regime_source"] = "ex_post_oos_forward_return_for_evaluation_only"
    return out


def _regime_from_pit_market_features(frame: pd.DataFrame) -> pd.Series:
    market_return = pd.to_numeric(frame["market_mean_return"], errors="coerce")
    breadth = pd.to_numeric(frame["market_breadth"], errors="coerce")
    high_return = float(market_return.quantile(0.67)) if market_return.notna().any() else 0.0
    low_return = float(market_return.quantile(0.33)) if market_return.notna().any() else 0.0
    high_breadth = float(breadth.quantile(0.67)) if breadth.notna().any() else 0.55
    low_breadth = float(breadth.quantile(0.33)) if breadth.notna().any() else 0.45
    out = pd.Series("sideways_pit", index=frame.index, dtype="object")
    out[(market_return >= high_return) & (breadth >= high_breadth)] = "bullish_pit"
    out[(market_return <= low_return) & (breadth <= low_breadth)] = "bearish_pit"
    if "volatility_20" in frame.columns:
        vol = pd.to_numeric(frame["volatility_20"], errors="coerce")
        if vol.notna().any():
            out[vol >= float(vol.quantile(0.75))] = "high_volatility_pit"
    out[market_return.isna() | breadth.isna()] = "regime_unavailable"
    return out


def _regime_for_part(frame: pd.DataFrame, ret_col: str) -> pd.Series:
    daily = (
        frame.assign(_ret=pd.to_numeric(frame[ret_col], errors="coerce"))
        .groupby("date", as_index=False)
        .agg(market_forward_return=("_ret", "mean"), cross_section_vol=("_ret", "std"))
    ).dropna(subset=["market_forward_return"])
    if daily.empty:
        return pd.Series(["regime_unavailable"] * len(frame), index=frame.index)
    vol_threshold = float(daily["cross_section_vol"].quantile(0.75))
    up_threshold = float(daily["market_forward_return"].quantile(0.67))
    down_threshold = float(daily["market_forward_return"].quantile(0.33))

    def classify(row: pd.Series) -> str:
        if pd.notna(row["cross_section_vol"]) and row["cross_section_vol"] >= vol_threshold:
            return "high_volatility"
        if row["market_forward_return"] >= up_threshold:
            return "bullish_oos"
        if row["market_forward_return"] <= down_threshold:
            return "bearish_oos"
        return "sideways_oos"

    daily["market_regime"] = daily.apply(classify, axis=1)
    mapped = frame[["date"]].merge(daily[["date", "market_regime"]], on="date", how="left")["market_regime"]
    mapped.index = frame.index
    return mapped.fillna("regime_unavailable")


def _quantile_bucket(values: pd.Series, labels: list[str]) -> pd.Series:
    if values.notna().sum() < len(labels):
        return pd.Series([f"{labels[0]}_or_unknown"] * len(values), index=values.index)
    try:
        return pd.qcut(values.rank(method="first"), len(labels), labels=labels, duplicates="drop").astype(str)
    except ValueError:
        return pd.Series([f"{labels[0]}_or_unknown"] * len(values), index=values.index)


def _rank_bucket(values: pd.Series, labels: list[str]) -> pd.Series:
    out = pd.Series(labels[1], index=values.index, dtype="object")
    out[values <= 1 / 3] = labels[0]
    out[values >= 2 / 3] = labels[2]
    out[values.isna()] = "unknown"
    return out


def _auc(prob: pd.Series, direction: pd.Series) -> float:
    y = direction.astype(int)
    positives = int((y == 1).sum())
    negatives = int((y == 0).sum())
    if positives == 0 or negatives == 0:
        return 0.0
    ranks = prob.rank(method="average")
    positive_rank_sum = float(ranks[y == 1].sum())
    return float((positive_rank_sum - positives * (positives + 1) / 2) / (positives * negatives))


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


def _joined_values(frame: pd.DataFrame, column: str) -> str:
    if column not in frame.columns:
        return ""
    return ";".join(sorted(frame[column].dropna().astype(str).unique().tolist()))


def _ready_ratio(frame: pd.DataFrame) -> float:
    if "probability_calibration_status" not in frame.columns:
        return 0.0
    statuses = frame["probability_calibration_status"].dropna().astype(str)
    if statuses.empty:
        return 0.0
    return float(statuses.isin({"calibrated", "calibration_watch"}).mean())


def _pit_ratio(frame: pd.DataFrame) -> float:
    if "probability_calibration_pit_passed" not in frame.columns:
        return 0.0
    values = frame["probability_calibration_pit_passed"].map(_truthy)
    return float(values.mean()) if len(values) else 0.0


def _truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _safe_corr(left: pd.Series, right: pd.Series, method: str) -> float:
    if left.nunique(dropna=True) < 2 or right.nunique(dropna=True) < 2:
        return 0.0
    value = left.corr(right, method=method)
    if value is None or np.isnan(value):
        return 0.0
    return float(value)
