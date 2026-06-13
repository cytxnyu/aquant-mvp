# AQuant 个股预测报告：000630

## 核心结论

- 最新交易日：`2026-06-10`
- 最新收盘价：`6.3500`
- 数据源：`baostock`
- 模型：`factor_score`
- 结论性质：概率化研究信号，不保证涨跌，不构成投资建议。

## 多周期预测

- `1d`: direction=`中性`, prob_up=`0.475`, expected_return=`0.083%`, p10/p50/p90=`-2.999%/0.083%/3.165%`, trust=`weak`
- `5d`: direction=`中性`, prob_up=`0.481`, expected_return=`0.461%`, p10/p50/p90=`-6.736%/0.461%/7.658%`, trust=`weak`
- `20d`: direction=`中性`, prob_up=`0.498`, expected_return=`2.065%`, p10/p50/p90=`-12.997%/2.065%/17.127%`, trust=`model_failed`
- `60d`: direction=`震荡偏多`, prob_up=`0.553`, expected_return=`6.507%`, p10/p50/p90=`-19.863%/6.507%/32.876%`, trust=`model_failed`

## 预测 K 线说明


## K-line Forecast Nodes

- `intraday_next_day` date=`2026-06-11`, base_close=`6.3553`, bearish/base/bullish=`6.1595/6.3553/6.5510`, prob_up=`0.475`, trust=`weak`
- `1d` date=`2026-06-11`, base_close=`6.3553`, bearish/base/bullish=`6.1595/6.3553/6.5510`, prob_up=`0.475`, trust=`weak`
- `5d` date=`2026-06-17`, base_close=`6.3793`, bearish/base/bullish=`5.9223/6.3793/6.8363`, prob_up=`0.481`, trust=`weak`
- `20d` date=`2026-07-08`, base_close=`6.4811`, bearish/base/bullish=`5.5247/6.4811/7.4375`, prob_up=`0.498`, trust=`model_failed`

## Predicted K-line Details

- Base 情景第 60 日收盘：`6.7632`；p10/p50/p90 收盘带：`5.0887/6.7632/8.4376`。
- 最近风险标记：`high_volatility`；趋势标签：`无明显形态`；置信度：`0.080`。

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