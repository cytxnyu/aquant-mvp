# AQuant v0.2 Final Report Index

## 验收结论

v0.2 已完成核心升级：股票池扩容、免费真实源 smoke、177 因子、walk-forward/embargo、多模型基座、个股预测报告、单票回测、模拟盘风控、PIT 审计和真实下单阻断。

## 关键结果

- `all-a-free`：5527 只唯一股票。
- `mega-hot`：39 个主题、1421 行、1200 只唯一股票。
- 因子数量：177。
- 测试：`15 passed`。
- BaoStock smoke：000630 拉取 346 行。
- feature store：BaoStock 金属池 31128 行、177 因子，审计列完整。
- sample 全链路：总收益 50.62%，最大回撤 -17.47%，Sharpe 0.784。
- 000630 预测：1/5/20 日均输出概率、收益、风险区间、因子贡献、同池排名、trust_status。
- 000630 回测：20 日方向准确率 56.09%，return IC 0.1110；但风险指标较高。
- walk-forward：正式生成 `walk_forward_metrics.csv`，并写入 `data/warehouse/model_registry.parquet`。
- Paper trade：20 日 dry-run，风控通过，生成 6 条订单计划。
- Live trade：已验证强制阻断，返回预期安全退出。

## 主要报告目录

- `reports/aquant_v02_audit/system_capability_report.md`
- `reports/aquant_v02_final/universe_all_a_free`
- `reports/aquant_v02_final/verify_mega_hot`
- `reports/aquant_v02_final/verify_sample_run`
- `reports/aquant_v02_final/verify_baostock_smoke`
- `reports/aquant_v02_final/verify_audit_data`
- `reports/aquant_v02_final/verify_audit_data_final`
- `reports/aquant_v02_final/verify_feature_store`
- `reports/aquant_v02_final/verify_predict_000630`
- `reports/aquant_v02_final/verify_backtest_000630`
- `reports/aquant_v02_final/verify_walk_forward`
- `reports/aquant_v02_final/verify_model_evaluation`
- `reports/aquant_v02_final/verify_paper_trade`
- `reports/aquant_v02_final/stocks/000630`
- `reports/aquant_v02_final/stocks/601899`
- `reports/aquant_v02_final/stocks/600362`
- `reports/aquant_v02_final/stocks/300308`
- `reports/aquant_v02_final/stocks/300750`

## 文档

- `docs/AQUANT_V02_FULL_SYSTEM.md`
- `docs/UNIVERSE_EXPANSION.md`
- `docs/FACTOR_MODEL_REPORT.md`
- `docs/RISK_AND_PAPER_TRADING.md`

## 仍需注意

免费源仍不等于机构级数据。公告结构化、历史行业/指数成分、分钟级稳定性、实时行情和合规授权仍需后续接入专业数据源或券商授权。所有预测只作为概率化研究信号，不保证涨跌，不构成投资建议。
