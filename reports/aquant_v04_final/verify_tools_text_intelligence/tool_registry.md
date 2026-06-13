# Tool Registry

This registry records which AQuant tools are currently exposed as runnable commands.

- total: 18
- live trading allowed tools: 0

| tool | category | maturity | live | command |
| --- | --- | --- | --- | --- |
| stock_backtest | backtest | implemented | False | `python run_mvp.py backtest-stock --symbol 601899` |
| live_trade_blocker | broker | safety_block | False | `python run_mvp.py live-trade --confirm` |
| paper_trade | broker | implemented | False | `python run_mvp.py paper-trade --days 20 --no-live` |
| qmt_readonly | broker | implemented_readonly | False | `python run_mvp.py qmt-readonly-sync` |
| free_max_sync | data | implemented | False | `python run_mvp.py sync-free-all --universe mega-hot` |
| source_discovery | data | implemented | False | `python run_mvp.py discover-sources --domestic-only` |
| pit_audit | data_quality | implemented | False | `python run_mvp.py audit-data --strict-pit` |
| event_impact_study | explainability | implemented | False | `python run_mvp.py analyze-event-impact --universe 000630,601899,600362` |
| similar_event_evidence | explainability | implemented | False | `python run_mvp.py build-event-store --source sample --allow-sample --universe 000630,601899,600362` |
| stock_explain | explainability | implemented | False | `python run_mvp.py explain-stock --symbol 601899` |
| feature_store | features | implemented | False | `python run_mvp.py build-feature-store --point-in-time` |
| foundation_registry | foundation | implemented | False | `python run_mvp.py discover-foundations` |
| text_intelligence_registry | foundation | implemented | False | `python run_mvp.py discover-text-intelligence` |
| model_evaluation | model | implemented | False | `python run_mvp.py evaluate-models --by-year --by-industry` |
| walk_forward_training | model | implemented | False | `python run_mvp.py train-walk-forward --model ensemble` |
| stock_forecast | prediction | implemented | False | `python run_mvp.py predict-stock --symbol 601899 --universe mega-hot` |
| tool_registry | tooling | implemented | False | `python run_mvp.py discover-tools` |
| mega_hot_universe | universe | implemented | False | `python run_mvp.py build-universe --themes mega-hot` |
