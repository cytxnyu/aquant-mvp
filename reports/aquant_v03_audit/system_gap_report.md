# AQuant v0.3 System Gap Report

## Current Landing

- CLI: added `predict-kline`, `plot-kline`, and `report-stock`.
- Factor library: expanded to 237 factors, including KDJ, CCI, Williams %R, MFI, VWAP bias, OBV slope, flow/crowding, contraction, and cross-sectional market factors.
- Stock prediction: keeps probabilistic `1/5/20/60` day outputs with `prob_up`, expected return, p10/p50/p90, direction, trend, risk flags, metrics, model id, and data version.
- K-line forecast: generates historical + future probabilistic OHLC scenarios, p10/p50/p90 band, PNG chart, HTML report, CSV/JSON, and Markdown report.
- Report chain: `report-stock --with-kline` now writes forecast, explanation, similar history, backtest, metrics, K-line chart, and manifest in one directory.
- Safety: `live-trade` remains blocked. QMT is still read-only/paper-trade only.

## Main Remaining Gaps

- Data depth is still limited by free sources. BaoStock/AKShare can support research, but not institution-grade PIT coverage for all announcements, historical index membership, full industry history, and stable minute-level data.
- Trust gating is intentionally strict. A 20-symbol metals config produces usable reports but `data_insufficient`, because trusted predictions require at least 200 symbols and sample-out validation.
- Model validation is still shallow unless the user runs `train-walk-forward` on a 200+ or all-A universe.
- QMT read-only exists as a skeleton, but real account reconciliation depends on local MiniQMT, xtquant availability, and the user's broker permissions.
- Text/event factors are still mostly placeholders until announcement and news ingestion is expanded.
- Predicted K-line is a scenario visualization, not a deterministic price forecast.

## Verification Snapshot

- Factor count: 237.
- Unit tests: 16 passed after v0.3 K-line work.
- Real free-source report generated for `000630` using BaoStock under `reports/aquant_v03_final/stocks/000630`.
- K-line artifacts generated: `forecast_kline.csv/json/png/html`.
- Report artifacts generated: `stock_forecast.csv/json`, `stock_explanation.md`, `stock_forecast_backtest.csv`, `stock_forecast_metrics.csv`, `stock_prediction_report.md`, `stock_report_manifest.json`.

## Risk Statement

All outputs are research signals only. They do not guarantee price movement and are not investment advice. No live trading path is enabled.
