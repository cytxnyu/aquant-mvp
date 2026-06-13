# AQuant 个股预测报告：000630

## 核心结论

- 最新交易日：`2025-12-31`
- 最新收盘价：`33.6344`
- 数据源：`sample`
- 模型：`factor_score`
- 结论性质：概率化研究信号，不保证涨跌，不构成投资建议。

## 多周期预测

- `1d`: direction=`震荡偏多`, prob_up=`0.533`, expected_return=`0.121%`, p10/p50/p90=`-2.330%/0.121%/2.571%`, trust=`data_insufficient`
- `5d`: direction=`震荡偏多`, prob_up=`0.572`, expected_return=`0.642%`, p10/p50/p90=`-5.194%/0.642%/6.477%`, trust=`data_insufficient`
- `8d`: direction=`看多`, prob_up=`0.588`, expected_return=`1.046%`, p10/p50/p90=`-6.368%/1.046%/8.459%`, trust=`data_insufficient`
- `20d`: direction=`看多`, prob_up=`0.620`, expected_return=`2.541%`, p10/p50/p90=`-10.373%/2.541%/15.454%`, trust=`data_insufficient`
- `60d`: direction=`强看多`, prob_up=`0.736`, expected_return=`7.757%`, p10/p50/p90=`-13.602%/7.757%/29.116%`, trust=`data_insufficient`

## 预测 K 线说明


## K-line Forecast Nodes

- `intraday_next_day` date=`2026-01-01`, base_close=`33.6750`, bearish/base/bullish=`32.8508/33.6750/34.4992`, prob_up=`0.533`, trust=`data_insufficient`
- `1d` date=`2026-01-01`, base_close=`33.6750`, bearish/base/bullish=`32.8508/33.6750/34.4992`, prob_up=`0.533`, trust=`data_insufficient`
- `5d` date=`2026-01-07`, base_close=`33.8502`, bearish/base/bullish=`31.8875/33.8502/35.8129`, prob_up=`0.572`, trust=`data_insufficient`
- `20d` date=`2026-01-28`, base_close=`34.4889`, bearish/base/bullish=`30.1453/34.4889/38.8324`, prob_up=`0.620`, trust=`data_insufficient`

## Predicted K-line Details

- Base 情景第 20 日收盘：`34.4889`；p10/p50/p90 收盘带：`30.1453/34.4889/38.8324`。
- 最近风险标记：`none`；趋势标签：`趋势延续`；置信度：`0.218`。

## 输出文件

- `stock_forecast.csv/json`: 多周期个股预测。
- `forecast_kline.csv/json`: 未来 OHLC 概率情景。
- `forecast_kline.png/html`: 历史 + 未来预测 K 线图。
- `history_kline.csv`: 图表使用的历史 K 线。

## 风险声明

免费数据源存在缺口和延迟；预测必须通过大样本 walk-forward、单票回测、模拟盘和风控后才可讨论实盘。真实下单在当前项目中仍然强制关闭。

## Enhanced K-line Artifacts

- `forecast_kline.csv/json/png/html`: multi-day scenario K-line, always extended far enough to include 1d, 5d, and 20d nodes.
- `intraday_kline.csv/png`: next-session intraday checkpoint scenario K-line.
- `horizon_kline_summary.csv/json`: intraday, 1d, 5d, and 20d forecast-node evidence.
- `history_kline.csv`: historical OHLC bars used by the chart.
- `stock_evidence_audit.csv/json/md`: evidence completeness audit for the K-line's underlying stock forecast.

## K-line Trust Boundary

The K-line chart is a visualization of probabilistic research scenarios. It is not a tick-level forecast, not a guaranteed price path, and not investment advice. The `trust_status` field remains governed by data audit, walk-forward evidence, baseline comparison, calibration, conformal interval evidence, and risk gates.