# AQuant v0.2 Full System

## 已落地范围

AQuant v0.2 已从轻量 MVP 升级为可验证的 A 股免费源研究系统：

- 免费数据源：BaoStock、AKShare、Tushare free token 可选。
- 股票池：`core_hot`、`mega-hot`、`all-a-free` 三层。
- 因子：177 个量价/趋势/波动/流动性/拥挤/形态因子。
- 模型：factor score、sklearn logistic/ridge/linear、LightGBM classifier/regressor/ranker，XGBoost/CatBoost 可用时接入。
- 验证：walk-forward、embargo、样本外指标、单票预测回测。
- 报告：预测 CSV/JSON、解释 Markdown、回测指标、数据审计、模拟盘风控报告。
- 实盘安全：`live-trade` 继续强制拒绝真实下单。

## 关键命令

```powershell
python run_mvp.py build-universe --themes all-a-free --output-dir reports\aquant_v02_final\universe_all_a_free
python run_mvp.py build-universe --themes mega-hot --output-dir reports\aquant_v02_final\verify_mega_hot
python run_mvp.py sync-free-all --config configs\metals.json --source baostock --universe 000630 --start 2025-01-01 --max-symbols 1
python run_mvp.py predict-stock --config configs\metals.json --source baostock --universe config --symbol 000630 --horizons 1,5,20
python run_mvp.py backtest-stock --config configs\metals.json --source baostock --universe config --symbol 000630 --horizons 1,5,20
python run_mvp.py paper-trade --config configs\metals.json --source baostock --universe config --days 20 --no-live
```

## 当前限制

免费源能做研究验证，但不是机构级完整数据。行业历史、公告结构化、分钟级稳定性、实时行情一致性仍需要 Wind/iFinD/聚宽/米筐或券商授权数据补强。

所有预测均为概率化研究信号，不保证涨跌，不构成投资建议。
