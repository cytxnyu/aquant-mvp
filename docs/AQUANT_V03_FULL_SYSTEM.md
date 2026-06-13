# AQuant v0.3 Full System

## What Changed

AQuant v0.3 adds a usable individual-stock report chain and a predicted K-line scenario chart.

Core commands:

```powershell
python run_mvp.py predict-kline --config configs\metals.json --source baostock --symbol 000630 --days 20 --horizons 1,5,20,60
python run_mvp.py plot-kline --config configs\metals.json --source baostock --symbol 000630 --days 20 --horizons 1,5,20,60
python run_mvp.py report-stock --config configs\metals.json --source baostock --symbol 000630 --days 20 --horizons 1,5,20,60 --with-kline
```

## Current Modules

- Data: sample, AKShare, BaoStock, Tushare free router, cache, warehouse audit columns.
- Universe: all-A free discovery, mega-hot, professional themes, metals and hot-sector seeds.
- Factors: 237 technical/cross-sectional factors.
- Models: factor score baseline, LightGBM path when installed, walk-forward registry.
- Prediction: individual-stock probability, return, excess return, direction, trend, confidence, p10/p50/p90, trust status.
- K-line: future OHLC scenario paths with bearish/base/bullish scenarios and p10/p50/p90 band.
- Backtest: single-stock forecast validation and portfolio workflow.
- Broker: PaperBroker and QMT read-only skeleton; live trading blocked.

## Trust Rules

The system may output a prediction even with a small universe, but it cannot mark it trusted unless the data and validation pass stricter gates. A 20-symbol metal pool is useful for workflow and sector research, but it is normally `data_insufficient`.

## Safety

No output is a guaranteed forecast. No output is investment advice. Live orders are intentionally disabled.
