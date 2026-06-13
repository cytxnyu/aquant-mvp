# AQuant Run Summary

## Run Config

- Data source: `sample`
- Date range: `2022-01-01` to `2025-12-31`
- Loaded symbols: 3
- Selected universe: 3
- Rebalance: `W-FRI`
- Top N: 5

## Data Quality

- Issue count: 0
- Universe filters reserve ST, suspension, limit-up/down, delisting and industry hooks for the next data upgrade.

## Metrics

- `initial_cash`: 1000000.000000
- `final_equity`: 1915748.233949
- `total_return`: 0.915748
- `annual_return`: 0.170081
- `annual_volatility`: 0.161014
- `max_drawdown`: -0.210308
- `sharpe`: 1.056363
- `calmar`: 0.808726
- `win_rate`: 0.720848
- `avg_turnover`: 0.029696
- `total_turnover`: 6.176745
- `trade_count`: 548.000000
- `rebalance_count`: 208.000000

## Latest Predictions

- Method: `lightgbm`
- Horizon: 5 trading days

- `600362`: rank 1, signal 候选, predicted excess -0.7677%
- `601899`: rank 2, signal 观察, predicted excess -1.4582%
- `000630`: rank 3, signal 回避, predicted excess -1.9572%

## Outputs

- `equity_curve`: `equity_curve.csv`
- `trades`: `trades.csv`
- `holdings`: `holdings.csv`
- `rebalances`: `rebalances.csv`
- `yearly_metrics`: `yearly_metrics.csv`
- `theme_metrics`: `theme_metrics.csv`
- `metrics`: `metrics.json`
- `manifest`: `manifest.json`
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
- `factor_yearly_stability`: `factor_yearly_stability.csv`
- `factor_analysis_json`: `factor_analysis.json`
- `predictions`: `predictions.csv`
- `prediction_summary`: `prediction_summary.json`
- `scores`: `scores.csv`
- `targets`: `rebalance_targets.csv`
- `equity_plot`: `equity_curve.png`
- `drawdown_plot`: `drawdown.png`
- `factor_ic_plot`: `factor_ic.png`
- `quantile_returns_plot`: `quantile_returns.png`

## Notes

Sample data is only for workflow verification. Real strategy research must use point-in-time A-share data and handle survivorship bias, announcement dates, suspensions, ST flags and limit-up/down constraints.
