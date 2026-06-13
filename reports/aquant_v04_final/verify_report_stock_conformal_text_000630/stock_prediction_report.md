# AQuant 个股预测报告：000630

## 核心结论

- 最新交易日：`2025-12-31`
- 最新收盘价：`33.6344`
- 数据源：`sample`
- 模型：`event_aware_ensemble`
- 结论性质：概率化研究信号，不保证涨跌，不构成投资建议。

## 多周期预测

- `1d`: direction=`看空`, prob_up=`0.326`, expected_return=`-0.718%`, p10/p50/p90=`-3.168%/-0.718%/1.732%`, trust=`data_insufficient`
- `5d`: direction=`看空`, prob_up=`0.351`, expected_return=`0.215%`, p10/p50/p90=`-5.620%/0.215%/6.050%`, trust=`data_insufficient`
- `10d`: direction=`震荡偏弱`, prob_up=`0.397`, expected_return=`0.685%`, p10/p50/p90=`-8.010%/0.685%/9.379%`, trust=`data_insufficient`
- `20d`: direction=`看多`, prob_up=`0.637`, expected_return=`2.246%`, p10/p50/p90=`-10.668%/2.246%/15.160%`, trust=`data_insufficient`
- `60d`: direction=`震荡偏多`, prob_up=`0.533`, expected_return=`-0.627%`, p10/p50/p90=`-21.986%/-0.627%/20.732%`, trust=`data_insufficient`

## 预测 K 线说明

- Base 情景第 10 日收盘：`33.8647`；p10/p50/p90 收盘带：`30.9404/33.8647/36.7890`。
- 最近风险标记：`none`；趋势标签：`趋势延续`；置信度：`0.155`。

## 输出文件

- `stock_forecast.csv/json`: 多周期个股预测。
- `forecast_kline.csv/json`: 未来 OHLC 概率情景。
- `forecast_kline.png/html`: 历史 + 未来预测 K 线图。
- `history_kline.csv`: 图表使用的历史 K 线。

## 风险声明

免费数据源存在缺口和延迟；预测必须通过大样本 walk-forward、单票回测、模拟盘和风控后才可讨论实盘。真实下单在当前项目中仍然强制关闭。