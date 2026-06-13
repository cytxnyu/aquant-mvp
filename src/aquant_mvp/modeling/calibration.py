from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ProbabilityCalibrationResult:
    raw_latest_prob: float
    calibrated_latest_prob: float
    method: str
    status: str
    rows: int
    train_rows: int
    eval_rows: int
    raw_brier: float
    calibrated_brier: float
    raw_ece: float
    calibrated_ece: float
    improvement_brier: float
    improvement_ece: float
    candidates: pd.DataFrame


@dataclass(frozen=True)
class ProbabilitySeriesCalibrationResult:
    calibrated_probabilities: pd.Series
    method: str
    status: str
    rows: int
    train_rows: int
    eval_rows: int
    raw_brier: float
    calibrated_brier: float
    raw_ece: float
    calibrated_ece: float
    improvement_brier: float
    improvement_ece: float
    candidates: pd.DataFrame


def calibrate_probability(
    prob: pd.Series,
    target: pd.Series,
    latest_prob: float | None = None,
    *,
    min_train_rows: int = 80,
    min_eval_rows: int = 40,
    bins: int = 5,
) -> ProbabilityCalibrationResult:
    """Select an identity/Platt/isotonic probability calibrator using time order.

    The calibration split is deterministic and chronological. It is intended for
    local validation evidence; it never uses random splits.
    """
    aligned = pd.concat([prob.astype(float), target.astype(float)], axis=1).dropna()
    aligned.columns = ["prob", "target"]
    aligned["prob"] = aligned["prob"].clip(0.0, 1.0)
    latest = float(np.clip(latest_prob if latest_prob is not None else aligned["prob"].iloc[-1] if not aligned.empty else 0.5, 0.0, 1.0))
    if aligned.empty:
        return _empty_result(latest, "identity_missing", "calibration_missing", bins)
    aligned = _sort_by_time(aligned)
    rows = int(len(aligned))
    if rows < min_train_rows + min_eval_rows or aligned["target"].nunique() < 2:
        raw_brier = _brier(aligned["prob"], aligned["target"])
        raw_ece = _ece(aligned["prob"], aligned["target"], bins)
        return ProbabilityCalibrationResult(
            raw_latest_prob=latest,
            calibrated_latest_prob=latest,
            method="identity_insufficient",
            status="calibration_sparse",
            rows=rows,
            train_rows=0,
            eval_rows=0,
            raw_brier=raw_brier,
            calibrated_brier=raw_brier,
            raw_ece=raw_ece,
            calibrated_ece=raw_ece,
            improvement_brier=0.0,
            improvement_ece=0.0,
            candidates=_candidate_frame([]),
        )

    split = max(min_train_rows, int(rows * 0.70))
    if rows - split < min_eval_rows:
        split = rows - min_eval_rows
    train = aligned.iloc[:split]
    eval_frame = aligned.iloc[split:]
    if train["target"].nunique() < 2 or eval_frame.empty:
        raw_brier = _brier(aligned["prob"], aligned["target"])
        raw_ece = _ece(aligned["prob"], aligned["target"], bins)
        return ProbabilityCalibrationResult(
            raw_latest_prob=latest,
            calibrated_latest_prob=latest,
            method="identity_single_class",
            status="calibration_sparse",
            rows=rows,
            train_rows=int(len(train)),
            eval_rows=int(len(eval_frame)),
            raw_brier=raw_brier,
            calibrated_brier=raw_brier,
            raw_ece=raw_ece,
            calibrated_ece=raw_ece,
            improvement_brier=0.0,
            improvement_ece=0.0,
            candidates=_candidate_frame([]),
        )

    candidates: list[dict[str, object]] = []
    identity_eval = eval_frame["prob"].clip(0.0, 1.0)
    candidates.append(_candidate_metrics("identity", identity_eval, eval_frame["target"], latest, bins))
    platt = _fit_platt(train["prob"], train["target"], eval_frame["prob"], latest)
    if platt is not None:
        eval_prob, latest_value = platt
        candidates.append(_candidate_metrics("platt", eval_prob, eval_frame["target"], latest_value, bins))
    isotonic = _fit_isotonic(train["prob"], train["target"], eval_frame["prob"], latest)
    if isotonic is not None:
        eval_prob, latest_value = isotonic
        candidates.append(_candidate_metrics("isotonic", eval_prob, eval_frame["target"], latest_value, bins))

    candidate_frame = _candidate_frame(candidates)
    best = candidate_frame.sort_values(["brier", "ece", "method"], ascending=[True, True, True]).iloc[0]
    raw_row = candidate_frame[candidate_frame["method"] == "identity"].iloc[0]
    status = _calibration_status(int(len(eval_frame)), float(best["ece"]))
    return ProbabilityCalibrationResult(
        raw_latest_prob=latest,
        calibrated_latest_prob=float(np.clip(best["latest_prob"], 0.0, 1.0)),
        method=str(best["method"]),
        status=status,
        rows=rows,
        train_rows=int(len(train)),
        eval_rows=int(len(eval_frame)),
        raw_brier=float(raw_row["brier"]),
        calibrated_brier=float(best["brier"]),
        raw_ece=float(raw_row["ece"]),
        calibrated_ece=float(best["ece"]),
        improvement_brier=float(raw_row["brier"] - best["brier"]),
        improvement_ece=float(raw_row["ece"] - best["ece"]),
        candidates=candidate_frame,
    )


def calibrate_probability_series(
    calibration_prob: pd.Series,
    calibration_target: pd.Series,
    inference_prob: pd.Series,
    *,
    min_train_rows: int = 80,
    min_eval_rows: int = 40,
    bins: int = 5,
) -> ProbabilitySeriesCalibrationResult:
    """Calibrate unseen probabilities using only an earlier calibration sample.

    Candidate selection uses a chronological split inside the calibration
    sample. The selected method is then refit on the full calibration sample
    before transforming the unseen inference probabilities.
    """
    inference = inference_prob.astype(float).clip(0.0, 1.0)
    aligned = pd.concat([calibration_prob.astype(float), calibration_target.astype(float)], axis=1).dropna()
    aligned.columns = ["prob", "target"]
    aligned["prob"] = aligned["prob"].clip(0.0, 1.0)
    aligned = _sort_by_time(aligned)
    rows = int(len(aligned))
    if rows < min_train_rows + min_eval_rows or aligned.empty or aligned["target"].nunique() < 2:
        raw_brier = _brier(aligned["prob"], aligned["target"]) if not aligned.empty else 1.0
        raw_ece = _ece(aligned["prob"], aligned["target"], bins) if not aligned.empty else 1.0
        return ProbabilitySeriesCalibrationResult(
            calibrated_probabilities=inference,
            method="identity_insufficient",
            status="calibration_sparse",
            rows=rows,
            train_rows=0,
            eval_rows=0,
            raw_brier=raw_brier,
            calibrated_brier=raw_brier,
            raw_ece=raw_ece,
            calibrated_ece=raw_ece,
            improvement_brier=0.0,
            improvement_ece=0.0,
            candidates=_candidate_frame([]),
        )

    split = max(min_train_rows, int(rows * 0.70))
    if rows - split < min_eval_rows:
        split = rows - min_eval_rows
    train = aligned.iloc[:split]
    eval_frame = aligned.iloc[split:]
    if train["target"].nunique() < 2 or eval_frame.empty:
        raw_brier = _brier(aligned["prob"], aligned["target"])
        raw_ece = _ece(aligned["prob"], aligned["target"], bins)
        return ProbabilitySeriesCalibrationResult(
            calibrated_probabilities=inference,
            method="identity_single_class",
            status="calibration_sparse",
            rows=rows,
            train_rows=int(len(train)),
            eval_rows=int(len(eval_frame)),
            raw_brier=raw_brier,
            calibrated_brier=raw_brier,
            raw_ece=raw_ece,
            calibrated_ece=raw_ece,
            improvement_brier=0.0,
            improvement_ece=0.0,
            candidates=_candidate_frame([]),
        )

    candidates: list[dict[str, object]] = [
        _candidate_metrics("identity", eval_frame["prob"], eval_frame["target"], 0.5, bins)
    ]
    platt = _fit_platt(train["prob"], train["target"], eval_frame["prob"], 0.5)
    if platt is not None:
        candidates.append(_candidate_metrics("platt", platt[0], eval_frame["target"], platt[1], bins))
    isotonic = _fit_isotonic(train["prob"], train["target"], eval_frame["prob"], 0.5)
    if isotonic is not None:
        candidates.append(_candidate_metrics("isotonic", isotonic[0], eval_frame["target"], isotonic[1], bins))

    candidate_frame = _candidate_frame(candidates)
    best = candidate_frame.sort_values(["brier", "ece", "method"], ascending=[True, True, True]).iloc[0]
    raw_row = candidate_frame[candidate_frame["method"] == "identity"].iloc[0]
    method = str(best["method"])
    transformed = _transform_probability_series(method, aligned["prob"], aligned["target"], inference)
    if transformed is None:
        transformed = inference
        method = "identity_refit_failed"
        status = "calibration_failed"
    else:
        status = _calibration_status(int(len(eval_frame)), float(best["ece"]))
    return ProbabilitySeriesCalibrationResult(
        calibrated_probabilities=transformed.astype(float).clip(0.0, 1.0),
        method=method,
        status=status,
        rows=rows,
        train_rows=int(len(train)),
        eval_rows=int(len(eval_frame)),
        raw_brier=float(raw_row["brier"]),
        calibrated_brier=float(best["brier"]),
        raw_ece=float(raw_row["ece"]),
        calibrated_ece=float(best["ece"]),
        improvement_brier=float(raw_row["brier"] - best["brier"]),
        improvement_ece=float(raw_row["ece"] - best["ece"]),
        candidates=candidate_frame,
    )


def calibration_result_to_metrics(result: ProbabilityCalibrationResult) -> dict[str, object]:
    return {
        "raw_prob_up": result.raw_latest_prob,
        "calibrated_prob_up": result.calibrated_latest_prob,
        "probability_calibration_method": result.method,
        "probability_calibration_status": result.status,
        "probability_calibration_rows": result.rows,
        "probability_calibration_train_rows": result.train_rows,
        "probability_calibration_eval_rows": result.eval_rows,
        "probability_raw_brier": result.raw_brier,
        "probability_calibrated_brier": result.calibrated_brier,
        "probability_raw_ece": result.raw_ece,
        "probability_calibrated_ece": result.calibrated_ece,
        "probability_calibration_improvement_brier": result.improvement_brier,
        "probability_calibration_improvement_ece": result.improvement_ece,
    }


def _fit_platt(
    train_prob: pd.Series,
    train_target: pd.Series,
    eval_prob: pd.Series,
    latest_prob: float,
) -> tuple[pd.Series, float] | None:
    try:
        from sklearn.linear_model import LogisticRegression  # type: ignore
    except ImportError:
        return None
    if train_target.nunique() < 2:
        return None
    model = LogisticRegression(max_iter=1000)
    model.fit(train_prob.to_numpy().reshape(-1, 1), train_target.astype(int).to_numpy())
    eval_out = pd.Series(model.predict_proba(eval_prob.to_numpy().reshape(-1, 1))[:, 1], index=eval_prob.index).clip(0.0, 1.0)
    latest_out = float(model.predict_proba(np.array([[latest_prob]], dtype=float))[0, 1])
    return eval_out, latest_out


def _fit_isotonic(
    train_prob: pd.Series,
    train_target: pd.Series,
    eval_prob: pd.Series,
    latest_prob: float,
) -> tuple[pd.Series, float] | None:
    try:
        from sklearn.isotonic import IsotonicRegression  # type: ignore
    except ImportError:
        return None
    if train_prob.nunique() < 2 or train_target.nunique() < 2:
        return None
    model = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip")
    model.fit(train_prob.astype(float).to_numpy(), train_target.astype(float).to_numpy())
    eval_out = pd.Series(model.predict(eval_prob.astype(float).to_numpy()), index=eval_prob.index).clip(0.0, 1.0)
    latest_out = float(model.predict([latest_prob])[0])
    return eval_out, latest_out


def _transform_probability_series(
    method: str,
    calibration_prob: pd.Series,
    calibration_target: pd.Series,
    inference_prob: pd.Series,
) -> pd.Series | None:
    if method == "identity":
        return inference_prob.astype(float).clip(0.0, 1.0)
    if method == "platt":
        result = _fit_platt(calibration_prob, calibration_target, inference_prob, 0.5)
        return result[0] if result is not None else None
    if method == "isotonic":
        result = _fit_isotonic(calibration_prob, calibration_target, inference_prob, 0.5)
        return result[0] if result is not None else None
    return None


def _candidate_metrics(method: str, prob: pd.Series, target: pd.Series, latest_prob: float, bins: int) -> dict[str, object]:
    clean_prob = prob.astype(float).clip(0.0, 1.0)
    clean_target = target.astype(float)
    return {
        "method": method,
        "rows": int(len(clean_prob)),
        "brier": _brier(clean_prob, clean_target),
        "ece": _ece(clean_prob, clean_target, bins),
        "latest_prob": float(np.clip(latest_prob, 0.0, 1.0)),
    }


def _candidate_frame(rows: list[dict[str, object]]) -> pd.DataFrame:
    columns = ["method", "rows", "brier", "ece", "latest_prob"]
    return pd.DataFrame(rows, columns=columns)


def _empty_result(latest_prob: float, method: str, status: str, bins: int) -> ProbabilityCalibrationResult:
    del bins
    return ProbabilityCalibrationResult(
        raw_latest_prob=float(latest_prob),
        calibrated_latest_prob=float(latest_prob),
        method=method,
        status=status,
        rows=0,
        train_rows=0,
        eval_rows=0,
        raw_brier=1.0,
        calibrated_brier=1.0,
        raw_ece=1.0,
        calibrated_ece=1.0,
        improvement_brier=0.0,
        improvement_ece=0.0,
        candidates=_candidate_frame([]),
    )


def _brier(prob: pd.Series, target: pd.Series) -> float:
    aligned = pd.concat([prob.astype(float).clip(0.0, 1.0), target.astype(float)], axis=1).dropna()
    if aligned.empty:
        return 1.0
    return float(((aligned.iloc[:, 0] - aligned.iloc[:, 1]) ** 2).mean())


def _ece(prob: pd.Series, target: pd.Series, bins: int) -> float:
    aligned = pd.concat([prob.astype(float).clip(0.0, 1.0), target.astype(float)], axis=1).dropna()
    if aligned.empty:
        return 1.0
    p = aligned.iloc[:, 0]
    y = aligned.iloc[:, 1]
    edges = np.linspace(0.0, 1.0, bins + 1)
    ece = 0.0
    for left, right in zip(edges[:-1], edges[1:]):
        mask = (p >= left) & (p <= right) if right >= 1.0 else (p >= left) & (p < right)
        if mask.any():
            ece += float(mask.mean()) * abs(float(p[mask].mean()) - float(y[mask].mean()))
    return float(ece)


def _calibration_status(eval_rows: int, ece: float) -> str:
    if eval_rows < 40:
        return "calibration_sparse"
    if ece <= 0.05:
        return "calibrated"
    if ece <= 0.10:
        return "calibration_watch"
    return "calibration_failed"


def _sort_by_time(frame: pd.DataFrame) -> pd.DataFrame:
    if isinstance(frame.index, pd.MultiIndex) and "date" in frame.index.names:
        return frame.sort_index(level="date")
    if "date" in frame.columns:
        out = frame.copy()
        out["date"] = pd.to_datetime(out["date"], errors="coerce")
        return out.sort_values("date")
    return frame.sort_index()
