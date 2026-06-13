# Predicted K-line

## Definition

The predicted K-line is a probabilistic scenario chart. It combines recent real OHLC bars with future synthetic OHLC bars derived from model outputs:

- `prob_up`
- `expected_return`
- `expected_excess_return`
- `return_p10 / return_p50 / return_p90`
- `direction`
- `trend_label`
- `confidence`
- `risk_flags`
- `trust_status`
- `model_id`
- `data_version`

It is not a deterministic future price chart.

## Outputs

`predict-kline` and `plot-kline` write:

- `stock_forecast.csv`
- `stock_forecast.json`
- `forecast_kline.csv`
- `forecast_kline.json`
- `history_kline.csv`
- `forecast_kline.png`
- `forecast_kline.html`
- `stock_prediction_report.md`

`report-stock --with-kline` writes the same K-line files plus explanation and backtest files.

## Example

```powershell
python run_mvp.py report-stock --config configs\metals.json --source baostock --universe config --symbol 000630 --days 20 --history-days 120 --horizons 1,5,20,60 --model ensemble --with-kline --output-dir reports\aquant_v03_final\stocks\000630
```

## Interpretation

- Historical candles are real source bars.
- Future candles are scenario bars.
- The p10-p90 band is a risk interval.
- `trust_status=data_insufficient` means the report exists, but the validation/data coverage is not enough for high-confidence use.
