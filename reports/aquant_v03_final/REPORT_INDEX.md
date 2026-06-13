# AQuant v0.3 Final Report Index

## Core v0.3 Outputs

- System audit: `reports/aquant_v03_audit/system_gap_report.md`
- Next plan: `reports/aquant_v03_audit/next_iteration_plan.md`
- Full system doc: `docs/AQUANT_V03_FULL_SYSTEM.md`
- Predicted K-line doc: `docs/PREDICTED_KLINE.md`
- Factor/model doc: `docs/FACTOR_MODEL_V03.md`
- Data quality doc: `docs/DATA_QUALITY_V03.md`
- Risk doc: `docs/RISK_AND_PAPER_TRADING.md`

## Representative Stock Reports

Generated with BaoStock free source:

- `000630` Tongling Nonferrous Metals: `reports/aquant_v03_final/stocks/000630`
- `601899` Zijin Mining: `reports/aquant_v03_final/stocks/601899`
- `600362` Jiangxi Copper: `reports/aquant_v03_final/stocks/600362`
- `300308` Zhongji Innolight: `reports/aquant_v03_final/stocks/300308`
- `300750` CATL: `reports/aquant_v03_final/stocks/300750`

Each directory contains:

- `stock_forecast.csv/json`
- `forecast_kline.csv/json/png/html`
- `history_kline.csv`
- `stock_prediction_report.md`
- `stock_explanation.csv/md`
- `similar_history.csv`
- `stock_forecast_backtest.csv`
- `stock_forecast_metrics.csv`
- `stock_report_manifest.json`

## Important Status

- Factor count: 237.
- Unit tests: 16 passed.
- `all-a-free`: 5527 unique symbols.
- `mega-hot`: 1200 unique symbols.
- BaoStock smoke sync: 1 symbol, 346 rows.
- PIT feature store: 31128 rows, 237 features.
- `predict-stock`, `predict-kline`, `plot-kline`, `backtest-stock`, `paper-trade --no-live`: passed for `000630`.
- Live trading: blocked by design.
- Representative report trust status is mostly `data_insufficient`, because these reports use small 10-20 symbol sector pools rather than a 200+ symbol training universe.

## How To Reproduce

```powershell
python run_mvp.py report-stock --config configs\metals.json --source baostock --universe config --symbol 000630 --days 20 --history-days 120 --horizons 1,5,20,60 --model ensemble --with-kline --output-dir reports\aquant_v03_final\stocks\000630
```

Signals are probabilistic research outputs only and are not investment advice.
