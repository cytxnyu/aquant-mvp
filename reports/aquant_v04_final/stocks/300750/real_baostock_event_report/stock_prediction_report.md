# AQuant 个股预测报告：300750

## 核心结论

- 最新交易日：`2026-06-10`
- 最新收盘价：`388.5000`
- 数据源：`baostock`
- 模型：`event_aware_ensemble`
- 结论性质：概率化研究信号，不保证涨跌，不构成投资建议。

## 多周期预测

- `1d`: direction=`中性`, prob_up=`0.512`, expected_return=`-0.531%`, p10/p50/p90=`-3.111%/-0.531%/3.087%`, trust=`data_insufficient`
- `5d`: direction=`震荡偏弱`, prob_up=`0.430`, expected_return=`0.928%`, p10/p50/p90=`-5.807%/0.928%/7.737%`, trust=`data_insufficient`
- `20d`: direction=`看空`, prob_up=`0.306`, expected_return=`-3.332%`, p10/p50/p90=`-15.734%/-3.332%/13.585%`, trust=`data_insufficient`
- `60d`: direction=`中性`, prob_up=`0.485`, expected_return=`17.288%`, p10/p50/p90=`-5.017%/17.288%/53.905%`, trust=`data_insufficient`

## 预测 K 线说明

- Base 情景第 20 日收盘：`375.5533`；p10/p50/p90 收盘带：`327.3733/375.5533/441.2785`。
- 最近风险标记：`none`；趋势标签：`无明显形态`；置信度：`0.292`。

## 输出文件

- `stock_forecast.csv/json`: 多周期个股预测。
- `forecast_kline.csv/json`: 未来 OHLC 概率情景。
- `forecast_kline.png/html`: 历史 + 未来预测 K 线图。
- `history_kline.csv`: 图表使用的历史 K 线。

## 风险声明

免费数据源存在缺口和延迟；预测必须通过大样本 walk-forward、单票回测、模拟盘和风控后才可讨论实盘。真实下单在当前项目中仍然强制关闭。