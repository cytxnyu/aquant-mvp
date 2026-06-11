# AQuant Run Summary

## Run Config

- Data source: `sample`
- Date range: `2022-01-01` to `2025-12-31`
- Loaded symbols: 10
- Selected universe: 10
- Rebalance: `W-FRI`
- Top N: 5

## Data Quality

- Issue count: 0
- Universe filters reserve ST, suspension, limit-up/down, delisting and industry hooks for the next data upgrade.

## Metrics

- `initial_cash`: 1000000.000000
- `final_equity`: 1530886.462000
- `total_return`: 0.530886
- `annual_return`: 0.108369
- `annual_volatility`: 0.138286
- `max_drawdown`: -0.159213
- `sharpe`: 0.813295
- `calmar`: 0.680652
- `win_rate`: 0.714008
- `avg_turnover`: 0.427723
- `total_turnover`: 88.966369
- `trade_count`: 1000.000000
- `rebalance_count`: 208.000000

## Outputs

- `equity_curve`: `equity_curve.csv`
- `trades`: `trades.csv`
- `holdings`: `holdings.csv`
- `rebalances`: `rebalances.csv`
- `metrics`: `metrics.json`
- `config`: `config.json`
- `load_report`: `load_report.json`
- `data_quality_summary`: `data_quality_summary.csv`
- `data_quality_issues`: `data_quality_issues.csv`
- `universe`: `universe.csv`
- `factors`: `factors.csv`
- `labels`: `labels.csv`
- `factor_ic_summary`: `factor_ic_summary.csv`
- `factor_ic_series`: `factor_ic_series.csv`
- `factor_quantile_returns`: `factor_quantile_returns.csv`
- `factor_coverage`: `factor_coverage.csv`
- `scores`: `scores.csv`
- `targets`: `rebalance_targets.csv`
- `equity_plot`: `equity_curve.png`
- `drawdown_plot`: `drawdown.png`
- `factor_ic_plot`: `factor_ic.png`
- `quantile_returns_plot`: `quantile_returns.png`

## Notes

Sample data is only for workflow verification. Real strategy research must use point-in-time A-share data and handle survivorship bias, announcement dates, suspensions, ST flags and limit-up/down constraints.
