from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from aquant_mvp.config import RiskConfig, StrategyConfig


@dataclass(frozen=True)
class PortfolioConstraintConfig:
    max_single_weight: float = 0.30
    max_theme_weight: float = 0.45
    max_turnover: float = 1.0
    volatility_target: float = 0.35
    volatility_lookback_days: int = 20
    max_drawdown: float = 0.10
    drawdown_de_risk_multiplier: float = 0.0
    blacklist: tuple[str, ...] = ()


@dataclass(frozen=True)
class PortfolioConstraintResult:
    adjusted_targets: pd.DataFrame
    report: pd.DataFrame
    daily_summary: pd.DataFrame
    markdown: str
    metadata: dict[str, object]


def build_portfolio_constraint_config(
    strategy: StrategyConfig,
    risk: RiskConfig | None = None,
) -> PortfolioConstraintConfig:
    single_cap = float(strategy.max_single_weight)
    blacklist: tuple[str, ...] = ()
    max_drawdown = 0.10
    if risk is not None:
        single_cap = min(single_cap, float(risk.max_single_weight))
        blacklist = tuple(str(symbol).zfill(6) for symbol in risk.blacklist)
        max_drawdown = float(risk.max_drawdown)
    return PortfolioConstraintConfig(
        max_single_weight=single_cap,
        max_theme_weight=float(strategy.max_theme_weight),
        max_turnover=float(strategy.max_turnover),
        volatility_target=float(strategy.volatility_target),
        volatility_lookback_days=int(strategy.volatility_lookback_days),
        max_drawdown=max_drawdown,
        drawdown_de_risk_multiplier=float(strategy.drawdown_de_risk_multiplier),
        blacklist=blacklist,
    )


def apply_portfolio_constraints(
    targets: pd.DataFrame,
    *,
    bars_by_symbol: dict[str, pd.DataFrame] | None = None,
    strategy_config: StrategyConfig | None = None,
    risk_config: RiskConfig | None = None,
    constraint_config: PortfolioConstraintConfig | None = None,
    theme_membership: pd.DataFrame | None = None,
    equity_curve: pd.DataFrame | None = None,
) -> PortfolioConstraintResult:
    """Apply executable portfolio constraints and leave cash for reduced exposure.

    The function is intentionally point-in-time: volatility uses returns strictly
    before the target date, and drawdown uses the supplied equity curve as of the
    target date. Removed exposure is not redistributed, which keeps caps binding.
    """
    adjusted = _normalize_targets(targets)
    config = constraint_config or _config_from_optional(strategy_config, risk_config)
    if adjusted.empty:
        report = pd.DataFrame(columns=_REPORT_COLUMNS)
        daily = pd.DataFrame(columns=_DAILY_COLUMNS)
        metadata = _metadata(config, adjusted, report, daily)
        return PortfolioConstraintResult(adjusted, report, daily, _markdown(report, daily, metadata), metadata)

    returns = _returns_panel(bars_by_symbol or {})
    theme_map = _theme_map(theme_membership)
    drawdowns = _drawdown_series(equity_curve)
    report_rows: list[dict[str, object]] = []
    daily_rows: list[dict[str, object]] = []
    previous = pd.Series(0.0, index=adjusted.columns)
    blacklist = {symbol.zfill(6) for symbol in config.blacklist}

    for date, original in adjusted.iterrows():
        current = original.copy().astype(float)
        constraints: list[str] = []

        for symbol in [symbol for symbol in current.index if symbol in blacklist and current.get(symbol, 0.0) > 0]:
            old = float(current[symbol])
            current[symbol] = 0.0
            constraints.append("blacklist")
            _append_report(
                report_rows,
                date=date,
                symbol=symbol,
                constraint="blacklist",
                original_weight=old,
                adjusted_weight=0.0,
                reason="symbol_in_risk_blacklist",
            )

        if config.max_single_weight > 0:
            for symbol in list(current[current > config.max_single_weight].index):
                old = float(current[symbol])
                current[symbol] = float(config.max_single_weight)
                constraints.append("max_single_weight")
                _append_report(
                    report_rows,
                    date=date,
                    symbol=symbol,
                    constraint="max_single_weight",
                    original_weight=old,
                    adjusted_weight=float(current[symbol]),
                    reason="single_name_weight_cap",
                )

        if theme_map and config.max_theme_weight > 0:
            current = _apply_theme_cap(current, date, theme_map, config.max_theme_weight, report_rows, constraints)

        realized_vol = _realized_portfolio_volatility(returns, current, pd.Timestamp(date), config.volatility_lookback_days)
        if config.volatility_target > 0 and pd.notna(realized_vol) and realized_vol > config.volatility_target:
            old_current = current.copy()
            scale = max(0.0, min(1.0, float(config.volatility_target) / float(realized_vol)))
            current = current * scale
            constraints.append("volatility_target")
            _append_report(
                report_rows,
                date=date,
                symbol="__portfolio__",
                constraint="volatility_target",
                original_weight=float(old_current.sum()),
                adjusted_weight=float(current.sum()),
                reason="realized_volatility_above_target",
                scale=scale,
                realized_volatility=realized_vol,
            )

        drawdown = _drawdown_asof(drawdowns, pd.Timestamp(date))
        if config.max_drawdown > 0 and pd.notna(drawdown) and drawdown <= -abs(float(config.max_drawdown)):
            old_current = current.copy()
            multiplier = max(0.0, min(1.0, float(config.drawdown_de_risk_multiplier)))
            current = current * multiplier
            constraints.append("drawdown_circuit_breaker")
            _append_report(
                report_rows,
                date=date,
                symbol="__portfolio__",
                constraint="drawdown_circuit_breaker",
                original_weight=float(old_current.sum()),
                adjusted_weight=float(current.sum()),
                reason="portfolio_drawdown_breached",
                scale=multiplier,
                drawdown=drawdown,
            )

        turnover_before = float((current - previous).abs().sum())
        if config.max_turnover > 0 and turnover_before > config.max_turnover:
            old_current = current.copy()
            scale = float(config.max_turnover) / turnover_before
            current = previous + (current - previous) * scale
            constraints.append("max_turnover")
            _append_report(
                report_rows,
                date=date,
                symbol="__portfolio__",
                constraint="max_turnover",
                original_weight=float(old_current.sum()),
                adjusted_weight=float(current.sum()),
                reason="rebalance_turnover_cap",
                scale=scale,
                turnover_before=turnover_before,
                turnover_after=float((current - previous).abs().sum()),
            )

        adjusted.loc[date] = current.clip(lower=0.0)
        daily_rows.append(
            {
                "date": pd.Timestamp(date).date().isoformat(),
                "gross_weight_before": float(original.sum()),
                "gross_weight_after": float(adjusted.loc[date].sum()),
                "cash_weight_after": float(max(0.0, 1.0 - adjusted.loc[date].sum())),
                "max_single_weight_after": float(adjusted.loc[date].max()) if len(adjusted.columns) else 0.0,
                "max_theme_weight_after": _max_theme_weight(adjusted.loc[date], theme_map),
                "turnover_after": float((adjusted.loc[date] - previous).abs().sum()),
                "realized_volatility": float(realized_vol) if pd.notna(realized_vol) else np.nan,
                "drawdown": float(drawdown) if pd.notna(drawdown) else np.nan,
                "constraints_applied": ";".join(sorted(set(constraints))) if constraints else "none",
            }
        )
        previous = adjusted.loc[date].copy()

    report = pd.DataFrame(report_rows, columns=_REPORT_COLUMNS)
    daily = pd.DataFrame(daily_rows, columns=_DAILY_COLUMNS)
    metadata = _metadata(config, adjusted, report, daily)
    return PortfolioConstraintResult(adjusted, report, daily, _markdown(report, daily, metadata), metadata)


def write_portfolio_constraint_outputs(
    output_dir: Path,
    result: PortfolioConstraintResult,
    *,
    prefix: str = "portfolio_constraint",
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "targets": output_dir / f"{prefix}_adjusted_rebalance_targets.csv",
        "report": output_dir / f"{prefix}_report.csv",
        "daily": output_dir / f"{prefix}_daily.csv",
        "summary": output_dir / f"{prefix}_summary.json",
        "markdown": output_dir / f"{prefix}_report.md",
    }
    result.adjusted_targets.to_csv(paths["targets"])
    result.report.to_csv(paths["report"], index=False)
    result.daily_summary.to_csv(paths["daily"], index=False)
    paths["summary"].write_text(json.dumps(result.metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    paths["markdown"].write_text(result.markdown, encoding="utf-8")
    return paths


def _config_from_optional(
    strategy: StrategyConfig | None,
    risk: RiskConfig | None,
) -> PortfolioConstraintConfig:
    if strategy is None:
        strategy = StrategyConfig()
    return build_portfolio_constraint_config(strategy, risk)


def _normalize_targets(targets: pd.DataFrame) -> pd.DataFrame:
    out = targets.copy()
    if out.empty:
        return out
    out.index = pd.to_datetime(out.index).normalize()
    out.columns = [str(column).zfill(6) for column in out.columns]
    return out.sort_index().fillna(0.0).astype(float)


def _returns_panel(bars_by_symbol: dict[str, pd.DataFrame]) -> pd.DataFrame:
    frames = []
    for symbol, bars in bars_by_symbol.items():
        if bars.empty or "date" not in bars.columns or "close" not in bars.columns:
            continue
        frame = bars[["date", "close"]].copy()
        frame["date"] = pd.to_datetime(frame["date"], errors="coerce").dt.normalize()
        frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
        series = frame.dropna().sort_values("date").set_index("date")["close"].pct_change()
        frames.append(series.rename(str(symbol).zfill(6)))
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, axis=1).sort_index().fillna(0.0)


def _theme_map(theme_membership: pd.DataFrame | None) -> dict[str, str]:
    if theme_membership is None or theme_membership.empty:
        return {}
    if "symbol" not in theme_membership.columns:
        return {}
    frame = theme_membership.copy()
    frame["symbol"] = frame["symbol"].astype(str).str.zfill(6)
    if "themes" in frame.columns:
        frame["primary_theme"] = frame["themes"].fillna("unthemed").astype(str).map(lambda value: value.split(";")[0] or "unthemed")
    elif "theme" in frame.columns:
        frame["primary_theme"] = frame["theme"].fillna("unthemed").astype(str)
    else:
        return {}
    return dict(zip(frame["symbol"], frame["primary_theme"], strict=False))


def _apply_theme_cap(
    current: pd.Series,
    date: pd.Timestamp,
    theme_map: dict[str, str],
    max_theme_weight: float,
    report_rows: list[dict[str, object]],
    constraints: list[str],
) -> pd.Series:
    out = current.copy()
    theme_to_symbols: dict[str, list[str]] = {}
    for symbol in out.index:
        theme = theme_map.get(str(symbol).zfill(6), "unthemed")
        theme_to_symbols.setdefault(theme, []).append(symbol)
    for theme, symbols in theme_to_symbols.items():
        if theme == "unthemed":
            continue
        theme_weight = float(out.reindex(symbols).sum())
        if theme_weight <= max_theme_weight or theme_weight <= 0:
            continue
        scale = float(max_theme_weight) / theme_weight
        constraints.append("max_theme_weight")
        for symbol in symbols:
            old = float(out.get(symbol, 0.0))
            if old <= 0:
                continue
            out.loc[symbol] = old * scale
            _append_report(
                report_rows,
                date=date,
                symbol=symbol,
                constraint="max_theme_weight",
                original_weight=old,
                adjusted_weight=float(out.loc[symbol]),
                reason="theme_weight_cap",
                theme=theme,
                before_exposure=theme_weight,
                after_exposure=float(max_theme_weight),
                scale=scale,
            )
    return out


def _realized_portfolio_volatility(
    returns: pd.DataFrame,
    weights: pd.Series,
    date: pd.Timestamp,
    lookback: int,
) -> float:
    if returns.empty or lookback <= 1:
        return float("nan")
    hist = returns[returns.index < pd.Timestamp(date).normalize()].tail(int(lookback))
    if len(hist) < max(5, min(int(lookback), 10)):
        return float("nan")
    aligned = weights.reindex(hist.columns).fillna(0.0).astype(float)
    portfolio_returns = hist.mul(aligned, axis=1).sum(axis=1)
    if len(portfolio_returns) <= 1:
        return float("nan")
    return float(portfolio_returns.std(ddof=0) * np.sqrt(252))


def _drawdown_series(equity_curve: pd.DataFrame | None) -> pd.Series:
    if equity_curve is None or equity_curve.empty or "date" not in equity_curve.columns:
        return pd.Series(dtype=float)
    frame = equity_curve.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce").dt.normalize()
    if "drawdown" in frame.columns:
        drawdown = pd.to_numeric(frame["drawdown"], errors="coerce")
    elif "equity" in frame.columns:
        equity = pd.to_numeric(frame["equity"], errors="coerce")
        drawdown = equity / equity.cummax() - 1
    else:
        return pd.Series(dtype=float)
    return pd.Series(drawdown.to_numpy(), index=frame["date"]).dropna().sort_index()


def _drawdown_asof(drawdowns: pd.Series, date: pd.Timestamp) -> float:
    if drawdowns.empty:
        return float("nan")
    asof = drawdowns[drawdowns.index <= pd.Timestamp(date).normalize()]
    if asof.empty:
        return float("nan")
    return float(asof.iloc[-1])


def _max_theme_weight(row: pd.Series, theme_map: dict[str, str]) -> float:
    if not theme_map:
        return 0.0
    frame = pd.DataFrame({"symbol": row.index.astype(str), "weight": row.astype(float).to_numpy()})
    frame["theme"] = frame["symbol"].map(lambda symbol: theme_map.get(str(symbol).zfill(6), "unthemed"))
    grouped = frame[frame["theme"] != "unthemed"].groupby("theme")["weight"].sum()
    return float(grouped.max()) if not grouped.empty else 0.0


def _append_report(
    rows: list[dict[str, object]],
    *,
    date: pd.Timestamp,
    symbol: str,
    constraint: str,
    original_weight: float,
    adjusted_weight: float,
    reason: str,
    theme: str = "",
    before_exposure: float | None = None,
    after_exposure: float | None = None,
    scale: float | None = None,
    realized_volatility: float | None = None,
    drawdown: float | None = None,
    turnover_before: float | None = None,
    turnover_after: float | None = None,
) -> None:
    rows.append(
        {
            "date": pd.Timestamp(date).date().isoformat(),
            "symbol": symbol,
            "constraint": constraint,
            "original_weight": float(original_weight),
            "adjusted_weight": float(adjusted_weight),
            "weight_delta": float(adjusted_weight) - float(original_weight),
            "reason": reason,
            "theme": theme,
            "before_exposure": np.nan if before_exposure is None else float(before_exposure),
            "after_exposure": np.nan if after_exposure is None else float(after_exposure),
            "scale": np.nan if scale is None else float(scale),
            "realized_volatility": np.nan if realized_volatility is None else float(realized_volatility),
            "drawdown": np.nan if drawdown is None else float(drawdown),
            "turnover_before": np.nan if turnover_before is None else float(turnover_before),
            "turnover_after": np.nan if turnover_after is None else float(turnover_after),
        }
    )


def _metadata(
    config: PortfolioConstraintConfig,
    adjusted: pd.DataFrame,
    report: pd.DataFrame,
    daily: pd.DataFrame,
) -> dict[str, object]:
    constraints = sorted(report["constraint"].dropna().astype(str).unique().tolist()) if not report.empty else []
    return {
        "enabled": True,
        "target_dates": int(len(adjusted)),
        "symbols": int(len(adjusted.columns)),
        "adjustment_rows": int(len(report)),
        "constraints_triggered": constraints,
        "max_gross_weight_after": float(daily["gross_weight_after"].max()) if not daily.empty else 0.0,
        "min_gross_weight_after": float(daily["gross_weight_after"].min()) if not daily.empty else 0.0,
        "max_single_weight_after": float(daily["max_single_weight_after"].max()) if not daily.empty else 0.0,
        "max_theme_weight_after": float(daily["max_theme_weight_after"].max()) if not daily.empty else 0.0,
        "config": {
            "max_single_weight": config.max_single_weight,
            "max_theme_weight": config.max_theme_weight,
            "max_turnover": config.max_turnover,
            "volatility_target": config.volatility_target,
            "volatility_lookback_days": config.volatility_lookback_days,
            "max_drawdown": config.max_drawdown,
            "drawdown_de_risk_multiplier": config.drawdown_de_risk_multiplier,
            "blacklist": list(config.blacklist),
        },
    }


def _markdown(report: pd.DataFrame, daily: pd.DataFrame, metadata: dict[str, object]) -> str:
    lines = [
        "# Portfolio Constraint Report",
        "",
        "This report audits executable portfolio constraints applied after signal generation and before backtest or paper-trade order planning. It is a research risk-control report, not investment advice.",
        "",
        "## Summary",
        "",
        f"- Target dates: `{metadata.get('target_dates', 0)}`",
        f"- Symbols: `{metadata.get('symbols', 0)}`",
        f"- Adjustment rows: `{metadata.get('adjustment_rows', 0)}`",
        f"- Constraints triggered: `{', '.join(metadata.get('constraints_triggered', [])) if metadata.get('constraints_triggered') else 'none'}`",
        f"- Max gross weight after constraints: `{float(metadata.get('max_gross_weight_after', 0.0)):.4f}`",
        f"- Max single weight after constraints: `{float(metadata.get('max_single_weight_after', 0.0)):.4f}`",
        f"- Max theme weight after constraints: `{float(metadata.get('max_theme_weight_after', 0.0)):.4f}`",
        "",
    ]
    if not daily.empty:
        latest = daily.tail(5)
        lines.extend(["## Latest Daily State", ""])
        for row in latest.itertuples(index=False):
            lines.append(
                f"- `{row.date}` gross {row.gross_weight_before:.3f} -> {row.gross_weight_after:.3f}; "
                f"cash={row.cash_weight_after:.3f}; constraints={row.constraints_applied}"
            )
    if report.empty:
        lines.append("")
        lines.append("No constraints changed target weights.")
        return "\n".join(lines)
    lines.extend(["", "## Latest Adjustments", ""])
    for row in report.tail(20).itertuples(index=False):
        lines.append(
            f"- `{row.date}` `{row.symbol}` {row.constraint}: {row.original_weight:.3f} -> "
            f"{row.adjusted_weight:.3f}; reason={row.reason}"
        )
    return "\n".join(lines)


_REPORT_COLUMNS = [
    "date",
    "symbol",
    "constraint",
    "original_weight",
    "adjusted_weight",
    "weight_delta",
    "reason",
    "theme",
    "before_exposure",
    "after_exposure",
    "scale",
    "realized_volatility",
    "drawdown",
    "turnover_before",
    "turnover_after",
]

_DAILY_COLUMNS = [
    "date",
    "gross_weight_before",
    "gross_weight_after",
    "cash_weight_after",
    "max_single_weight_after",
    "max_theme_weight_after",
    "turnover_after",
    "realized_volatility",
    "drawdown",
    "constraints_applied",
]
