# AQuant Foundations And Tools

This document records the practical bases and tools that AQuant can use or inspect.

## Foundation Registry

Run:

```powershell
python run_mvp.py discover-foundations --output-dir reports\foundations
```

Outputs:

- `foundation_registry.csv`
- `foundation_registry.md`

The registry covers:

- Research bases: Qlib, RQAlpha.
- Backtest bases: Backtrader, vectorbt.
- Model bases: LightGBM, XGBoost, CatBoost, scikit-learn, PyTorch.
- Explainability and model ops: SHAP, Optuna.
- Free data bases: AKShare, BaoStock, Tushare free token.
- Authorized data bases: WindPy, iFinD, RQData.
- Broker base: QMT/XtQuant read-only, with live orders blocked.
- Factor tool base: TA-Lib.
- Storage base: DuckDB and Parquet.

Optional dependency groups:

```powershell
pip install -e .[model]
pip install -e .[model-extra]
pip install -e .[research-base]
pip install -e .[paid-data]
pip install -e .[broker-base]
pip install -e .[factor-tools]
```

Use a domestic mirror when needed:

```powershell
pip install -e .[model-extra] -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## Tool Registry

Run:

```powershell
python run_mvp.py discover-tools --output-dir reports\tools
```

Outputs:

- `tool_registry.csv`
- `tool_registry.md`

The registry covers data discovery, mega-hot universe generation, free-source sync, point-in-time audit, feature store build, walk-forward training, model evaluation, stock forecast, stock explanation, stock backtest, paper trading, QMT read-only sync, and live-trade blocking.

## Safety Rules

External tools can improve coverage and speed, but they do not remove the validation gates:

- Predictions remain probabilistic research signals.
- Sample data cannot produce trusted forecasts.
- Free data failures must be written into audit reports.
- QMT live order submission remains blocked by default.
- A model must beat the baseline in walk-forward validation before its signal can be trusted.

## Landing Plan And Result

Plan executed on 2026-06-12:

1. Install the native free-data, warehouse and model layer first: AKShare, BaoStock, Tushare, DuckDB, PyArrow, LightGBM and pytest.
2. Install model challengers and model-ops tools: XGBoost, CatBoost, scikit-learn, SHAP and Optuna.
3. Install research and backtest bases: Qlib, RQAlpha, Backtrader and vectorbt.
4. Install execution and professional-data candidates: vn.py, XtQuant, RQData and TA-Lib.
5. Keep WindPy and iFinDPy as authorized-terminal routes because public PyPI mirrors do not provide those SDKs.
6. Verify with registry reports, import checks, `pip check`, tests, universe generation, sample sync, stock forecast, QMT read-only smoke and paper-trade dry-run.

Final registry result:

- `reports\foundations_final`: 21 foundations tracked after adding TA-Lib; 19 installed.
- Installed and import-verified: Qlib, RQAlpha, Backtrader, vectorbt, LightGBM, XGBoost, CatBoost, scikit-learn, PyTorch, SHAP, Optuna, AKShare, BaoStock, Tushare, RQData, DuckDB, PyArrow, XtQuant, vn.py and TA-Lib.
- Not installed: WindPy and iFinDPy. They require licensed Wind/iFinD terminal SDKs and cannot be installed from the public Python mirror.
- Credential caveat: Tushare and RQData packages are installed, but real data access still needs valid user tokens/accounts.
- Safety caveat: `live-trade` remains blocked; QMT/XtQuant is only landed for read-only and guarded paper/simulation workflows in this project.

Verification commands that passed:

```powershell
python -m pip check
python -m pytest -q
python run_mvp.py build-universe --themes mega-hot --output-dir reports\mega_hot_final
python run_mvp.py build-universe --themes professional --output-dir reports\professional_final
python run_mvp.py sync-free-all --config configs\mvp.json --source sample --universe mega-hot --max-symbols 5 --output-dir reports\free_max_sync_final
python run_mvp.py predict-stock --config configs\mvp.json --source sample --universe professional --symbol 601899 --horizons 1 --model factor_score --allow-sample --output-dir reports\stock_forecast_professional_final
python run_mvp.py qmt-readonly-sync --output-dir reports\qmt_readonly_final
python run_mvp.py paper-trade --config configs\mvp.json --source sample --universe professional --days 20 --no-live --output-dir reports\paper_trade_final
```
