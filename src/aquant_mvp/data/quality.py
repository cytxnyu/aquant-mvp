from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class DataQualityReport:
    summary: pd.DataFrame
    issues: pd.DataFrame

    @property
    def issue_count(self) -> int:
        return int(len(self.issues))


def check_daily_bars(bars_by_symbol: dict[str, pd.DataFrame]) -> DataQualityReport:
    summary_rows: list[dict[str, object]] = []
    issue_rows: list[dict[str, object]] = []
    for symbol, bars in bars_by_symbol.items():
        df = bars.copy()
        df["date"] = pd.to_datetime(df["date"])
        duplicate_dates = int(df["date"].duplicated().sum())
        missing_cells = int(df[["open", "high", "low", "close", "volume", "amount", "turnover"]].isna().sum().sum())
        non_positive_price = int((df[["open", "high", "low", "close"]] <= 0).any(axis=1).sum())
        high_low_error = int(((df["high"] < df[["open", "close", "low"]].max(axis=1)) | (df["low"] > df[["open", "close", "high"]].min(axis=1))).sum())
        amount_error = int((df["amount"] < 0).sum())
        date_span = max(1, len(pd.bdate_range(df["date"].min(), df["date"].max()))) if not df.empty else 1
        missing_ratio = 1 - len(df) / date_span

        summary_rows.append(
            {
                "symbol": symbol,
                "rows": len(df),
                "start_date": df["date"].min() if not df.empty else pd.NaT,
                "end_date": df["date"].max() if not df.empty else pd.NaT,
                "missing_ratio": max(0.0, float(missing_ratio)),
                "duplicate_dates": duplicate_dates,
                "missing_cells": missing_cells,
                "non_positive_price_rows": non_positive_price,
                "high_low_error_rows": high_low_error,
                "amount_error_rows": amount_error,
            }
        )

        _append_issue(issue_rows, symbol, "duplicate_dates", duplicate_dates)
        _append_issue(issue_rows, symbol, "missing_cells", missing_cells)
        _append_issue(issue_rows, symbol, "non_positive_price", non_positive_price)
        _append_issue(issue_rows, symbol, "high_low_error", high_low_error)
        _append_issue(issue_rows, symbol, "amount_error", amount_error)

    summary = pd.DataFrame(summary_rows)
    issues = pd.DataFrame(issue_rows, columns=["symbol", "issue", "count"])
    return DataQualityReport(summary=summary, issues=issues)


def _append_issue(rows: list[dict[str, object]], symbol: str, issue: str, count: int) -> None:
    if count > 0:
        rows.append({"symbol": symbol, "issue": issue, "count": int(count)})

