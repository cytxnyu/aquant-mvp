from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from aquant_mvp.broker.base import ExecutionReport, OrderPlan


@dataclass
class QMTReadOnlyBroker:
    account_id: str = ""
    qmt_path: str = ""
    name: str = "qmt_readonly"

    def available(self) -> bool:
        try:
            import xtquant  # noqa: F401  # type: ignore

            return True
        except ImportError:
            return False

    def submit(self, order_plan: OrderPlan) -> ExecutionReport:
        raise RuntimeError("QMT live order submission is disabled. This project only supports QMT read-only/paper flow.")

    def reconcile(self) -> pd.DataFrame:
        if not self.available():
            raise RuntimeError("xtquant/QMT is not installed; cannot run read-only reconciliation.")
        return pd.DataFrame(columns=["account_id", "symbol", "shares", "market_value", "source"])
