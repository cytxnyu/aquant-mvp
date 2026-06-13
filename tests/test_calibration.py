from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from aquant_mvp.modeling.calibration import calibrate_probability, calibration_result_to_metrics


def test_probability_calibration_sparse_falls_back_to_identity() -> None:
    dates = pd.bdate_range("2024-01-01", periods=30)
    prob = pd.Series(np.linspace(0.35, 0.65, len(dates)), index=dates)
    target = pd.Series([0, 1] * 15, index=dates)

    result = calibrate_probability(prob, target, latest_prob=0.61)

    assert result.method == "identity_insufficient"
    assert result.status == "calibration_sparse"
    assert result.rows == 30
    assert result.train_rows == 0
    assert result.eval_rows == 0
    assert result.raw_latest_prob == pytest.approx(0.61)
    assert result.calibrated_latest_prob == pytest.approx(0.61)
    assert result.candidates.empty


def test_probability_calibration_uses_platt_and_isotonic_candidates_when_available() -> None:
    pytest.importorskip("sklearn")
    dates = pd.bdate_range("2023-01-02", periods=180)
    raw_prob = pd.Series(np.linspace(0.05, 0.95, len(dates)), index=dates)
    target = pd.Series((raw_prob > 0.52).astype(int), index=dates)

    result = calibrate_probability(raw_prob, target, latest_prob=0.82, min_train_rows=80, min_eval_rows=40)
    metrics = calibration_result_to_metrics(result)

    assert {"identity", "platt", "isotonic"}.issubset(set(result.candidates["method"]))
    assert result.method in {"identity", "platt", "isotonic"}
    assert result.status in {"calibrated", "calibration_watch", "calibration_failed"}
    assert result.train_rows >= 80
    assert result.eval_rows >= 40
    assert 0.0 <= result.calibrated_latest_prob <= 1.0
    assert result.calibrated_brier <= result.candidates["brier"].max()
    assert metrics["probability_calibration_method"] == result.method
    assert metrics["probability_calibrated_brier"] == pytest.approx(result.calibrated_brier)


def test_probability_calibration_is_chronological_and_input_order_stable() -> None:
    pytest.importorskip("sklearn")
    dates = pd.bdate_range("2023-01-02", periods=160)
    phase = np.arange(len(dates))
    raw_prob = pd.Series(np.clip(0.50 + 0.35 * np.sin(phase / 11.0), 0.02, 0.98), index=dates)
    target = pd.Series(((phase % 17) > 7).astype(int), index=dates)

    ordered = calibrate_probability(raw_prob, target, latest_prob=0.64, min_train_rows=70, min_eval_rows=35)
    shuffled_prob = raw_prob.sample(frac=1.0, random_state=7)
    shuffled_target = target.reindex(shuffled_prob.index)
    shuffled = calibrate_probability(shuffled_prob, shuffled_target, latest_prob=0.64, min_train_rows=70, min_eval_rows=35)

    assert shuffled.method == ordered.method
    assert shuffled.train_rows == ordered.train_rows
    assert shuffled.eval_rows == ordered.eval_rows
    assert shuffled.calibrated_latest_prob == pytest.approx(ordered.calibrated_latest_prob)
    assert shuffled.calibrated_brier == pytest.approx(ordered.calibrated_brier)
    assert shuffled.calibrated_ece == pytest.approx(ordered.calibrated_ece)
