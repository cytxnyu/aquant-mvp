# Factor And Model Report

## 因子体系

当前 `FACTOR_COLUMNS` 数量为 177。

已包含：

- 动量、反转、均线偏离、EMA、MACD、RSI。
- 波动率、下行波动、最大回撤、ATR、Bollinger。
- 突破、破位、价格区间位置、新高新低距离。
- 成交额、换手、量比、Amihud 非流动性、拥挤度。
- 跳空、上下影线、实体、连续上涨/下跌、涨跌停邻近。
- 价格效率、趋势强度、收益自相关。

## 因子报告

pipeline 输出：

- `factor_coverage.csv`
- `factor_ic_summary.csv`
- `factor_ic_series.csv`
- `factor_quantile_returns.csv`
- `factor_yearly_stability.csv`

`coverage` 现在同时包含覆盖率和缺失率。年度稳定性按年输出 RankIC、IC、正 RankIC 占比和观察数。

## 模型体系

已接入：

- `factor_score`
- `logistic`
- `ridge`
- `linear`
- `lightgbm_classifier`
- `lightgbm_regressor`
- `lightgbm_ranker`
- `ensemble`
- `xgboost` / `catboost` 可用时运行，不可用时自动降级。

walk-forward 使用时间切分，并在测试窗口前加入 `max(horizon, embargo_days)` 交易日 embargo。模型不优于基线时不得标为 `trusted`。
