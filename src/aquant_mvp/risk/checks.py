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
        all_reasons.extend(reasons)
        rows.append(
            {
                "symbol": symbol,
                "side": order.side,
                "shares": order.shares,
                "price": order.price,
                "order_value": order.order_value,
                "target_weight": order.target_weight,
                "passed": not reasons,
                "reasons": ";".join(reasons) if reasons else "none",
            }
        )

    report = pd.DataFrame(rows)
    return RiskDecision(passed=not all_reasons, reasons=all_reasons, report=report)
