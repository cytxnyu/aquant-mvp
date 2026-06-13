from __future__ import annotations

import json

import pandas as pd
import pytest

from aquant_mvp.backtest.stock import _metrics
from aquant_mvp.cli import _stock_forecast_for_horizons
from aquant_mvp.factors import FACTOR_COLUMNS, compute_factor_panel
from aquant_mvp.labels import compute_return_labels
from aquant_mvp.prediction import build_kline_forecast, build_latest_predictions, build_stock_forecast, save_kline_forecast_outputs
from aquant_mvp.strategy import score_factors


def _sample_bars(symbol: str, offset: float) -> pd.DataFrame:
    dates = pd.bdate_range("2024-01-01", periods=140)
    close = pd.Series(range(20, 160), dtype="float64") + offset
    return pd.DataFrame(
        {
            "date": dates,
            "symbol": symbol,
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": 100000.0 + offset,
            "amount": close * (100000.0 + offset),
            "turnover": 1.0 + offset / 1000,
        }
    )


def test_latest_predictions_have_rank_and_signal() -> None:
    bars = {
        "000001": _sample_bars("000001", 0),
        "000002": _sample_bars("000002", 10),
        "000003": _sample_bars("000003", 20),
    }
    factors = compute_factor_panel(bars)
    labels = compute_return_labels(bars, [5])
    scores = score_factors(factors, {"momentum_20": 0.5, "volatility_20": -0.2, "amount_mean_20": 0.3})
    result = build_latest_predictions(factors, labels, scores, FACTOR_COLUMNS, horizon=5)
    assert len(result.predictions) == 3
    assert set(result.predictions["signal"]).issubset({"候选", "观察", "回避"})
    assert result.summary["method"] in {"score_proxy", "lightgbm"}


def test_stock_backtest_drawdown_is_bounded() -> None:
    frame = pd.DataFrame(
        {
            "prob_up": [0.8, 0.7, 0.6],
            "direction_up_5d": [0, 0, 0],
            "future_return_5d": [-0.5, -0.5, -0.5],
        }
    )
    metrics = _metrics(frame, 5, "future_return_5d", "direction_up_5d")
    assert -1.0 <= metrics["max_forward_drawdown"] <= 0.0


def test_kline_forecast_outputs_valid_scenarios(tmp_path) -> None:
    bars = {
        "000630": _sample_bars("000630", 0),
        "601899": _sample_bars("601899", 10),
        "600362": _sample_bars("600362", 20),
    }
    result = build_kline_forecast(
        bars,
        "000630",
        [1, 5, 20],
        source="sample",
        days=10,
        history_days=60,
        allow_sample=True,
    )
    assert int(result.summary["requested_days"]) == 10
    assert int(result.summary["days"]) >= 20
    assert len(result.forecast) == int(result.summary["days"]) * 3
    assert len(result.intraday_forecast) == 18
    assert set(result.intraday_forecast["scenario"]) == {"bearish", "base", "bullish"}
    assert {"intraday_next_day", "1d", "5d", "20d"}.issubset(set(result.horizon_summary["horizon"]))
    assert set(result.forecast["scenario"]) == {"bearish", "base", "bullish"}
    assert result.forecast["high"].ge(result.forecast[["open", "close"]].max(axis=1)).all()
    assert result.forecast["low"].le(result.forecast[["open", "close"]].min(axis=1)).all()
    assert result.intraday_forecast["high"].ge(result.intraday_forecast[["open", "close"]].max(axis=1)).all()
    assert result.intraday_forecast["low"].le(result.intraday_forecast[["open", "close"]].min(axis=1)).all()
    assert result.forecast["p10_close"].le(result.forecast["p50_close"]).all()
    assert result.forecast["p50_close"].le(result.forecast["p90_close"]).all()
    paths = save_kline_forecast_outputs(result, tmp_path)
    assert paths["forecast_kline"].exists()
    assert paths["intraday_kline"].exists()
    assert paths["horizon_kline_summary"].exists()
    assert paths["horizon_kline_summary_json"].exists()
    assert paths["intraday_kline_png"].exists()
    assert paths["forecast_kline_html"].exists()
    assert paths["stock_prediction_report"].exists()
    assert paths["stock_evidence_audit"].exists()
    assert paths["stock_evidence_audit_json"].exists()
    assert paths["stock_evidence_audit_md"].exists()
    audit_payload = json.loads(paths["stock_evidence_audit_json"].read_text(encoding="utf-8"))
    assert audit_payload["symbol"] == "000630"
    assert "walk_forward_evidence" in audit_payload["failed_checks"]
    html = paths["forecast_kline_html"].read_text(encoding="utf-8")
    assert "Next-session Intraday Forecast" in html
    assert "1/5/20 Day Forecast Nodes" in html


def test_kline_forecast_can_reuse_superset_stock_forecast() -> None:
    bars = {
        "000630": _sample_bars("000630", 0),
        "601899": _sample_bars("601899", 10),
        "600362": _sample_bars("600362", 20),
    }
    superset = build_stock_forecast(bars, "000630", [1, 5, 8, 20, 60], source="sample", allow_sample=True)
    filtered = _stock_forecast_for_horizons(superset, [1, 5, 20])
    assert filtered.forecast["horizon_days"].astype(int).tolist() == [1, 5, 20]
    assert set(filtered.summary["internal_horizons_available"]) == {1, 5, 8, 20, 60}
    result = build_kline_forecast(
        bars,
        "000630",
        [1, 5, 20],
        source="sample",
        days=8,
        history_days=60,
        allow_sample=True,
        stock_forecast_override=superset,
    )
    assert result.stock_forecast is superset
    assert int(result.summary["days"]) >= 20
    missing = build_stock_forecast(bars, "000630", [1, 5, 20], source="sample", allow_sample=True)
    with pytest.raises(ValueError, match="missing K-line horizons"):
        build_kline_forecast(
            bars,
            "000630",
            [1, 5, 20],
            source="sample",
            days=8,
            history_days=60,
            allow_sample=True,
            stock_forecast_override=missing,
        )
