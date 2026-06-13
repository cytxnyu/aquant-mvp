from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class PaperTradeValidationResult:
    checks: pd.DataFrame
    summary: dict[str, object]
    markdown: str


def validate_paper_trade(
    order_plan: pd.DataFrame,
    risk_report: pd.DataFrame,
    paper_summary: dict[str, Any],
    *,
    executions: pd.DataFrame | None = None,
    positions: pd.DataFrame | None = None,
    requested_days: int = 20,
    no_live_required: bool = True,
) -> PaperTradeValidationResult:
    """Validate that a dry-run paper-trade path stayed auditable and non-live."""

    checks = _checks(
        order_plan,
        risk_report,
        paper_summary,
        executions=executions,
        positions=positions,
        requested_days=requested_days,
        no_live_required=no_live_required,
    )
    summary = _summary(checks, order_plan, risk_report, paper_summary, executions, positions)
    return PaperTradeValidationResult(checks=checks, summary=summary, markdown=_markdown(summary, checks))


def write_paper_trade_validation_outputs(
    output_dir: Path,
    result: PaperTradeValidationResult,
    *,
    prefix: str = "paper_validation",
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "checks": output_dir / f"{prefix}_checks.csv",
        "summary": output_dir / f"{prefix}_summary.json",
        "markdown": output_dir / f"{prefix}_report.md",
    }
    result.checks.to_csv(paths["checks"], index=False)
    paths["summary"].write_text(json.dumps(result.summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    paths["markdown"].write_text(result.markdown, encoding="utf-8")
    return paths


def _checks(
    order_plan: pd.DataFrame,
    risk_report: pd.DataFrame,
    paper_summary: dict[str, Any],
    *,
    executions: pd.DataFrame | None,
    positions: pd.DataFrame | None,
    requested_days: int,
    no_live_required: bool,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    def add(gate: str, passed: bool, severity: str, observed: object, threshold: object, detail: str) -> None:
        rows.append(
            {
                "gate": gate,
                "status": "pass" if passed else severity,
                "passed": bool(passed),
                "severity": "info" if passed else severity,
                "observed": observed,
                "threshold": threshold,
                "detail": detail,
            }
        )

    risk_passed = bool(paper_summary.get("passed", False))
    no_live = bool(paper_summary.get("no_live", False))
    add("no_live_required", (not no_live_required) or no_live, "fail", no_live, True, "Paper dry-run must explicitly keep live order submission disabled.")
    add("paper_summary_present", bool(paper_summary), "fail", sorted(paper_summary.keys()), "non-empty", "Paper summary JSON is the run manifest for the dry-run.")
    add("requested_days_recorded", int(paper_summary.get("requested_days", 0) or 0) >= requested_days, "warn", paper_summary.get("requested_days", 0), f">= {requested_days}", "A 20-day simulation target should be recorded when requested.")
    add("order_plan_present", not order_plan.empty, "warn", len(order_plan), ">0 rows", "No orders can be valid after risk/targets, but order evidence should be visible.")
    add("risk_report_present", not risk_report.empty, "fail", len(risk_report), ">0 rows", "Risk checks must write row-level order evidence.")
    if not risk_report.empty and "passed" in risk_report.columns:
        add("risk_report_matches_summary", bool(risk_report["passed"].astype(bool).all()) == risk_passed, "fail", bool(risk_report["passed"].astype(bool).all()), risk_passed, "Summary pass/fail should match row-level risk report.")

    if risk_passed:
        add("executions_present_when_risk_passed", executions is not None and not executions.empty, "fail", 0 if executions is None else len(executions), ">0 rows", "Risk-passed paper orders must write simulated executions.")
        add("positions_present_when_risk_passed", positions is not None, "fail", positions is not None, True, "Risk-passed paper orders must write simulated positions, even if flat.")
        if executions is not None and not executions.empty:
            filled = executions["status"].astype(str).str.upper().eq("FILLED").all() if "status" in executions.columns else False
            add("paper_only_filled_status", bool(filled), "fail", sorted(executions.get("status", pd.Series(dtype=str)).astype(str).unique().tolist()), "FILLED", "PaperBroker executions should be simulated fills, not live broker statuses.")
            add("execution_count_matches_orders", len(executions) == len(order_plan), "warn", len(executions), len(order_plan), "Each generated order should have a simulated execution row.")
            add("execution_costs_recorded", {"gross_value", "fee", "tax"}.issubset(executions.columns), "fail", sorted(executions.columns), "gross_value/fee/tax", "Paper fills must preserve cost fields.")
    else:
        reasons = paper_summary.get("reasons", [])
        add("risk_blocked_has_reasons", bool(reasons), "fail", reasons, "non-empty reasons", "Blocked paper runs must explain which risk gate stopped orders.")
        add("no_executions_when_risk_blocked", executions is None or executions.empty, "fail", 0 if executions is None else len(executions), "0 rows", "Risk-blocked runs should not generate simulated fills.")

    metadata = paper_summary.get("metadata", {})
    add("broker_is_paper", (not risk_passed) or str(metadata.get("broker", "")).lower() == "paper", "fail", metadata.get("broker", ""), "paper", "Dry-run execution must use PaperBroker only.")
    add("portfolio_constraints_recorded", isinstance(paper_summary.get("portfolio_constraints"), dict), "fail", type(paper_summary.get("portfolio_constraints")).__name__, "dict", "Paper order planning must record portfolio constraint metadata.")
    add("event_guard_recorded", isinstance(paper_summary.get("event_risk_guard"), dict), "warn", type(paper_summary.get("event_risk_guard")).__name__, "dict", "Paper order planning should record event-risk guard state.")
    return pd.DataFrame(rows)


def _summary(
    checks: pd.DataFrame,
    order_plan: pd.DataFrame,
    risk_report: pd.DataFrame,
    paper_summary: dict[str, Any],
    executions: pd.DataFrame | None,
    positions: pd.DataFrame | None,
) -> dict[str, object]:
    failed = checks[checks["status"] == "fail"]["gate"].tolist() if not checks.empty else []
    warned = checks[checks["status"] == "warn"]["gate"].tolist() if not checks.empty else []
    if failed:
        status = "failed"
    elif warned:
        status = "watchlist"
    else:
        status = "passed"
    return {
        "validation_status": status,
        "validation_passed": not failed,
        "failed_checks": failed,
        "warning_checks": warned,
        "check_count": int(len(checks)),
        "pass_count": int((checks["status"] == "pass").sum()) if not checks.empty else 0,
        "warn_count": int((checks["status"] == "warn").sum()) if not checks.empty else 0,
        "fail_count": int((checks["status"] == "fail").sum()) if not checks.empty else 0,
        "risk_passed": bool(paper_summary.get("passed", False)),
        "no_live": bool(paper_summary.get("no_live", False)),
        "requested_days": int(paper_summary.get("requested_days", 0) or 0),
        "order_count": int(len(order_plan)),
        "risk_rows": int(len(risk_report)),
        "execution_rows": int(len(executions)) if executions is not None else 0,
        "position_rows": int(len(positions)) if positions is not None else 0,
        "broker": str((paper_summary.get("metadata") or {}).get("broker", "")),
        "note": "Paper validation proves the simulated path is auditable and non-live; it is not live-trading permission.",
    }


def _markdown(summary: dict[str, object], checks: pd.DataFrame) -> str:
    lines = [
        "# Paper Trade Validation Report",
        "",
        "This report verifies that the dry-run trading path stayed paper-only and produced auditable risk/order/execution evidence. It is not live-trading permission.",
        "",
        "## Summary",
        "",
        f"- Validation status: `{summary.get('validation_status', 'unknown')}`",
        f"- Risk passed: `{summary.get('risk_passed', False)}`; no-live: `{summary.get('no_live', False)}`; broker: `{summary.get('broker', '')}`",
        f"- Orders/executions/positions: `{summary.get('order_count', 0)}` / `{summary.get('execution_rows', 0)}` / `{summary.get('position_rows', 0)}`",
        f"- Failed checks: `{summary.get('fail_count', 0)}`; warnings: `{summary.get('warn_count', 0)}`; passes: `{summary.get('pass_count', 0)}`",
        "",
    ]
    if not checks.empty:
        lines.extend(["## Gate Results", ""])
        for row in checks.itertuples(index=False):
            lines.append(f"- `{row.status}` `{row.gate}` observed=`{row.observed}` threshold=`{row.threshold}`")
    return "\n".join(lines)

