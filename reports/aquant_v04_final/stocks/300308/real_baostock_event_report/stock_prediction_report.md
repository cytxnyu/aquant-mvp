# AQuant 个股预测报告：300308

## 核心结论

- 最新交易日：`2026-06-10`
- 最新收盘价：`1147.0000`
- 数据源：`baostock`
- 模型：`event_aware_ensemble`
- 结论性质：概率化研究信号，不保证涨跌，不构成投资建议。

## 多周期预测

- `1d`: direction=`震荡偏多`, prob_up=`0.547`, expected_return=`-1.065%`, p10/p50/p90=`-4.641%/-1.065%/3.485%`, trust=`data_insufficient`
- `5d`: direction=`强看空`, prob_up=`0.256`, expected_return=`-3.134%`, p10/p50/p90=`-11.039%/-3.134%/10.525%`, trust=`data_insufficient`
- `20d`: direction=`看空`, prob_up=`0.361`, expected_return=`-10.564%`, p10/p50/p90=`-26.758%/-10.564%/28.730%`, trust=`data_insufficient`
- `60d`: direction=`强看空`, prob_up=`0.229`, expected_return=`-7.284%`, p10/p50/p90=`-36.820%/-7.284%/110.195%`, trust=`data_insufficient`

## 预测 K 线说明

- Base 情景第 20 日收盘：`1025.8311`；p10/p50/p90 收盘带：`840.0862/1025.8311/1476.5318`。
- 最近风险标记：`none`；趋势标签：`无明显形态`；置信度：`0.214`。

## 输出文件

- `stock_forecast.csv/json`: 多周期个股预测。
- `forecast_kline.csv/json`: 未来 OHLC 概率情景。
- `forecast_kline.png/html`: 历史 + 未来预测 K 线图。
- `history_kline.csv`: 图表使用的历史 K 线。

## 风险声明

免费数据源存在缺口和延迟；预测必须通过大样本 walk-forward、单票回测、模拟盘和风控后才可讨论实盘。真实下单在当前项目中仍然强制关闭。