from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from aquant_mvp.risk import OrderIntent


@dataclass(frozen=True)
class OrderPlan:
    trade_date: str
    orders: list[OrderIntent]
    metadata: dict[str, object] = field(default_factory=dict)

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "trade_date": self.trade_date,
                    "symbol": order.symbol,
                    "side": order.side,
                    "shares": order.shares,
                    "price": order.price,
                    "order_value": order.order_value,
                    "target_weight": order.target_weight,
                }
                for order in self.orders
            ]
        )


@dataclass(frozen=True)
class ExecutionReport:
    trade_date: str
    executions: pd.DataFrame
    positions: pd.DataFrame
    metadata: dict[str, object] = field(default_factory=dict)


class BrokerAdapter:
    name: str

    def submit(self, order_plan: OrderPlan) -> ExecutionReport:
        raise NotImplementedError
