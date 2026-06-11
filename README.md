# AQuant MVP: A 股量化研究平台第一阶段

这是一个面向 A 股的轻量量化研究平台。它不是“神奇预测器”，而是一个可运行、可验证、可扩展的研究闭环：数据读取、数据质量检查、股票池过滤、因子计算、标签生成、因子分析、选股策略、A 股规则回测和报告输出。

默认使用确定性 sample 数据，保证没有网络也能跑通；也支持切换到 AKShare 拉取真实 A 股日线数据。

## 架构

```text
src/aquant_mvp
├─ data        # AKShare/sample 数据、缓存、数据质量检查
├─ universe    # 股票池过滤，预留 ST/停牌/涨跌停/行业接口
├─ factors     # 多因子计算与横截面标准化
├─ labels      # 未来收益与超额收益标签
├─ analysis    # IC、RankIC、分组收益、覆盖率
├─ strategy    # 多因子打分选股、top_n、权重与换手控制
├─ backtest    # A 股基础规则回测
├─ reporting   # CSV/JSON/PNG/summary.md 报告
└─ workflow    # 研究流程入口
```

更多细节见：

- `docs/ARCHITECTURE.md`
- `docs/SCHEMA.md`
- `docs/GITHUB.md`
- `docs/REFERENCES.md`

## 快速运行

```powershell
python run_mvp.py run-demo
```

指定输出目录：

```powershell
python run_mvp.py run-demo --output-dir reports\verify_run
```

只做数据检查：

```powershell
python run_mvp.py check-data --source sample --output-dir reports\data_check
```

运行因子分析和完整回测：

```powershell
python run_mvp.py analyze-factors --source sample
```

## 使用 AKShare

安装可选依赖：

```powershell
pip install -e .[data]
```

运行：

```powershell
python run_mvp.py run --source akshare
```

如果你希望 AKShare 不可用时自动回退到 sample：

```powershell
python run_mvp.py run --source auto
```

## 当前因子

- 动量：`momentum_20`、`momentum_60`
- 反转：`reversal_5`、`reversal_10`
- 波动：`volatility_20`、`volatility_60`
- 流动性：`amount_mean_20`、`amount_mean_60`、`turnover_mean_20`、`turnover_mean_60`
- 量价：`volume_ratio_5_20`、`price_position_60`、`ma_bias_20`
- 风险：`max_drawdown_60`、`downside_volatility_20`

因子只使用当前日及历史数据。策略信号在调仓日生成，并在下一交易日开盘成交，避免同日收盘信号同日成交的常见回测幻觉。

## 当前标签与分析

- 未来 5 日收益：`future_return_5d`
- 未来 20 日收益：`future_return_20d`
- 截面超额收益：`excess_return_5d`、`excess_return_20d`
- 因子分析：IC、RankIC、ICIR、分组收益、覆盖率

## 回测规则

- 下一交易日开盘成交
- T+1 可卖约束
- 100 股一手
- 手续费
- 印花税
- 滑点
- 最小成交金额
- 每日资金曲线、每日收益、回撤
- 交易记录、持仓记录、调仓记录

## 输出文件

每次完整运行会生成一个报告目录，例如 `reports/verify_run/`：

- `summary.md`：本次运行摘要
- `manifest.json`：运行清单、输入配置、指标和产物大小
- `config.json`：运行配置快照
- `load_report.json`：数据加载报告
- `data_quality_summary.csv`、`data_quality_issues.csv`：数据质量检查
- `universe.csv`：股票池过滤结果
- `factors.csv`：因子面板
- `labels.csv`：未来收益标签
- `factor_ic_summary.csv`、`factor_ic_series.csv`：因子 IC
- `factor_quantile_returns.csv`、`factor_coverage.csv`：分组收益和覆盖率
- `factor_analysis.json`：因子分析摘要 JSON
- `scores.csv`：股票打分
- `rebalance_targets.csv`：调仓目标权重
- `equity_curve.csv`、`trades.csv`、`holdings.csv`、`rebalances.csv`
- `metrics.json`
- `equity_curve.png`、`drawdown.png`、`factor_ic.png`、`quantile_returns.png`

## 配置

默认配置在 `configs/mvp.json`。常改字段：

- `data.symbols`：股票池
- `data.start_date` / `data.end_date`：回测区间
- `universe.min_history_days`：最少历史天数
- `universe.min_amount`：最低成交额过滤
- `strategy.rebalance`：调仓频率，如 `W-FRI`、`ME`
- `strategy.top_n`：持仓数量
- `strategy.max_single_weight`：单票权重上限
- `strategy.max_turnover`：单次目标换手上限
- `strategy.factor_weights`：因子权重
- `backtest.fee_rate` / `tax_rate` / `slippage_rate`：交易成本
- `analysis.label_horizons`：标签周期

## 真实研究注意事项

sample 数据只用于验证流程，不代表真实收益。真实 A 股研究必须补齐：ST、停牌、涨跌停、退市、新股、复权、指数成分历史、行业分类历史、财报公告日、幸存者偏差和未来函数检查。

下一阶段路线见 `ROADMAP.md`。

## 推到 GitHub

当前会话中的 GitHub MCP 可以读取账号和仓库元数据，但没有暴露 fork/clone/create repo/push 写入工具；本地 GitHub CLI 已认证，可用于创建和推送远端。本项目已经整理成可直接发布的形态，命令见 `docs/GITHUB.md`。
