# AQuant 个股预测报告：000630

## 核心结论

- 最新交易日：`2026-06-10`
- 最新收盘价：`109.6710`
- 数据源：`sample`
- 模型：`ensemble`
- 结论性质：概率化研究信号，不保证涨跌，不构成投资建议。

## 多周期预测

- `1d`: direction=`中性`, prob_up=`0.499`, expected_return=`0.046%`, p10/p50/p90=`-2.455%/0.046%/2.585%`, trust=`data_insufficient`
- `5d`: direction=`震荡偏弱`, prob_up=`0.464`, expected_return=`-0.191%`, p10/p50/p90=`-5.308%/-0.191%/5.495%`, trust=`data_insufficient`
- `10d`: direction=`震荡偏弱`, prob_up=`0.463`, expected_return=`-0.482%`, p10/p50/p90=`-7.957%/-0.482%/7.718%`, trust=`data_insufficient`
- `20d`: direction=`震荡偏多`, prob_up=`0.569`, expected_return=`-0.641%`, p10/p50/p90=`-11.013%/-0.641%/11.247%`, trust=`data_insufficient`
- `60d`: direction=`震荡偏多`, prob_up=`0.572`, expected_return=`4.486%`, p10/p50/p90=`-14.664%/4.486%/26.043%`, trust=`data_insufficient`

## 预测 K 线说明

- Base 情景第 10 日收盘：`109.1427`；p10/p50/p90 收盘带：`100.9442/109.1427/118.1357`。
- 最近风险标记：`none`；趋势标签：`无明显形态`；置信度：`0.067`。

## 输出文件

- `stock_forecast.csv/json`: 多周期个股预测。
- `forecast_kline.csv/json`: 未来 OHLC 概率情景。
- `forecast_kline.png/html`: 历史 + 未来预测 K 线图。
- `history_kline.csv`: 图表使用的历史 K 线。

## 风险声明

免费数据源存在缺口和延迟；预测必须通过大样本 walk-forward、单票回测、模拟盘和风控后才可讨论实盘。真实下单在当前项目中仍然强制关闭。