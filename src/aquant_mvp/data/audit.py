from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class DataAuditResult:
    summary: pd.DataFrame
    issues: pd.DataFrame
    cross_source_diff: pd.DataFrame


def add_source_audit_columns(frame: pd.DataFrame, source: str, quality_flag: str = "ok") -> pd.DataFrame:
    out = frame.copy()
    fetched_at = pd.Timestamp.now().isoformat(timespec="seconds")
    out["audit_source"] = source
    out["audit_fetched_at"] = fetched_at
    out["audit_quality_flag"] = quality_flag
    if "source" not in out.columns:
        out["source"] = source
    if "fetched_at" not in out.columns:
        out["fetched_at"] = fetched_at
    if "date" in out.columns:
        if "effective_date" not in out.columns:
            out["effective_date"] = pd.to_datetime(out["date"], errors="coerce")
    elif "effective_date" not in out.columns:
        out["effective_date"] = pd.Timestamp(fetched_at)
    if "announce_date" not in out.columns:
        out["announce_date"] = pd.NaT
    if "quality_flag" not in out.columns:
        out["quality_flag"] = quality_flag
    out["audit_raw_hash"] = pd.util.hash_pandas_object(out.astype(str), index=False).astype(str)
    if "raw_hash" not in out.columns:
        out["raw_hash"] = out["audit_raw_hash"]
    return out


def audit_point_in_time_tables(tables: dict[str, pd.DataFrame], strict_pit: bool = True) -> DataAuditResult:
    summary_rows: list[dict[str, object]] = []
    issue_rows: list[dict[str, object]] = []
    for name, frame in tables.items():
        rows = int(len(frame))
        columns = set(frame.columns)
        date_col = "date" if "date" in columns else "effective_date" if "effective_date" in columns else None
        min_date = str(pd.to_datetime(frame[date_col]).min().date()) if date_col and rows else ""
        max_date = str(pd.to_datetime(frame[date_col]).max().date()) if date_col and rows else ""
        pit_ready = _pit_ready(name, columns)
        summary_rows.append(
            {
                "table": name,
                "rows": rows,
                "columns": len(columns),
                "min_date": min_date,
                "max_date": max_date,
                "pit_ready": pit_ready,
                "missing_ratio": float(frame.isna().to_numpy().mean()) if rows else 0.0,
            }
        )
        if strict_pit and not pit_ready:
            issue_rows.append({"table": name, "issue": "missing_point_in_time_columns", "severity": "high"})
        if rows and date_col:
            duplicated = frame.duplicated(subset=[date_col, "symbol"] if "symbol" in columns else [date_col]).sum()
            if duplicated:
                issue_rows.append({"table": name, "issue": "duplicate_key_rows", "severity": "medium", "count": int(duplicated)})
        if name == "daily_bar" and rows:
            issue_rows.extend(_daily_bar_issues(frame))
    return DataAuditResult(
        summary=pd.DataFrame(summary_rows),
        issues=pd.DataFrame(issue_rows),
        cross_source_diff=pd.DataFrame(columns=["symbol", "date", "field", "left_source", "right_source", "diff"]),
    )


def compare_daily_bar_sources(left: pd.DataFrame, right: pd.DataFrame, left_source: str, right_source: str) -> pd.DataFrame:
    if left.empty or right.empty:
        return pd.DataFrame(columns=["symbol", "date", "field", "left_source", "right_source", "diff"])
    keys = ["date", "symbol"]
    merged = left[keys + ["close", "amount"]].merge(
        right[keys + ["close", "amount"]],
        on=keys,
        how="inner",
        suffixes=("_left", "_right"),
    )
    rows = []
    for field in ["close", "amount"]:
        denom = merged[f"{field}_right"].replace(0, np.nan)
        diff = (merged[f"{field}_left"] - merged[f"{field}_right"]).abs() / denom
        flagged = merged[diff > (0.005 if field == "close" else 0.05)]
        for idx, row in flagged.iterrows():
            rows.append(
                {
                    "symbol": row["symbol"],
                    "date": row["date"],
                    "field": field,
                    "left_source": left_source,
                    "right_source": right_source,
                    "diff": float(diff.loc[idx]),
                }
            )
    return pd.DataFrame(rows)


def _pit_ready(table: str, columns: set[str]) -> bool:
    if table in {"daily_bar", "minute_bar", "trade_calendar", "raw_events", "event_store", "event_factor"}:
        return "date" in columns or "effective_date" in columns
    if table in {"financial", "announcement"}:
        return "announce_date" in columns
    if table in {"industry", "index_member", "concept"}:
        return "effective_date" in columns
    if table in {"factor_registry", "factor_trust_audit"}:
        return True
    return "date" in columns or "effective_date" in columns or "announce_date" in columns


def _daily_bar_issues(frame: pd.DataFrame) -> list[dict[str, object]]:
    out = []
    numeric = frame[["open", "high", "low", "close", "amount"]].apply(pd.to_numeric, errors="coerce")
    bad_price = (~(numeric[["open", "high", "low", "close"]] > 0).all(axis=1)).sum()
    if bad_price:
        out.append({"table": "daily_bar", "issue": "non_positive_price", "severity": "high", "count": int(bad_price)})
    returns = frame.sort_values(["symbol", "date"]).groupby("symbol")["close"].pct_change()
    abnormal = returns.abs().gt(0.25).sum()
    if abnormal:
        out.append({"table": "daily_bar", "issue": "abnormal_return_over_25pct", "severity": "medium", "count": int(abnormal)})
    zero_amount = numeric["amount"].fillna(0).le(0).sum()
    if zero_amount:
        out.append({"table": "daily_bar", "issue": "zero_or_missing_amount", "severity": "medium", "count": int(zero_amount)})
    return out
