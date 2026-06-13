from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from aquant_mvp.analysis import FactorAnalysisResult


@dataclass(frozen=True)
class FactorTrustResult:
    registry: pd.DataFrame
    audit: pd.DataFrame
    markdown: str


def build_factor_registry(factor_columns: list[str]) -> pd.DataFrame:
    rows = []
    for factor in factor_columns:
        category = _factor_category(factor)
        rows.append(
            {
                "factor_id": factor,
                "name": factor,
                "category": category,
                "data_dependency": _data_dependency(factor, category),
                "effective_lag": "T+0 close-based, usable from next trade day",
                "economic_rationale": _economic_rationale(factor, category),
                "direction": _expected_direction(factor, category),
                "owner": "aquant_factor_engine",
                "tests": "coverage,IC,RankIC,ICIR,monotonicity,yearly_stability,corr_vif,crowding,leakage_guard",
                "status": "candidate",
                "pit_rule": "computed only from current and historical rows; prediction must trade no earlier than next bar",
            }
        )
    return pd.DataFrame(rows)


def analyze_factor_trust(
    factors: pd.DataFrame,
    analysis: FactorAnalysisResult,
    factor_columns: list[str],
    min_coverage: float = 0.35,
    min_observations: int = 20,
    labels: pd.DataFrame | None = None,
    label_column: str | None = None,
    cost_rate: float = 0.0016,
) -> FactorTrustResult:
    registry = build_factor_registry(factor_columns)
    coverage = analysis.coverage.set_index("factor") if not analysis.coverage.empty else pd.DataFrame()
    ic = analysis.ic_summary.set_index("factor") if not analysis.ic_summary.empty else pd.DataFrame()
    monotonicity = _monotonicity_table(analysis.quantile_returns, factor_columns)
    stability = _stability_table(analysis.stability, factor_columns)
    correlation = _correlation_table(factors, factor_columns)
    half_life = _half_life_table(factors, factor_columns)
    turnover = _turnover_cost_table(factors, factor_columns)
    cost_adjusted = _cost_adjusted_spread_table(analysis.quantile_returns, turnover, factor_columns, cost_rate=cost_rate)
    regime = _regime_stability_table(factors, labels, label_column, factor_columns)

    audit = registry.copy()
    for table in [coverage, ic, monotonicity, stability, correlation, half_life, turnover, cost_adjusted, regime]:
        if table.empty:
            continue
        audit = audit.merge(table.reset_index(), left_on="factor_id", right_on="factor", how="left").drop(columns=["factor"], errors="ignore")

    defaults = {
        "coverage": 0.0,
        "missing_ratio": 1.0,
        "ic_mean": 0.0,
        "rank_ic_mean": 0.0,
        "ic_ir": 0.0,
        "observations": 0,
        "quantile_monotonicity": 0.0,
        "year_count": 0,
        "yearly_positive_ratio": 0.0,
        "max_abs_correlation": 0.0,
        "max_corr_factor": "",
        "vif_proxy": 1.0,
        "half_life_days": 0.0,
        "rank_turnover": 0.0,
        "gross_top_bottom_spread": 0.0,
        "estimated_cost_drag": 0.0,
        "cost_adjusted_spread": 0.0,
        "regime_count": 0,
        "regime_positive_ratio": 0.0,
        "worst_regime_rank_ic": 0.0,
    }
    for column, value in defaults.items():
        if column not in audit.columns:
            audit[column] = value
        if isinstance(value, str):
            audit[column] = audit[column].fillna(value).astype(str)
        else:
            audit[column] = pd.to_numeric(audit[column], errors="coerce").fillna(value)

    audit["leakage_suspect"] = audit["factor_id"].map(_leakage_suspect)
    audit["crowding_flag"] = (
        audit["factor_id"].str.contains("crowding|amount|turnover|volume|shock", case=False, regex=True)
        | audit["max_abs_correlation"].gt(0.95)
        | audit["rank_turnover"].gt(0.85)
    )
    audit["cost_drag_flag"] = audit["cost_adjusted_spread"].lt(0) & audit["rank_turnover"].gt(0.25)
    audit["regime_unstable_flag"] = audit["regime_count"].ge(3) & (
        audit["regime_positive_ratio"].lt(0.34) | audit["worst_regime_rank_ic"].lt(-0.05)
    )
    audit["trust_status"] = audit.apply(
        lambda row: _trust_status(row, min_coverage=min_coverage, min_observations=min_observations),
        axis=1,
    )
    audit["quarantine_reason"] = audit.apply(_quarantine_reason, axis=1)
    registry = registry.drop(columns=["status"]).merge(audit[["factor_id", "trust_status"]], on="factor_id", how="left")
    registry = registry.rename(columns={"trust_status": "status"})
    markdown = _markdown(audit)
    return FactorTrustResult(registry=registry, audit=audit, markdown=markdown)


def write_factor_trust_report(result: FactorTrustResult, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "factor_registry": output_dir / "factor_registry.csv",
        "factor_trust_audit": output_dir / "factor_trust_audit.csv",
        "factor_trust_report": output_dir / "factor_trust_report.md",
    }
    result.registry.to_csv(paths["factor_registry"], index=False)
    result.audit.to_csv(paths["factor_trust_audit"], index=False)
    paths["factor_trust_report"].write_text(result.markdown, encoding="utf-8")
    return paths


def _factor_category(factor: str) -> str:
    rules = [
        ("price_volume", ["momentum", "reversal", "ma_", "ema_", "macd", "rsi", "kdj", "cci", "williams", "bollinger", "breakout", "breakdown", "position"]),
        ("volatility_risk", ["volatility", "drawdown", "atr", "amplitude", "tail", "skew", "kurt", "range_compression"]),
        ("liquidity_flow", ["amount", "turnover", "volume", "obv", "money_flow", "signed", "pvt", "illiquidity"]),
        ("trend_shape", ["shadow", "body", "streak", "gap", "limit", "efficiency", "trend_strength", "alignment", "pullback"]),
        ("market_environment", ["market_", "cs_"]),
        ("style_exposure", ["beta", "size", "value", "growth", "quality"]),
        ("event_proxy", ["dragon", "announcement", "news", "event"]),
        ("fundamental", ["roe", "roic", "margin", "profit", "revenue", "cashflow", "debt"]),
        ("valuation", ["pe", "pb", "ps", "dividend", "ev_"]),
    ]
    lower = factor.lower()
    for category, keywords in rules:
        if any(keyword in lower for keyword in keywords):
            return category
    return "technical_other"


def _data_dependency(factor: str, category: str) -> str:
    if category in {"price_volume", "volatility_risk", "liquidity_flow", "trend_shape", "market_environment", "technical_other"}:
        return "daily_bar"
    if category == "fundamental":
        return "financial with announce_date"
    if category == "valuation":
        return "valuation with effective_date"
    if category == "event_proxy":
        return "event_store with published_at/effective_date"
    return "feature_store"


def _economic_rationale(factor: str, category: str) -> str:
    text = {
        "price_volume": "captures trend, reversal, and price-location effects that may proxy investor under/over-reaction",
        "volatility_risk": "captures downside risk, instability, and volatility risk premium",
        "liquidity_flow": "captures attention, liquidity, and fund-flow pressure",
        "trend_shape": "captures candle shape and path behavior linked to supply-demand imbalance",
        "market_environment": "captures cross-sectional and broad-market state that changes factor payoffs",
        "style_exposure": "controls common style exposures so alpha is not just risk loading",
        "event_proxy": "captures structured news/announcement shocks after public release",
        "fundamental": "captures business quality and growth known after disclosure",
        "valuation": "captures relative valuation and re-rating pressure",
        "technical_other": "technical descriptor; must earn inclusion through out-of-sample evidence",
    }
    return text.get(category, "candidate factor with required empirical validation")


def _expected_direction(factor: str, category: str) -> str:
    lower = factor.lower()
    if any(token in lower for token in ["volatility", "drawdown", "illiquidity", "crowding", "upper_shadow", "limit_down"]):
        return "lower_is_better"
    if any(token in lower for token in ["momentum", "money_flow", "breakout", "trend_strength", "market_breadth"]):
        return "higher_is_better"
    if category in {"market_environment", "style_exposure"}:
        return "control_or_regime_dependent"
    return "empirical"


def _monotonicity_table(quantile_returns: pd.DataFrame, factor_columns: list[str]) -> pd.DataFrame:
    if quantile_returns.empty:
        return pd.DataFrame({"factor": factor_columns, "quantile_monotonicity": 0.0})
    grouped = quantile_returns.groupby(["factor", "quantile"])["mean_forward_return"].mean().reset_index()
    rows = []
    for factor in factor_columns:
        part = grouped[grouped["factor"] == factor]
        if len(part) < 3 or part["mean_forward_return"].nunique() < 2:
            value = 0.0
        else:
            value = float(part["quantile"].corr(part["mean_forward_return"], method="spearman") or 0.0)
        rows.append({"factor": factor, "quantile_monotonicity": value})
    return pd.DataFrame(rows).set_index("factor")


def _stability_table(stability: pd.DataFrame, factor_columns: list[str]) -> pd.DataFrame:
    rows = []
    for factor in factor_columns:
        part = stability[stability["factor"] == factor] if not stability.empty and "factor" in stability.columns else pd.DataFrame()
        if part.empty:
            rows.append({"factor": factor, "year_count": 0, "yearly_positive_ratio": 0.0})
            continue
        rows.append(
            {
                "factor": factor,
                "year_count": int(part["year"].nunique()),
                "yearly_positive_ratio": float((pd.to_numeric(part["rank_ic_mean"], errors="coerce") > 0).mean()),
            }
        )
    return pd.DataFrame(rows).set_index("factor")


def _correlation_table(factors: pd.DataFrame, factor_columns: list[str]) -> pd.DataFrame:
    usable = factors[factor_columns].replace([np.inf, -np.inf], np.nan).dropna(how="all")
    if usable.empty:
        return pd.DataFrame({"factor": factor_columns, "max_abs_correlation": 0.0, "max_corr_factor": "", "vif_proxy": 1.0}).set_index("factor")
    sample = usable.tail(min(len(usable), 10000))
    sample = sample.loc[:, sample.nunique(dropna=True) > 1]
    corr = sample.corr(numeric_only=True).abs() if not sample.empty else pd.DataFrame()
    rows = []
    for factor in factor_columns:
        if factor not in corr.columns:
            max_corr = 0.0
            max_corr_factor = ""
        else:
            values = corr[factor].drop(labels=[factor], errors="ignore").dropna()
            max_corr = float(values.max()) if not values.empty else 0.0
            max_corr_factor = str(values.idxmax()) if not values.empty else ""
        vif_proxy = float(1.0 / max(0.05, 1 - min(max_corr, 0.999) ** 2))
        rows.append({"factor": factor, "max_abs_correlation": max_corr, "max_corr_factor": max_corr_factor, "vif_proxy": vif_proxy})
    return pd.DataFrame(rows).set_index("factor")


def _half_life_table(factors: pd.DataFrame, factor_columns: list[str]) -> pd.DataFrame:
    rows = []
    for factor in factor_columns:
        if factor not in factors.columns:
            rows.append({"factor": factor, "half_life_days": 0.0})
            continue
        series = factors[factor].replace([np.inf, -np.inf], np.nan)
        autocorrs = []
        for _symbol, part in series.groupby(level="symbol", sort=False):
            value = part.astype(float).autocorr(lag=1)
            if value is not None and not np.isnan(value):
                autocorrs.append(float(np.clip(value, 0.0, 0.999)))
        rho = float(np.mean(autocorrs)) if autocorrs else 0.0
        half_life = float(np.log(0.5) / np.log(rho)) if rho > 0 and rho != 1 else 0.0
        rows.append({"factor": factor, "half_life_days": max(0.0, min(252.0, half_life))})
    return pd.DataFrame(rows).set_index("factor")


def _turnover_cost_table(factors: pd.DataFrame, factor_columns: list[str]) -> pd.DataFrame:
    rows = []
    for factor in factor_columns:
        if factor not in factors.columns:
            rows.append({"factor": factor, "rank_turnover": 0.0})
            continue
        ranks = factors[factor].groupby(level="date").rank(pct=True)
        daily_turnover = ranks.groupby(level="symbol", sort=False).diff().abs().groupby(level="date").mean()
        rows.append({"factor": factor, "rank_turnover": float(daily_turnover.mean()) if not daily_turnover.empty else 0.0})
    return pd.DataFrame(rows).set_index("factor")


def _cost_adjusted_spread_table(
    quantile_returns: pd.DataFrame,
    turnover: pd.DataFrame,
    factor_columns: list[str],
    cost_rate: float,
) -> pd.DataFrame:
    turnover_lookup = turnover["rank_turnover"] if not turnover.empty and "rank_turnover" in turnover.columns else pd.Series(dtype=float)
    rows = []
    if quantile_returns.empty:
        for factor in factor_columns:
            rows.append(
                {
                    "factor": factor,
                    "gross_top_bottom_spread": 0.0,
                    "estimated_cost_drag": float(turnover_lookup.get(factor, 0.0) * cost_rate),
                    "cost_adjusted_spread": 0.0,
                }
            )
        return pd.DataFrame(rows).set_index("factor")
    grouped = quantile_returns.groupby(["factor", "quantile"])["mean_forward_return"].mean().reset_index()
    for factor in factor_columns:
        part = grouped[grouped["factor"] == factor]
        if part.empty:
            gross = 0.0
        else:
            low_q = part["quantile"].min()
            high_q = part["quantile"].max()
            low = float(part.loc[part["quantile"] == low_q, "mean_forward_return"].mean())
            high = float(part.loc[part["quantile"] == high_q, "mean_forward_return"].mean())
            gross = high - low
        cost_drag = float(turnover_lookup.get(factor, 0.0) * cost_rate)
        rows.append(
            {
                "factor": factor,
                "gross_top_bottom_spread": gross,
                "estimated_cost_drag": cost_drag,
                "cost_adjusted_spread": gross - cost_drag,
            }
        )
    return pd.DataFrame(rows).set_index("factor")


def _regime_stability_table(
    factors: pd.DataFrame,
    labels: pd.DataFrame | None,
    label_column: str | None,
    factor_columns: list[str],
) -> pd.DataFrame:
    if labels is None or not label_column or label_column not in labels.columns or "market_mean_return" not in factors.columns:
        return pd.DataFrame(
            {
                "factor": factor_columns,
                "regime_count": 0,
                "regime_positive_ratio": 0.0,
                "worst_regime_rank_ic": 0.0,
                "regime_stability_note": "regime_data_unavailable",
            }
        ).set_index("factor")
    selected_columns = list(dict.fromkeys(column for column in [*factor_columns, "market_mean_return", "market_breadth"] if column in factors.columns))
    joined = factors[selected_columns].join(
        labels[[label_column]],
        how="inner",
    )
    if joined.empty:
        return pd.DataFrame(
            {
                "factor": factor_columns,
                "regime_count": 0,
                "regime_positive_ratio": 0.0,
                "worst_regime_rank_ic": 0.0,
                "regime_stability_note": "joined_data_empty",
            }
        ).set_index("factor")
    date_market = joined.groupby(level="date")["market_mean_return"].mean()
    low = float(date_market.quantile(0.33))
    high = float(date_market.quantile(0.67))

    def regime_for_date(value: float) -> str:
        if value <= low:
            return "bearish"
        if value >= high:
            return "bullish"
        return "sideways"

    regime_map = date_market.map(regime_for_date)
    frame = joined.reset_index()
    frame["regime"] = frame["date"].map(regime_map)
    rows = []
    for factor in factor_columns:
        if factor not in frame.columns:
            rows.append(
                {
                    "factor": factor,
                    "regime_count": 0,
                    "regime_positive_ratio": 0.0,
                    "worst_regime_rank_ic": 0.0,
                    "regime_stability_note": "factor_missing",
                }
            )
            continue
        regime_ics = []
        for _regime, part in frame.dropna(subset=[factor, label_column]).groupby("regime", sort=True):
            if len(part) < 10 or part[factor].nunique() < 2 or part[label_column].nunique() < 2:
                continue
            value = part[factor].rank(method="average").corr(part[label_column].rank(method="average"))
            if value is not None and not np.isnan(value):
                regime_ics.append(float(value))
        if not regime_ics:
            rows.append(
                {
                    "factor": factor,
                    "regime_count": 0,
                    "regime_positive_ratio": 0.0,
                    "worst_regime_rank_ic": 0.0,
                    "regime_stability_note": "insufficient_regime_observations",
                }
            )
            continue
        rows.append(
            {
                "factor": factor,
                "regime_count": int(len(regime_ics)),
                "regime_positive_ratio": float((np.array(regime_ics) > 0).mean()),
                "worst_regime_rank_ic": float(np.min(regime_ics)),
                "regime_stability_note": "bullish_sideways_bearish_from_pit_market_mean_return",
            }
        )
    return pd.DataFrame(rows).set_index("factor")


def _leakage_suspect(factor: str) -> bool:
    lower = factor.lower()
    return any(token in lower for token in ["future_", "label_", "target_", "next_", "forward_"])


def _trust_status(row: pd.Series, min_coverage: float, min_observations: int) -> str:
    if bool(row["leakage_suspect"]):
        return "quarantine"
    if float(row["coverage"]) < min_coverage or int(row["observations"]) < min_observations:
        return "quarantine"
    if abs(float(row["rank_ic_mean"])) < 0.002 and abs(float(row["quantile_monotonicity"])) < 0.10:
        return "quarantine"
    if float(row["max_abs_correlation"]) > 0.98 or bool(row["crowding_flag"]):
        return "watchlist"
    if bool(row.get("cost_drag_flag", False)) or bool(row.get("regime_unstable_flag", False)):
        return "watchlist"
    if float(row["year_count"]) >= 2 and float(row["yearly_positive_ratio"]) < 0.35:
        return "watchlist"
    return "approved"


def _quarantine_reason(row: pd.Series) -> str:
    reasons = []
    if bool(row["leakage_suspect"]):
        reasons.append("leakage_suspect")
    if float(row["coverage"]) < 0.35:
        reasons.append("low_coverage")
    if int(row["observations"]) < 20:
        reasons.append("low_observations")
    if abs(float(row["rank_ic_mean"])) < 0.002 and abs(float(row["quantile_monotonicity"])) < 0.10:
        reasons.append("weak_empirical_signal")
    if float(row["max_abs_correlation"]) > 0.98:
        peer = str(row.get("max_corr_factor", ""))
        reasons.append(f"near_duplicate_factor:{peer}" if peer else "near_duplicate_factor")
    if bool(row["crowding_flag"]):
        reasons.append("crowding_or_cost_watch")
    if bool(row.get("cost_drag_flag", False)):
        reasons.append("negative_after_estimated_cost")
    if bool(row.get("regime_unstable_flag", False)):
        reasons.append("regime_unstable")
    return ";".join(reasons) or "none"


def _markdown(audit: pd.DataFrame) -> str:
    counts = audit["trust_status"].value_counts().to_dict() if not audit.empty else {}
    lines = [
        "# Factor Trust Report",
        "",
        "## Summary",
        "",
        f"- Total factors: {len(audit)}",
        f"- Approved: {counts.get('approved', 0)}",
        f"- Watchlist: {counts.get('watchlist', 0)}",
        f"- Quarantine: {counts.get('quarantine', 0)}",
        "",
        "## Rules",
        "",
        "- Factors require economic rationale and point-in-time inputs.",
        "- Low coverage, weak empirical signal, suspected leakage, near-duplicate/crowded factors, negative cost-adjusted spread, and regime instability are excluded or downgraded.",
        "- Approval here is a research gate, not a guarantee of future profitability.",
        "",
        "## Top Approved Candidates",
        "",
    ]
    approved = audit[audit["trust_status"] == "approved"].sort_values("rank_ic_mean", ascending=False).head(20)
    if approved.empty:
        lines.append("- No approved factors under current sample.")
    else:
        for row in approved.itertuples(index=False):
            lines.append(
                f"- `{row.factor_id}`: category={row.category}, coverage={row.coverage:.2f}, "
                f"rank_ic={row.rank_ic_mean:.4f}, net_spread={row.cost_adjusted_spread:.4f}, "
                f"regime_pos={row.regime_positive_ratio:.2f}, monotonicity={row.quantile_monotonicity:.3f}"
            )
    lines.extend(["", "## Cost/Regime Watchlist", ""])
    watch = audit[
        (audit["trust_status"] == "watchlist")
        & (audit.get("cost_drag_flag", False) | audit.get("regime_unstable_flag", False))
    ].head(20)
    if watch.empty:
        lines.append("- No cost/regime watchlist factors under current sample.")
    else:
        for row in watch.itertuples(index=False):
            lines.append(
                f"- `{row.factor_id}`: net_spread={row.cost_adjusted_spread:.4f}, "
                f"rank_turnover={row.rank_turnover:.3f}, regime_pos={row.regime_positive_ratio:.2f}, "
                f"worst_regime_rank_ic={row.worst_regime_rank_ic:.4f}"
            )
    lines.extend(["", "## Quarantine Examples", ""])
    quarantine = audit[audit["trust_status"] == "quarantine"].head(20)
    if quarantine.empty:
        lines.append("- No quarantined factors.")
    else:
        for row in quarantine.itertuples(index=False):
            lines.append(f"- `{row.factor_id}`: {row.quarantine_reason}")
    return "\n".join(lines)
