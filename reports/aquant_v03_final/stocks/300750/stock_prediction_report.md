# AQuant 个股预测报告：300750

## 核心结论

- 最新交易日：`2025-12-31`
- 最新收盘价：`361.5902`
- 数据源：`baostock`
- 模型：`ensemble`
- 结论性质：概率化研究信号，不保证涨跌，不构成投资建议。

## 多周期预测

- `1d`: direction=`中性`, prob_up=`0.489`, expected_return=`0.399%`, p10/p50/p90=`-2.071%/0.399%/3.738%`, trust=`data_insufficient`
- `5d`: direction=`看空`, prob_up=`0.341`, expected_return=`-2.102%`, p10/p50/p90=`-8.260%/-2.102%/4.485%`, trust=`data_insufficient`
- `20d`: direction=`看多`, prob_up=`0.597`, expected_return=`2.708%`, p10/p50/p90=`-9.427%/2.708%/18.465%`, trust=`data_insufficient`
- `60d`: direction=`看多`, prob_up=`0.630`, expected_return=`18.001%`, p10/p50/p90=`-4.482%/18.001%/53.972%`, trust=`data_insufficient`

## 预测 K 线说明

- Base 情景第 20 日收盘：`371.3813`；p10/p50/p90 收盘带：`327.5016/371.3813/428.3596`。
- 最近风险标记：`none`；趋势标签：`无明显形态`；置信度：`0.145`。

## 输出文件

- `stock_forecast.csv/json`: 多周期个股预测。
- `forecast_kline.csv/json`: 未来 OHLC 概率情景。
- `forecast_kline.png/html`: 历史 + 未来预测 K 线图。
- `history_kline.csv`: 图表使用的历史 K 线。

## 风险声明

免费数据源存在缺口和延迟；预测必须通过大样本 walk-forward、单票回测、模拟盘和风控后才可讨论实盘。真实下单在当前项目中仍然强制关闭。