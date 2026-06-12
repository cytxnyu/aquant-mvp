# Foundation Registry

This registry records which external quant bases can be used by AQuant, whether they are installed, and how they fit into the system.

- total: 20
- installed: 5
- native_supported: 5

| foundation | category | status | installed | license | package |
| --- | --- | --- | --- | --- | --- |
| backtrader | backtest_engine | candidate_adapter | False | open_source | backtrader |
| vectorbt | backtest_engine | candidate_adapter | False | open_source | vectorbt |
| qmt_xtquant | broker_base | read_only_supported_live_blocked | False | broker_authorized | xtquant |
| pytorch | deep_learning_base | future_candidate | True | open_source | torch |
| vnpy | execution_platform | candidate_adapter | False | open_source_plus_gateway_auth | vnpy |
| shap | explainability | candidate_explainer | False | open_source | shap |
| akshare | free_data | native_supported | True | free_public | akshare |
| baostock | free_data | native_supported | True | free_public | baostock |
| tushare_free | free_data | native_supported | False | free_token_limited | tushare |
| lightgbm | model_base | native_supported | True | open_source | lightgbm |
| scikit_learn | model_base | candidate_model | True | open_source | scikit-learn |
| xgboost | model_base | candidate_model | False | open_source | xgboost |
| catboost | model_base | candidate_model | False | open_source | catboost |
| optuna | model_ops | candidate_model_ops | False | open_source | optuna |
| ifind | paid_data | future_adapter | False | paid_or_authorized | iFinDPy |
| rqdata | paid_data | future_adapter | False | paid_or_authorized | rqdatac |
| windpy | paid_data | future_adapter | False | paid_or_authorized | WindPy |
| qlib | research_platform | candidate_adapter | False | open_source | pyqlib |
| rqalpha | research_platform | candidate_adapter | False | open_source | rqalpha |
| duckdb_parquet | storage_base | native_supported | False | open_source | duckdb pyarrow |
