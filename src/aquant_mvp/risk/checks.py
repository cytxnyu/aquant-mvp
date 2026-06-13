from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class TradingRiskConfig:
    max_capital: float = 1_000_000.0
    max_single_weight: float = 0.20
    max_order_value: float = 200_000.0
    max_daily_loss: float = 0.03
    max_drawdown: float = 0.10
    blacklist: tuple[str, ...] = ()
    max_event_risk_count: int | None = None
    min_event_impact_score: float | None = None
    min_event_confidence: float = 0.45


@dataclass(frozen=True)
class OrderIntent:
    symbol: str
    side: str
    shares: int
    price: float
    target_weight: float = 0.0

    @property
    def order_value(self) -> float:
        return float(self.shares) * float(self.price)


@dataclass(frozen=True)
class RiskDecision:
    passed: bool
    reasons: list[str]
    report: pd.DataFrame


def check_order_plan(
    orders: list[OrderIntent],
    config: TradingRiskConfig,
    equity: float,
    daily_pnl: float = 0.0,
    drawdown: float = 0.0,
    event_context: dict[str, dict[str, object]] | None = None,
) -> RiskDecision:
    rows: list[dict[str, object]] = []
    all_reasons: list[str] = []
    if equity > config.max_capital:
        all_reasons.append("equity_exceeds_max_capital")
    if equity > 0 and daily_pnl / equity <= -config.max_daily_loss:
        all_reasons.append("daily_loss_circuit_breaker")
    if drawdown <= -config.max_drawdown:
        all_reasons.append("drawdown_circuit_breaker")

    blacklist = {symbol.zfill(6) for symbol in config.blacklist}
    for order in orders:
        reasons = []
        symbol = order.symbol.zfill(6)
        if symbol in blacklist:
            reasons.append("blacklisted_symbol")
        if order.order_value > config.max_order_value:
            reasons.append("order_value_exceeds_limit")
        if order.target_weight > config.max_single_weight:
            reasons.append("target_weight_exceeds_limit")
        if order.shares <= 0 or order.price <= 0:
            reasons.append("invalid_order")
        event_row = (event_context or {}).get(symbol, {})
        event_risk_count = _safe_float(event_row.get("event_risk_count", 0.0))
        event_impact_score = _safe_float(event_row.get("event_impact_score", 0.0))
        event_weighted_impact_score = _event_impact_for_decision(event_row)
        event_confidence = _safe_float(event_row.get("event_confidence_mean", 0.0))
        if (
            config.max_event_risk_count is not None
            and event_confidence >= config.min_event_confidence
            and event_risk_count > config.max_event_risk_count
            and config.min_event_impact_score is not None
            and event_weighted_impact_score <= config.min_event_impact_score
        ):
            reasons.append("event_risk_count_exceeds_limit")
        if (
            config.min_event_impact_score is not None
            and event_confidence >= config.min_event_confidence
            and event_weighted_impact_score <= config.min_event_impact_score
        ):
            reasons.append("event_negative_impact_exceeds_limit")
        all_reasons.extend(reasons)
        rows.append(
            {
                "symbol": symbol,
                "side": order.side,
                "shares": order.shares,
                "price": order.price,
                "order_value": order.order_value,
                "target_weight": order.target_weight,
                "event_risk_count": event_risk_count,
                "event_impact_score": event_impact_score,
                "event_weighted_impact_score": event_weighted_impact_score,
                "event_confidence_mean": event_confidence,
                "event_reliability_mean": _safe_float(event_row.get("event_reliability_mean", 0.0)),
                "latest_event_type": str(event_row.get("latest_event_type", "")),
                "passed": not reasons,
                "reasons": ";".join(reasons) if reasons else "none",
            }
        )

    report = pd.DataFrame(rows)
    return RiskDecision(passed=not all_reasons, reasons=all_reasons, report=report)


def _safe_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _event_impact_for_decision(event_row: dict[str, object]) -> float:
    weighted = event_row.get("event_weighted_impact_score")
    try:
        weighted_value = float(weighted)
    except (TypeError, ValueError):
        weighted_value = float("nan")
    if pd.notna(weighted_value):
        return weighted_value
    return _safe_float(event_row.get("event_impact_score", 0.0))
