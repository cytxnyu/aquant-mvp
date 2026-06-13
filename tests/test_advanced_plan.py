from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from aquant_mvp.broker import PaperBroker, build_order_plan_from_targets
from aquant_mvp.config import DataConfig, RiskConfig, StrategyConfig
from aquant_mvp.data import add_source_audit_columns, audit_point_in_time_tables
from aquant_mvp.events import (
    analyze_event_impact,
    audit_event_coverage,
    build_event_store,
    build_similar_event_report,
    commodity_symbol_map,
    discover_text_intelligence,
    sync_commodity_events,
    sync_public_events,
    write_event_impact_outputs,
    write_similar_event_outputs,
    write_text_intelligence_report,
)
from aquant_mvp.factors import FACTOR_COLUMNS, analyze_factor_trust, build_factor_registry
from aquant_mvp.analysis import analyze_factors, attribute_portfolio_events, evaluate_walk_forward_slices, summarize_model_registry
from aquant_mvp.features import build_point_in_time_feature_store
from aquant_mvp.labels import compute_return_labels
from aquant_mvp.foundations import discover_foundations
from aquant_mvp.modeling import discover_model_bases, train_model, train_walk_forward
from aquant_mvp.modeling import register_model
from aquant_mvp.modeling.walk_forward import _trust_status
from aquant_mvp.prediction import build_stock_forecast, build_stock_trust_gate_report, explain_stock_forecast, write_stock_trust_gate_outputs
from aquant_mvp.prediction.stock import _forecast_trust_status, _load_walk_forward_evidence, _match_walk_forward_evidence
from aquant_mvp.risk import EventRiskConfig, TradingRiskConfig, apply_event_risk_guard, check_order_plan, event_context_by_symbol
from aquant_mvp.sources import (
    discover_domestic_sources,
    fetch_cninfo_announcements_direct,
    fetch_official_public_events,
    official_public_source_ids,
    write_source_coverage,
)
from aquant_mvp.storage import LocalWarehouse
from aquant_mvp.strategy import apply_portfolio_constraints, write_portfolio_constraint_outputs
from aquant_mvp.tooling import discover_tools
from aquant_mvp.universe import build_theme_universe, symbol_theme_membership, symbols_for_themes, theme_universe_summary
from aquant_mvp.vendors import TushareFreeAdapter, VendorNotConfigured
from aquant_mvp import cli as cli_module


def _bars(symbol: str, offset: float = 0.0, periods: int = 220) -> pd.DataFrame:
    dates = pd.bdate_range("2024-01-01", periods=periods)
    trend = pd.Series(range(periods), dtype="float64") * (0.03 + offset / 10000)
    cycle = pd.Series(range(periods), dtype="float64").map(lambda value: 0.4 * ((value % 20) / 20))
    close = 20 + offset + trend + cycle
    return pd.DataFrame(
        {
            "date": dates,
            "symbol": symbol,
            "open": close * 0.998,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": 100000.0 + offset,
            "amount": close * (100000.0 + offset),
            "turnover": 1.0 + offset / 1000,
        }
    )


def test_hot_theme_universe_contains_required_themes() -> None:
    universe = build_theme_universe("hot")
    assert universe["theme"].nunique() >= 20
    assert universe["symbol"].nunique() >= 500
    assert "601899" in set(universe["symbol"])
    assert universe["symbol"].str.fullmatch(r"\d{6}").all()
    assert set(build_theme_universe("core-hot")["theme"]).issubset(set(universe["theme"]))
    assert set(build_theme_universe("professional")["theme"]).issubset(set(universe["theme"]))
    assert symbols_for_themes("mega-hot") == symbols_for_themes("hot")
    assert len(symbols_for_themes("professional")) >= 100

    summary = theme_universe_summary(universe)
    membership = symbol_theme_membership(universe)
    assert not summary.empty
    assert not membership.empty
    assert membership["theme_count"].max() >= 2


def test_foundation_and_tool_registries_cover_external_bases() -> None:
    foundations = discover_foundations()
    required_foundations = {"qlib", "backtrader", "vectorbt", "lightgbm", "xgboost", "catboost", "akshare", "baostock", "qmt_xtquant"}
    assert required_foundations.issubset(set(foundations["foundation_id"]))
    assert {"sentence_transformers", "transformers_text_models", "faiss", "lancedb"}.issubset(set(foundations["foundation_id"]))
    assert {"native_supported", "candidate_adapter", "read_only_supported_live_blocked"}.intersection(set(foundations["integration_status"]))

    tools = discover_tools()
    required_tools = {"foundation_registry", "text_intelligence_registry", "tool_registry", "mega_hot_universe", "stock_forecast", "paper_trade", "qmt_readonly", "live_trade_blocker"}
    assert required_tools.issubset(set(tools["tool_id"]))
    live_blocker = tools[tools["tool_id"] == "live_trade_blocker"].iloc[0]
    assert live_blocker["live_trading_allowed"] is False or live_blocker["live_trading_allowed"] == 0

    model_bases = discover_model_bases()
    assert {"factor_score", "lightgbm", "xgboost", "catboost", "sklearn_linear"}.issubset(set(model_bases["model_base_id"]))
    assert bool(model_bases[model_bases["model_base_id"] == "factor_score"]["available"].iloc[0]) is True
    assert {"train_model_supported", "walk_forward_supported", "fallback_policy"}.issubset(model_bases.columns)

    text_bases = discover_text_intelligence()
    required_text_bases = {
        "sentence_transformers_bge_m3",
        "transformers_finbert_roberta",
        "faiss_vector_store",
        "lancedb_vector_store",
        "qwen_local_summary",
        "deepseek_local_summary",
    }
    assert required_text_bases.issubset(set(text_bases["capability_id"]))
    assert {"fallback_policy", "can_enter_event_factors", "decision_rule"}.issubset(text_bases.columns)
    assert text_bases["can_enter_event_factors"].eq(False).all()


def test_text_intelligence_report_is_auditable(tmp_path: Path) -> None:
    frame = discover_text_intelligence()
    paths = write_text_intelligence_report(tmp_path, frame)
    assert paths["csv"].exists()
    assert paths["md"].exists()
    text = paths["md"].read_text(encoding="utf-8")
    assert "Text Intelligence Registry" in text
    assert "do not issue trading instructions" in text
    assert "sentence_transformers_bge_m3" in text


def test_similar_event_report_is_pit_safe_and_auditable(tmp_path: Path) -> None:
    raw = pd.DataFrame(
        [
            {
                "source": "cninfo_disclosure",
                "published_at": "2024-01-03",
                "symbol": "000630",
                "related_symbols": "000630",
                "title": "000630 copper capacity expansion announcement",
                "summary": "copper capacity expansion order contract and production progress",
                "source_url": "https://www.cninfo.com.cn/a",
                "quality_flag": "test",
            },
            {
                "source": "eastmoney_stock_news",
                "published_at": "2024-01-10",
                "symbol": "000630",
                "related_symbols": "000630",
                "title": "000630 copper production progress and order contract",
                "summary": "capacity expansion and copper order contract remain the key event",
                "source_url": "https://finance.eastmoney.com/a",
                "quality_flag": "test",
            },
            {
                "source": "cninfo_disclosure",
                "published_at": "2024-02-20",
                "symbol": "000630",
                "related_symbols": "000630",
                "title": "000630 copper capacity expansion order contract update",
                "summary": "production progress and order contract update for copper business",
                "source_url": "https://www.cninfo.com.cn/b",
                "quality_flag": "test",
            },
        ]
    )
    event_result = build_event_store(raw, ["000630"])
    similar = build_similar_event_report(
        event_result.event_store,
        bars_by_symbol={"000630": _bars("000630", periods=100)},
        symbol="000630",
        horizons=(1, 5, 20),
        query_events=1,
        top_k=3,
        min_similarity=0.01,
    )
    assert not similar.matches.empty
    assert similar.matches["pit_ok"].astype(bool).all()
    assert (
        pd.to_datetime(similar.matches["match_published_at"])
        < pd.to_datetime(similar.matches["query_published_at"])
    ).all()
    assert bool(similar.matches["return_available_1d"].any())
    assert similar.summary["can_enter_event_factors"] is False
    assert similar.summary["known_return_rows_1d"] >= 1
    assert "Similar Event Evidence Report" in similar.markdown
    paths = write_similar_event_outputs(tmp_path, similar)
    assert paths["csv"].exists()
    assert paths["json"].exists()
    assert paths["md"].exists()


def test_event_impact_study_builds_cohorts_and_pit_priors(tmp_path: Path) -> None:
    dates = pd.bdate_range("2024-01-01", periods=90)
    close = pd.Series(range(90), dtype="float64") * 0.10 + 10.0
    bars = {
        "000630": pd.DataFrame(
            {
                "date": dates,
                "symbol": "000630",
                "open": close,
                "high": close * 1.01,
                "low": close * 0.99,
                "close": close,
                "volume": 100000.0,
                "amount": close * 100000.0,
                "turnover": 1.0,
            }
        )
    }
    raw = pd.DataFrame(
        [
            {
                "source": "cninfo_disclosure",
                "published_at": date,
                "symbol": "000630",
                "related_symbols": "000630",
                "title": f"000630 order contract event {idx}",
                "summary": "order contract and production progress",
                "source_url": f"https://www.cninfo.com.cn/{idx}",
                "quality_flag": "test",
            }
            for idx, date in enumerate(pd.bdate_range("2024-01-03", periods=12, freq="5B"))
        ]
    )
    event_result = build_event_store(raw, ["000630"])
    study = analyze_event_impact(event_result.event_store, bars, horizons=(1, 5), min_prior_rows=2)
    assert not study.event_returns.empty
    assert not study.cohorts.empty
    assert not study.pit_priors.empty
    assert {"event_type", "event_type_sentiment"}.issubset(set(study.cohorts["cohort_level"]))
    assert study.summary["no_future_leakage"] is True
    assert study.pit_priors["no_future_leakage"].astype(bool).all()
    assert study.pit_priors["pit_ready"].astype(bool).any()
    ready = study.pit_priors[study.pit_priors["pit_ready"].astype(bool)].iloc[0]
    assert ready["prior_sample_count"] >= 2
    assert pd.Timestamp(ready["prior_outcome_cutoff"]) < pd.Timestamp(ready["published_at"])
    assert study.cohorts["can_enter_trusted_model"].eq(False).all()
    assert "Event Impact Study" in study.markdown
    paths = write_event_impact_outputs(tmp_path, study)
    assert paths["event_returns"].exists()
    assert paths["cohorts"].exists()
    assert paths["pit_priors"].exists()
    assert paths["md"].exists()


def test_stock_forecast_outputs_required_fields_with_sample_opt_in() -> None:
    bars = {
        "601899": _bars("601899", 0),
        "603993": _bars("603993", 10),
        "600547": _bars("600547", 20),
    }
    result = build_stock_forecast(bars, "601899", [1, 5, 20], source="sample", allow_sample=True)
    assert set(result.forecast["horizon_days"]) == {1, 5, 20}
    required = {
        "prob_up",
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
        "conformal_target_coverage",
        "conformal_interval_half_width",
        "conformal_status",
        "risk_flags",
        "top_factor_contributors",
        "model_id",
        "data_version",
        "universe_symbol_count",
        "minimum_trusted_symbols",
        "walk_forward_status",
        "walk_forward_gate_reasons",
        "raw_prob_up",
        "calibrated_prob_up",
        "probability_calibration_method",
        "probability_calibration_status",
        "probability_raw_brier",
        "probability_calibrated_brier",
        "probability_raw_ece",
        "probability_calibrated_ece",
        "probability_calibration_improvement_brier",
        "probability_calibration_improvement_ece",
        "calibration_rows",
        "calibration_ece",
        "calibration_status",
    }
    assert required.issubset(result.forecast.columns)
    assert result.forecast["prob_up"].between(0, 1).all()
    assert result.forecast["raw_prob_up"].between(0, 1).all()
    assert result.forecast["calibrated_prob_up"].between(0, 1).all()
    assert (result.forecast["prob_up"] == result.forecast["calibrated_prob_up"]).all()
    assert result.forecast["return_p10"].le(result.forecast["return_p50"]).all()
    assert result.forecast["return_p50"].le(result.forecast["return_p90"]).all()
    assert set(result.forecast["conformal_status"]).issubset({"conformal_ready", "conformal_sparse"})
    gate_report = build_stock_trust_gate_report(result.forecast, source="sample", news_summary={"with_news": False})
    assert {"sample_data_block", "minimum_universe_size", "walk_forward_trusted"}.issubset(set(gate_report.gates["gate"]))
    assert gate_report.summary["blocking_gate_count"] > 0
    assert "not investment advice" in gate_report.markdown


def test_stock_trust_gate_outputs_are_written(tmp_path: Path) -> None:
    bars = {
        "000630": _bars("000630", 0),
        "601899": _bars("601899", 10),
        "600362": _bars("600362", 20),
    }
    forecast = build_stock_forecast(bars, "000630", [5], source="sample", allow_sample=True)
    gates = build_stock_trust_gate_report(forecast.forecast, source="sample", news_summary={"with_news": True, "event_rows": 2, "event_factor_rows": 1})
    paths = write_stock_trust_gate_outputs(tmp_path, gates)
    assert paths["csv"].exists()
    assert paths["json"].exists()
    assert paths["md"].exists()
    assert "Stock Trust Gate Report" in paths["md"].read_text(encoding="utf-8")


def test_stock_forecast_requires_walk_forward_evidence_for_trusted(tmp_path: Path) -> None:
    registry_dir = tmp_path / "registry"
    registry_dir.mkdir()
    records = [
        {
            "model_id": "walk_forward_factor_score_h5",
            "model_type": "factor_score",
            "model_family": "walk_forward_validation",
            "horizon_days": 5,
            "registered_at": "2026-01-01T00:00:00",
            "metrics": {
                "trust_status": "weak",
                "trust_gate_reasons": "auc_above_052",
                "rows": 6000,
                "auc": 0.51,
                "brier": 0.24,
                "rank_ic": 0.02,
            },
        }
    ]
    (registry_dir / "model_registry.json").write_text(json.dumps(records), encoding="utf-8")
    evidence = _load_walk_forward_evidence(registry_dir)
    matched = _match_walk_forward_evidence(evidence, "factor_score", 5)
    assert matched["trust_status"] == "weak"
    row = {
        "confidence": 0.9,
        "sample_rank_ic": 0.1,
        "sample_oos_brier": 0.2,
        "calibration_status": "calibrated",
        "calibration_ece": 0.02,
        "conformal_status": "conformal_ready",
    }
    quality = {"method": "score_baseline"}
    assert _forecast_trust_status(row, quality, 205, "free_real", matched) == "weak"
    assert _forecast_trust_status(dict(row), quality, 205, "free_real", {}) == "model_failed"
    trusted_evidence = dict(matched, trust_status="trusted")
    assert _forecast_trust_status(dict(row), quality, 205, "free_real", trusted_evidence) == "trusted"
    failed_calibration = dict(row, calibration_status="calibration_failed", calibration_ece=0.20)
    assert _forecast_trust_status(failed_calibration, quality, 205, "free_real", trusted_evidence) == "model_failed"
    sparse_calibration = dict(row, calibration_status="calibration_sparse", calibration_ece=0.03)
    assert _forecast_trust_status(sparse_calibration, quality, 205, "free_real", trusted_evidence) == "weak"
    sparse_conformal = dict(row, conformal_status="conformal_sparse")
    assert _forecast_trust_status(sparse_conformal, quality, 205, "free_real", trusted_evidence) == "weak"


def test_risk_blocks_blacklist_and_paper_broker_fills() -> None:
    prices = pd.Series({"601899": 20.0, "603993": 10.0})
    targets = pd.Series({"601899": 0.5, "603993": 0.1})
    plan = build_order_plan_from_targets(targets, prices, equity=100000, trade_date="2026-06-11")
    decision = check_order_plan(
        plan.orders,
        TradingRiskConfig(max_single_weight=0.2, max_order_value=30000, blacklist=("601899",)),
        equity=100000,
    )
    assert not decision.passed
    assert "blacklisted_symbol" in decision.reasons

    safe_plan = build_order_plan_from_targets(pd.Series({"603993": 0.1}), prices, equity=100000, trade_date="2026-06-11")
    report = PaperBroker(initial_cash=100000).submit(safe_plan)
    assert not report.executions.empty
    assert set(report.executions["status"]) == {"FILLED"}


def test_portfolio_constraints_cap_theme_single_and_blacklist(tmp_path: Path) -> None:
    dates = pd.to_datetime(["2024-03-01", "2024-03-08"])
    targets = pd.DataFrame(
        [
            {"000630": 0.35, "601899": 0.35, "300308": 0.30},
            {"000630": 0.10, "601899": 0.45, "300308": 0.45},
        ],
        index=dates,
    )
    theme_membership = pd.DataFrame(
        [
            {"symbol": "000630", "themes": "metals_energy_metals"},
            {"symbol": "601899", "themes": "metals_energy_metals"},
            {"symbol": "300308", "themes": "ai_compute_semiconductor"},
        ]
    )
    result = apply_portfolio_constraints(
        targets,
        bars_by_symbol={"000630": _bars("000630", periods=80), "601899": _bars("601899", 5, periods=80), "300308": _bars("300308", 10, periods=80)},
        strategy_config=StrategyConfig(max_single_weight=0.30, max_theme_weight=0.40, max_turnover=2.0, volatility_target=0.0),
        risk_config=RiskConfig(max_single_weight=0.25, blacklist=["300308"]),
        theme_membership=theme_membership,
    )

    assert result.adjusted_targets[["000630", "601899"]].sum(axis=1).le(0.4000001).all()
    assert result.adjusted_targets.max(axis=1).le(0.2500001).all()
    assert result.adjusted_targets["300308"].eq(0.0).all()
    assert {"blacklist", "max_single_weight", "max_theme_weight"}.issubset(set(result.report["constraint"]))
    paths = write_portfolio_constraint_outputs(tmp_path, result)
    assert paths["report"].exists()
    assert paths["summary"].exists()
    assert "Portfolio Constraint Report" in paths["markdown"].read_text(encoding="utf-8")


def test_registry_and_warehouse_write(tmp_path: Path) -> None:
    registry_record = register_model(tmp_path / "registry", {"model_id": "demo", "metrics": {"rank_ic": 0.1}})
    assert registry_record["model_id"] == "demo"
    assert (tmp_path / "registry" / "model_registry.json").exists()

    warehouse = LocalWarehouse(tmp_path / "warehouse", file_format="csv")
    result = warehouse.write_table("daily_bar", _bars("601899", periods=5))
    assert result.rows == 5
    assert result.path.exists()
    assert not warehouse.read_table("daily_bar").empty


def test_train_model_records_requested_effective_and_fallback(tmp_path: Path) -> None:
    bars = {
        "000630": _bars("000630", periods=180),
        "601899": _bars("601899", 10, periods=180),
        "600362": _bars("600362", 20, periods=180),
    }
    summary = train_model(
        bars,
        model_type="unsupported_model_base",
        horizons=[5],
        output_dir=tmp_path / "train",
        registry_dir=tmp_path / "registry",
    )
    record = summary["records"][0]
    assert record["requested_model_type"] == "unsupported_model_base"
    assert record["effective_model_type"] == "factor_score"
    assert record["model_base_status"] == "fallback"
    assert record["fallback_reason"]


def test_tushare_free_adapter_requires_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TUSHARE_TOKEN", raising=False)
    with pytest.raises(VendorNotConfigured):
        TushareFreeAdapter().fetch_daily_bars("601899", "2024-01-01", "2024-02-01", "qfq")


def test_source_discovery_and_data_audit(tmp_path: Path) -> None:
    sources = discover_domestic_sources()
    assert {"akshare", "baostock", "cninfo", "cninfo_direct"}.issubset(set(sources["source"]))
    assert {"exchange_regulator", "macro_policy", "commodity_exchange"}.issubset(set(sources["source_group"]))
    assert {"sse_public", "szse_public", "csrc_public", "shfe_public", "pbc_public"}.issubset(set(sources["source"]))
    assert sources[sources["source"] == "sse_public"]["ready_for_event_factor"].iloc[0] in {True, 1}
    assert sources[sources["source"] == "sse_public"]["requires_followup"].iloc[0] in {True, 1}
    assert sources[sources["source"] == "cninfo_direct"]["ready_for_event_factor"].iloc[0] in {True, 1}
    assert sources[sources["source"] == "shfe_public"]["implementation_status"].iloc[0] == "partial_via_akshare_sina_futures"
    write_source_coverage(tmp_path, sources)
    assert (tmp_path / "source_gap_report.md").exists()
    assert "Missing sources are explicit gaps" in (tmp_path / "source_gap_report.md").read_text(encoding="utf-8")

    audited = add_source_audit_columns(_bars("601899", periods=10), "sample")
    result = audit_point_in_time_tables({"daily_bar": audited}, strict_pit=True)
    assert not result.summary.empty
    assert "pit_ready" in result.summary.columns
    raw_event = pd.DataFrame(
        [{"source": "akshare_futures_main_sina", "quality_flag": "commodity_shock:copper", "title": "event"}]
    )
    audited_event = add_source_audit_columns(raw_event, "akshare", quality_flag="raw_event")
    assert audited_event["source"].iloc[0] == "akshare_futures_main_sina"
    assert audited_event["quality_flag"].iloc[0] == "commodity_shock:copper"
    assert audited_event["audit_source"].iloc[0] == "akshare"
    assert audited_event["audit_quality_flag"].iloc[0] == "raw_event"


def test_direct_cninfo_source_maps_public_announcements() -> None:
    def fake_post(url: str, payload: dict[str, str], headers: dict[str, str], timeout: int) -> dict[str, object]:
        assert "cninfo.com.cn" in url
        assert payload["stock"] == "000630"
        assert headers["Origin"] == "http://www.cninfo.com.cn"
        assert timeout > 0
        return {
            "announcements": [
                {
                    "secCode": "000630",
                    "announcementTitle": "<em>000630 profit forecast announcement</em>",
                    "announcementTime": 1717372800000,
                    "adjunctUrl": "finalpage/2024-06-03/test.PDF",
                }
            ]
        }

    result = fetch_cninfo_announcements_direct(
        ["000630"],
        "2024-01-01",
        "2024-12-31",
        http_post=fake_post,
    )
    assert result.warnings == []
    assert len(result.events) == 1
    row = result.events.iloc[0]
    assert row["source"] == "cninfo_direct"
    assert row["symbol"] == "000630"
    assert str(row["source_url"]).startswith("http://static.cninfo.com.cn/finalpage/")

    event_result = build_event_store(result.events, ["000630"])
    assert event_result.event_store["source_reliability"].iloc[0] >= 0.90


def test_direct_cninfo_can_extract_html_announcement_text() -> None:
    def fake_post(url: str, payload: dict[str, str], headers: dict[str, str], timeout: int) -> dict[str, object]:
        return {
            "announcements": [
                {
                    "secCode": "000630",
                    "announcementTitle": "000630 annual report",
                    "announcementTime": 1717372800000,
                    "announcementUrl": "https://static.cninfo.com.cn/finalpage/test.html",
                }
            ]
        }

    def fake_get(url: str, headers: dict[str, str], timeout: int) -> bytes:
        assert url.endswith("test.html")
        return "<html><body><h1>Annual Report</h1><p>Revenue increased and risk factors disclosed.</p></body></html>".encode()

    result = fetch_cninfo_announcements_direct(
        ["000630"],
        "2024-01-01",
        "2024-12-31",
        fetch_text=True,
        http_post=fake_post,
        http_get=fake_get,
    )
    assert result.warnings == []
    row = result.events.iloc[0]
    assert row["source_text_status"] == "ok_html"
    assert int(row["source_text_length"]) > 20
    assert "Revenue increased" in row["summary"]

    event_result = build_event_store(result.events, ["000630"])
    event_row = event_result.event_store.iloc[0]
    assert event_row["source_text_status"] == "ok_html"
    assert int(event_row["source_text_length"]) > 20
    assert "text=ok_html" in event_result.evidence_markdown
    assert "Recent Major Announcement Summary" in event_result.evidence_markdown


def test_direct_cninfo_failure_returns_auditable_empty_schema() -> None:
    def failing_post(url: str, payload: dict[str, str], headers: dict[str, str], timeout: int) -> dict[str, object]:
        raise RuntimeError("blocked")

    result = fetch_cninfo_announcements_direct(
        ["000630"],
        "2024-01-01",
        "2024-12-31",
        http_post=failing_post,
    )
    assert result.events.empty
    assert {"source", "source_url", "published_at", "symbol", "related_symbols", "title", "summary", "quality_flag"}.issubset(result.events.columns)
    assert result.warnings and "cninfo_direct failed" in result.warnings[0]


def test_event_store_accepts_empty_direct_source_schema() -> None:
    result = fetch_cninfo_announcements_direct(
        ["000630"],
        "2024-01-01",
        "2024-12-31",
        http_post=lambda _url, _payload, _headers, _timeout: {"announcements": []},
    )
    event_result = build_event_store(result.events, ["000630"])
    assert event_result.event_store.empty
    assert {"event_id", "source", "raw_hash"}.issubset(event_result.event_store.columns)
    assert event_result.warnings == ["event_store_empty"]


def test_official_public_source_fetches_url_backed_events() -> None:
    assert "csrc_public" in official_public_source_ids()

    def fake_get(url: str, headers: dict[str, str], timeout: int) -> bytes:
        assert "csrc.gov.cn" in url
        assert headers["User-Agent"].startswith("Mozilla")
        assert timeout > 0
        return """
        <html><body>
          <div class="item"><span>2026年06月12日</span>
            <a href="/csrc/c100028/test-policy.html">支持半导体和人工智能产业政策发布 300308</a>
          </div>
          <div class="item"><span>2026-06-11</span>
            <a href="/csrc/c100035/test-risk.html">对上市公司监管问询 000630</a>
          </div>
        </body></html>
        """.encode("utf-8")

    result = fetch_official_public_events(
        ["000630", "300308"],
        "2026-06-01",
        "2026-06-30",
        source="csrc_public",
        http_get=fake_get,
    )
    assert result.warnings == []
    assert len(result.events) >= 2
    assert set(result.events["source"]) == {"csrc_public"}
    assert result.events["source_url"].astype(str).str.startswith("https://www.csrc.gov.cn/").all()
    assert "000630" in ";".join(result.events["related_symbols"].astype(str))
    assert "300308" in ";".join(result.events["related_symbols"].astype(str))
    assert result.events["quality_flag"].astype(str).str.contains("official_public:csrc").all()

    event_result = build_event_store(result.events, ["000630", "300308"])
    assert {"000630", "300308"}.issubset(set(event_result.event_store["symbol"]))
    assert event_result.event_store["source_reliability"].min() >= 0.85
    assert set(event_result.event_store["entity_link_method"]).issubset({"provided_related_symbols", "code_mention", "explicit_symbol"})
    assert not event_result.event_factors.empty


def test_official_public_source_can_attach_body_text() -> None:
    def fake_get(url: str, headers: dict[str, str], timeout: int) -> bytes:
        assert timeout > 0
        if url.endswith("common_list.shtml"):
            return """
            <html><body>
              <span>2026年06月12日</span>
              <a href="/csrc/c100028/policy-body.html">支持人工智能产业政策 300308</a>
            </body></html>
            """.encode("utf-8")
        if url.endswith("policy-body.html"):
            return """
            <html><body>
              <h1>支持人工智能产业政策 300308</h1>
              <p>政策正文披露，支持算力、半导体、先进制造等方向，并提示投资风险。</p>
            </body></html>
            """.encode("utf-8")
        return b""

    result = fetch_official_public_events(
        ["300308"],
        "2026-06-01",
        "2026-06-30",
        source="csrc_public",
        fetch_text=True,
        http_get=fake_get,
    )
    assert result.warnings == []
    row = result.events.iloc[0]
    assert row["source_text_status"] == "official_text_ok_html"
    assert int(row["source_text_length"]) > 30
    assert row["source_text_hash"]
    assert "advanced" not in str(row["summary"]).lower()
    assert "300308" in row["related_symbols"]

    event_result = build_event_store(result.events, ["300308"])
    event_row = event_result.event_store.iloc[0]
    assert event_row["source_text_status"] == "official_text_ok_html"
    assert int(event_row["source_text_length"]) > 30
    assert "text=official_text_ok_html" in event_result.evidence_markdown


def test_official_public_text_failure_keeps_audited_headline() -> None:
    def fake_get(url: str, headers: dict[str, str], timeout: int) -> bytes:
        if url.endswith("common_list.shtml"):
            return """
            <html><body>
              <span>2026-06-11</span>
              <a href="/csrc/c100035/risk-body.html">对上市公司监管问询 000630</a>
            </body></html>
            """.encode("utf-8")
        raise RuntimeError("body blocked")

    result = fetch_official_public_events(
        ["000630"],
        "2026-06-01",
        "2026-06-30",
        source="csrc_public",
        fetch_text=True,
        http_get=fake_get,
    )
    assert len(result.events) == 1
    assert result.warnings and "official text download failed" in result.warnings[0]
    row = result.events.iloc[0]
    assert row["source_text_status"].startswith("official_text_download_failed")
    assert int(row["source_text_length"]) == 0
    assert row["source_text_hash"] == ""
    assert "监管问询" in row["title"]

    event_result = build_event_store(result.events, ["000630"])
    assert len(event_result.event_store) == 1
    assert event_result.event_store["source_text_status"].iloc[0].startswith("official_text_download_failed")


def test_official_public_source_supports_bounded_pagination() -> None:
    seen_urls: list[str] = []

    def fake_get(url: str, headers: dict[str, str], timeout: int) -> bytes:
        seen_urls.append(url)
        if url.endswith("common_list.shtml"):
            return """
            <html><body>
              <span>2026-06-12</span>
              <a href="/csrc/c100028/page0.html">第一页政策 300308</a>
            </body></html>
            """.encode("utf-8")
        if url.endswith("common_list_1.shtml"):
            return """
            <html><body>
              <span>2026-06-10</span>
              <a href="/csrc/c100028/page1.html">第二页监管问询 000630</a>
            </body></html>
            """.encode("utf-8")
        return b""

    result = fetch_official_public_events(
        ["000630", "300308"],
        "2026-06-01",
        "2026-06-30",
        source="csrc_public",
        max_pages_per_seed=2,
        http_get=fake_get,
    )
    assert result.warnings == []
    assert any(url.endswith("common_list_1.shtml") for url in seen_urls)
    assert {"000630", "300308"}.issubset(set(";".join(result.events["related_symbols"].astype(str)).split(";")))
    assert result.events["quality_flag"].astype(str).str.contains("page_").all()

    event_result = build_event_store(result.events, ["000630", "300308"])
    assert {"000630", "300308"}.issubset(set(event_result.event_store["symbol"]))


def test_official_public_pagination_failure_is_warning_only() -> None:
    def fake_get(url: str, headers: dict[str, str], timeout: int) -> bytes:
        if url.endswith("common_list.shtml"):
            return """
            <html><body>
              <span>2026-06-12</span>
              <a href="/csrc/c100028/page0.html">第一页政策 300308</a>
            </body></html>
            """.encode("utf-8")
        raise RuntimeError("page blocked")

    result = fetch_official_public_events(
        ["300308"],
        "2026-06-01",
        "2026-06-30",
        source="csrc_public",
        max_pages_per_seed=2,
        http_get=fake_get,
    )
    assert len(result.events) == 1
    assert result.warnings and "official page fetch failed page=2" in result.warnings[0]
    assert set(result.events["related_symbols"]) == {"300308"}


def test_official_public_source_classifies_structured_event_types() -> None:
    def fake_get(url: str, headers: dict[str, str], timeout: int) -> bytes:
        if "c100028" in url:
            return """
            <html><body>
              <span>2026-06-12</span>
              <a href="/csrc/c100028/penalty.html">regulatory penalty for listed company 000630</a>
              <span>2026-06-11</span>
              <a href="/csrc/c100028/buyback.html">share repurchase and dividend plan 300308</a>
            </body></html>
            """.encode("utf-8")
        return """
        <html><body>
          <span>2026-06-10</span>
          <a href="/csrc/c100035/export.html">export control risk notice 000630</a>
        </body></html>
        """.encode("utf-8")

    result = fetch_official_public_events(
        ["000630", "300308"],
        "2026-06-01",
        "2026-06-30",
        source="csrc_public",
        http_get=fake_get,
    )
    by_title = result.events.set_index("title")
    penalty = by_title.loc["regulatory penalty for listed company 000630"]
    buyback = by_title.loc["share repurchase and dividend plan 300308"]
    export = by_title.loc["export control risk notice 000630"]
    assert penalty["event_type"] == "regulatory_penalty"
    assert penalty["sentiment"] == "negative"
    assert float(penalty["impact_score"]) < -0.5
    assert buyback["event_type"] == "buyback_dividend"
    assert buyback["sentiment"] == "positive"
    assert export["event_type"] == "export_control"

    event_result = build_event_store(result.events, ["000630", "300308"])
    risk_counts = event_result.event_factors.groupby("symbol")["event_risk_count"].max().to_dict()
    assert risk_counts["000630"] >= 2
    assert risk_counts.get("300308", 0) == 0


def test_cli_event_source_router_preserves_direct_cninfo() -> None:
    class DummyConfig:
        class data:
            source = "baostock"

    class DummyArgs:
        allow_sample = False

    assert cli_module._event_source_from_data_source(DummyConfig(), DummyArgs(), "cninfo_direct") == "cninfo_direct"
    assert cli_module._event_source_from_data_source(DummyConfig(), DummyArgs(), "baostock") == "akshare"
    assert cli_module._event_source_from_data_source(DummyConfig(), DummyArgs(), "csrc_public") == "csrc_public"


def test_feature_store_walk_forward_and_explanation(tmp_path: Path) -> None:
    bars = {
        "601899": _bars("601899", 0),
        "603993": _bars("603993", 10),
        "600547": _bars("600547", 20),
    }
    store = build_point_in_time_feature_store(bars, [1, 5], "sample")
    assert not store.features.empty
    assert store.metadata["feature_count"] > 50

    latest_event_date = pd.Timestamp(bars["601899"]["date"].max()).date().isoformat()
    raw_events, _warnings = sync_public_events(list(bars), "2024-01-01", latest_event_date, source="sample")
    event_result = build_event_store(raw_events, list(bars))
    event_store = build_point_in_time_feature_store(bars, [1, 5], "sample", event_factors=event_result.event_factors)
    assert event_store.metadata["event_feature_count"] > 0
    assert "event_impact_score" in event_store.features.columns
    event_forecast = build_stock_forecast(
        bars,
        "601899",
        [1],
        source="sample",
        model_type="event_aware_ensemble",
        allow_sample=True,
        event_factors=event_result.event_factors,
    )
    assert int(event_forecast.forecast["event_feature_count"].iloc[0]) > 0
    assert "event_" in str(event_forecast.forecast["top_factor_contributors"].iloc[0])

    walk = train_walk_forward(
        bars,
        "factor_score",
        [1],
        tmp_path / "walk",
        tmp_path / "registry",
        min_symbols=2,
        train_years=1,
        test_months=2,
    )
    assert not walk.metrics.empty
    assert "trust_status" in walk.metrics.columns
    assert {"amount_mean_20", "cs_amount_rank_20", "market_breadth", "market_mean_return"}.issubset(walk.predictions.columns)

    event_walk = train_walk_forward(
        bars,
        "event_aware_ensemble",
        [1],
        tmp_path / "walk_event",
        tmp_path / "registry_event",
        min_symbols=2,
        train_years=1,
        test_months=2,
        event_factors=event_result.event_factors,
    )
    assert event_walk.summary["event_feature_count"] > 0
    assert event_walk.summary["feature_count"] > len(FACTOR_COLUMNS)

    forecast = build_stock_forecast(bars, "601899", [1, 5], source="sample", allow_sample=True)
    explanation = explain_stock_forecast(bars, forecast, "601899", [1, 5])
    assert not explanation.report.empty
    assert "Similar History" in explanation.markdown


def test_factor_trust_registry_quarantines_weak_or_unproven_factors() -> None:
    bars = {
        "601899": _bars("601899", 0),
        "603993": _bars("603993", 10),
        "600547": _bars("600547", 20),
    }
    store = build_point_in_time_feature_store(bars, [5], "sample")
    factors = store.features.set_index(["date", "symbol"])
    factor_columns = [factor for factor in FACTOR_COLUMNS if factor in factors.columns][:40]
    labels = compute_return_labels(bars, [5])
    analysis = analyze_factors(factors, labels, factor_columns, "future_return_5d", quantiles=5)
    registry = build_factor_registry(factor_columns)
    result = analyze_factor_trust(factors, analysis, factor_columns, labels=labels, label_column="future_return_5d")
    assert {"factor_id", "category", "economic_rationale", "pit_rule", "status"}.issubset(registry.columns)
    assert {
        "trust_status",
        "quarantine_reason",
        "leakage_suspect",
        "crowding_flag",
        "cost_adjusted_spread",
        "estimated_cost_drag",
        "regime_positive_ratio",
        "worst_regime_rank_ic",
        "max_corr_factor",
    }.issubset(result.audit.columns)
    assert set(result.audit["trust_status"]).issubset({"approved", "watchlist", "quarantine"})
    assert result.audit["estimated_cost_drag"].ge(0).all()
    assert "Factor Trust Report" in result.markdown
    assert "Cost/Regime Watchlist" in result.markdown


def test_event_bus_builds_required_evidence_fields() -> None:
    raw, warnings = sync_public_events(["000630", "601899"], "2024-01-01", "2024-12-31", source="sample")
    result = build_event_store(raw, ["000630", "601899"])
    required = {
        "source_url",
        "published_at",
        "fetched_at",
        "related_symbols",
        "entity_link_method",
        "entity_link_confidence",
        "entity_link_keywords",
        "event_type",
        "impact_score",
        "confidence",
        "source_category",
        "source_reliability",
        "weighted_impact_score",
        "raw_hash",
    }
    assert warnings == []
    assert required.issubset(result.event_store.columns)
    assert result.event_store["source_reliability"].between(0.05, 1.0).all()
    assert not result.event_factors.empty
    assert {
        "event_weighted_impact_score",
        "event_reliability_mean",
        "event_entity_link_confidence_mean",
        "latest_event_source",
        "latest_entity_link_method",
    }.issubset(result.event_factors.columns)
    assert "News And Event Evidence Report" in result.evidence_markdown
    coverage = audit_event_coverage(result.event_store, result.event_factors, ["000630", "601899", "000001"])
    assert {
        "symbol",
        "event_rows",
        "event_factor_rows",
        "avg_source_reliability",
        "avg_entity_link_confidence",
        "entity_link_methods",
        "coverage_status",
    }.issubset(coverage.columns)
    assert set(coverage["coverage_status"]).issubset({"ok", "sparse", "no_linked_news"})


def test_theme_keyword_entity_link_maps_policy_news_to_stocks() -> None:
    raw = pd.DataFrame(
        [
            {
                "source": "cctv_macro",
                "published_at": "2024-06-03",
                "symbol": "",
                "related_symbols": "",
                "title": "政策支持AI算力和半导体先进封装产业链",
                "summary": "数据中心、光模块、芯片和先进封装方向获得产业政策支持。",
                "source_url": "https://news.cctv.com/",
                "quality_flag": "macro_policy",
            }
        ]
    )
    result = build_event_store(raw, ["300308", "000630"])
    assert "300308" in set(result.event_store["symbol"])
    assert "000630" not in set(result.event_store["symbol"])
    row = result.event_store.iloc[0]
    assert row["entity_link_method"] == "theme_keyword"
    assert float(row["entity_link_confidence"]) >= 0.50
    assert "算力" in row["entity_link_keywords"] or "半导体" in row["entity_link_keywords"]
    assert result.event_factors["event_entity_link_confidence_mean"].max() > 0


def test_event_source_reliability_weights_structured_impact() -> None:
    raw = pd.DataFrame(
        [
            {
                "source": "cninfo_disclosure",
                "published_at": "2024-06-03",
                "symbol": "000630",
                "related_symbols": "000630",
                "title": "000630 regulatory inquiry",
                "summary": "regulatory inquiry",
                "impact_score": -0.6,
                "confidence": 0.8,
                "source_url": "https://www.cninfo.com.cn/",
                "quality_flag": "ok",
            },
            {
                "source": "eastmoney_stock_news",
                "published_at": "2024-06-04",
                "symbol": "000630",
                "related_symbols": "000630",
                "title": "000630 market rumor",
                "summary": "market rumor",
                "impact_score": -0.6,
                "confidence": 0.8,
                "source_url": "https://finance.eastmoney.com/",
                "quality_flag": "ok",
            },
        ]
    )
    result = build_event_store(raw, ["000630"])
    by_source = result.event_store.set_index("source")
    assert by_source.loc["cninfo_disclosure", "source_reliability"] > by_source.loc["eastmoney_stock_news", "source_reliability"]
    assert abs(by_source.loc["cninfo_disclosure", "weighted_impact_score"]) > abs(by_source.loc["eastmoney_stock_news", "weighted_impact_score"])
    assert result.event_factors["event_reliability_mean"].max() > 0.60


def test_commodity_events_map_futures_shocks_to_related_stocks() -> None:
    class FakeAk:
        @staticmethod
        def futures_main_sina(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
            dates = pd.bdate_range("2024-01-01", periods=8)
            prices = [100, 101, 100, 106, 107, 108, 109, 110] if symbol == "CU0" else [100] * 8
            return pd.DataFrame({"日期": dates, "收盘价": prices, "成交量": [1000] * len(dates)})

    mapping = commodity_symbol_map(["000630"])
    assert "copper" in mapping["000630"]
    raw, warnings = sync_commodity_events(
        ["000630"],
        "2024-01-01",
        "2024-01-31",
        shock_threshold=0.03,
        ak_module=FakeAk(),
    )
    assert warnings == []
    assert not raw.empty
    assert set(raw["symbol"].astype(str).str.zfill(6)) == {"000630"}
    assert "commodity_shock" in set(raw["event_type"])
    result = build_event_store(raw, ["000630"])
    assert not result.event_factors.empty
    assert "commodity_shock" in set(result.event_store["event_type"])
    assert result.event_store["impact_score"].abs().max() > 0


def test_event_cache_fetches_missing_symbols(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    class DummyStorage:
        root_dir = tmp_path / "warehouse"
        file_format = "csv"

    class DummyConfig:
        storage = DummyStorage()

        class data:
            source = "akshare"
            start_date = "2024-01-01"
            end_date = "2024-12-31"

    class DummyArgs:
        allow_sample = False
        start = "2024-01-01"

    partial = pd.DataFrame(
        [
            {
                "source": "eastmoney_stock_news",
                "published_at": "2024-06-01",
                "symbol": "000630",
                "related_symbols": "000630",
                "title": "000630 cached news",
                "summary": "000630 cached news",
                "source_url": "",
                "quality_flag": "ok",
            }
        ]
    )

    class DummyWarehouse:
        def __init__(self, root_dir, file_format):
            self.writes = []

        def read_table(self, table: str) -> pd.DataFrame:
            assert table == "raw_events"
            return partial

        def write_table(self, table: str, frame: pd.DataFrame):
            self.writes.append((table, frame))
            return None

    def fake_sync(symbols, start_date, end_date, source, **_kwargs):
        assert symbols == ["601899"]
        return (
            pd.DataFrame(
                [
                    {
                        "source": "eastmoney_stock_news",
                        "published_at": "2024-06-02",
                        "symbol": "601899",
                        "related_symbols": "601899",
                        "title": "601899 fetched news",
                        "summary": "601899 fetched news",
                        "source_url": "",
                        "quality_flag": "ok",
                    }
                ]
            ),
            [],
        )

    monkeypatch.setattr(cli_module, "LocalWarehouse", DummyWarehouse)
    monkeypatch.setattr(cli_module, "sync_public_events", fake_sync)
    raw = cli_module._load_or_sync_events(DummyConfig(), DummyArgs(), "akshare", ["000630", "601899"])
    assert set(raw["symbol"].astype(str).str.zfill(6)) == {"000630", "601899"}


def test_portfolio_event_attribution_links_holdings_to_event_factors() -> None:
    holdings = pd.DataFrame(
        [
            {"date": "2024-01-02", "symbol": "000630", "weight": 0.30},
            {"date": "2024-01-02", "symbol": "601899", "weight": 0.20},
            {"date": "2024-01-03", "symbol": "000630", "weight": 0.25},
        ]
    )
    events = pd.DataFrame(
        [
            {
                "date": "2024-01-02",
                "symbol": "000630",
                "event_count_20d": 3,
                "positive_event_count": 2,
                "negative_event_count": 1,
                "event_risk_count": 1,
                "event_impact_score": 0.2,
            },
            {
                "date": "2024-01-02",
                "symbol": "601899",
                "event_count_20d": 2,
                "positive_event_count": 1,
                "negative_event_count": 0,
                "event_risk_count": 0,
                "event_impact_score": 0.4,
            },
        ]
    )
    result = attribute_portfolio_events(holdings, events)
    assert not result.daily.empty
    assert not result.symbol.empty
    assert "Portfolio Event Attribution" in result.markdown
    assert result.daily["event_exposed_weight"].max() > 0


def test_event_risk_guard_reduces_targets_and_blocks_orders() -> None:
    targets = pd.DataFrame(
        [
            {"000630": 0.0, "601899": 0.20},
            {"000630": 0.20, "601899": 0.20},
            {"000630": 0.20, "601899": 0.20},
        ],
        index=pd.to_datetime(["2024-01-05", "2024-01-12", "2024-01-19"]),
    )
    event_factors = pd.DataFrame(
        [
            {
                "date": "2024-01-10",
                "symbol": "000630",
                "event_risk_count": 1,
                "negative_event_count": 1,
                "event_impact_score": -0.70,
                "event_weighted_impact_score": -0.55,
                "event_confidence_mean": 0.80,
                "event_reliability_mean": 0.90,
                "latest_event_type": "regulatory_inquiry",
                "latest_event_title": "risk event",
            },
            {
                "date": "2024-01-10",
                "symbol": "601899",
                "event_risk_count": 1,
                "negative_event_count": 1,
                "event_impact_score": -0.40,
                "event_weighted_impact_score": -0.10,
                "event_confidence_mean": 0.75,
                "event_reliability_mean": 0.60,
                "latest_event_type": "performance_miss",
                "latest_event_title": "miss event",
            },
        ]
    )
    adjustment = apply_event_risk_guard(
        targets,
        event_factors,
        EventRiskConfig(weight_multiplier=0.5, block_new_buy=True, max_event_age_days=20),
    )
    assert float(adjustment.adjusted_targets.loc[pd.Timestamp("2024-01-12"), "000630"]) == 0.0
    assert float(adjustment.adjusted_targets.loc[pd.Timestamp("2024-01-12"), "601899"]) == 0.10
    assert "000630" in adjustment.blocked_symbols
    assert "601899" in adjustment.reduced_symbols
    assert "Event Risk Guard Report" in adjustment.markdown

    prices = pd.Series({"000630": 10.0, "601899": 20.0})
    plan = build_order_plan_from_targets(
        pd.Series({"000630": 0.10, "601899": 0.10}),
        prices,
        equity=100000,
        trade_date="2024-01-12",
    )
    context = event_context_by_symbol(event_factors, "2024-01-12", max_age_days=20)
    decision = check_order_plan(
        plan.orders,
        TradingRiskConfig(max_event_risk_count=0, min_event_impact_score=-0.20, min_event_confidence=0.45),
        equity=100000,
        event_context=context,
    )
    assert not decision.passed
    assert {"event_risk_count_exceeds_limit", "event_negative_impact_exceeds_limit"}.intersection(decision.reasons)
    assert {"event_impact_score", "event_weighted_impact_score", "event_reliability_mean"}.issubset(decision.report.columns)


def test_order_risk_uses_weighted_event_impact_when_available() -> None:
    plan = build_order_plan_from_targets(
        pd.Series({"000630": 0.10}),
        pd.Series({"000630": 10.0}),
        equity=100000,
        trade_date="2024-01-12",
    )
    context = {
        "000630": {
            "event_risk_count": 1,
            "event_impact_score": -0.05,
            "event_weighted_impact_score": -0.35,
            "event_confidence_mean": 0.80,
            "event_reliability_mean": 0.95,
            "latest_event_type": "regulatory_inquiry",
        }
    }
    decision = check_order_plan(
        plan.orders,
        TradingRiskConfig(max_event_risk_count=0, min_event_impact_score=-0.20, min_event_confidence=0.45),
        equity=100000,
        event_context=context,
    )
    assert not decision.passed
    assert "event_negative_impact_exceeds_limit" in decision.reasons


def test_walk_forward_trust_gate_requires_multiple_oos_metrics() -> None:
    strong = {
        "model_status": "ok",
        "rows": 6000,
        "beats_baseline": True,
        "auc": 0.53,
        "brier": 0.24,
        "rank_ic": 0.01,
        "top_bottom_spread": 0.002,
    }
    assert _trust_status(strong, "trusted_candidate") == "trusted"
    assert strong["trust_gate_passed"] is True

    weak_auc = dict(strong, auc=0.50)
    assert _trust_status(weak_auc, "trusted_candidate") == "weak"
    assert weak_auc["trust_gate_passed"] is False
    assert "auc_above_052" in weak_auc["trust_gate_reasons"]

    insufficient = dict(strong)
    assert _trust_status(insufficient, "data_insufficient") == "data_insufficient"


def test_model_evaluation_slices_are_real_metrics() -> None:
    records = [
        {
            "model_id": "walk_forward_factor_score_h5",
            "model_type": "factor_score",
            "model_family": "walk_forward_validation",
            "horizon_days": 5,
            "artifact_path": "reports/walk_forward/walk_forward_predictions.csv",
            "metrics": {
                "rows": 80,
                "direction_accuracy": 0.55,
                "auc": 0.56,
                "brier": 0.24,
                "rank_ic": 0.03,
                "top_bottom_spread": 0.01,
                "trust_status": "weak",
            },
        }
    ]
    registry = summarize_model_registry(records)
    assert {"auc", "trust_gate_reasons", "artifact_path"}.issubset(registry.columns)

    dates = pd.bdate_range("2024-01-01", periods=12)
    rows = []
    symbols = ["000630", "601899", "300750", "600362", "000002", "002594"]
    for day_idx, date in enumerate(dates):
        for symbol_idx, symbol in enumerate(symbols):
            ret = (symbol_idx - 2) * 0.002 + (day_idx % 3 - 1) * 0.001
            direction = int(ret > 0)
            rows.append(
                {
                    "date": date,
                    "symbol": symbol,
                    "horizon_days": 5,
                    "model_type": "factor_score",
                    "future_return_5d": ret,
                    "direction_up_5d": direction,
                    "prob_up": 0.40 + symbol_idx * 0.08,
                    "amount_mean_20": 1_000_000 + symbol_idx * 100_000,
                    "market_mean_return": (day_idx % 4 - 1.5) * 0.002,
                    "market_breadth": 0.35 + (day_idx % 4) * 0.10,
                    "volatility_20": 0.01 + symbol_idx * 0.002,
                }
            )
    slices = evaluate_walk_forward_slices(pd.DataFrame(rows))
    assert {"year", "industry", "theme", "size", "regime"}.issubset(slices)
    assert int(slices["year"]["rows"].sum()) == len(rows)
    assert "top_bottom_spread" in slices["theme"].columns
    assert set(slices["size"]["size_bucket"]).intersection({"low_liquidity_proxy", "mid_liquidity_proxy", "high_liquidity_proxy"})
    assert "amount_mean_20_liquidity_proxy" in set(slices["size"]["size_source"])
    assert "pit_market_mean_return_and_breadth" in set(slices["regime"]["regime_source"])
    assert slices["regime"]["market_regime"].nunique() >= 1


def test_resilient_loader_keeps_large_free_run_moving(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyArgs:
        max_symbols = 0

    class DummyConfig:
        data = DataConfig(source="free_real", symbols=[], start_date="2024-01-01", end_date="2024-12-31")

    def fake_load_daily_bars_resilient(data_config):
        loaded = {symbol: _bars(symbol, periods=80) for symbol in data_config.symbols if symbol != "000002"}
        warnings = [f"{symbol}: ok" for symbol in loaded]
        warnings.append("000002: failed to load (simulated vendor outage)")
        return loaded, cli_module.LoadReport("free_real", sorted(loaded), warnings)

    monkeypatch.setattr(cli_module, "load_daily_bars_resilient", fake_load_daily_bars_resilient)
    loaded, report = cli_module._load_symbols_resilient(DummyConfig(), DummyArgs(), ["000001", "000002", "000003"], "free_real", "2024-01-01")
    assert sorted(loaded) == ["000001", "000003"]
    assert any("000002" in warning and "failed" in warning for warning in report.warnings)


def test_data_config_max_symbols_keeps_requested_stock() -> None:
    class DummyConfig:
        data = DataConfig(source="baostock", symbols=["000001"], start_date="2024-01-01", end_date="2026-06-10")

    class DummyArgs:
        universe = "000001,000002,000003,000004"
        themes = None
        max_symbols = 2
        start = "2024-01-01"

    data_config = cli_module._data_config_with_source(DummyConfig(), DummyArgs(), "baostock", ensure_symbol="000004")
    assert data_config.symbols == ["000001", "000002", "000004"]
