# AQuant 个股预测报告：601899

## 核心结论

- 最新交易日：`2026-06-10`
- 最新收盘价：`27.7000`
- 数据源：`baostock`
- 模型：`ensemble`
- 结论性质：概率化研究信号，不保证涨跌，不构成投资建议。

## 多周期预测

- `1d`: direction=`看多`, prob_up=`0.692`, expected_return=`0.475%`, p10/p50/p90=`-2.405%/0.475%/3.591%`, trust=`data_insufficient`
- `5d`: direction=`看多`, prob_up=`0.600`, expected_return=`3.000%`, p10/p50/p90=`-3.622%/3.000%/9.994%`, trust=`data_insufficient`
- `20d`: direction=`震荡偏弱`, prob_up=`0.370`, expected_return=`1.985%`, p10/p50/p90=`-9.874%/1.985%/19.255%`, trust=`data_insufficient`
- `60d`: direction=`震荡偏弱`, prob_up=`0.373`, expected_return=`4.443%`, p10/p50/p90=`-12.902%/4.443%/39.947%`, trust=`data_insufficient`

## 预测 K 线说明

- Base 情景第 20 日收盘：`28.2498`；p10/p50/p90 收盘带：`24.9650/28.2498/33.0336`。
- 最近风险标记：`none`；趋势标签：`破位`；置信度：`0.210`。

## 输出文件

- `stock_forecast.csv/json`: 多周期个股预测。
- `forecast_kline.csv/json`: 未来 OHLC 概率情景。
- `forecast_kline.png/html`: 历史 + 未来预测 K 线图。
- `history_kline.csv`: 图表使用的历史 K 线。

## 风险声明

免费数据源存在缺口和延迟；预测必须通过大样本 walk-forward、单票回测、模拟盘和风控后才可讨论实盘。真实下单在当前项目中仍然强制关闭。