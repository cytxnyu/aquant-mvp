# AQuant Run Summary

## Run Config

- Data source: `baostock`
- Date range: `2020-01-01` to `2026-06-10`
- Loaded symbols: 20
- Selected universe: 20
- Rebalance: `W-FRI`
- Top N: 6

## Data Quality

- Issue count: 0
- Universe filters reserve ST, suspension, limit-up/down, delisting and industry hooks for the next data upgrade.

## Metrics

- `initial_cash`: 1000000.000000
- `final_equity`: 3945943.458683
- `total_return`: 2.945943
- `annual_return`: 0.248605
- `annual_volatility`: 0.378132
- `max_drawdown`: -0.465472
- `sharpe`: 0.777032
- `calmar`: 0.534091
- `win_rate`: 0.576456
- `avg_turnover`: 0.590417
- `total_turnover`: 194.247103
- `trade_count`: 2869.000000
- `rebalance_count`: 329.000000

## Latest Predictions

- Method: `lightgbm`
- Horizon: 5 trading days

- `600489`: rank 1, signal 候选, predicted excess 2.2629%
- `600547`: rank 2, signal 候选, predicted excess 2.2608%
- `601899`: rank 3, signal 候选, predicted excess 1.9874%
- `601600`: rank 4, signal 候选, predicted excess 1.9087%
- `000960`: rank 5, signal 候选, predicted excess 1.5676%

## Outputs

- `equity_curve`: `equity_curve.csv`
- `trades`: `trades.csv`
- `holdings`: `holdings.csv`
- `rebalances`: `rebalances.csv`
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
