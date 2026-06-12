# 铜陵有色 000630 全报告索引

生成时间：2026-06-12

## 数据与范围

- 股票：铜陵有色 `000630`
- 数据源：BaoStock，严格真实免费源，未使用 sample 预测
- 数据区间：2020-01-01 到 2026-06-10
- 股票池：`configs/metals.json` 的 20 只核心金属/有色股票
- 日线行数：31128 行，已过滤 32 行零成交额/疑似停牌行
- 严格 PIT 审计：0 个问题

## 走势预测摘要

来源文件：`08_stock_forecast/stock_forecast.csv`

| 周期 | 上涨概率 | 预期收益 | 预期超额收益 | 方向 | K线趋势 | 风险 | 可信等级 |
|---|---:|---:|---:|---|---|---|---|
| 1日 | 53.14% | 0.141% | -0.048% | 震荡偏多 | 无明显形态 | high_volatility | data_insufficient |
| 5日 | 50.91% | 2.445% | -0.556% | 中性 | 无明显形态 | high_volatility | data_insufficient |
| 20日 | 42.92% | 7.971% | 2.839% | 震荡偏弱 | 无明显形态 | high_volatility | data_insufficient |

解释：20日“预期收益为正但上涨概率低于 50%”说明模型给出的收益分布偏斜，不能简单理解为确定看多。当前股票池只有 20 只，低于系统的 200 只可信门槛，所以全部结论都被降级为 `data_insufficient`。

## 横截面组合预测

来源文件：`06_portfolio_predict/predictions.csv`

- 铜陵有色在 20 只金属池中排名：17/20
- 组合信号：回避
- 预测超额收益：-0.6625%

这只是当前因子/模型组合下的横截面研究信号，不是交易建议。

## 单票历史验证

来源文件：`09_stock_backtest/stock_forecast_metrics.csv`

| 周期 | 样本数 | 方向准确率 | Brier | Return IC | Top组收益 | Bottom组收益 | 最大回撤 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1日 | 1547 | 53.26% | 0.2495 | -0.0381 | -0.074% | 0.204% | -51.45% |
| 5日 | 1543 | 50.75% | 0.2484 | 0.0163 | 1.460% | -0.096% | -96.28% |
| 20日 | 1528 | 56.09% | 0.2434 | 0.1110 | 3.305% | 0.567% | -99.995% |

## 模型验证摘要

来源文件：`04_walk_forward_fixed/walk_forward_metrics.csv`

- 1日：方向准确率 51.06%，RankIC 0.0241，beats_baseline=True，trust=data_insufficient
- 5日：方向准确率 50.81%，RankIC 0.0446，beats_baseline=True，trust=data_insufficient
- 20日：方向准确率 48.99%，RankIC 0.0556，beats_baseline=True，trust=data_insufficient

## 解释报告

来源目录：`10_stock_explain_fixed`

关键因子：

- `downside_volatility_5`
- `volatility_5`
- `volatility_20`
- `downside_volatility_10`
- `downside_volatility_20`
- `reversal_2`
- `momentum_2`
- `max_drawdown_120`

历史相似状态均值：

- 1日：0.345%，样本 20
- 5日：3.262%，样本 17
- 20日：1.027%，样本 15

## 模拟盘与安全

来源目录：`12_paper_trade`

- 风控：通过
- 模拟订单数：6
- 铜陵有色模拟目标：买入 26200 股，目标权重约 16.67%
- 说明：这是 PaperBroker dry-run 的机械订单计划，不是真实委托，也不是投资建议。

QMT 只读：

- 来源目录：`13_qmt_readonly`
- `xtquant` 可用
- live submit disabled

真实下单：

- `live-trade --confirm` 已验证仍然强制拒绝真实下单

## 报告目录

- `00_universe_metals`：金属主题股票池
- `00_universe_mega_hot`：mega-hot 大股票池快照
- `01_sync_baostock_fixed`：BaoStock 同步结果
- `02_audit_fixed`：严格 PIT 数据审计
- `03_feature_store_fixed`：PIT 特征库
- `04_walk_forward_fixed`：walk-forward 样本外训练
- `05_train_model_fixed`：模型训练注册
- `06_portfolio_predict`：组合横截面预测
- `07_portfolio_backtest`：组合回测
- `08_stock_forecast`：铜陵有色单票预测
- `09_stock_backtest`：铜陵有色单票预测回测
- `10_stock_explain_fixed`：铜陵有色解释报告
- `11_evaluate_models_fixed`：模型评估汇总
- `12_paper_trade`：模拟盘订单计划和风控
- `13_qmt_readonly`：QMT 只读状态

## 复跑命令

```powershell
python run_mvp.py sync-free-all --config configs\metals.json --source baostock --universe config --start 2020-01-01 --output-dir reports\tongling_000630_full\01_sync_baostock_fixed
python run_mvp.py audit-data --config configs\metals.json --source baostock --strict-pit --output-dir reports\tongling_000630_full\02_audit_fixed
python run_mvp.py build-feature-store --config configs\metals.json --source baostock --universe config --horizons 1,5,20 --point-in-time --output-dir reports\tongling_000630_full\03_feature_store_fixed
python run_mvp.py train-walk-forward --config configs\metals.json --source baostock --universe config --model ensemble --horizons 1,5,20 --output-dir reports\tongling_000630_full\04_walk_forward_fixed
python run_mvp.py predict-stock --config configs\metals.json --source baostock --universe config --symbol 000630 --horizons 1,5,20 --model ensemble --output-dir reports\tongling_000630_full\08_stock_forecast
python run_mvp.py backtest-stock --config configs\metals.json --source baostock --universe config --symbol 000630 --horizons 1,5,20 --output-dir reports\tongling_000630_full\09_stock_backtest
python run_mvp.py explain-stock --config configs\metals.json --source baostock --universe config --symbol 000630 --horizons 1,5,20 --model ensemble --output-dir reports\tongling_000630_full\10_stock_explain_fixed
```

## 边界

这是一套概率化研究报告，不保证涨跌，不构成投资建议。若要把 `data_insufficient` 提升到更可信等级，需要用至少 200 只以上股票池或全 A 样本重新训练、walk-forward 验证，并连续跑模拟盘。
