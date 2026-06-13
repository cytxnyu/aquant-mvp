# AQuant 个股预测报告：600362

## 核心结论

- 最新交易日：`2026-06-10`
- 最新收盘价：`40.4900`
- 数据源：`baostock`
- 模型：`event_aware_ensemble`
- 结论性质：概率化研究信号，不保证涨跌，不构成投资建议。

## 多周期预测

- `1d`: direction=`看多`, prob_up=`0.674`, expected_return=`0.717%`, p10/p50/p90=`-2.035%/0.717%/3.596%`, trust=`data_insufficient`
- `5d`: direction=`看多`, prob_up=`0.699`, expected_return=`1.856%`, p10/p50/p90=`-4.216%/1.856%/8.614%`, trust=`data_insufficient`
- `20d`: direction=`看多`, prob_up=`0.612`, expected_return=`8.396%`, p10/p50/p90=`-2.390%/8.396%/25.981%`, trust=`data_insufficient`
- `60d`: direction=`震荡偏弱`, prob_up=`0.271`, expected_return=`5.878%`, p10/p50/p90=`-11.381%/5.878%/44.385%`, trust=`data_insufficient`

## 预测 K 线说明

- Base 情景第 20 日收盘：`43.8897`；p10/p50/p90 收盘带：`39.5221/43.8897/51.0097`。
- 最近风险标记：`none`；趋势标签：`破位`；置信度：`0.183`。

## 输出文件

- `stock_forecast.csv/json`: 多周期个股预测。
- `forecast_kline.csv/json`: 未来 OHLC 概率情景。
- `forecast_kline.png/html`: 历史 + 未来预测 K 线图。
- `history_kline.csv`: 图表使用的历史 K 线。

## 风险声明

免费数据源存在缺口和延迟；预测必须通过大样本 walk-forward、单票回测、模拟盘和风控后才可讨论实盘。真实下单在当前项目中仍然强制关闭。