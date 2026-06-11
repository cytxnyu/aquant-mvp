from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from aquant_mvp.config import UniverseConfig


@dataclass(frozen=True)
class UniverseReport:
    selected_symbols: list[str]
    detail: pd.DataFrame


def filter_universe(
    bars_by_symbol: dict[str, pd.DataFrame],
    config: UniverseConfig,
) -> tuple[dict[str, pd.DataFrame], UniverseReport]:
    selected: dict[str, pd.DataFrame] = {}
    rows: list[dict[str, object]] = []
    excluded = set(config.exclude_symbols)

    for symbol, bars in bars_by_symbol.items():
        df = bars.sort_values("date").copy()
        dates = pd.to_datetime(df["date"])
        expected = max(1, len(pd.bdate_range(dates.min(), dates.max()))) if not df.empty else 1
        missing_ratio = max(0.0, 1 - len(df) / expected)
        avg_amount = float(pd.to_numeric(df["amount"], errors="coerce").tail(60).mean()) if not df.empty else 0.0
        reasons = []
        if symbol in excluded:
            reasons.append("excluded_by_config")
        if len(df) < config.min_history_days:
            reasons.append("insufficient_history")
        if missing_ratio > config.max_missing_ratio:
            reasons.append("too_many_missing_days")
        if avg_amount < config.min_amount:
            reasons.append("low_amount")

        passed = not reasons
        if passed:
            selected[symbol] = df
        rows.append(
            {
                "symbol": symbol,
                "passed": passed,
                "rows": len(df),
                "missing_ratio": missing_ratio,
                "avg_amount_60": avg_amount,
                "reasons": ";".join(reasons),
                "reserved_filters": "st,suspend,limit_up_down,new_stock,delist,industry",
            }
        )

    detail = pd.DataFrame(rows)
    report = UniverseReport(selected_symbols=sorted(selected), detail=detail)
    return selected, report

