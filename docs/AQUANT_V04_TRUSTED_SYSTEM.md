# AQuant v0.4 Trusted System

## Goal

v0.4 upgrades AQuant from a runnable prediction system into a verifiable research system:

- factor trust registry
- news/event evidence chain
- free domestic source matrix and explicit source gap report
- point-in-time data audit
- walk-forward validation
- stock report with forecast, K-line, factor contribution, event evidence, and risk flags
- stock trust-gate report explaining each horizon's data/model/calibration/conformal/news blockers
- portfolio constraint audit for single-name caps, theme caps, volatility targeting, turnover, blacklist, and drawdown circuit breakers
- event-risk guardrail for portfolio targets and paper orders
- model-base availability audit for factor_score, scikit-learn, LightGBM, XGBoost, and CatBoost
- commodity/industry-chain shock events for metals and energy-linked stocks
- text-intelligence registry and PIT-safe similar-event retrieval for news explanation
- event impact study for event-type/sentiment/source-reliability outcome cohorts and PIT priors
- live trading remains blocked

## Trust Contract

The system never guarantees a price move. It only reports whether a signal is supported by:

- enough data
- point-in-time inputs
- out-of-sample metrics
- factor trust audit
- event evidence
- risk checks

If these gates fail, the signal must be `weak`, `data_insufficient`, or `model_failed`, not `trusted`.

## New v0.4 Commands

```powershell
python run_mvp.py analyze-factor-trust --config configs\mvp.json --source sample --horizons 5
python run_mvp.py discover-sources --domestic-only --output-dir reports\aquant_v04_final\verify_source_gap_matrix
python run_mvp.py discover-text-intelligence --output-dir reports\aquant_v04_final\verify_text_intelligence_registry
python run_mvp.py sync-news --config configs\mvp.json --source akshare --universe 000630,601899 --start 2025-01-01
python run_mvp.py sync-news --config configs\metals.json --source akshare --universe 000630,600362,601899 --start 2025-01-01
python run_mvp.py sync-announcements --config configs\mvp.json --source akshare --universe 000630,601899 --start 2025-01-01
python run_mvp.py sync-announcements --config configs\mvp.json --source cninfo_direct --universe 000630 --start 2026-01-01 --fetch-announcement-text
python run_mvp.py build-event-store --config configs\mvp.json --source akshare --universe 000630,601899 --start 2025-01-01
python run_mvp.py build-event-store --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --start 2024-01-01 --output-dir reports\aquant_v04_final\verify_similar_event_store_sample
python run_mvp.py analyze-event-impact --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --horizons 1,5,20 --start 2024-01-01 --output-dir reports\aquant_v04_final\verify_event_impact_study_sample
python run_mvp.py audit-news --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --start 2024-01-01
python run_mvp.py build-feature-store --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --horizons 1,5,20,60 --point-in-time --with-news
python run_mvp.py train-walk-forward --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --model event_aware_ensemble --horizons 1,5,20,60
python run_mvp.py train-walk-forward --config configs\mvp.json --source sample --allow-sample --universe mega-hot --max-symbols 220 --min-symbols 200 --model factor_score --horizons 5 --train-years 1 --test-months 3 --start 2024-01-01
python run_mvp.py train-model --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --model xgboost --horizons 5 --output-dir reports\aquant_v04_final\verify_train_model_xgboost_sample
python run_mvp.py train-model --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --model catboost --horizons 5 --output-dir reports\aquant_v04_final\verify_train_model_catboost_sample
python run_mvp.py evaluate-models --config configs\mvp.json --by-year --by-industry --output-dir reports\aquant_v04_final\verify_evaluate_models_with_model_bases
python run_mvp.py backtest-portfolio --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362
python run_mvp.py backtest-portfolio --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --with-news
python run_mvp.py backtest-portfolio --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --output-dir reports\aquant_v04_final\verify_portfolio_constraints_sample
python run_mvp.py paper-trade --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --days 20 --no-live --output-dir reports\aquant_v04_final\verify_portfolio_constraints_paper_trade_sample
python run_mvp.py paper-trade --config configs\mvp.json --source sample --allow-sample --with-news --no-live
python run_mvp.py report-stock --config configs\mvp.json --source sample --allow-sample --symbol 000630 --with-news --with-kline
python run_mvp.py predict-stock --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --symbol 000630 --horizons 1,5,20 --model factor_score --output-dir reports\aquant_v04_final\verify_stock_trust_gates_predict_000630
python run_mvp.py predict-stock --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --symbol 000630 --horizons 1,5,20 --model factor_score --output-dir reports\aquant_v04_final\verify_predict_stock_probability_calibrators_000630
python run_mvp.py report-stock --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --symbol 000630 --horizons 1,5,20 --model factor_score --days 8 --history-days 80 --with-news --with-kline --output-dir reports\aquant_v04_final\verify_stock_trust_gates_report_000630
```

## Current v0.4 Evidence

- Factor trust report generated for 237 factors.
- AKShare public news sync generated 174 raw rows for `000630,601899`.
- Event store generated 160 structured events and 228 event-factor rows.
- `report-stock --with-news --with-kline` generated a full stock report with event evidence.
- Event factors now flow into `build-feature-store`, `train-walk-forward`, `predict-stock`, `predict-kline`, `explain-stock`, and `report-stock`.
- `event_aware_ensemble` records 237 base factors + 13 event factors in the latest theme entity-link feature store.
- Event evidence now includes source reliability weighting and optional direct announcement text audit fields (`source_text_status`, length, hash).
- Event evidence now includes audited entity-link fields, so macro/policy/industry news without stock codes can be linked by hot-theme keywords while still exposing link method, confidence, and matched keywords.
- Direct CNINFO smoke tests write warnings for unexpected schemas or empty event stores instead of inserting fake announcement content.
- `discover-sources --domestic-only` now writes a 26-source matrix and a source gap report. Eighteen sources are currently ready or partially ready for event factors, and 18 still carry explicit follow-up gaps such as body parsing, pagination, credentials, local-client requirements, or richer direct schemas; no missing field is fabricated.
- The source matrix covers AKShare, BaoStock, Tushare free, CNINFO/direct CNINFO, Eastmoney wrappers, QMT read-only, SSE/SZSE/BSE, CSRC, NDRC, MIIT, MOFCOM, PBC, customs, NBS, Sina/Tencent/NetEase finance, and SHFE/INE/DCE/CZCE/CFFEX/GFEX commodity sources.
- Official public index-page adapters now exist for SSE/SZSE/BSE/CSRC/NDRC/MIIT/MOFCOM/PBC/customs/NBS. They can add URL-backed headline/index events to the event bus when they contain timestamp and entity-link evidence. `--max-pages` enables bounded generic pagination, and `--fetch-announcement-text` attempts bounded body-text extraction with `source_text_status`, length, and hash. They still do not claim site-specific pagination completeness or source-specific structured fields.
- Official-source headlines now receive rule-based structured event labels before feature generation, including regulatory penalty, regulatory inquiry, litigation risk, buyback/dividend, export control, monetary liquidity, macro indicator, and industry policy. Matching is title-first to reduce false links from adjacent index-page headlines.
- Text intelligence discovery now records optional embedding/classifier/summarizer/vector-store bases, including sentence-transformer/BGE-style retrieval, transformer event classifiers, FAISS/LanceDB, and local Qwen/DeepSeek model paths. They are evidence aids only and cannot promote trusted forecasts without PIT-labeled walk-forward proof.
- PIT-safe similar-event retrieval now writes `similar_events.*` for event stores and `stock_similar_events.*` for stock reports. It matches only earlier events and only reports forward returns that would already be known at the query time.
- Event impact study now writes `event_impact_study_returns/cohorts/pit_priors` and stock-level `stock_event_impact_study.*`. It evaluates event-type, sentiment, source-reliability, and source-category cohorts while keeping PIT priors separate from ex-post diagnostics.
- `backtest-portfolio` is available and respects command-line universe selection.
- Sample event data is isolated from the shared real-event warehouse to prevent sample/real source mixing.
- `audit-news` reports per-symbol event/news coverage and explicitly marks sparse or unlinked coverage.
- `000630` real free-source report ran with BaoStock daily bars plus public news/event evidence in `reports/aquant_v04_final/stocks/000630/06_real_baostock_event_report`.
- Five key-stock full reports are generated under `reports/aquant_v04_final/stocks`: `000630`, `601899`, `600362`, `300308`, `300750`.
- Key-stock news coverage audit reports 414 linked events and 521 event-factor rows across the five focus names.
- Partial event-cache reuse now fetches missing symbols before coverage audit, preventing false `no_linked_news` results.
- `backtest-portfolio --with-news` produces portfolio event attribution by date and symbol.
- `backtest-portfolio` and `paper-trade --no-live` now apply an audited portfolio constraint layer before executable simulation, with single-name caps, theme caps, turnover, volatility target, blacklist, and drawdown circuit-breaker outputs.
- The portfolio-constraint sample wrote `portfolio_constraint_report.*`, `portfolio_constraint_metrics.json`, and a constrained backtest. The constrained sample reduced max drawdown from about `-0.2103` to about `-0.1103` while also lowering total return, which is recorded as risk-control cost rather than hidden.
- `backtest-portfolio --with-news` now also writes event-guarded target weights, trades, holdings, attribution, and metrics for side-by-side risk-control comparison.
- `paper-trade --with-news --no-live` now applies structured event-risk guardrails before simulated order generation and writes `event_risk_guard_report.*`.
- The event bus now adds domestic futures `commodity_shock` events through AKShare/Sina main continuous contracts and maps them to related metal/energy-chain stocks.
- Commodity event verification for `000630,600362,601899` produced 691 structured events and 810 event-factor rows, including 447 raw `akshare_futures_main_sina` futures-shock events.
- Walk-forward trust gates now require enough out-of-sample rows, baseline improvement, AUC >= 0.52, Brier <= 0.25, positive RankIC, and positive top-bottom spread before `trusted`.
- A 220-symbol sample walk-forward smoke produced 58,520 OOS rows and correctly stayed `weak` because AUC and Brier gates failed; the system did not over-claim trust.
- `predict-stock` and `report-stock` now attach the matching walk-forward registry row to each forecast. A stock-level forecast cannot become `trusted` unless the same model/horizon has trusted large-universe out-of-sample evidence.
- `evaluate-models` now produces OOS slices by year, theme proxy, size/liquidity availability, and ex-post market regime, so aggregate performance can be challenged by period and market environment.
- `predict-stock` now records raw and calibrated probability evidence. Platt and isotonic calibrators are candidates when there is enough chronological validation data; identity is retained when it is best or when data is sparse. The forecast rows expose raw/calibrated Brier, raw/calibrated ECE, calibration method, and improvement fields. Sparse or failed probability calibration blocks `trusted` status.
- Probability calibration verification for `000630` is written under `reports/aquant_v04_final/verify_predict_stock_probability_calibrators_000630`; the sample run remains `data_insufficient`, and the 20d horizon is blocked by `calibration_failed` because ECE is too high.
- `predict-stock` now records conformal-style return interval evidence for p10/p50/p90: method, rows, target coverage, interval half-width, and status. Sparse conformal evidence blocks direct `trusted` promotion.
- `predict-stock` and `report-stock` now write `stock_trust_gates.csv/json/md`, a horizon-by-horizon gate report for sample data, universe size, walk-forward evidence, calibration, Brier, conformal interval, local signal quality, risk flags, and news evidence.
- `report-stock --with-news` now adds similar historical event evidence into `news_summary`, including match rows, known-return rows, and PIT policy. This remains explanatory evidence, not a direct trading signal.
- `report-stock --with-news` now adds event-impact summary evidence into `news_summary`, including event-return rows, PIT-prior rows, PIT-ready counts, and explicit `can_enter_trusted_model=false` until large-universe walk-forward proof exists.
- `report-stock --with-kline` keeps the requested-horizon `stock_forecast.csv/json` separate from K-line internal horizons via `kline_stock_forecast.csv/json`, so forecast evidence is not overwritten by chart scaffolding.
- New walk-forward prediction artifacts include PIT diagnostics for liquidity and market state (`amount_mean_20`, `cs_amount_rank_20`, `market_breadth`, `market_mean_return`). Evaluation uses these fields when present and clearly marks older artifacts where they are unavailable.
- A BaoStock 220-symbol real-source walk-forward run loaded 220/220 symbols and generated 72,748 OOS rows. It correctly stayed `weak` because AUC, Brier, and RankIC gates failed, proving the system can reject an insufficient real signal instead of overstating accuracy.
- `predict-stock --source baostock --universe mega-hot --max-symbols 220 --symbol 000630` now attaches that real walk-forward evidence and outputs `weak`, not `trusted`.
- BaoStock batch loading now uses a lazy reusable session and resilient large-universe commands keep an audit trail for failed symbols.
- `train-model` now supports real XGBoost and CatBoost training when installed, and records `requested_model_type`, `effective_model_type`, `model_base_status`, and `fallback_reason` when it must degrade to the factor baseline.
- Local model-base audit reports `factor_score`, `scikit-learn 1.6.1`, `LightGBM 4.6.0`, `XGBoost 3.2.0`, and `CatBoost 1.2.10` as available in this environment.
- XGBoost and CatBoost sample training runs both registered `model_base_status=trained`, so the challenger bases are not merely documented placeholders.
- Unit tests pass for factor trust, event bus, event-aware feature store, event-aware forecast output, event-risk guardrails, and risk/live-trade blockers.

## Remaining Work

- Expand official public source adapters from headline/index snippets plus bounded generic pagination/body text into source-specific pagination calibration, regulatory/policy schemas, and stronger PIT release-calendar handling.
- Convert remaining high-priority source gaps in `source_gap_report.md` into richer direct adapters, especially PBC liquidity fields, customs import/export detail, direct finance-news portals, and SHFE/GFEX direct inventory/notice feeds.
- Calibrate theme-keyword entity links against historical industry/concept membership and reduce false positives in broad policy news.
- Extend event-risk guardrails with empirical severity calibration and regime-specific thresholds.
- Calibrate commodity shock thresholds by commodity and stock exposure instead of using one default threshold.
- Run 200+ symbol walk-forward on real/free data, not sample data, before any real signal can be marked `trusted`.
- Refit probability calibrators on large real/free walk-forward artifacts and compare Platt/Isotonic/identity by year, industry, and regime before treating calibration stability as production-grade.
- Run BaoStock-heavy and shared event-warehouse write jobs sequentially unless adapters are refactored to use isolated sessions/transactional writes; parallel runs can collide at the vendor or cache layer.
