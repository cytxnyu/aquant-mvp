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
- `final_equity`: 1506241.187089
- `total_return`: 0.506241
- `annual_return`: 0.104031
- `annual_volatility`: 0.138492
- `max_drawdown`: -0.174736
- `sharpe`: 0.783971
- `calmar`: 0.595360
- `win_rate`: 0.710372
- `avg_turnover`: 0.423465
- `total_turnover`: 88.080654
- `trade_count`: 993.000000
- `rebalance_count`: 208.000000

## Latest Predictions

- Method: `lightgbm`
- Horizon: 5 trading days

- `600900`: rank 1, signal 候选, predicted excess 2.6390%
- `000001`: rank 2, signal 候选, predicted excess 1.2735%
- `000333`: rank 3, signal 候选, predicted excess 0.9351%
- `601318`: rank 4, signal 观察, predicted excess 0.5385%
- `600519`: rank 5, signal 观察, predicted excess 0.5297%

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
