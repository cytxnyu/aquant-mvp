# AQuant v0.2 System Capability Report

## 当前能力

- CLI 已覆盖：数据检查、数据同步、股票池构建、PIT 审计、feature store、模型训练、walk-forward、模型评估、个股预测、个股回测、解释报告、模拟盘、QMT 只读状态、真实下单阻断。
- 股票池已覆盖：`core_hot`、`mega-hot`、`all-a-free`。本轮 `all-a-free` 5527 只，`mega-hot` 1200 只。
- 数据源已覆盖：BaoStock、AKShare、Tushare free token 可选；QMT/XtQuant 保留只读接口。
- 仓库表已覆盖：`daily_bar / source_audit / feature_store / universe / model_registry / stock_forecast / backtest_result / paper_trade`。
- 审计列已覆盖：上述核心表均包含 `source / fetched_at / effective_date / announce_date / raw_hash / quality_flag`。
- 因子已扩展：177 个免费可计算量价技术因子，并输出覆盖率、缺失率、IC、RankIC、分层收益、年度稳定性。
- 模型已扩展：factor score、logistic/ridge/linear、LightGBM classifier/regressor/ranker，XGBoost/CatBoost 可用时接入。
- 验证已覆盖：时间切分、walk-forward、embargo、样本外指标、单票预测回测。
- 风控已覆盖：资金、单票、单笔订单、黑名单、亏损/回撤配置、100 股手数、手续费、印花税、滑点。
- 实盘安全：`live-trade` 强制拒绝真实下单。

## 本轮验收证据

- `python -m pip check`：通过。
- `python -m compileall -q src tests run_mvp.py`：通过。
- `python -m pytest -q`：15 passed。
- `build-universe --themes all-a-free`：5527 只。
- `build-universe --themes mega-hot`：1200 只。
- `sync-free-all --source baostock --universe 000630`：346 行。
- `audit-data --strict-pit`：0 issues。
- `predict-stock --symbol 000630`：输出 1/5/20 日预测。
- `backtest-stock --symbol 000630`：输出方向准确率、Brier、return IC、分层收益、最大回撤。
- `paper-trade --days 20 --no-live`：风控通过，生成订单计划。
- `live-trade --confirm`：预期阻断。

## 仍然不足

- 免费源不保证机构级稳定性，尤其是公告结构化、历史行业分类、指数成分历史、资金流一致性、分钟级稳定性和实时行情。
- 当前代表股报告多使用 10-20 只横截面池，系统按规则标记 `data_insufficient`，没有伪装成高置信。
- `theme_metrics.csv` 仍是免费模式占位，后续需要真实行业/主题历史表才能做严格主题归因。
- QMT 仍未做真实账户对账实测，因为本机是否安装并登录 MiniQMT 取决于用户环境。

## 结论

AQuant v0.2 已经达到“免费源下可运行、可验证、可解释、可模拟”的研究系统状态，但还不是机构级实盘系统。下一阶段应重点补专业数据授权、全市场 walk-forward 长周期验证、行业/风格中性组合优化和 QMT 只读实盘对账。
