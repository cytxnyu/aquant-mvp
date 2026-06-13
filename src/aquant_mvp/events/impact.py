from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class EventImpactStudyResult:
    event_returns: pd.DataFrame
    cohorts: pd.DataFrame
    pit_priors: pd.DataFrame
    summary: dict[str, object]
    markdown: str


EVENT_RETURN_COLUMNS = [
    "event_id",
    "symbol",
    "published_at",
    "effective_trade_date",
    "horizon_days",
    "outcome_known_at",
    "event_type",
    "sentiment",
    "source",
    "source_category",
    "source_reliability",
    "source_reliability_bucket",
    "entity_link_confidence",
    "impact_score",
    "weighted_impact_score",
    "forward_return",
    "expected_excess_return_proxy",
    "return_available",
    "evaluation_scope",
]

COHORT_COLUMNS = [
    "cohort_level",
    "cohort_key",
    "horizon_days",
    "sample_count",
    "mean_return",
    "median_return",
    "positive_rate",
    "mean_excess_return_proxy",
    "return_std",
    "t_stat",
    "avg_source_reliability",
    "avg_entity_link_confidence",
    "evidence_status",
    "can_enter_trusted_model",
    "reason",
]

PIT_PRIOR_COLUMNS = [
    "event_id",
    "symbol",
    "published_at",
    "horizon_days",
    "cohort_key",
    "prior_sample_count",
    "prior_mean_return",
    "prior_positive_rate",
    "prior_mean_excess_return_proxy",
    "prior_outcome_cutoff",
    "pit_ready",
    "no_future_leakage",
    "reason",
]


def analyze_event_impact(
    event_store: pd.DataFrame,
    bars_by_symbol: dict[str, pd.DataFrame],
    horizons: tuple[int, ...] = (1, 5, 20),
    min_prior_rows: int = 20,
) -> EventImpactStudyResult:
    events = _prepare_events(event_store)
    labels = _build_forward_return_labels(bars_by_symbol, horizons)
    if events.empty or not labels:
        empty_returns = pd.DataFrame(columns=EVENT_RETURN_COLUMNS)
        empty_cohorts = pd.DataFrame(columns=COHORT_COLUMNS)
        empty_priors = pd.DataFrame(columns=PIT_PRIOR_COLUMNS)
        summary = _study_summary(empty_returns, empty_cohorts, empty_priors, horizons, min_prior_rows)
        return EventImpactStudyResult(empty_returns, empty_cohorts, empty_priors, summary, _study_markdown(summary, empty_cohorts))

    rows: list[dict[str, object]] = []
    for event in events.itertuples(index=False):
        symbol = str(event.symbol).zfill(6)
        if symbol not in bars_by_symbol:
            continue
        trade_date = _first_trade_date_on_or_after(bars_by_symbol[symbol], pd.Timestamp(event.published_at))
        if trade_date is None:
            continue
        for horizon in horizons:
            label_key = (pd.Timestamp(trade_date).normalize(), symbol, int(horizon))
            label = labels.get(label_key)
            if label is None:
                rows.append(_event_return_row(event, trade_date, horizon, None))
                continue
            rows.append(_event_return_row(event, trade_date, horizon, label))
    event_returns = pd.DataFrame(rows, columns=EVENT_RETURN_COLUMNS)
    cohorts = _build_cohorts(event_returns)
    pit_priors = _build_pit_priors(event_returns, min_prior_rows=min_prior_rows)
    summary = _study_summary(event_returns, cohorts, pit_priors, horizons, min_prior_rows)
    return EventImpactStudyResult(event_returns, cohorts, pit_priors, summary, _study_markdown(summary, cohorts))


def write_event_impact_outputs(
    output_dir: Path,
    result: EventImpactStudyResult,
    *,
    prefix: str = "event_impact_study",
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "event_returns": output_dir / f"{prefix}_returns.csv",
        "cohorts": output_dir / f"{prefix}_cohorts.csv",
        "pit_priors": output_dir / f"{prefix}_pit_priors.csv",
        "json": output_dir / f"{prefix}.json",
        "md": output_dir / f"{prefix}.md",
    }
    result.event_returns.to_csv(paths["event_returns"], index=False)
    result.cohorts.to_csv(paths["cohorts"], index=False)
    result.pit_priors.to_csv(paths["pit_priors"], index=False)
    paths["json"].write_text(json.dumps(result.summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    paths["md"].write_text(result.markdown, encoding="utf-8")
    return paths


def _prepare_events(event_store: pd.DataFrame) -> pd.DataFrame:
    if event_store is None or event_store.empty:
        return pd.DataFrame()
    required = {"published_at", "symbol", "event_type", "sentiment"}
    if not required.issubset(event_store.columns):
        return pd.DataFrame()
    frame = event_store.copy()
    frame["published_at"] = pd.to_datetime(frame["published_at"], errors="coerce")
    frame["symbol"] = frame["symbol"].astype(str).str.replace(r"\D", "", regex=True).str[-6:].str.zfill(6)
    frame = frame.dropna(subset=["published_at"])
    frame = frame[frame["symbol"].str.fullmatch(r"\d{6}", na=False)]
    for column, default in {
        "event_id": "",
        "source": "",
        "source_category": "",
        "source_reliability": 0.0,
        "entity_link_confidence": 0.0,
        "impact_score": 0.0,
        "weighted_impact_score": 0.0,
    }.items():
        if column not in frame.columns:
            frame[column] = default
    frame["event_id"] = frame["event_id"].astype(str)
    missing_id = frame["event_id"].str.len() == 0
    frame.loc[missing_id, "event_id"] = frame.index[missing_id].map(lambda idx: f"event_{idx}")
    return frame.sort_values(["published_at", "symbol", "event_id"]).reset_index(drop=True)


def _build_forward_return_labels(
    bars_by_symbol: dict[str, pd.DataFrame],
    horizons: tuple[int, ...],
) -> dict[tuple[pd.Timestamp, str, int], dict[str, object]]:
    rows = []
    for symbol, bars in bars_by_symbol.items():
        if bars is None or bars.empty or "date" not in bars.columns or "close" not in bars.columns:
            continue
        frame = bars[["date", "close"]].copy()
        frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
        frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
        frame = frame.dropna(subset=["date", "close"]).sort_values("date").reset_index(drop=True)
        if frame.empty:
            continue
        for idx, row in frame.iterrows():
            entry_close = float(row["close"])
            if entry_close <= 0:
                continue
            for horizon in horizons:
                exit_idx = idx + int(horizon)
                if exit_idx >= len(frame):
                    continue
                exit_row = frame.iloc[exit_idx]
                rows.append(
                    {
                        "date": pd.Timestamp(row["date"]).normalize(),
                        "symbol": str(symbol).zfill(6),
                        "horizon_days": int(horizon),
                        "forward_return": float(exit_row["close"] / entry_close - 1.0),
                        "outcome_known_at": pd.Timestamp(exit_row["date"]).normalize(),
                    }
                )
    if not rows:
        return {}
    labels = pd.DataFrame(rows)
    labels["cross_section_mean_return"] = labels.groupby(["date", "horizon_days"])["forward_return"].transform("mean")
    labels["expected_excess_return_proxy"] = labels["forward_return"] - labels["cross_section_mean_return"]
    out = {}
    for row in labels.itertuples(index=False):
        out[(pd.Timestamp(row.date), str(row.symbol).zfill(6), int(row.horizon_days))] = {
            "forward_return": float(row.forward_return),
            "expected_excess_return_proxy": float(row.expected_excess_return_proxy),
            "outcome_known_at": pd.Timestamp(row.outcome_known_at),
        }
    return out


def _event_return_row(event: object, trade_date: pd.Timestamp, horizon: int, label: dict[str, object] | None) -> dict[str, object]:
    reliability = _safe_float(getattr(event, "source_reliability", 0.0))
    return {
        "event_id": str(getattr(event, "event_id", "")),
        "symbol": str(getattr(event, "symbol", "")).zfill(6),
        "published_at": pd.Timestamp(getattr(event, "published_at")).isoformat(),
        "effective_trade_date": pd.Timestamp(trade_date).date().isoformat(),
        "horizon_days": int(horizon),
        "outcome_known_at": pd.Timestamp(label["outcome_known_at"]).date().isoformat() if label else "",
        "event_type": str(getattr(event, "event_type", "")),
        "sentiment": str(getattr(event, "sentiment", "")),
        "source": str(getattr(event, "source", "")),
        "source_category": str(getattr(event, "source_category", "")),
        "source_reliability": reliability,
        "source_reliability_bucket": _reliability_bucket(reliability),
        "entity_link_confidence": _safe_float(getattr(event, "entity_link_confidence", 0.0)),
        "impact_score": _safe_float(getattr(event, "impact_score", 0.0)),
        "weighted_impact_score": _safe_float(getattr(event, "weighted_impact_score", 0.0)),
        "forward_return": float(label["forward_return"]) if label else float("nan"),
        "expected_excess_return_proxy": float(label["expected_excess_return_proxy"]) if label else float("nan"),
        "return_available": bool(label),
        "evaluation_scope": "ex_post_event_outcome;not_a_trade_signal",
    }


def _first_trade_date_on_or_after(bars: pd.DataFrame, timestamp: pd.Timestamp) -> pd.Timestamp | None:
    if bars is None or bars.empty or "date" not in bars.columns:
        return None
    dates = pd.to_datetime(bars["date"], errors="coerce").dropna().sort_values()
    if dates.empty:
        return None
    query = timestamp.normalize()
    candidates = dates[dates.dt.normalize() >= query]
    if candidates.empty:
        return None
    return pd.Timestamp(candidates.iloc[0]).normalize()


def _build_cohorts(event_returns: pd.DataFrame) -> pd.DataFrame:
    if event_returns.empty:
        return pd.DataFrame(columns=COHORT_COLUMNS)
    available = event_returns[event_returns["return_available"].astype(bool)].copy()
    if available.empty:
        return pd.DataFrame(columns=COHORT_COLUMNS)
    cohort_specs = {
        "event_type": ["event_type"],
        "sentiment": ["sentiment"],
        "event_type_sentiment": ["event_type", "sentiment"],
        "event_type_reliability": ["event_type", "source_reliability_bucket"],
        "source_category": ["source_category"],
    }
    rows: list[dict[str, object]] = []
    for level, columns in cohort_specs.items():
        group_cols = ["horizon_days", *columns]
        for keys, part in available.groupby(group_cols, dropna=False):
            if not isinstance(keys, tuple):
                keys = (keys,)
            horizon = int(keys[0])
            values = pd.to_numeric(part["forward_return"], errors="coerce").dropna()
            excess = pd.to_numeric(part["expected_excess_return_proxy"], errors="coerce").dropna()
            sample_count = int(len(values))
            std = float(values.std(ddof=1)) if sample_count > 1 else 0.0
            mean = float(values.mean()) if sample_count else 0.0
            t_stat = float(mean / (std / math.sqrt(sample_count))) if sample_count > 1 and std > 0 else 0.0
            status, reason = _cohort_status(sample_count, t_stat, part)
            rows.append(
                {
                    "cohort_level": level,
                    "cohort_key": "|".join(str(value) for value in keys[1:]),
                    "horizon_days": horizon,
                    "sample_count": sample_count,
                    "mean_return": mean,
                    "median_return": float(values.median()) if sample_count else 0.0,
                    "positive_rate": float((values > 0).mean()) if sample_count else 0.0,
                    "mean_excess_return_proxy": float(excess.mean()) if not excess.empty else 0.0,
                    "return_std": std,
                    "t_stat": t_stat,
                    "avg_source_reliability": float(pd.to_numeric(part["source_reliability"], errors="coerce").fillna(0.0).mean()),
                    "avg_entity_link_confidence": float(pd.to_numeric(part["entity_link_confidence"], errors="coerce").fillna(0.0).mean()),
                    "evidence_status": status,
                    "can_enter_trusted_model": False,
                    "reason": reason,
                }
            )
    return pd.DataFrame(rows, columns=COHORT_COLUMNS).sort_values(
        ["horizon_days", "cohort_level", "sample_count", "cohort_key"],
        ascending=[True, True, False, True],
    )


def _build_pit_priors(event_returns: pd.DataFrame, min_prior_rows: int) -> pd.DataFrame:
    if event_returns.empty:
        return pd.DataFrame(columns=PIT_PRIOR_COLUMNS)
    frame = event_returns.copy()
    frame["published_at_ts"] = pd.to_datetime(frame["published_at"], errors="coerce")
    frame["outcome_known_at_ts"] = pd.to_datetime(frame["outcome_known_at"], errors="coerce")
    frame["cohort_key"] = frame["event_type"].astype(str) + "|" + frame["sentiment"].astype(str)
    rows: list[dict[str, object]] = []
    for row in frame.itertuples(index=False):
        published = pd.Timestamp(row.published_at_ts) if pd.notna(row.published_at_ts) else pd.NaT
        prior = frame[
            (frame["horizon_days"].astype(int) == int(row.horizon_days))
            & (frame["cohort_key"].astype(str) == str(row.cohort_key))
            & (frame["return_available"].astype(bool))
            & (frame["outcome_known_at_ts"] < published)
        ].copy()
        returns = pd.to_numeric(prior["forward_return"], errors="coerce").dropna()
        excess = pd.to_numeric(prior["expected_excess_return_proxy"], errors="coerce").dropna()
        prior_count = int(len(returns))
        cutoff = prior["outcome_known_at_ts"].max() if not prior.empty else pd.NaT
        pit_ready = prior_count >= int(min_prior_rows)
        rows.append(
            {
                "event_id": str(row.event_id),
                "symbol": str(row.symbol).zfill(6),
                "published_at": row.published_at,
                "horizon_days": int(row.horizon_days),
                "cohort_key": str(row.cohort_key),
                "prior_sample_count": prior_count,
                "prior_mean_return": float(returns.mean()) if prior_count else 0.0,
                "prior_positive_rate": float((returns > 0).mean()) if prior_count else 0.0,
                "prior_mean_excess_return_proxy": float(excess.mean()) if not excess.empty else 0.0,
                "prior_outcome_cutoff": pd.Timestamp(cutoff).date().isoformat() if pd.notna(cutoff) else "",
                "pit_ready": bool(pit_ready),
                "no_future_leakage": bool(prior.empty or pd.Timestamp(cutoff) < published),
                "reason": "prior_ready" if pit_ready else f"prior_rows={prior_count}, minimum={min_prior_rows}",
            }
        )
    return pd.DataFrame(rows, columns=PIT_PRIOR_COLUMNS)


def _study_summary(
    event_returns: pd.DataFrame,
    cohorts: pd.DataFrame,
    pit_priors: pd.DataFrame,
    horizons: tuple[int, ...],
    min_prior_rows: int,
) -> dict[str, object]:
    available = event_returns[event_returns["return_available"].astype(bool)] if not event_returns.empty else pd.DataFrame()
    return {
        "event_rows": int(event_returns["event_id"].nunique()) if not event_returns.empty and "event_id" in event_returns.columns else 0,
        "event_return_rows": int(len(event_returns)),
        "available_return_rows": int(len(available)),
        "cohort_rows": int(len(cohorts)),
        "pit_prior_rows": int(len(pit_priors)),
        "pit_ready_rows": int(pit_priors["pit_ready"].astype(bool).sum()) if not pit_priors.empty else 0,
        "no_future_leakage": bool(pit_priors["no_future_leakage"].astype(bool).all()) if not pit_priors.empty else True,
        "horizons": [int(item) for item in horizons],
        "min_prior_rows": int(min_prior_rows),
        "can_enter_trusted_model": False,
        "note": "Historical event impact statistics are audit evidence only. They do not guarantee future returns or provide investment advice.",
    }


def _study_markdown(summary: dict[str, object], cohorts: pd.DataFrame) -> str:
    lines = [
        "# Event Impact Study",
        "",
        "This report tests how structured events behaved historically after publication. It is ex-post audit evidence and a PIT-prior diagnostic, not a trading instruction.",
        "",
        "## Summary",
        "",
        f"- Event rows: `{summary.get('event_rows', 0)}`",
        f"- Event-return rows: `{summary.get('event_return_rows', 0)}`",
        f"- Available return rows: `{summary.get('available_return_rows', 0)}`",
        f"- Cohort rows: `{summary.get('cohort_rows', 0)}`",
        f"- PIT-prior rows: `{summary.get('pit_prior_rows', 0)}`",
        f"- PIT-ready rows: `{summary.get('pit_ready_rows', 0)}`",
        f"- No future leakage: `{summary.get('no_future_leakage', True)}`",
        f"- Can enter trusted model directly: `{summary.get('can_enter_trusted_model', False)}`",
        "",
        "## Top Cohorts",
        "",
    ]
    if cohorts.empty:
        lines.append("- No event cohorts had available forward returns.")
    else:
        display = cohorts.sort_values(["sample_count", "horizon_days"], ascending=[False, True]).head(30)
        for row in display.itertuples(index=False):
            lines.append(
                f"- {row.cohort_level} `{row.cohort_key}` h={int(row.horizon_days)} "
                f"n={int(row.sample_count)}, mean={float(row.mean_return):.4%}, "
                f"positive={float(row.positive_rate):.2%}, t={float(row.t_stat):.2f}, "
                f"status={row.evidence_status}; {row.reason}"
            )
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- Cohort statistics are ex-post validation evidence; they are not direct buy/sell signals.",
            "- `pit_priors` only uses earlier events whose outcome window was already complete before the query event.",
            "- `can_enter_trusted_model` remains false until large-universe walk-forward evidence proves event factors beat baselines.",
        ]
    )
    return "\n".join(lines) + "\n"


def _cohort_status(sample_count: int, t_stat: float, part: pd.DataFrame) -> tuple[str, str]:
    reliability = float(pd.to_numeric(part["source_reliability"], errors="coerce").fillna(0.0).mean()) if not part.empty else 0.0
    link_conf = float(pd.to_numeric(part["entity_link_confidence"], errors="coerce").fillna(0.0).mean()) if not part.empty else 0.0
    if sample_count < 20:
        return "data_insufficient", f"sample_count={sample_count}, minimum=20"
    if reliability < 0.55:
        return "weak", f"avg_source_reliability={reliability:.2f}"
    if link_conf < 0.50:
        return "weak", f"avg_entity_link_confidence={link_conf:.2f}"
    if sample_count < 50 or abs(t_stat) < 1.0:
        return "watchlist", f"sample_count={sample_count}, t_stat={t_stat:.2f}"
    return "candidate_for_walk_forward", "requires walk-forward baseline comparison before model use"


def _reliability_bucket(value: float) -> str:
    if value >= 0.80:
        return "high"
    if value >= 0.55:
        return "medium"
    return "low"


def _safe_float(value: object) -> float:
    try:
        if pd.isna(value):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0
