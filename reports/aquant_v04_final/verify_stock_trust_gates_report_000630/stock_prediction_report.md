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

- Base 情景第 8 日收盘：`33.9860`；p10/p50/p90 收盘带：`31.4925/33.9860/36.4795`。
- 最近风险标记：`none`；趋势标签：`趋势延续`；置信度：`0.173`。

## 输出文件

- `stock_forecast.csv/json`: 多周期个股预测。
- `forecast_kline.csv/json`: 未来 OHLC 概率情景。
- `forecast_kline.png/html`: 历史 + 未来预测 K 线图。
- `history_kline.csv`: 图表使用的历史 K 线。

## 风险声明

免费数据源存在缺口和延迟；预测必须通过大样本 walk-forward、单票回测、模拟盘和风控后才可讨论实盘。真实下单在当前项目中仍然强制关闭。