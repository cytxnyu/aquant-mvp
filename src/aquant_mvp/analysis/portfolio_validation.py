from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from aquant_mvp.config import BacktestConfig, RiskConfig, StrategyConfig


@dataclass(frozen=True)
class PortfolioValidationResult:
    checks: pd.DataFrame
    annual: pd.DataFrame
    costs: pd.DataFrame
    summary: dict[str, object]
    markdown: str


def validate_portfolio_backtest(
    equity_curve: pd.DataFrame,
    trades: pd.DataFrame,
    rebalances: pd.DataFrame,
    metrics: dict[str, Any],
    *,
    constrained_equity_curve: pd.DataFrame | None = None,
    constrained_trades: pd.DataFrame | None = None,
    constrained_rebalances: pd.DataFrame | None = None,
    constrained_metrics: dict[str, Any] | None = None,
    constraint_report: pd.DataFrame | None = None,
    constraint_daily: pd.DataFrame | None = None,
    event_attribution_daily: pd.DataFrame | None = None,
    event_guard_metadata: dict[str, Any] | None = None,
    event_attribution_required: bool = False,
    backtest_config: BacktestConfig | None = None,
    strategy_config: StrategyConfig | None = None,
    risk_config: RiskConfig | None = None,
) -> PortfolioValidationResult:
    """Audit whether a portfolio backtest is traceable enough for v0.4 validation.

    The audit is intentionally evidence-oriented. It does not certify that a
    strategy is profitable; it checks whether the run exposes enough cost,
    stability, constraint, and event-risk evidence to be challenged.
    """

    eval_equity = constrained_equity_curve if constrained_equity_curve is not None and not constrained_equity_curve.empty else equity_curve
    eval_trades = constrained_trades if constrained_trades is not None else trades
    eval_rebalances = constrained_rebalances if constrained_rebalances is not None else rebalances
    eval_metrics = constrained_metrics or metrics or {}

    annual = _annual_metrics(eval_equity)
    costs = _cost_summary(eval_trades, backtest_config)
    checks = _validation_checks(
        eval_equity,
        eval_trades,
        eval_rebalances,
        eval_metrics,
        annual,
        costs,
        constraint_report=constraint_report,
        constraint_daily=constraint_daily,
        event_attribution_daily=event_attribution_daily,
        event_guard_metadata=event_guard_metadata,
        event_attribution_required=event_attribution_required,
        strategy_config=strategy_config,
        risk_config=risk_config,
    )
    summary = _summary(eval_metrics, checks, annual, costs, constraint_report, constraint_daily)
    return PortfolioValidationResult(
        checks=checks,
        annual=annual,
        costs=costs,
        summary=summary,
        markdown=_markdown(summary, checks, annual, costs),
    )


def write_portfolio_validation_outputs(
    output_dir: Path,
    result: PortfolioValidationResult,
    *,
    prefix: str = "portfolio_validation",
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "checks": output_dir / f"{prefix}_checks.csv",
        "annual": output_dir / f"{prefix}_annual.csv",
        "costs": output_dir / f"{prefix}_costs.csv",
        "summary": output_dir / f"{prefix}_summary.json",
        "markdown": output_dir / f"{prefix}_report.md",
    }
    result.checks.to_csv(paths["checks"], index=False)
    result.annual.to_csv(paths["annual"], index=False)
    result.costs.to_csv(paths["costs"], index=False)
    paths["summary"].write_text(json.dumps(result.summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    paths["markdown"].write_text(result.markdown, encoding="utf-8")
    return paths


def _annual_metrics(equity_curve: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "year",
        "start_equity",
        "end_equity",
        "year_return",
        "annual_volatility",
        "sharpe",
        "max_drawdown",
        "trading_days",
        "stability_status",
    ]
    if equity_curve.empty or not {"date", "equity"}.issubset(equity_curve.columns):
        return pd.DataFrame(columns=columns)
    frame = equity_curve.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["equity"] = pd.to_numeric(frame["equity"], errors="coerce")
    frame = frame.dropna(subset=["date", "equity"]).sort_values("date")
    if frame.empty:
        return pd.DataFrame(columns=columns)
    if "daily_return" not in frame.columns:
        frame["daily_return"] = frame["equity"].pct_change().fillna(0.0)
    if "drawdown" not in frame.columns:
        frame["drawdown"] = frame["equity"] / frame["equity"].cummax() - 1.0
    frame["year"] = frame["date"].dt.year

    rows = []
    for year, part in frame.groupby("year", sort=True):
        returns = pd.to_numeric(part["daily_return"], errors="coerce").dropna()
        start = float(part["equity"].iloc[0])
        end = float(part["equity"].iloc[-1])
        year_return = end / start - 1.0 if start > 0 else 0.0
        vol = float(returns.std(ddof=0) * np.sqrt(252)) if len(returns) > 1 else 0.0
        sharpe = float(returns.mean() / returns.std(ddof=0) * np.sqrt(252)) if returns.std(ddof=0) > 0 else 0.0
        max_drawdown = float(pd.to_numeric(part["drawdown"], errors="coerce").min())
        status = "positive" if year_return > 0 else "negative"
        if max_drawdown <= -0.20:
            status = "drawdown_watch"
        rows.append(
            {
                "year": int(year),
                "start_equity": start,
                "end_equity": end,
                "year_return": float(year_return),
                "annual_volatility": vol,
                "sharpe": sharpe,
                "max_drawdown": max_drawdown,
                "trading_days": int(len(part)),
                "stability_status": status,
            }
        )
    return pd.DataFrame(rows, columns=columns)


def _cost_summary(trades: pd.DataFrame, backtest_config: BacktestConfig | None) -> pd.DataFrame:
    columns = [
        "scope",
        "trade_count",
        "gross_value",
        "fee",
        "tax",
        "estimated_slippage_cost",
        "total_cost",
        "avg_cost_bps",
    ]
    if trades is None or trades.empty:
        return pd.DataFrame(
            [
                {
                    "scope": "all",
                    "trade_count": 0,
                    "gross_value": 0.0,
                    "fee": 0.0,
                    "tax": 0.0,
                    "estimated_slippage_cost": 0.0,
                    "total_cost": 0.0,
                    "avg_cost_bps": 0.0,
                }
            ],
            columns=columns,
        )
    frame = trades.copy()
    gross = pd.to_numeric(frame.get("gross_value", 0.0), errors="coerce").fillna(0.0).abs()
    fee = pd.to_numeric(frame.get("fee", 0.0), errors="coerce").fillna(0.0)
    tax = pd.to_numeric(frame.get("tax", 0.0), errors="coerce").fillna(0.0)
    if "slippage_rate" in frame.columns:
        slippage_rate = pd.to_numeric(frame["slippage_rate"], errors="coerce").fillna(0.0).abs()
    else:
        slippage_rate = pd.Series(float(backtest_config.slippage_rate) if backtest_config else 0.0, index=frame.index)
    slippage_cost = gross * slippage_rate
    total_cost = fee + tax + slippage_cost
    side = frame["side"].astype(str).str.upper() if "side" in frame.columns else pd.Series("", index=frame.index)
    rows = []
    for scope, mask in {
        "all": pd.Series(True, index=frame.index),
        "buy": side.eq("BUY"),
        "sell": side.eq("SELL"),
    }.items():
        scoped_gross = float(gross[mask].sum())
        scoped_cost = float(total_cost[mask].sum())
        rows.append(
            {
                "scope": scope,
                "trade_count": int(mask.sum()),
                "gross_value": scoped_gross,
                "fee": float(fee[mask].sum()),
                "tax": float(tax[mask].sum()),
                "estimated_slippage_cost": float(slippage_cost[mask].sum()),
                "total_cost": scoped_cost,
                "avg_cost_bps": float(scoped_cost / scoped_gross * 10000) if scoped_gross > 0 else 0.0,
            }
        )
    return pd.DataFrame(rows, columns=columns)


def _validation_checks(
    equity_curve: pd.DataFrame,
    trades: pd.DataFrame,
    rebalances: pd.DataFrame,
    metrics: dict[str, Any],
    annual: pd.DataFrame,
    costs: pd.DataFrame,
    *,
    constraint_report: pd.DataFrame | None,
    constraint_daily: pd.DataFrame | None,
    event_attribution_daily: pd.DataFrame | None,
    event_guard_metadata: dict[str, Any] | None,
    event_attribution_required: bool,
    strategy_config: StrategyConfig | None,
    risk_config: RiskConfig | None,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    def add(gate: str, passed: bool, severity: str, observed: object, threshold: object, detail: str) -> None:
        status = "pass" if passed else severity
        rows.append(
            {
                "gate": gate,
                "status": status,
                "passed": bool(passed),
                "severity": "info" if passed else severity,
                "observed": observed,
                "threshold": threshold,
                "detail": detail,
            }
        )

    add("equity_curve_present", not equity_curve.empty, "fail", len(equity_curve), ">0 rows", "Backtest must write daily equity evidence.")
    add("rebalance_trace_present", not rebalances.empty, "fail", len(rebalances), ">0 rows", "Rebalance rows are required for turnover and T+1 traceability.")
    add("trade_trace_present", not trades.empty, "warn", len(trades), ">0 rows", "No trades can be valid for tiny samples, but it is not enough for strategy validation.")

    trade_count = int(float(metrics.get("trade_count", len(trades)) or 0))
    total_cost = _lookup_cost(costs, "all", "total_cost")
    gross_value = _lookup_cost(costs, "all", "gross_value")
    add("costs_recorded", trade_count == 0 or total_cost >= 0.0, "fail", total_cost, ">=0", "Fees, taxes, and slippage-cost proxy must be present and non-negative.")
    add("cost_after_metrics_available", {"total_return", "max_drawdown", "sharpe", "calmar"}.issubset(metrics.keys()), "fail", sorted(metrics.keys()), "required metrics", "Strategy validation must use cost-after backtest metrics.")

    max_turnover = float(strategy_config.max_turnover) if strategy_config else 1.0
    avg_turnover = float(metrics.get("avg_turnover", 0.0) or 0.0)
    add("turnover_within_config", avg_turnover <= max_turnover * 1.05 if max_turnover > 0 else True, "warn", round(avg_turnover, 6), f"<= {max_turnover}", "Average realized turnover should respect the configured turnover budget.")

    max_drawdown_limit = float(risk_config.max_drawdown) if risk_config else 0.10
    max_drawdown = float(metrics.get("max_drawdown", 0.0) or 0.0)
    add("drawdown_within_risk_budget", abs(min(0.0, max_drawdown)) <= max_drawdown_limit * 1.50, "warn", round(max_drawdown, 6), f">= {-max_drawdown_limit * 1.50:.4f}", "Drawdown outside the risk budget is evidence against deployment.")

    add("annual_stability_available", not annual.empty, "fail", len(annual), ">=1 year rows", "Year-by-year stability must be visible.")
    if not annual.empty:
        positive_ratio = float((annual["year_return"] > 0).mean())
        add("annual_positive_ratio", positive_ratio >= 0.50, "warn", round(positive_ratio, 4), ">=0.50", "A strategy that only works in aggregate should remain challenged by year.")
        add("worst_year_not_extreme", float(annual["year_return"].min()) > -0.50, "warn", round(float(annual["year_return"].min()), 4), "> -0.50", "Extreme bad years require separate explanation.")

    constraints_present = constraint_report is not None and constraint_daily is not None
    add("portfolio_constraints_audited", constraints_present, "fail", constraints_present, True, "Constraint report and daily summary must be written.")
    if constraints_present and constraint_daily is not None and not constraint_daily.empty:
        single_cap = min(
            float(strategy_config.max_single_weight) if strategy_config else 0.30,
            float(risk_config.max_single_weight) if risk_config else 0.30,
        )
        theme_cap = float(strategy_config.max_theme_weight) if strategy_config else 0.45
        max_single = float(pd.to_numeric(constraint_daily["max_single_weight_after"], errors="coerce").max())
        max_theme = float(pd.to_numeric(constraint_daily["max_theme_weight_after"], errors="coerce").max())
        max_daily_turnover = float(pd.to_numeric(constraint_daily["turnover_after"], errors="coerce").max())
        add("single_name_cap_enforced", max_single <= single_cap + 1e-6, "fail", round(max_single, 6), f"<= {single_cap}", "Single-name exposure cap must hold after constraints.")
        add("theme_cap_enforced", max_theme <= theme_cap + 1e-6, "fail", round(max_theme, 6), f"<= {theme_cap}", "Theme exposure cap must hold after constraints.")
        add("daily_turnover_cap_enforced", max_daily_turnover <= max_turnover + 1e-6 if max_turnover > 0 else True, "fail", round(max_daily_turnover, 6), f"<= {max_turnover}", "Daily target turnover cap must hold after constraints.")

    attribution_rows = int(len(event_attribution_daily)) if event_attribution_daily is not None else 0
    add("event_attribution_available", attribution_rows > 0 if event_attribution_required else True, "warn", attribution_rows, ">0 when --with-news", "News-aware portfolio runs must write event attribution evidence.")
    guard_enabled = bool((event_guard_metadata or {}).get("enabled", False))
    add("event_guard_evidence_available", guard_enabled if event_attribution_required else True, "warn", guard_enabled, "true when --with-news", "News-aware portfolio runs should record event-risk guard metadata.")

    add("capacity_proxy_available", gross_value >= 0.0 and "avg_cost_bps" in costs.columns, "warn", round(float(gross_value), 4), "cost table with gross/cost bps", "Free-source capacity is approximate, so the audit requires traded value and cost-bps evidence.")
    return pd.DataFrame(rows)


def _summary(
    metrics: dict[str, Any],
    checks: pd.DataFrame,
    annual: pd.DataFrame,
    costs: pd.DataFrame,
    constraint_report: pd.DataFrame | None,
    constraint_daily: pd.DataFrame | None,
) -> dict[str, object]:
    failed = checks[checks["status"] == "fail"]["gate"].tolist() if not checks.empty else []
    warned = checks[checks["status"] == "warn"]["gate"].tolist() if not checks.empty else []
    if failed:
        status = "failed"
    elif warned:
        status = "watchlist"
    else:
        status = "passed"
    annual_positive_ratio = float((annual["year_return"] > 0).mean()) if not annual.empty else 0.0
    worst_year_return = float(annual["year_return"].min()) if not annual.empty else 0.0
    return {
        "validation_status": status,
        "validation_passed": not failed,
        "failed_checks": failed,
        "warning_checks": warned,
        "check_count": int(len(checks)),
        "pass_count": int((checks["status"] == "pass").sum()) if not checks.empty else 0,
        "warn_count": int((checks["status"] == "warn").sum()) if not checks.empty else 0,
        "fail_count": int((checks["status"] == "fail").sum()) if not checks.empty else 0,
        "total_return": float(metrics.get("total_return", 0.0) or 0.0),
        "annual_return": float(metrics.get("annual_return", 0.0) or 0.0),
        "max_drawdown": float(metrics.get("max_drawdown", 0.0) or 0.0),
        "sharpe": float(metrics.get("sharpe", 0.0) or 0.0),
        "calmar": float(metrics.get("calmar", 0.0) or 0.0),
        "avg_turnover": float(metrics.get("avg_turnover", 0.0) or 0.0),
        "trade_count": float(metrics.get("trade_count", 0.0) or 0.0),
        "annual_years": int(len(annual)),
        "annual_positive_ratio": annual_positive_ratio,
        "worst_year_return": worst_year_return,
        "total_cost": _lookup_cost(costs, "all", "total_cost"),
        "avg_cost_bps": _lookup_cost(costs, "all", "avg_cost_bps"),
        "constraint_adjustment_rows": int(len(constraint_report)) if constraint_report is not None else 0,
        "constraint_days": int(len(constraint_daily)) if constraint_daily is not None else 0,
        "note": "Portfolio validation is evidence for research quality only; it is not live-trading permission.",
    }


def _lookup_cost(costs: pd.DataFrame, scope: str, column: str) -> float:
    if costs.empty or column not in costs.columns or "scope" not in costs.columns:
        return 0.0
    part = costs[costs["scope"] == scope]
    if part.empty:
        return 0.0
    return float(pd.to_numeric(part[column], errors="coerce").fillna(0.0).iloc[0])


def _markdown(
    summary: dict[str, object],
    checks: pd.DataFrame,
    annual: pd.DataFrame,
    costs: pd.DataFrame,
) -> str:
    lines = [
        "# Portfolio Validation Report",
        "",
        "This report challenges whether the portfolio backtest is traceable and stable enough for research review. It does not certify future returns and is not investment advice.",
        "",
        "## Summary",
        "",
        f"- Validation status: `{summary.get('validation_status', 'unknown')}`",
        f"- Failed checks: `{summary.get('fail_count', 0)}`; warnings: `{summary.get('warn_count', 0)}`; passes: `{summary.get('pass_count', 0)}`",
        f"- Total/annual return: `{float(summary.get('total_return', 0.0)):.4f}` / `{float(summary.get('annual_return', 0.0)):.4f}`",
        f"- Max drawdown: `{float(summary.get('max_drawdown', 0.0)):.4f}`; Sharpe: `{float(summary.get('sharpe', 0.0)):.4f}`; Calmar: `{float(summary.get('calmar', 0.0)):.4f}`",
        f"- Avg turnover: `{float(summary.get('avg_turnover', 0.0)):.4f}`; total cost: `{float(summary.get('total_cost', 0.0)):.2f}`; avg cost bps: `{float(summary.get('avg_cost_bps', 0.0)):.2f}`",
        f"- Annual positive ratio: `{float(summary.get('annual_positive_ratio', 0.0)):.4f}`; worst year: `{float(summary.get('worst_year_return', 0.0)):.4f}`",
        "",
    ]
    if not checks.empty:
        lines.extend(["## Gate Results", ""])
        for row in checks.itertuples(index=False):
            lines.append(f"- `{row.status}` `{row.gate}` observed=`{row.observed}` threshold=`{row.threshold}`")
        lines.append("")
    if not annual.empty:
        lines.extend(["## Annual Stability", ""])
        for row in annual.itertuples(index=False):
            lines.append(
                f"- `{row.year}` return `{row.year_return:.4f}`, drawdown `{row.max_drawdown:.4f}`, "
                f"Sharpe `{row.sharpe:.4f}`, status `{row.stability_status}`"
            )
        lines.append("")
    if not costs.empty:
        lines.extend(["## Cost Evidence", ""])
        for row in costs.itertuples(index=False):
            lines.append(
                f"- `{row.scope}` trades `{row.trade_count}`, gross `{row.gross_value:.2f}`, "
                f"cost `{row.total_cost:.2f}`, avg bps `{row.avg_cost_bps:.2f}`"
            )
    return "\n".join(lines)
