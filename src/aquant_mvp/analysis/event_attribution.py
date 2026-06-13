from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class EventAttributionResult:
    daily: pd.DataFrame
    symbol: pd.DataFrame
    markdown: str


def attribute_portfolio_events(holdings: pd.DataFrame, event_factors: pd.DataFrame) -> EventAttributionResult:
    if holdings.empty or event_factors.empty:
        empty_daily = pd.DataFrame(columns=_DAILY_COLUMNS)
        empty_symbol = pd.DataFrame(columns=_SYMBOL_COLUMNS)
        return EventAttributionResult(empty_daily, empty_symbol, _markdown(empty_daily, empty_symbol))
    required_holdings = {"date", "symbol", "weight"}
    required_events = {
        "date",
        "symbol",
        "event_count_20d",
        "positive_event_count",
        "negative_event_count",
        "event_risk_count",
        "event_impact_score",
    }
    if not required_holdings.issubset(holdings.columns) or not required_events.issubset(event_factors.columns):
        empty_daily = pd.DataFrame(columns=_DAILY_COLUMNS)
        empty_symbol = pd.DataFrame(columns=_SYMBOL_COLUMNS)
        return EventAttributionResult(empty_daily, empty_symbol, _markdown(empty_daily, empty_symbol))

    left = holdings[["date", "symbol", "weight"]].copy()
    left["date"] = pd.to_datetime(left["date"]).dt.normalize()
    left["symbol"] = left["symbol"].astype(str).str.zfill(6)
    left["weight"] = pd.to_numeric(left["weight"], errors="coerce").fillna(0.0)

    optional_events = ["event_weighted_impact_score", "event_reliability_mean"]
    event_columns = list(required_events) + [column for column in optional_events if column in event_factors.columns]
    right = event_factors[event_columns].copy()
    right["date"] = pd.to_datetime(right["date"], errors="coerce").dt.normalize()
    right["symbol"] = right["symbol"].astype(str).str.zfill(6)
    for column in required_events - {"date", "symbol"}:
        right[column] = pd.to_numeric(right[column], errors="coerce").fillna(0.0)
    right = right.dropna(subset=["date"]).drop_duplicates(["date", "symbol"], keep="last")

    merged = left.merge(right, on=["date", "symbol"], how="left").fillna(
        {
            "event_count_20d": 0.0,
            "positive_event_count": 0.0,
            "negative_event_count": 0.0,
            "event_risk_count": 0.0,
            "event_impact_score": 0.0,
            "event_weighted_impact_score": 0.0,
            "event_reliability_mean": 0.0,
        }
    )
    if "event_weighted_impact_score" not in merged.columns:
        merged["event_weighted_impact_score"] = merged["event_impact_score"]
    merged["event_effective_impact_score"] = merged["event_weighted_impact_score"].where(
        merged["event_weighted_impact_score"].notna(),
        merged["event_impact_score"],
    )
    merged["weighted_event_impact"] = merged["weight"] * merged["event_effective_impact_score"]
    merged["weighted_positive_events"] = merged["weight"] * merged["positive_event_count"]
    merged["weighted_negative_events"] = merged["weight"] * merged["negative_event_count"]
    merged["weighted_risk_events"] = merged["weight"] * merged["event_risk_count"]
    merged["event_exposed_weight"] = merged["weight"].where(merged["event_count_20d"] > 0, 0.0)
    merged["risk_event_weight"] = merged["weight"].where(merged["event_risk_count"] > 0, 0.0)

    daily = (
        merged.groupby("date", as_index=False)
        .agg(
            holding_count=("symbol", "nunique"),
            gross_weight=("weight", "sum"),
            event_exposed_weight=("event_exposed_weight", "sum"),
            risk_event_weight=("risk_event_weight", "sum"),
            weighted_event_impact=("weighted_event_impact", "sum"),
            weighted_positive_events=("weighted_positive_events", "sum"),
            weighted_negative_events=("weighted_negative_events", "sum"),
            weighted_risk_events=("weighted_risk_events", "sum"),
        )
        .sort_values("date")
    )
    daily["date"] = daily["date"].dt.date.astype(str)

    symbol = (
        merged.groupby("symbol", as_index=False)
        .agg(
            days_held=("date", "nunique"),
            avg_weight=("weight", "mean"),
            max_weight=("weight", "max"),
            event_exposed_days=("event_count_20d", lambda values: int((values > 0).sum())),
            risk_event_days=("event_risk_count", lambda values: int((values > 0).sum())),
            avg_event_impact=("event_effective_impact_score", "mean"),
            weighted_event_impact=("weighted_event_impact", "sum"),
            weighted_risk_events=("weighted_risk_events", "sum"),
        )
        .sort_values(["weighted_risk_events", "weighted_event_impact"], ascending=[False, False])
    )
    return EventAttributionResult(daily[_DAILY_COLUMNS], symbol[_SYMBOL_COLUMNS], _markdown(daily, symbol))


_DAILY_COLUMNS = [
    "date",
    "holding_count",
    "gross_weight",
    "event_exposed_weight",
    "risk_event_weight",
    "weighted_event_impact",
    "weighted_positive_events",
    "weighted_negative_events",
    "weighted_risk_events",
]

_SYMBOL_COLUMNS = [
    "symbol",
    "days_held",
    "avg_weight",
    "max_weight",
    "event_exposed_days",
    "risk_event_days",
    "avg_event_impact",
    "weighted_event_impact",
    "weighted_risk_events",
]


def _markdown(daily: pd.DataFrame, symbol: pd.DataFrame) -> str:
    lines = [
        "# Portfolio Event Attribution",
        "",
        "This report links portfolio holdings to structured event factors. It is diagnostic evidence only, not trading advice.",
        "",
    ]
    if daily.empty:
        lines.extend(["## Summary", "", "- No portfolio event attribution is available for this run."])
        return "\n".join(lines)
    latest = daily.sort_values("date").iloc[-1]
    lines.extend(
        [
            "## Latest Exposure",
            "",
            f"- Date: `{latest['date']}`",
            f"- Gross weight: `{float(latest['gross_weight']):.3f}`",
            f"- Event-exposed weight: `{float(latest['event_exposed_weight']):.3f}`",
            f"- Risk-event weight: `{float(latest['risk_event_weight']):.3f}`",
            f"- Weighted event impact: `{float(latest['weighted_event_impact']):.3f}`",
            "",
            "## Highest Risk Event Contributors",
            "",
        ]
    )
    if symbol.empty:
        lines.append("- No symbol-level attribution rows.")
    else:
        for row in symbol.head(10).itertuples(index=False):
            lines.append(
                f"- `{row.symbol}`: avg_weight={row.avg_weight:.3f}, risk_days={int(row.risk_event_days)}, "
                f"weighted_risk_events={row.weighted_risk_events:.3f}, avg_impact={row.avg_event_impact:.3f}"
            )
    lines.extend(["", "## Guardrail", "", "- A high event exposure is a reason to inspect evidence, not a direct buy/sell signal."])
    return "\n".join(lines)
