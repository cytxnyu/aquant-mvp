# AQuant v0.4 Final Report Index

## New Documentation

- `docs/AQUANT_V04_TRUSTED_SYSTEM.md`
- `docs/NEWS_EVENT_ENGINE.md`
- `docs/FACTOR_TRUST_FRAMEWORK.md`

## Audit

- `reports/aquant_v04_audit/system_gap_report.md`

## Verification Outputs

- Factor trust: `reports/aquant_v04_final/verify_factor_trust_sample`
- Factor trust with cost/regime gates: `reports/aquant_v04_final/verify_factor_trust_cost_regime_sample`
- Sample news sync: `reports/aquant_v04_final/verify_sync_news_sample`
- Sample announcements sync: `reports/aquant_v04_final/verify_sync_announcements_sample`
- Sample event store: `reports/aquant_v04_final/verify_event_store_sample`
- Event source reliability weighting: `reports/aquant_v04_final/verify_event_reliability_weighting_sample`
- Event reliability feature store: `reports/aquant_v04_final/verify_feature_store_event_reliability_sample`
- Event reliability paper-trade guard: `reports/aquant_v04_final/verify_event_reliability_paper_trade_sample`
- 000630 report with event reliability features: `reports/aquant_v04_final/verify_report_stock_event_reliability_000630`
- Source discovery with `cninfo_direct`: `reports/aquant_v04_final/verify_discover_sources_cninfo_direct`
- Direct CNINFO announcement sync smoke: `reports/aquant_v04_final/verify_sync_announcements_cninfo_direct_000630`
- Direct CNINFO event-store empty-source audit: `reports/aquant_v04_final/verify_event_store_cninfo_direct_000630`
- Direct CNINFO announcement text smoke: `reports/aquant_v04_final/verify_sync_announcements_cninfo_text_000630`
- Direct CNINFO event-store text audit: `reports/aquant_v04_final/verify_event_store_cninfo_text_000630`
- Major announcement summary evidence: `reports/aquant_v04_final/verify_event_major_announcement_summary_sample`
- 000630 report with announcement text audit fields: `reports/aquant_v04_final/verify_report_stock_event_text_000630`
- 000630 report with conformal intervals and announcement text audit: `reports/aquant_v04_final/verify_report_stock_conformal_text_000630`
- Theme-keyword entity link sample: `reports/aquant_v04_final/verify_theme_entity_link_sample`
- Theme entity-link feature store: `reports/aquant_v04_final/verify_feature_store_theme_entity_link_sample`
- AKShare news sync: `reports/aquant_v04_final/verify_sync_news_akshare`
- AKShare event store: `reports/aquant_v04_final/verify_event_store_akshare`
- Stock report with news and K-line: `reports/aquant_v04_final/verify_report_stock_sample_000630`
- Event-aware feature store: `reports/aquant_v04_final/verify_feature_store_event_sample`
- Event-aware walk-forward: `reports/aquant_v04_final/verify_walk_forward_event_sample`
- News coverage audit: `reports/aquant_v04_final/verify_news_coverage_sample`
- Strict PIT data audit: `reports/aquant_v04_final/verify_audit_data_strict_pit`
- Model evaluation: `reports/aquant_v04_final/verify_evaluate_models`
- Model evaluation by year/theme/size/regime slices: `reports/aquant_v04_final/verify_evaluate_models_v04_slices`
- Walk-forward PIT diagnostic columns: `reports/aquant_v04_final/verify_walk_forward_pit_diagnostics_sample`
- Model evaluation with PIT liquidity/regime diagnostics: `reports/aquant_v04_final/verify_evaluate_models_pit_diagnostics_v2`
- BaoStock 20-symbol real-source walk-forward smoke: `reports/aquant_v04_final/verify_walk_forward_baostock_20_smoke`
- BaoStock 220-symbol real-source walk-forward: `reports/aquant_v04_final/verify_walk_forward_baostock_220_real`
- Model evaluation including BaoStock 220-symbol real-source evidence: `reports/aquant_v04_final/verify_evaluate_models_baostock_220_real`
- 000630 BaoStock 220-symbol real-source prediction: `reports/aquant_v04_final/verify_predict_stock_000630_baostock_220_real`
- Portfolio backtest: `reports/aquant_v04_final/verify_backtest_portfolio_sample`
- Portfolio constraint backtest: `reports/aquant_v04_final/verify_portfolio_constraints_sample`
- Portfolio constraint paper-trade dry run: `reports/aquant_v04_final/verify_portfolio_constraints_paper_trade_sample`
- Portfolio event attribution backtest: `reports/aquant_v04_final/verify_backtest_portfolio_event_attribution_sample`
- Event-risk guarded portfolio backtest: `reports/aquant_v04_final/verify_event_guard_backtest_sample`
- Event-risk guarded paper-trade dry run: `reports/aquant_v04_final/verify_event_guard_paper_trade_sample`
- Commodity news sync for metal stocks: `reports/aquant_v04_final/verify_commodity_news_metals`
- Commodity event store for metal stocks: `reports/aquant_v04_final/verify_commodity_event_store_metals`
- 220-symbol sample walk-forward trust gate: `reports/aquant_v04_final/verify_walk_forward_220_sample_trust_gate`
- Predict-stock walk-forward evidence gate: `reports/aquant_v04_final/verify_predict_stock_walk_forward_gate_sample`
- Report-stock walk-forward evidence gate: `reports/aquant_v04_final/verify_report_stock_walk_forward_gate_sample`
- Predict-stock probability calibration gate: `reports/aquant_v04_final/verify_predict_stock_calibration_gate_sample`
- Predict-stock conformal interval audit: `reports/aquant_v04_final/verify_predict_stock_conformal_000630_sample`
- 20-day paper-trade dry run: `reports/aquant_v04_final/verify_paper_trade_20d_sample`
- Key-stock news coverage audit: `reports/aquant_v04_final/verify_news_coverage_key_stocks`
- 000630 event-aware prediction chain: `reports/aquant_v04_final/stocks/000630`
- 000630 BaoStock event-aware prediction chain: `reports/aquant_v04_final/stocks/000630/06_real_baostock_event_report`

## Key Stock Full Reports

All five reports use probabilistic research output, forecast K-line charts, event evidence, factor contribution, stock forecast backtest, and manifest checks. All remain `data_insufficient` because the free-source local universes are below the 200-symbol trusted threshold.

- `000630` Tongling Nonferrous: `reports/aquant_v04_final/stocks/000630/06_real_baostock_event_report`
- `601899` Zijin Mining: `reports/aquant_v04_final/stocks/601899/real_baostock_event_report`
- `600362` Jiangxi Copper: `reports/aquant_v04_final/stocks/600362/real_baostock_event_report`
- `300308` Zhongji Innolight: `reports/aquant_v04_final/stocks/300308/real_baostock_event_report`
- `300750` CATL: `reports/aquant_v04_final/stocks/300750/real_baostock_event_report`

## Reproduce Core Commands

```powershell
python run_mvp.py analyze-factor-trust --config configs\mvp.json --source sample --universe config --horizons 5 --output-dir reports\aquant_v04_final\verify_factor_trust_sample
python run_mvp.py analyze-factor-trust --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --horizons 5 --output-dir reports\aquant_v04_final\verify_factor_trust_cost_regime_sample
python run_mvp.py sync-news --config configs\mvp.json --source akshare --universe 000630,601899 --start 2025-01-01 --output-dir reports\aquant_v04_final\verify_sync_news_akshare
python run_mvp.py build-event-store --config configs\mvp.json --source akshare --universe 000630,601899 --start 2025-01-01 --output-dir reports\aquant_v04_final\verify_event_store_akshare
python run_mvp.py build-event-store --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --start 2024-01-01 --output-dir reports\aquant_v04_final\verify_event_reliability_weighting_sample
python run_mvp.py discover-sources --domestic-only --output-dir reports\aquant_v04_final\verify_discover_sources_cninfo_direct
python run_mvp.py sync-announcements --config configs\mvp.json --source cninfo_direct --universe 000630 --start 2026-01-01 --output-dir reports\aquant_v04_final\verify_sync_announcements_cninfo_direct_000630
python run_mvp.py build-event-store --config configs\mvp.json --source cninfo_direct --universe 000630 --start 2026-01-01 --output-dir reports\aquant_v04_final\verify_event_store_cninfo_direct_000630
python run_mvp.py sync-announcements --config configs\mvp.json --source cninfo_direct --universe 000630 --start 2026-01-01 --fetch-announcement-text --output-dir reports\aquant_v04_final\verify_sync_announcements_cninfo_text_000630
python run_mvp.py build-event-store --config configs\mvp.json --source cninfo_direct --universe 000630 --start 2026-01-01 --fetch-announcement-text --output-dir reports\aquant_v04_final\verify_event_store_cninfo_text_000630
python run_mvp.py build-event-store --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --start 2024-01-01 --output-dir reports\aquant_v04_final\verify_event_major_announcement_summary_sample
python run_mvp.py build-event-store --config configs\mvp.json --source sample --allow-sample --universe 000630,300308 --start 2024-01-01 --output-dir reports\aquant_v04_final\verify_theme_entity_link_sample
python run_mvp.py build-feature-store --config configs\mvp.json --source sample --allow-sample --universe 000630,300308 --horizons 1,5,20,60 --point-in-time --with-news --output-dir reports\aquant_v04_final\verify_feature_store_theme_entity_link_sample
python run_mvp.py audit-news --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --start 2024-01-01 --output-dir reports\aquant_v04_final\verify_news_coverage_sample
python run_mvp.py build-feature-store --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --horizons 1,5,20,60 --point-in-time --with-news --output-dir reports\aquant_v04_final\verify_feature_store_event_sample
python run_mvp.py build-feature-store --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --horizons 1,5,20,60 --point-in-time --with-news --output-dir reports\aquant_v04_final\verify_feature_store_event_reliability_sample
python run_mvp.py train-walk-forward --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --model event_aware_ensemble --horizons 1,5,20,60 --output-dir reports\aquant_v04_final\verify_walk_forward_event_sample
python run_mvp.py backtest-portfolio --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --output-dir reports\aquant_v04_final\verify_backtest_portfolio_sample
python run_mvp.py backtest-portfolio --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --output-dir reports\aquant_v04_final\verify_portfolio_constraints_sample
python run_mvp.py paper-trade --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --days 20 --no-live --output-dir reports\aquant_v04_final\verify_portfolio_constraints_paper_trade_sample
python run_mvp.py backtest-portfolio --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --with-news --output-dir reports\aquant_v04_final\verify_backtest_portfolio_event_attribution_sample
python run_mvp.py backtest-portfolio --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --with-news --output-dir reports\aquant_v04_final\verify_event_guard_backtest_sample
python run_mvp.py paper-trade --config configs\mvp.json --source sample --allow-sample --with-news --no-live --output-dir reports\aquant_v04_final\verify_event_guard_paper_trade_sample
python run_mvp.py paper-trade --config configs\mvp.json --source sample --allow-sample --with-news --no-live --output-dir reports\aquant_v04_final\verify_event_reliability_paper_trade_sample
python run_mvp.py report-stock --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --symbol 000630 --horizons 1,5,20,60 --model event_aware_ensemble --days 10 --history-days 80 --with-news --with-kline --output-dir reports\aquant_v04_final\verify_report_stock_event_reliability_000630
python run_mvp.py report-stock --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --symbol 000630 --horizons 1,5,20,60 --model event_aware_ensemble --days 10 --history-days 80 --with-news --with-kline --output-dir reports\aquant_v04_final\verify_report_stock_event_text_000630
python run_mvp.py report-stock --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --symbol 000630 --horizons 1,5,20,60 --model event_aware_ensemble --days 10 --history-days 80 --with-news --with-kline --output-dir reports\aquant_v04_final\verify_report_stock_conformal_text_000630
python run_mvp.py sync-news --config configs\metals.json --source akshare --universe 000630,600362,601899 --start 2025-01-01 --output-dir reports\aquant_v04_final\verify_commodity_news_metals
python run_mvp.py build-event-store --config configs\metals.json --source akshare --universe 000630,600362,601899 --start 2025-01-01 --output-dir reports\aquant_v04_final\verify_commodity_event_store_metals
python run_mvp.py train-walk-forward --config configs\mvp.json --source sample --allow-sample --universe mega-hot --max-symbols 220 --min-symbols 200 --model factor_score --horizons 5 --train-years 1 --test-months 3 --start 2024-01-01 --output-dir reports\aquant_v04_final\verify_walk_forward_220_sample_trust_gate
python run_mvp.py evaluate-models --config configs\mvp.json --by-year --by-industry --output-dir reports\aquant_v04_final\verify_evaluate_models_v04_slices
python run_mvp.py train-walk-forward --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --model factor_score --horizons 5 --train-years 1 --test-months 2 --output-dir reports\aquant_v04_final\verify_walk_forward_pit_diagnostics_sample
python run_mvp.py evaluate-models --config configs\mvp.json --by-year --by-industry --output-dir reports\aquant_v04_final\verify_evaluate_models_pit_diagnostics_v2
python run_mvp.py train-walk-forward --config configs\prod.example.json --source baostock --universe mega-hot --max-symbols 220 --min-symbols 200 --model factor_score --horizons 5 --train-years 1 --test-months 3 --start 2024-01-01 --output-dir reports\aquant_v04_final\verify_walk_forward_baostock_220_real
python run_mvp.py evaluate-models --config configs\prod.example.json --by-year --by-industry --output-dir reports\aquant_v04_final\verify_evaluate_models_baostock_220_real
python run_mvp.py predict-stock --config configs\prod.example.json --source baostock --universe mega-hot --max-symbols 220 --symbol 000630 --horizons 5 --model factor_score --start 2024-01-01 --output-dir reports\aquant_v04_final\verify_predict_stock_000630_baostock_220_real
python run_mvp.py predict-stock --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --symbol 000630 --horizons 5 --model factor_score --output-dir reports\aquant_v04_final\verify_predict_stock_walk_forward_gate_sample
python run_mvp.py predict-stock --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --symbol 000630 --horizons 5 --model factor_score --output-dir reports\aquant_v04_final\verify_predict_stock_calibration_gate_sample
python run_mvp.py predict-stock --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --symbol 000630 --horizons 1,5,20,60 --model factor_score --output-dir reports\aquant_v04_final\verify_predict_stock_conformal_000630_sample
python run_mvp.py report-stock --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --symbol 000630 --horizons 5 --model factor_score --days 5 --history-days 60 --with-news --with-kline --output-dir reports\aquant_v04_final\verify_report_stock_walk_forward_gate_sample
python run_mvp.py audit-news --config configs\prod.example.json --source baostock --universe 000630,601899,600362,300308,300750 --start 2025-01-01 --output-dir reports\aquant_v04_final\verify_news_coverage_key_stocks
python run_mvp.py report-stock --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --symbol 000630 --days 10 --history-days 80 --horizons 1,5,20,60 --with-news --with-kline --output-dir reports\aquant_v04_final\verify_report_stock_sample_000630
python run_mvp.py report-stock --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --symbol 000630 --model event_aware_ensemble --days 20 --history-days 120 --horizons 1,5,20,60 --with-news --with-kline --output-dir reports\aquant_v04_final\stocks\000630\04_full_report_source_isolated
python run_mvp.py report-stock --config configs\metals.json --source baostock --universe config --symbol 000630 --horizons 1,5,20,60 --model event_aware_ensemble --with-news --with-kline --days 20 --history-days 160 --output-dir reports\aquant_v04_final\stocks\000630\06_real_baostock_event_report
```

## Operational Notes

- BaoStock has a global login/session behavior; run BaoStock-heavy jobs sequentially rather than in parallel to avoid `用户未登录` session collisions.
- News cache loading now fetches missing symbols before auditing coverage, so partial `raw_events` cache no longer causes false `no_linked_news` results.
- `backtest-portfolio --with-news` writes `portfolio_event_attribution_daily.csv`, `portfolio_event_attribution_symbol.csv`, and `portfolio_event_attribution.md`.
- `backtest-portfolio` writes portfolio-constraint audit outputs plus a constrained backtest (`portfolio_constraint_*`). The sample constrained run reduced drawdown at the cost of lower return, and that trade-off is explicitly reported.
- `paper-trade --no-live` applies portfolio constraints before order generation and records the constraint metadata in `paper_summary.json`.
- `backtest-portfolio --with-news` now also writes event-risk guarded targets, trades, holdings, attribution, and `event_guarded_metrics.json`.
- `paper-trade --with-news --no-live` applies event-risk target adjustment before order planning and writes `event_risk_guard_report.*`.
- Metals commodity event verification writes `akshare_futures_main_sina` evidence into `news_evidence.md`; run shared event-warehouse write jobs sequentially to avoid cache races.
- The 220-symbol sample walk-forward run is a trust-gate smoke test only; it produced `weak`, not `trusted`, because AUC and Brier gates failed.
- `predict-stock` and `report-stock` now carry walk-forward registry evidence into every forecast row. A single-stock report cannot become `trusted` unless matching large-universe walk-forward evidence for the same model and horizon is itself `trusted`.
- `evaluate-models` now reads registered walk-forward artifacts and writes real OOS slices by year, theme proxy, size/liquidity availability, and ex-post market regime. It exposes weak periods such as the 2026 sample slice instead of hiding them in aggregate metrics.
- `predict-stock` now writes probability calibration evidence (`calibration_rows`, bins, ECE, status). Sparse or failed calibration prevents `trusted`, even when the raw probability looks strong.
- `predict-stock` now writes conformal-style interval evidence (`conformal_method`, rows, target coverage, half-width, status) next to `return_p10/p50/p90`; sparse interval evidence prevents a real signal from becoming `trusted`.
- New walk-forward artifacts carry PIT diagnostic fields such as `amount_mean_20`, `cs_amount_rank_20`, `market_breadth`, and `market_mean_return`, allowing evaluation to separate PIT liquidity/regime slices from older artifacts where those fields are unavailable.
- The BaoStock 220-symbol real-source walk-forward loaded 220/220 symbols and produced 72,748 OOS rows, but stayed `weak` because AUC, Brier, and RankIC gates failed. The 000630 real-source prediction therefore also stayed `weak`.
- BaoStock batch loading now reuses a lazy session and resilient free-source commands record per-symbol failures instead of aborting the whole large-universe run.
- Factor trust now includes top correlated factor ids, cost-adjusted top-bottom spread, estimated cost drag, and bullish/sideways/bearish regime stability. The latest sample audit kept 67/237 factors approved, put 157 on watchlist, and quarantined 13; this gate is intentionally allowed to reject attractive-looking but expensive or regime-fragile factors.
- Event evidence now carries `source_category`, `source_reliability`, and `weighted_impact_score`; event factors add weighted impact and reliability features, and event risk uses the weighted impact when available.
- `cninfo_direct` is now a first direct public-source adapter. In the 000630 smoke run the endpoint returned an unexpected schema, so the system wrote 0 rows plus warnings instead of fabricating announcement events.
- `--fetch-announcement-text` now attempts bounded direct announcement body extraction and records `source_text_status`, length, and hash. The evidence report includes a `Recent Major Announcement Summary` section.
- Macro/policy/industry news without stock codes can now enter event factors through audited theme-keyword entity links. The sample verification mapped AI/semiconductor policy news to `300308` and metals policy news to `000630`, while recording method, confidence, and keywords.

All outputs are probabilistic research evidence, not guaranteed predictions or investment advice.
