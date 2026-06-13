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
- BaoStock 220-symbol real factor trust audit: `reports/aquant_v04_final/verify_factor_trust_baostock_220_real`
- BaoStock 220-symbol approved-factor walk-forward: `reports/aquant_v04_final/verify_walk_forward_baostock_220_factor_trust_approved_real`
- Directed model evaluation for approved-factor BaoStock walk-forward: `reports/aquant_v04_final/verify_evaluate_models_baostock_220_factor_trust_approved_real`
- XGBoost walk-forward model-base audit smoke: `reports/aquant_v04_final/verify_walk_forward_xgboost_model_audit_sample`
- LightGBM walk-forward model-base audit smoke: `reports/aquant_v04_final/verify_walk_forward_lightgbm_model_audit_sample`
- CatBoost walk-forward model-base audit smoke: `reports/aquant_v04_final/verify_walk_forward_catboost_model_audit_sample`
- BaoStock 220-symbol LightGBM approved-factor walk-forward: `reports/aquant_v04_final/verify_walk_forward_baostock_220_lightgbm_approved_real`
- Directed model evaluation for BaoStock LightGBM approved-factor walk-forward: `reports/aquant_v04_final/verify_evaluate_models_baostock_220_lightgbm_approved_real`
- Mega-hot theme coverage audit: `reports/aquant_v04_final/verify_mega_hot_theme_coverage`
- Professional theme coverage audit: `reports/aquant_v04_final/verify_professional_theme_coverage`
- Sample news sync: `reports/aquant_v04_final/verify_sync_news_sample`
- Sample announcements sync: `reports/aquant_v04_final/verify_sync_announcements_sample`
- Sample event store: `reports/aquant_v04_final/verify_event_store_sample`
- Event source reliability weighting: `reports/aquant_v04_final/verify_event_reliability_weighting_sample`
- Event factor quality event-store audit: `reports/aquant_v04_final/verify_event_factor_quality_store_sample`
- Event reliability feature store: `reports/aquant_v04_final/verify_feature_store_event_reliability_sample`
- Event factor quality feature-store audit: `reports/aquant_v04_final/verify_event_factor_quality_feature_store_sample`
- Event factor quality walk-forward gate: `reports/aquant_v04_final/verify_walk_forward_event_factor_quality_sample`
- Event reliability paper-trade guard: `reports/aquant_v04_final/verify_event_reliability_paper_trade_sample`
- 000630 report with event reliability features: `reports/aquant_v04_final/verify_report_stock_event_reliability_000630`
- Text intelligence registry: `reports/aquant_v04_final/verify_text_intelligence_registry`
- Event store with text intelligence registry: `reports/aquant_v04_final/verify_event_store_text_intelligence_sample`
- PIT-safe similar-event store evidence: `reports/aquant_v04_final/verify_similar_event_store_sample`
- 000630 report with stock similar-event evidence: `reports/aquant_v04_final/verify_report_stock_similar_events_000630`
- Event impact study: `reports/aquant_v04_final/verify_event_impact_study_sample`
- 000630 report with event-impact evidence: `reports/aquant_v04_final/verify_report_stock_event_impact_000630`
- Source discovery with `cninfo_direct`: `reports/aquant_v04_final/verify_discover_sources_cninfo_direct`
- Domestic source gap matrix: `reports/aquant_v04_final/verify_source_gap_matrix`
- Direct CNINFO announcement sync smoke: `reports/aquant_v04_final/verify_sync_announcements_cninfo_direct_000630`
- Direct CNINFO event-store empty-source audit: `reports/aquant_v04_final/verify_event_store_cninfo_direct_000630`
- Direct CNINFO announcement text smoke: `reports/aquant_v04_final/verify_sync_announcements_cninfo_text_000630`
- Direct CNINFO event-store text audit: `reports/aquant_v04_final/verify_event_store_cninfo_text_000630`
- Official CSRC public sync smoke: `reports/aquant_v04_final/verify_official_public_sync_csrc`
- Official CSRC public event-store empty-source audit: `reports/aquant_v04_final/verify_official_public_event_store_csrc`
- Official CSRC public text sync smoke: `reports/aquant_v04_final/verify_official_public_sync_csrc_text`
- Official CSRC public text event-store audit: `reports/aquant_v04_final/verify_official_public_event_store_csrc_text`
- Official CSRC public pagination sync smoke: `reports/aquant_v04_final/verify_official_public_sync_csrc_pages`
- Official CSRC public pagination event-store audit: `reports/aquant_v04_final/verify_official_public_event_store_csrc_pages`
- Official CSRC public structured sync smoke: `reports/aquant_v04_final/verify_official_public_sync_csrc_structured`
- Official CSRC public structured event-store audit: `reports/aquant_v04_final/verify_official_public_event_store_csrc_structured`
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
- Walk-forward chronological probability calibration: `reports/aquant_v04_final/verify_walk_forward_probability_calibration_sample`
- Model evaluation with probability calibration slices: `reports/aquant_v04_final/verify_evaluate_models_probability_calibration`
- Model evaluation with PIT liquidity/regime diagnostics: `reports/aquant_v04_final/verify_evaluate_models_pit_diagnostics_v2`
- BaoStock 20-symbol real-source walk-forward smoke: `reports/aquant_v04_final/verify_walk_forward_baostock_20_smoke`
- BaoStock 220-symbol real-source walk-forward: `reports/aquant_v04_final/verify_walk_forward_baostock_220_real`
- BaoStock 220-symbol real-source walk-forward with fold-local probability calibration: `reports/aquant_v04_final/verify_walk_forward_baostock_220_probability_calibration_real`
- Model evaluation including BaoStock 220-symbol real-source evidence: `reports/aquant_v04_final/verify_evaluate_models_baostock_220_real`
- Model evaluation including BaoStock 220-symbol probability-calibration evidence: `reports/aquant_v04_final/verify_evaluate_models_baostock_220_probability_calibration_real`
- XGBoost train-model smoke: `reports/aquant_v04_final/verify_train_model_xgboost_sample`
- CatBoost train-model smoke: `reports/aquant_v04_final/verify_train_model_catboost_sample`
- Model evaluation with model-base availability: `reports/aquant_v04_final/verify_evaluate_models_with_model_bases`
- 000630 BaoStock 220-symbol real-source prediction: `reports/aquant_v04_final/verify_predict_stock_000630_baostock_220_real`
- 000630 BaoStock 220-symbol calibrated real-source prediction: `reports/aquant_v04_final/verify_predict_stock_000630_baostock_220_probability_calibration_real`
- 000630 BaoStock 220-symbol calibrated full report with news/K-line/evidence audits: `reports/aquant_v04_final/verify_report_stock_000630_baostock_220_probability_calibration_real`
- Portfolio backtest: `reports/aquant_v04_final/verify_backtest_portfolio_sample`
- Portfolio constraint backtest: `reports/aquant_v04_final/verify_portfolio_constraints_sample`
- Portfolio validation audit: `reports/aquant_v04_final/verify_portfolio_validation_sample`
- Portfolio constraint paper-trade dry run: `reports/aquant_v04_final/verify_portfolio_constraints_paper_trade_sample`
- Paper-trade validation audit: `reports/aquant_v04_final/verify_paper_trade_validation_sample`
- Portfolio event attribution backtest: `reports/aquant_v04_final/verify_backtest_portfolio_event_attribution_sample`
- Event-risk guarded portfolio backtest: `reports/aquant_v04_final/verify_event_guard_backtest_sample`
- Event-risk guarded paper-trade dry run: `reports/aquant_v04_final/verify_event_guard_paper_trade_sample`
- Commodity news sync for metal stocks: `reports/aquant_v04_final/verify_commodity_news_metals`
- Commodity event store for metal stocks: `reports/aquant_v04_final/verify_commodity_event_store_metals`
- 220-symbol sample walk-forward trust gate: `reports/aquant_v04_final/verify_walk_forward_220_sample_trust_gate`
- Predict-stock walk-forward evidence gate: `reports/aquant_v04_final/verify_predict_stock_walk_forward_gate_sample`
- Report-stock walk-forward evidence gate: `reports/aquant_v04_final/verify_report_stock_walk_forward_gate_sample`
- Predict-stock probability calibration gate: `reports/aquant_v04_final/verify_predict_stock_calibration_gate_sample`
- Predict-stock chronological Platt/isotonic/identity calibration evidence: `reports/aquant_v04_final/verify_predict_stock_probability_calibrators_000630`
- Predict-stock conformal interval audit: `reports/aquant_v04_final/verify_predict_stock_conformal_000630_sample`
- Predict-stock trust-gate report: `reports/aquant_v04_final/verify_stock_trust_gates_predict_000630`
- Report-stock trust-gate report with news/K-line: `reports/aquant_v04_final/verify_stock_trust_gates_report_000630`
- Predict-stock evidence audit with news: `reports/aquant_v04_final/verify_stock_evidence_audit_predict_000630`
- Predict-kline evidence audit with news: `reports/aquant_v04_final/verify_predict_kline_evidence_audit_000630`
- Report-stock evidence audit with news/K-line: `reports/aquant_v04_final/verify_stock_evidence_audit_report_000630`
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
python run_mvp.py build-universe --config configs\mvp.json --themes mega-hot --output-dir reports\aquant_v04_final\verify_mega_hot_theme_coverage
python run_mvp.py build-universe --config configs\mvp.json --themes professional --output-dir reports\aquant_v04_final\verify_professional_theme_coverage
python run_mvp.py analyze-factor-trust --config configs\mvp.json --source sample --universe config --horizons 5 --output-dir reports\aquant_v04_final\verify_factor_trust_sample
python run_mvp.py analyze-factor-trust --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --horizons 5 --output-dir reports\aquant_v04_final\verify_factor_trust_cost_regime_sample
python run_mvp.py analyze-factor-trust --config configs\prod.example.json --source baostock --universe mega-hot --max-symbols 220 --horizons 5 --output-dir reports\aquant_v04_final\verify_factor_trust_baostock_220_real
python run_mvp.py sync-news --config configs\mvp.json --source akshare --universe 000630,601899 --start 2025-01-01 --output-dir reports\aquant_v04_final\verify_sync_news_akshare
python run_mvp.py build-event-store --config configs\mvp.json --source akshare --universe 000630,601899 --start 2025-01-01 --output-dir reports\aquant_v04_final\verify_event_store_akshare
python run_mvp.py discover-text-intelligence --output-dir reports\aquant_v04_final\verify_text_intelligence_registry
python run_mvp.py build-event-store --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --start 2024-01-01 --output-dir reports\aquant_v04_final\verify_event_reliability_weighting_sample
python run_mvp.py build-event-store --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --start 2024-01-01 --output-dir reports\aquant_v04_final\verify_event_factor_quality_store_sample
python run_mvp.py build-event-store --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --start 2024-01-01 --output-dir reports\aquant_v04_final\verify_similar_event_store_sample
python run_mvp.py analyze-event-impact --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --horizons 1,5,20 --start 2024-01-01 --output-dir reports\aquant_v04_final\verify_event_impact_study_sample
python run_mvp.py discover-sources --domestic-only --output-dir reports\aquant_v04_final\verify_discover_sources_cninfo_direct
python run_mvp.py sync-announcements --config configs\mvp.json --source cninfo_direct --universe 000630 --start 2026-01-01 --output-dir reports\aquant_v04_final\verify_sync_announcements_cninfo_direct_000630
python run_mvp.py build-event-store --config configs\mvp.json --source cninfo_direct --universe 000630 --start 2026-01-01 --output-dir reports\aquant_v04_final\verify_event_store_cninfo_direct_000630
python run_mvp.py sync-announcements --config configs\mvp.json --source cninfo_direct --universe 000630 --start 2026-01-01 --fetch-announcement-text --output-dir reports\aquant_v04_final\verify_sync_announcements_cninfo_text_000630
python run_mvp.py build-event-store --config configs\mvp.json --source cninfo_direct --universe 000630 --start 2026-01-01 --fetch-announcement-text --output-dir reports\aquant_v04_final\verify_event_store_cninfo_text_000630
python run_mvp.py sync-news --config configs\mvp.json --source csrc_public --universe 000630,300308 --start 2026-01-01 --output-dir reports\aquant_v04_final\verify_official_public_sync_csrc
python run_mvp.py build-event-store --config configs\mvp.json --source csrc_public --universe 000630,300308 --start 2026-01-01 --output-dir reports\aquant_v04_final\verify_official_public_event_store_csrc
python run_mvp.py sync-news --config configs\mvp.json --source csrc_public --universe 000630,300308 --start 2026-01-01 --fetch-announcement-text --output-dir reports\aquant_v04_final\verify_official_public_sync_csrc_text
python run_mvp.py build-event-store --config configs\mvp.json --source csrc_public --universe 000630,300308 --start 2026-01-01 --fetch-announcement-text --output-dir reports\aquant_v04_final\verify_official_public_event_store_csrc_text
python run_mvp.py sync-news --config configs\mvp.json --source csrc_public --universe 000630,300308 --start 2026-01-01 --max-pages 2 --output-dir reports\aquant_v04_final\verify_official_public_sync_csrc_pages
python run_mvp.py build-event-store --config configs\mvp.json --source csrc_public --universe 000630,300308 --start 2026-01-01 --max-pages 2 --output-dir reports\aquant_v04_final\verify_official_public_event_store_csrc_pages
python run_mvp.py sync-news --config configs\mvp.json --source csrc_public --universe 000630,300308 --start 2026-01-01 --max-pages 2 --fetch-announcement-text --output-dir reports\aquant_v04_final\verify_official_public_sync_csrc_structured
python run_mvp.py build-event-store --config configs\mvp.json --source csrc_public --universe 000630,300308 --start 2026-01-01 --max-pages 2 --fetch-announcement-text --output-dir reports\aquant_v04_final\verify_official_public_event_store_csrc_structured
python run_mvp.py build-event-store --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --start 2024-01-01 --output-dir reports\aquant_v04_final\verify_event_major_announcement_summary_sample
python run_mvp.py build-event-store --config configs\mvp.json --source sample --allow-sample --universe 000630,300308 --start 2024-01-01 --output-dir reports\aquant_v04_final\verify_theme_entity_link_sample
python run_mvp.py build-feature-store --config configs\mvp.json --source sample --allow-sample --universe 000630,300308 --horizons 1,5,20,60 --point-in-time --with-news --output-dir reports\aquant_v04_final\verify_feature_store_theme_entity_link_sample
python run_mvp.py audit-news --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --start 2024-01-01 --output-dir reports\aquant_v04_final\verify_news_coverage_sample
python run_mvp.py build-feature-store --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --horizons 1,5,20,60 --point-in-time --with-news --output-dir reports\aquant_v04_final\verify_feature_store_event_sample
python run_mvp.py build-feature-store --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --horizons 1,5,20,60 --point-in-time --with-news --output-dir reports\aquant_v04_final\verify_feature_store_event_reliability_sample
python run_mvp.py build-feature-store --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --horizons 1,5,20,60 --point-in-time --with-news --output-dir reports\aquant_v04_final\verify_event_factor_quality_feature_store_sample
python run_mvp.py train-walk-forward --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --model event_aware_ensemble --horizons 1,5,20,60 --output-dir reports\aquant_v04_final\verify_walk_forward_event_sample
python run_mvp.py train-walk-forward --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --model event_aware_ensemble --horizons 1 --train-years 1 --test-months 2 --min-symbols 2 --with-news --output-dir reports\aquant_v04_final\verify_walk_forward_event_factor_quality_sample
python run_mvp.py discover-sources --domestic-only --output-dir reports\aquant_v04_final\verify_source_gap_matrix
python run_mvp.py backtest-portfolio --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --output-dir reports\aquant_v04_final\verify_backtest_portfolio_sample
python run_mvp.py backtest-portfolio --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --output-dir reports\aquant_v04_final\verify_portfolio_constraints_sample
python run_mvp.py backtest-portfolio --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --with-news --output-dir reports\aquant_v04_final\verify_portfolio_validation_sample
python run_mvp.py paper-trade --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --days 20 --no-live --output-dir reports\aquant_v04_final\verify_portfolio_constraints_paper_trade_sample
python run_mvp.py paper-trade --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --days 20 --no-live --with-news --output-dir reports\aquant_v04_final\verify_paper_trade_validation_sample
python run_mvp.py backtest-portfolio --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --with-news --output-dir reports\aquant_v04_final\verify_backtest_portfolio_event_attribution_sample
python run_mvp.py backtest-portfolio --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --with-news --output-dir reports\aquant_v04_final\verify_event_guard_backtest_sample
python run_mvp.py paper-trade --config configs\mvp.json --source sample --allow-sample --with-news --no-live --output-dir reports\aquant_v04_final\verify_event_guard_paper_trade_sample
python run_mvp.py paper-trade --config configs\mvp.json --source sample --allow-sample --with-news --no-live --output-dir reports\aquant_v04_final\verify_event_reliability_paper_trade_sample
python run_mvp.py report-stock --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --symbol 000630 --horizons 1,5,20,60 --model event_aware_ensemble --days 10 --history-days 80 --with-news --with-kline --output-dir reports\aquant_v04_final\verify_report_stock_event_reliability_000630
python run_mvp.py report-stock --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --symbol 000630 --horizons 1,5,20 --model factor_score --days 8 --history-days 80 --with-news --with-kline --output-dir reports\aquant_v04_final\verify_report_stock_similar_events_000630
python run_mvp.py report-stock --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --symbol 000630 --horizons 1,5,20 --model factor_score --days 8 --history-days 80 --with-news --with-kline --output-dir reports\aquant_v04_final\verify_report_stock_event_impact_000630
python run_mvp.py report-stock --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --symbol 000630 --horizons 1,5,20,60 --model event_aware_ensemble --days 10 --history-days 80 --with-news --with-kline --output-dir reports\aquant_v04_final\verify_report_stock_event_text_000630
python run_mvp.py report-stock --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --symbol 000630 --horizons 1,5,20,60 --model event_aware_ensemble --days 10 --history-days 80 --with-news --with-kline --output-dir reports\aquant_v04_final\verify_report_stock_conformal_text_000630
python run_mvp.py sync-news --config configs\metals.json --source akshare --universe 000630,600362,601899 --start 2025-01-01 --output-dir reports\aquant_v04_final\verify_commodity_news_metals
python run_mvp.py build-event-store --config configs\metals.json --source akshare --universe 000630,600362,601899 --start 2025-01-01 --output-dir reports\aquant_v04_final\verify_commodity_event_store_metals
python run_mvp.py train-walk-forward --config configs\mvp.json --source sample --allow-sample --universe mega-hot --max-symbols 220 --min-symbols 200 --model factor_score --horizons 5 --train-years 1 --test-months 3 --start 2024-01-01 --output-dir reports\aquant_v04_final\verify_walk_forward_220_sample_trust_gate
python run_mvp.py evaluate-models --config configs\mvp.json --by-year --by-industry --output-dir reports\aquant_v04_final\verify_evaluate_models_v04_slices
python run_mvp.py train-walk-forward --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --model factor_score --horizons 5 --train-years 1 --test-months 2 --output-dir reports\aquant_v04_final\verify_walk_forward_pit_diagnostics_sample
python run_mvp.py train-walk-forward --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --model factor_score --horizons 1 --train-years 1 --test-months 2 --min-symbols 2 --output-dir reports\aquant_v04_final\verify_walk_forward_probability_calibration_sample
python run_mvp.py evaluate-models --config configs\mvp.json --by-year --by-industry --output-dir reports\aquant_v04_final\verify_evaluate_models_probability_calibration
python run_mvp.py evaluate-models --config configs\mvp.json --by-year --by-industry --output-dir reports\aquant_v04_final\verify_evaluate_models_pit_diagnostics_v2
python run_mvp.py train-walk-forward --config configs\prod.example.json --source baostock --universe mega-hot --max-symbols 220 --min-symbols 200 --model factor_score --horizons 5 --train-years 1 --test-months 3 --start 2024-01-01 --output-dir reports\aquant_v04_final\verify_walk_forward_baostock_220_real
python run_mvp.py train-walk-forward --config configs\prod.example.json --source baostock --universe mega-hot --max-symbols 220 --min-symbols 200 --model factor_score --horizons 5 --train-years 1 --test-months 3 --start 2024-01-01 --output-dir reports\aquant_v04_final\verify_walk_forward_baostock_220_probability_calibration_real
python run_mvp.py train-walk-forward --config configs\prod.example.json --source baostock --universe mega-hot --max-symbols 220 --min-symbols 200 --model factor_score --horizons 5 --train-years 1 --test-months 3 --start 2024-01-01 --factor-trust-audit reports\aquant_v04_final\verify_factor_trust_baostock_220_real\factor_trust_audit.csv --factor-trust-status approved --output-dir reports\aquant_v04_final\verify_walk_forward_baostock_220_factor_trust_approved_real
python run_mvp.py train-walk-forward --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --model xgboost --horizons 1 --train-years 1 --test-months 2 --min-symbols 2 --output-dir reports\aquant_v04_final\verify_walk_forward_xgboost_model_audit_sample
python run_mvp.py train-walk-forward --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --model lightgbm --horizons 1 --train-years 1 --test-months 2 --min-symbols 2 --output-dir reports\aquant_v04_final\verify_walk_forward_lightgbm_model_audit_sample
python run_mvp.py train-walk-forward --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --model catboost --horizons 1 --train-years 1 --test-months 2 --min-symbols 2 --output-dir reports\aquant_v04_final\verify_walk_forward_catboost_model_audit_sample
python run_mvp.py train-walk-forward --config configs\prod.example.json --source baostock --universe mega-hot --max-symbols 220 --min-symbols 200 --model lightgbm --horizons 5 --train-years 1 --test-months 3 --start 2024-01-01 --factor-trust-audit reports\aquant_v04_final\verify_factor_trust_baostock_220_real\factor_trust_audit.csv --factor-trust-status approved --output-dir reports\aquant_v04_final\verify_walk_forward_baostock_220_lightgbm_approved_real
python run_mvp.py evaluate-models --config configs\prod.example.json --by-year --by-industry --output-dir reports\aquant_v04_final\verify_evaluate_models_baostock_220_real
python run_mvp.py evaluate-models --config configs\prod.example.json --by-year --by-industry --output-dir reports\aquant_v04_final\verify_evaluate_models_baostock_220_probability_calibration_real
python run_mvp.py evaluate-models --config configs\prod.example.json --by-year --by-industry --walk-forward-artifact reports\aquant_v04_final\verify_walk_forward_baostock_220_factor_trust_approved_real\walk_forward_predictions.csv --output-dir reports\aquant_v04_final\verify_evaluate_models_baostock_220_factor_trust_approved_real
python run_mvp.py evaluate-models --config configs\prod.example.json --by-year --by-industry --walk-forward-artifact reports\aquant_v04_final\verify_walk_forward_baostock_220_lightgbm_approved_real\walk_forward_predictions.csv --output-dir reports\aquant_v04_final\verify_evaluate_models_baostock_220_lightgbm_approved_real
python run_mvp.py train-model --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --model xgboost --horizons 5 --output-dir reports\aquant_v04_final\verify_train_model_xgboost_sample
python run_mvp.py train-model --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --model catboost --horizons 5 --output-dir reports\aquant_v04_final\verify_train_model_catboost_sample
python run_mvp.py evaluate-models --config configs\mvp.json --by-year --by-industry --output-dir reports\aquant_v04_final\verify_evaluate_models_with_model_bases
python run_mvp.py predict-stock --config configs\prod.example.json --source baostock --universe mega-hot --max-symbols 220 --symbol 000630 --horizons 5 --model factor_score --start 2024-01-01 --output-dir reports\aquant_v04_final\verify_predict_stock_000630_baostock_220_real
python run_mvp.py predict-stock --config configs\prod.example.json --source baostock --universe mega-hot --max-symbols 220 --symbol 000630 --horizons 1,5,20 --model factor_score --start 2024-01-01 --with-news --output-dir reports\aquant_v04_final\verify_predict_stock_000630_baostock_220_probability_calibration_real
python run_mvp.py report-stock --config configs\prod.example.json --source baostock --universe mega-hot --max-symbols 220 --symbol 000630 --model factor_score --start 2024-01-01 --with-news --with-kline --days 8 --history-days 80 --max-event-impact-symbols 80 --max-event-impact-events 1500 --output-dir reports\aquant_v04_final\verify_report_stock_000630_baostock_220_probability_calibration_real
python run_mvp.py predict-stock --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --symbol 000630 --horizons 5 --model factor_score --output-dir reports\aquant_v04_final\verify_predict_stock_walk_forward_gate_sample
python run_mvp.py predict-stock --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --symbol 000630 --horizons 5 --model factor_score --output-dir reports\aquant_v04_final\verify_predict_stock_calibration_gate_sample
python run_mvp.py predict-stock --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --symbol 000630 --horizons 1,5,20 --model factor_score --output-dir reports\aquant_v04_final\verify_predict_stock_probability_calibrators_000630
python run_mvp.py predict-stock --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --symbol 000630 --horizons 1,5,20,60 --model factor_score --output-dir reports\aquant_v04_final\verify_predict_stock_conformal_000630_sample
python run_mvp.py predict-stock --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --symbol 000630 --horizons 1,5,20 --model factor_score --output-dir reports\aquant_v04_final\verify_stock_trust_gates_predict_000630
python run_mvp.py predict-stock --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --symbol 000630 --horizons 1,5,20 --model factor_score --with-news --output-dir reports\aquant_v04_final\verify_stock_evidence_audit_predict_000630
python run_mvp.py predict-kline --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --symbol 000630 --horizons 1,5,20 --model factor_score --days 8 --history-days 80 --with-news --output-dir reports\aquant_v04_final\verify_predict_kline_evidence_audit_000630
python run_mvp.py report-stock --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --symbol 000630 --horizons 1,5,20 --model factor_score --days 8 --history-days 80 --with-news --with-kline --output-dir reports\aquant_v04_final\verify_stock_trust_gates_report_000630
python run_mvp.py report-stock --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --symbol 000630 --horizons 1,5,20 --model factor_score --days 8 --history-days 80 --with-news --with-kline --output-dir reports\aquant_v04_final\verify_stock_evidence_audit_report_000630
python run_mvp.py report-stock --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --symbol 000630 --horizons 5 --model factor_score --days 5 --history-days 60 --with-news --with-kline --output-dir reports\aquant_v04_final\verify_report_stock_walk_forward_gate_sample
python run_mvp.py audit-news --config configs\prod.example.json --source baostock --universe 000630,601899,600362,300308,300750 --start 2025-01-01 --output-dir reports\aquant_v04_final\verify_news_coverage_key_stocks
python run_mvp.py report-stock --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --symbol 000630 --days 10 --history-days 80 --horizons 1,5,20,60 --with-news --with-kline --output-dir reports\aquant_v04_final\verify_report_stock_sample_000630
python run_mvp.py report-stock --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --symbol 000630 --model event_aware_ensemble --days 20 --history-days 120 --horizons 1,5,20,60 --with-news --with-kline --output-dir reports\aquant_v04_final\stocks\000630\04_full_report_source_isolated
python run_mvp.py report-stock --config configs\metals.json --source baostock --universe config --symbol 000630 --horizons 1,5,20,60 --model event_aware_ensemble --with-news --with-kline --days 20 --history-days 160 --output-dir reports\aquant_v04_final\stocks\000630\06_real_baostock_event_report
```

## Operational Notes

- BaoStock has a global login/session behavior; run BaoStock-heavy jobs sequentially rather than in parallel to avoid `用户未登录` session collisions.
- News cache loading now fetches missing symbols before auditing coverage, so partial `raw_events` cache no longer causes false `no_linked_news` results.
- Stock-report event-impact diagnostics now have runtime bounds via `--max-event-impact-symbols` and `--max-event-impact-events`. The full event store and event factors are still written; the historical impact study records its bounded scope in `news_summary.event_impact_scope`.
- `report-stock --with-kline` computes a superset stock forecast once and reuses it for K-line charting. Requested-horizon `stock_forecast.*` stays separate from K-line internal `kline_stock_forecast.*`.
- `backtest-portfolio --with-news` writes `portfolio_event_attribution_daily.csv`, `portfolio_event_attribution_symbol.csv`, and `portfolio_event_attribution.md`.
- `backtest-portfolio` writes portfolio-constraint audit outputs plus a constrained backtest (`portfolio_constraint_*`). The sample constrained run reduced drawdown at the cost of lower return, and that trade-off is explicitly reported.
- `paper-trade --no-live` applies portfolio constraints before order generation and records the constraint metadata in `paper_summary.json`.
- `backtest-portfolio --with-news` now also writes event-risk guarded targets, trades, holdings, attribution, and `event_guarded_metrics.json`.
- `paper-trade --with-news --no-live` applies event-risk target adjustment before order planning and writes `event_risk_guard_report.*`.
- Metals commodity event verification writes `akshare_futures_main_sina` evidence into `news_evidence.md`; run shared event-warehouse write jobs sequentially to avoid cache races.
- The 220-symbol sample walk-forward run is a trust-gate smoke test only; it produced `weak`, not `trusted`, because AUC and Brier gates failed.
- `predict-stock` and `report-stock` now carry walk-forward registry evidence into every forecast row. A single-stock report cannot become `trusted` unless matching large-universe walk-forward evidence for the same model and horizon is itself `trusted`.
- `evaluate-models` now reads registered walk-forward artifacts and writes real OOS slices by year, theme proxy, size/liquidity availability, and ex-post market regime. It exposes weak periods such as the 2026 sample slice instead of hiding them in aggregate metrics.
- `train-walk-forward` now performs fold-local probability calibration with `identity/platt/isotonic` candidates. Each OOS row keeps raw and calibrated probabilities plus the calibration/test date ranges and PIT flag; trusted walk-forward status also requires calibration readiness and calibrated ECE.
- `predict-stock` now selects among identity, Platt, and isotonic calibration using a deterministic chronological validation split. It writes raw/calibrated probability, Brier, ECE, selected method, and improvement fields; sparse or failed calibration prevents `trusted`, even when the raw probability looks strong.
- `predict-stock` now writes conformal-style interval evidence (`conformal_method`, rows, target coverage, half-width, status) next to `return_p10/p50/p90`; sparse interval evidence prevents a real signal from becoming `trusted`.
- `predict-stock` and `report-stock` now write `stock_trust_gates.*`. The report expands each horizon into explicit pass/fail gates, so `data_insufficient`, `weak`, and `model_failed` are explained instead of inferred from many forecast columns.
- `predict-stock` and `report-stock` now write `stock_evidence_audit.*`. The audit verifies each horizon has data/model versioning, forecast probability and return interval fields, factor contributors, risk flags, walk-forward metric evidence, calibration/conformal evidence, news/event factor evidence when requested, and the research-only disclaimer.
- `predict-kline` now also writes `stock_evidence_audit.*` for the underlying stock forecast used by the scenario chart. `report-stock --with-kline` writes the K-line internal-horizon audit separately as `kline_stock_evidence_audit.*`.
- `report-stock --with-kline` preserves requested-horizon `stock_forecast.*` and writes K-line internal forecast horizons separately as `kline_stock_forecast.*`.
- New walk-forward artifacts carry PIT diagnostic fields such as `amount_mean_20`, `cs_amount_rank_20`, `market_breadth`, and `market_mean_return`, allowing evaluation to separate PIT liquidity/regime slices from older artifacts where those fields are unavailable.
- The BaoStock 220-symbol real-source walk-forward loaded 220/220 symbols and produced 72,748 OOS rows, but stayed `weak` because AUC, Brier, and RankIC gates failed. The 000630 real-source prediction therefore also stayed `weak`.
- The BaoStock 220-symbol probability-calibrated walk-forward also loaded 220/220 symbols and produced 72,748 OOS rows. Calibration improved Brier and ECE, but the signal still stayed `weak` with failed gates for baseline improvement, AUC, Brier, calibration readiness, RankIC, and top-bottom spread. This is evidence that calibration is audited rather than used to overrule failed predictive power.
- The calibrated `000630` BaoStock 220-symbol prediction and full news/K-line report stayed `weak/model_failed`, not `trusted`. The prediction now writes `stock_evidence_audit.*`; the full report writes both `stock_evidence_audit.*` and `kline_stock_evidence_audit.*`. Each audit failed only on walk-forward evidence, while preserving news/event evidence, similar-event retrieval, bounded event-impact PIT priors, K-line HTML/PNG, trust gates, backtest metrics, and manifest files.
- BaoStock batch loading now reuses a lazy session and resilient free-source commands record per-symbol failures instead of aborting the whole large-universe run.
- `train-model` now writes `model_base_availability.*` and records requested/effective model ids plus fallback reasons. XGBoost and CatBoost sample runs produced real artifacts and registered `model_base_status=trained`.
- `evaluate-models` writes `model_base_availability.csv/md`, so reports show which challenger bases are actually importable rather than assumed.
- Factor trust now includes top correlated factor ids, cost-adjusted top-bottom spread, estimated cost drag, and bullish/sideways/bearish regime stability. The latest sample audit kept 67/237 factors approved, put 157 on watchlist, and quarantined 13; this gate is intentionally allowed to reject attractive-looking but expensive or regime-fragile factors.
- BaoStock 220-symbol real factor trust audit kept only 11/237 factors approved, put 223 on watchlist, and quarantined 3. The approved-only walk-forward used exactly those 11 factors and still stayed `weak`, proving the factor gate is wired to model validation and does not promote weak signals.
- `evaluate-models --walk-forward-artifact` can now produce a clean slice report for one selected walk-forward artifact. The approved-only BaoStock evaluation sliced exactly 72,748 rows and identified weak high-volatility/sideways regimes without mixing older registry runs.
- Walk-forward now audits requested/effective model type, prediction method, model-base status, fallback reason, and fallback rate. A challenger that falls back to the factor baseline cannot pass `trusted`.
- XGBoost, LightGBM, and CatBoost sample walk-forward smokes all confirmed `model_base_status=trained` and `fallback_rate=0.0`; all stayed `weak` because the sample universe is too small.
- BaoStock 220-symbol LightGBM approved-factor walk-forward confirmed a real trained LightGBM path with `fallback_rate=0.0`, but stayed `weak` with AUC `0.4927`, Brier `0.2565`, RankIC `-0.0082`, and failed calibration readiness/quality gates.
- Event evidence now carries `source_category`, `source_reliability`, and `weighted_impact_score`; event factors add weighted impact and reliability features, and event risk uses the weighted impact when available.
- `cninfo_direct` is now a first direct public-source adapter. In the 000630 smoke run the endpoint returned an unexpected schema, so the system wrote 0 rows plus warnings instead of fabricating announcement events.
- Official public index-page adapters now exist for SSE/SZSE/BSE/CSRC/NDRC/MIIT/MOFCOM/PBC/customs/NBS. `--max-pages` enables bounded generic pagination, and `--fetch-announcement-text` attempts bounded body-text extraction with `source_text_status`, length, and hash. The CSRC smoke runs returned 0 rows with recorded warnings, so the event stores stayed empty instead of fabricating policy events.
- Official-source headlines now receive title-first structured event labels before factor generation. The risk set includes regulatory penalties, regulatory inquiries, litigation risk, performance misses, export controls, and public-opinion risk, while positive corporate actions such as buyback/dividend are kept separate from risk counts.
- `discover-sources --domestic-only` now writes `free_source_coverage.*` plus `source_gap_report.*`, covering 26 domestic/free-priority sources. Eighteen sources are ready or partially ready for event factors, while 18 still carry explicit follow-up gaps such as site-specific pagination calibration, structured fields, credentials, local-client state, or richer direct schemas.
- `--fetch-announcement-text` now attempts bounded direct announcement body extraction and records `source_text_status`, length, and hash. The evidence report includes a `Recent Major Announcement Summary` section.
- Macro/policy/industry news without stock codes can now enter event factors through audited theme-keyword entity links. The sample verification mapped AI/semiconductor policy news to `300308` and metals policy news to `000630`, while recording method, confidence, and keywords.
- `build-event-store` writes `similar_events.*`, and stock reports with news write `stock_similar_events.*`. These reports use PIT-safe earlier-event matching and only include forward returns whose full horizon was already known at query time.
- `analyze-event-impact` writes event-return, cohort, and PIT-prior diagnostics. Stock reports with news write bounded `stock_event_impact_study.*` diagnostics by default; the latest real 000630 run analyzed 1,500 events and 6,000 event-return rows with `no_future_leakage=true`. Event factors still need walk-forward proof before promotion.
- `discover-text-intelligence` now records 8 text/retrieval capabilities, including native TF-IDF similar-event retrieval plus optional transformer, BGE, FAISS, LanceDB, Qwen, and DeepSeek bases. All remain evidence-only until PIT-labeled walk-forward proof exists.
- Event factor quality artifacts now exist at both the event-store and walk-forward layers. CLI event-store outputs now include universe-aware `requested_symbols`, `linked_symbols`, and `symbol_coverage`. The sample event-aware walk-forward correctly stayed `weak` because event features were sparse/constant and `event_feature_quality_passed` failed.
- Portfolio validation artifacts now exist for `backtest-portfolio`: `portfolio_validation_checks.csv`, `portfolio_validation_annual.csv`, `portfolio_validation_costs.csv`, `portfolio_validation_summary.json`, and `portfolio_validation_report.md`. The sample report validates traceability and risk-control evidence, not future profitability.
- Paper-trade validation artifacts now exist for `paper-trade --no-live`: `paper_validation_checks.csv`, `paper_validation_summary.json`, and `paper_validation_report.md`. The sample report confirms PaperBroker/no-live execution traceability and does not enable live trading.
- Latest local validation passes 58 pytest cases, compileall, pip dependency check, and the explicit `live-trade --confirm` blocker.

All outputs are probabilistic research evidence, not guaranteed predictions or investment advice.
