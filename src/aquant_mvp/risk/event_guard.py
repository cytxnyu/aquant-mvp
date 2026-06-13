from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class EventRiskConfig:
    enabled: bool = True
    max_event_risk_count: int = 0
    min_negative_impact: float = -0.20
    min_confidence: float = 0.45
    weight_multiplier: float = 0.50
    block_new_buy: bool = True
    max_event_age_days: int = 30


@dataclass(frozen=True)
class EventRiskAdjustment:
    adjusted_targets: pd.DataFrame
    report: pd.DataFrame
    markdown: str
    blocked_symbols: list[str]
    reduced_symbols: list[str]
    metadata: dict[str, object]


def apply_event_risk_guard(
    targets: pd.DataFrame,
    event_factors: pd.DataFrame,
    config: EventRiskConfig,
) -> EventRiskAdjustment:
    """Reduce or block target weights for symbols with recent adverse events.

    The guard is intentionally conservative: it only reacts to structured event
    factors already linked to a stock and already timestamped as point-in-time.
    """
    adjusted = _normalize_targets(targets)
    empty = pd.DataFrame(columns=_REPORT_COLUMNS)
    if adjusted.empty or event_factors.empty or not config.enabled:
        markdown = _markdown(empty, {"enabled": config.enabled, "note": "no_adjustment"})
        return EventRiskAdjustment(adjusted, empty, markdown, [], [], {"enabled": config.enabled, "adjusted_rows": 0})

    events = _normalize_events(event_factors)
    if events.empty:
        markdown = _markdown(empty, {"enabled": config.enabled, "note": "no_valid_event_factors"})
        return EventRiskAdjustment(adjusted, empty, markdown, [], [], {"enabled": config.enabled, "adjusted_rows": 0})

    report_rows: list[dict[str, object]] = []
    previous = pd.Series(0.0, index=adjusted.columns)
    blocked_symbols: set[str] = set()
    reduced_symbols: set[str] = set()

    for date, row in adjusted.iterrows():
        current = row.copy()
        daily_events = _latest_events_asof(events, pd.Timestamp(date), max_age_days=config.max_event_age_days)
        for symbol in adjusted.columns.astype(str):
            original_weight = float(row.get(symbol, 0.0))
            if original_weight <= 0:
                continue
            event_row = daily_events.get(symbol)
            if event_row is None:
                continue
            decision = _decision_for_event(event_row, previous_weight=float(previous.get(symbol, 0.0)), config=config)
            if decision["action"] == "none":
                continue
            adjusted_weight = float(original_weight) * float(decision["multiplier"])
            current.loc[symbol] = adjusted_weight
            if decision["action"] == "block_new_buy":
                blocked_symbols.add(symbol)
            else:
                reduced_symbols.add(symbol)
            report_rows.append(
                {
                    "date": pd.Timestamp(date).date().isoformat(),
                    "symbol": symbol,
                    "original_weight": original_weight,
                    "adjusted_weight": adjusted_weight,
                    "weight_delta": adjusted_weight - original_weight,
                    "action": decision["action"],
                    "reason": decision["reason"],
                    "event_risk_count": int(event_row.get("event_risk_count", 0)),
                    "negative_event_count": int(event_row.get("negative_event_count", 0)),
                    "event_impact_score": float(event_row.get("event_impact_score", 0.0)),
                    "event_weighted_impact_score": _event_impact_for_decision(event_row),
                    "event_confidence_mean": float(event_row.get("event_confidence_mean", 0.0)),
                    "event_reliability_mean": float(event_row.get("event_reliability_mean", 0.0)),
                    "latest_event_type": str(event_row.get("latest_event_type", "")),
                    "latest_event_title": str(event_row.get("latest_event_title", "")),
                }
            )
        adjusted.loc[date] = current
        previous = current

    report = pd.DataFrame(report_rows, columns=_REPORT_COLUMNS)
    metadata = {
        "enabled": config.enabled,
        "adjusted_rows": int(len(report)),
        "blocked_symbols": sorted(blocked_symbols),
        "reduced_symbols": sorted(reduced_symbols),
        "weight_removed": float(-report["weight_delta"].clip(upper=0).sum()) if not report.empty else 0.0,
        "config": {
            "max_event_risk_count": config.max_event_risk_count,
            "min_negative_impact": config.min_negative_impact,
            "min_confidence": config.min_confidence,
            "weight_multiplier": config.weight_multiplier,
            "block_new_buy": config.block_new_buy,
            "max_event_age_days": config.max_event_age_days,
        },
    }
    return EventRiskAdjustment(adjusted, report, _markdown(report, metadata), sorted(blocked_symbols), sorted(reduced_symbols), metadata)


def event_context_by_symbol(
    event_factors: pd.DataFrame,
    asof_date: str | pd.Timestamp | None = None,
    max_age_days: int = 30,
) -> dict[str, dict[str, object]]:
    events = _normalize_events(event_factors)
    if events.empty:
        return {}
    date = pd.Timestamp(asof_date) if asof_date is not None else events["date"].max()
    return _latest_events_asof(events, date, max_age_days=max_age_days)


def _normalize_targets(targets: pd.DataFrame) -> pd.DataFrame:
    out = targets.copy()
    if out.empty:
        return out
    out.index = pd.to_datetime(out.index).normalize()
    out.columns = [str(column).zfill(6) for column in out.columns]
    return out.sort_index().fillna(0.0)


def _normalize_events(event_factors: pd.DataFrame) -> pd.DataFrame:
    required = {"date", "symbol", "event_risk_count", "event_impact_score"}
    if event_factors.empty or not required.issubset(event_factors.columns):
        return pd.DataFrame()
    out = event_factors.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.normalize()
    out["symbol"] = out["symbol"].astype(str).str.zfill(6)
    numeric_columns = [
        "event_risk_count",
        "negative_event_count",
        "event_impact_score",
        "event_weighted_impact_score",
        "event_confidence_mean",
        "event_reliability_mean",
        "latest_event_source_reliability",
    ]
    for column in numeric_columns:
        if column not in out.columns:
            out[column] = out["event_impact_score"] if column == "event_weighted_impact_score" else 0.0
        out[column] = pd.to_numeric(out[column], errors="coerce").fillna(0.0)
    for column in ["latest_event_type", "latest_event_title"]:
        if column not in out.columns:
            out[column] = ""
        out[column] = out[column].fillna("").astype(str)
    return out.dropna(subset=["date"]).sort_values(["date", "symbol"])


def _latest_events_asof(events: pd.DataFrame, date: pd.Timestamp, max_age_days: int) -> dict[str, dict[str, object]]:
    asof = pd.Timestamp(date).normalize()
    lower = asof - pd.Timedelta(days=max(0, int(max_age_days)))
    usable = events[(events["date"] <= asof) & (events["date"] >= lower)]
    if usable.empty:
        return {}
    latest = usable.drop_duplicates(["date", "symbol"], keep="last").sort_values("date").groupby("symbol", sort=False).tail(1)
    return {str(row.symbol).zfill(6): row._asdict() for row in latest.itertuples(index=False)}


def _decision_for_event(event_row: dict[str, object], previous_weight: float, config: EventRiskConfig) -> dict[str, object]:
    risk_count = int(float(event_row.get("event_risk_count", 0) or 0))
    negative_count = int(float(event_row.get("negative_event_count", 0) or 0))
    impact = _event_impact_for_decision(event_row)
    confidence = float(event_row.get("event_confidence_mean", 0.0) or 0.0)
    if confidence < config.min_confidence:
        return {"action": "none", "multiplier": 1.0, "reason": "event_confidence_below_threshold"}
    high_risk = risk_count > config.max_event_risk_count
    adverse_impact = impact <= config.min_negative_impact
    adverse_count = negative_count > 0 and impact < 0
    if not (high_risk or adverse_impact or adverse_count):
        return {"action": "none", "multiplier": 1.0, "reason": "event_risk_below_threshold"}
    severe_negative = adverse_impact or adverse_count
    if config.block_new_buy and previous_weight <= 0 and severe_negative:
        return {
            "action": "block_new_buy",
            "multiplier": 0.0,
            "reason": _join_reasons(high_risk, adverse_impact, adverse_count),
        }
    multiplier = min(max(float(config.weight_multiplier), 0.0), 1.0)
    return {
        "action": "reduce_weight",
        "multiplier": multiplier,
        "reason": _join_reasons(high_risk, adverse_impact, adverse_count),
    }


def _join_reasons(high_risk: bool, adverse_impact: bool, adverse_count: bool) -> str:
    reasons = []
    if high_risk:
        reasons.append("event_risk_count_threshold")
    if adverse_impact:
        reasons.append("negative_event_impact_threshold")
    if adverse_count:
        reasons.append("negative_event_count")
    return ";".join(reasons) if reasons else "event_guard"


def _event_impact_for_decision(event_row: dict[str, object]) -> float:
    weighted = event_row.get("event_weighted_impact_score")
    try:
        weighted_value = float(weighted)
    except (TypeError, ValueError):
        weighted_value = float("nan")
    if pd.notna(weighted_value):
        return weighted_value
    try:
        return float(event_row.get("event_impact_score", 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _markdown(report: pd.DataFrame, metadata: dict[str, object]) -> str:
    lines = [
        "# Event Risk Guard Report",
        "",
        "This guard uses structured, timestamped event factors to reduce or block target weights before simulated order generation. It is a risk control, not trading advice.",
        "",
        "## Summary",
        "",
        f"- Enabled: `{metadata.get('enabled', False)}`",
        f"- Adjusted rows: `{metadata.get('adjusted_rows', 0)}`",
        f"- Blocked symbols: `{', '.join(metadata.get('blocked_symbols', [])) if metadata.get('blocked_symbols') else 'none'}`",
        f"- Reduced symbols: `{', '.join(metadata.get('reduced_symbols', [])) if metadata.get('reduced_symbols') else 'none'}`",
        f"- Weight removed: `{float(metadata.get('weight_removed', 0.0)):.4f}`",
        "",
    ]
    if report.empty:
        lines.append("- No target weights were adjusted by event risk.")
        return "\n".join(lines)
    lines.extend(["## Latest Adjustments", ""])
    for row in report.sort_values(["date", "symbol"]).tail(20).itertuples(index=False):
        lines.append(
            f"- `{row.date}` `{row.symbol}` {row.action}: {row.original_weight:.3f} -> {row.adjusted_weight:.3f}; "
            f"impact={row.event_impact_score:.3f}, weighted={row.event_weighted_impact_score:.3f}, "
            f"reliability={row.event_reliability_mean:.2f}, risk_events={int(row.event_risk_count)}, reason={row.reason}"
        )
    return "\n".join(lines)


_REPORT_COLUMNS = [
    "date",
    "symbol",
    "original_weight",
    "adjusted_weight",
    "weight_delta",
    "action",
    "reason",
    "event_risk_count",
    "negative_event_count",
    "event_impact_score",
    "event_weighted_impact_score",
    "event_confidence_mean",
    "event_reliability_mean",
    "latest_event_type",
    "latest_event_title",
]
