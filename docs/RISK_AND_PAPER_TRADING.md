# Risk And Paper Trading

## Simulation Chain

The paper-trading chain is:

```text
signal -> target_position -> order_plan -> risk_check -> paper_fill -> execution_report -> reconcile
```

Current outputs:

- `portfolio_constraint_adjusted_rebalance_targets.csv`
- `portfolio_constraint_report.csv`
- `portfolio_constraint_report.md`
- `portfolio_constraint_daily.csv`
- `portfolio_constraint_summary.json`
- `event_guarded_rebalance_targets.csv` when `--with-news` is used
- `event_risk_guard_report.csv` when `--with-news` is used
- `event_risk_guard_summary.json` when `--with-news` is used
- `order_plan.csv`
- `risk_report.csv`
- `paper_executions.csv`
- `paper_positions.csv`
- `paper_summary.json`
- `rebalance_targets.csv`

## Risk Controls

Supported controls:

- capital limit
- single-stock weight limit
- theme weight limit
- turnover cap
- realized volatility target
- drawdown circuit breaker
- single-order value limit
- blacklist
- daily loss / drawdown config hooks
- 100-share lot handling
- fee, stamp tax, and slippage assumptions

## Portfolio Constraints

`backtest-portfolio` and `paper-trade --no-live` now apply a portfolio constraint layer after raw signal targets are generated and before research backtest or simulated order planning:

```text
signal -> raw target_position -> portfolio_constraints -> order_plan/backtest -> risk_check
```

The constraint layer writes a full audit trail:

- `portfolio_constraint_adjusted_rebalance_targets.csv`
- `portfolio_constraint_report.csv`
- `portfolio_constraint_report.md`
- `portfolio_constraint_daily.csv`
- `portfolio_constraint_summary.json`

`backtest-portfolio` also writes a side-by-side constrained run:

- `portfolio_constraint_equity_curve.csv`
- `portfolio_constraint_trades.csv`
- `portfolio_constraint_holdings.csv`
- `portfolio_constraint_rebalances.csv`
- `portfolio_constraint_metrics.json`

Reduced exposure is left as cash rather than redistributed. This keeps single-name, theme, volatility, and drawdown caps binding and makes the cost of risk control visible.

## Event Risk Guard

`paper-trade --with-news --no-live` applies the event-risk guard before order generation:

- Recent negative high-confidence events can reduce target weights.
- Severe negative new-buy candidates can be set to zero.
- Positive or mixed events remain visible in `risk_report.csv` but do not automatically block a simulated order.
- The default event recency window is 30 days.

`backtest-portfolio --with-news` also writes an event-guarded comparison run:

- `event_guarded_rebalance_targets.csv`
- `event_guarded_equity_curve.csv`
- `event_guarded_trades.csv`
- `event_guarded_holdings.csv`
- `event_guarded_metrics.json`

The guard is a conservative simulation control. It does not claim news interpretation is correct, and it does not unlock live trading.

## Live Trading Safety

`live-trade` currently refuses real order submission:

```text
Live trading is disabled in this project. QMT order submission is intentionally blocked.
```

QMT/XtQuant is only allowed for read-only status and future reconciliation work unless the project later passes 20 trading days of simulation, data audit, risk checks, and manual confirmation design.
