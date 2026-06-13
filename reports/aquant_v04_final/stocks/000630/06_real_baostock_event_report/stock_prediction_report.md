# AQuant 个股预测报告：000630

## 核心结论

- 最新交易日：`2026-06-10`
- 最新收盘价：`6.3500`
- 数据源：`baostock`
- 模型：`event_aware_ensemble`
- 结论性质：概率化研究信号，不保证涨跌，不构成投资建议。

## 多周期预测

- `1d`: direction=`震荡偏多`, prob_up=`0.560`, expected_return=`0.489%`, p10/p50/p90=`-2.106%/0.489%/3.350%`, trust=`data_insufficient`
- `5d`: direction=`看多`, prob_up=`0.619`, expected_return=`1.446%`, p10/p50/p90=`-4.375%/1.446%/8.820%`, trust=`data_insufficient`
- `20d`: direction=`震荡偏多`, prob_up=`0.575`, expected_return=`2.791%`, p10/p50/p90=`-7.753%/2.791%/19.025%`, trust=`data_insufficient`
- `60d`: direction=`强看空`, prob_up=`0.249`, expected_return=`-2.621%`, p10/p50/p90=`-19.656%/-2.621%/24.445%`, trust=`data_insufficient`

## 预测 K 线说明

- Base 情景第 20 日收盘：`6.5272`；p10/p50/p90 收盘带：`5.8577/6.5272/7.5581`。
- 最近风险标记：`high_volatility`；趋势标签：`无明显形态`；置信度：`0.127`。

## 输出文件

- `stock_forecast.csv/json`: 多周期个股预测。
- `forecast_kline.csv/json`: 未来 OHLC 概率情景。
- `forecast_kline.png/html`: 历史 + 未来预测 K 线图。
- `history_kline.csv`: 图表使用的历史 K 线。

## 风险声明

免费数据源存在缺口和延迟；预测必须通过大样本 walk-forward、单票回测、模拟盘和风控后才可讨论实盘。真实下单在当前项目中仍然强制关闭。