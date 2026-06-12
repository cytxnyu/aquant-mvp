from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from aquant_mvp.backtest.engine import _floor_lot
from aquant_mvp.broker.base import ExecutionReport, OrderPlan
from aquant_mvp.risk import OrderIntent


@dataclass
class PaperBroker:
    initial_cash: float = 1_000_000.0
    fee_rate: float = 0.0003
    tax_rate: float = 0.001
    slippage_rate: float = 0.0005

    name: str = "paper"

    def submit(self, order_plan: OrderPlan) -> ExecutionReport:
        rows = []
        cash = float(self.initial_cash)
        positions: dict[str, int] = {}
        for order in order_plan.orders:
            side = order.side.upper()
            fill_price = order.price * (1 + self.slippage_rate if side == "BUY" else 1 - self.slippage_rate)
            gross = fill_price * order.shares
            fee = gross * self.fee_rate
            tax = gross * self.tax_rate if side == "SELL" else 0.0
            cash_delta = -(gross + fee) if side == "BUY" else gross - fee - tax
            cash += cash_delta
            positions[order.symbol] = positions.get(order.symbol, 0) + (order.shares if side == "BUY" else -order.shares)
            rows.append(
                {
                    "trade_date": order_plan.trade_date,
                    "symbol": order.symbol,
                    "side": side,
                    "requested_shares": order.shares,
                    "filled_shares": order.shares,
                    "fill_price": fill_price,
                    "gross_value": gross,
                    "fee": fee,
                    "tax": tax,
                    "status": "FILLED",
                }
            )
        executions = pd.DataFrame(rows)
        positions_frame = pd.DataFrame(
            [{"symbol": symbol, "shares": shares} for symbol, shares in positions.items() if shares != 0]
        )
        return ExecutionReport(
            trade_date=order_plan.trade_date,
            executions=executions,
            positions=positions_frame,
            metadata={"broker": self.name, "cash_after": cash},
        )

    def save_report(self, report: ExecutionReport, output_dir: Path) -> dict[str, Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        paths = {
            "executions": output_dir / "paper_executions.csv",
            "positions": output_dir / "paper_positions.csv",
        }
        report.executions.to_csv(paths["executions"], index=False)
        report.positions.to_csv(paths["positions"], index=False)
        return paths


def build_order_plan_from_targets(
    targets: pd.Series,
    latest_prices: pd.Series,
    equity: float,
    trade_date: str,
    lot_size: int = 100,
) -> OrderPlan:
    orders: list[OrderIntent] = []
    for symbol, weight in targets.items():
        weight = float(weight)
        if weight <= 0:
            continue
        price = float(latest_prices.get(symbol, np.nan))
        if np.isnan(price) or price <= 0:
            continue
        shares = _floor_lot(equity * weight / price, lot_size)
        if shares <= 0:
            continue
        orders.append(OrderIntent(symbol=str(symbol).zfill(6), side="BUY", shares=shares, price=price, target_weight=weight))
    return OrderPlan(trade_date=trade_date, orders=orders, metadata={"source": "target_weights"})
