from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from aquant_mvp.broker import PaperBroker, build_order_plan_from_targets
from aquant_mvp.data import add_source_audit_columns, audit_point_in_time_tables
from aquant_mvp.features import build_point_in_time_feature_store
from aquant_mvp.foundations import discover_foundations
from aquant_mvp.modeling import train_walk_forward
from aquant_mvp.modeling import register_model
from aquant_mvp.prediction import build_stock_forecast, explain_stock_forecast
from aquant_mvp.risk import TradingRiskConfig, check_order_plan
from aquant_mvp.sources import discover_domestic_sources
from aquant_mvp.storage import LocalWarehouse
from aquant_mvp.tooling import discover_tools
from aquant_mvp.universe import build_theme_universe, symbol_theme_membership, symbols_for_themes, theme_universe_summary
from aquant_mvp.vendors import TushareFreeAdapter, VendorNotConfigured


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
    assert {"native_supported", "candidate_adapter", "read_only_supported_live_blocked"}.intersection(set(foundations["integration_status"]))

    tools = discover_tools()
    required_tools = {"foundation_registry", "tool_registry", "mega_hot_universe", "stock_forecast", "paper_trade", "qmt_readonly", "live_trade_blocker"}
    assert required_tools.issubset(set(tools["tool_id"]))
    live_blocker = tools[tools["tool_id"] == "live_trade_blocker"].iloc[0]
    assert live_blocker["live_trading_allowed"] is False or live_blocker["live_trading_allowed"] == 0


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
        "risk_flags",
        "top_factor_contributors",
        "model_id",
        "data_version",
        "universe_symbol_count",
        "minimum_trusted_symbols",
    }
    assert required.issubset(result.forecast.columns)
    assert result.forecast["prob_up"].between(0, 1).all()


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


def test_registry_and_warehouse_write(tmp_path: Path) -> None:
    registry_record = register_model(tmp_path / "registry", {"model_id": "demo", "metrics": {"rank_ic": 0.1}})
    assert registry_record["model_id"] == "demo"
    assert (tmp_path / "registry" / "model_registry.json").exists()

    warehouse = LocalWarehouse(tmp_path / "warehouse", file_format="csv")
    result = warehouse.write_table("daily_bar", _bars("601899", periods=5))
    assert result.rows == 5
    assert result.path.exists()
    assert not warehouse.read_table("daily_bar").empty


def test_tushare_free_adapter_requires_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TUSHARE_TOKEN", raising=False)
    with pytest.raises(VendorNotConfigured):
        TushareFreeAdapter().fetch_daily_bars("601899", "2024-01-01", "2024-02-01", "qfq")


def test_source_discovery_and_data_audit() -> None:
    sources = discover_domestic_sources()
    assert {"akshare", "baostock", "cninfo"}.issubset(set(sources["source"]))

    audited = add_source_audit_columns(_bars("601899", periods=10), "sample")
    result = audit_point_in_time_tables({"daily_bar": audited}, strict_pit=True)
    assert not result.summary.empty
    assert "pit_ready" in result.summary.columns


def test_feature_store_walk_forward_and_explanation(tmp_path: Path) -> None:
    bars = {
        "601899": _bars("601899", 0),
        "603993": _bars("603993", 10),
        "600547": _bars("600547", 20),
    }
    store = build_point_in_time_feature_store(bars, [1, 5], "sample")
    assert not store.features.empty
    assert store.metadata["feature_count"] > 50

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

    forecast = build_stock_forecast(bars, "601899", [1, 5], source="sample", allow_sample=True)
    explanation = explain_stock_forecast(bars, forecast, "601899", [1, 5])
    assert not explanation.report.empty
    assert "Similar History" in explanation.markdown
