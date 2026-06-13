# News/Event Intelligence Bus

## Pipeline

```text
source -> raw_store -> dedup -> timestamp_normalize -> entity_link -> event_classify -> sentiment/impact_score -> decay -> event_factor -> evidence_report
```

## Implemented Sources

The current implementation uses AKShare wrappers when available:

- Eastmoney stock news: `stock_news_em`
- CNINFO disclosure reports: `stock_zh_a_disclosure_report_cninfo`
- CCTV macro news: `news_cctv`
- Domestic commodity futures shocks: `futures_main_sina`, currently mapped through contracts such as `CU0` copper, `AL0` aluminum, `AU0` gold, `AG0` silver, `ZN0` zinc, `NI0` nickel, `SN0` tin, `LC0` lithium carbonate, `SI0` industrial silicon, `I0` iron ore, and `SC0` crude oil.

Direct public-source adapters now include:

- `cninfo_direct`: direct CNINFO announcement metadata query with source URL, announcement timestamp, symbol link, optional bounded announcement body extraction, raw warning audit, and no sample fallback.
- official public index-page adapters: `sse_public`, `szse_public`, `bse_public`, `csrc_public`, `ndrc_public`, `miit_public`, `mofcom_public`, `pbc_public`, `customs_public`, and `stats_nbs_public`. These fetch URL-backed headline/index snippets and preserve `published_at`, `source_url`, source reliability, and entity-link evidence. `--max-pages N` enables bounded generic pagination per seed URL. With `--fetch-announcement-text`, they also attempt bounded body-text extraction and record `source_text_status`, length, and hash. Official-source headlines are rule-classified before entering the event bus, using title-first matching to avoid neighboring headline contamination. The adapters are intentionally conservative: source-specific pagination calibration, source-specific schemas, and supervised event classifiers still need expansion.

If a source fails, the failure must be recorded. The system may use deterministic sample fallback only when explicitly using sample/demo mode.

Use `--fetch-announcement-text` with direct announcement or official public sources to try HTML/text/PDF body extraction. Use `--max-pages` with official public sources to request bounded index pagination. HTML/text bodies are parsed directly. PDF text is parsed only when a compatible local PDF parser such as `pypdf` is installed; otherwise the event records `pdf_parser_unavailable` instead of fabricating content.

## Required Event Schema

Every structured event must include:

- `source`
- `source_url`
- `published_at`
- `fetched_at`
- `related_symbols`
- `symbol`
- `title`
- `summary`
- `entity_link_method`
- `entity_link_confidence`
- `entity_link_keywords`
- `event_type`
- `sentiment`
- `impact_score`
- `confidence`
- `source_category`
- `source_reliability`
- `weighted_impact_score`
- `source_text_status`
- `source_text_length`
- `source_text_hash`
- `effective_date`
- `raw_hash`
- `quality_flag`

Unlinked events are kept out of individual-stock event factors.

## Entity Linking

The event bus now supports audited multi-symbol entity linking:

- `explicit_symbol`: the raw event already carries a stock code.
- `provided_related_symbols`: the source provides one or more related stock codes.
- `code_mention`: the event text contains a loaded stock code.
- `name_mention`: the event text contains a loaded stock name.
- `theme_keyword`: the event has no stock code, but policy/industry/commodity keywords match the loaded hot-theme universe.

Every linked event records `entity_link_method`, `entity_link_confidence`, and `entity_link_keywords`. Unlinked macro news is still excluded from individual-stock factors; broad policy news only enters factors when the keyword-to-theme link is explicit and auditable.

## Source Reliability Weighting

The event bus now assigns a conservative source reliability score before events become factors:

- official disclosure/regulator/exchange/CNINFO-like evidence: high reliability
- official policy or macro sources: high reliability
- commodity market data: medium-high reliability
- public finance media such as Eastmoney/Sina/Tencent/NetEase: medium reliability
- sample/demo fallback: low reliability
- unknown source without URL: low reliability

`weighted_impact_score = impact_score * confidence * source_reliability`. Models and risk reports keep both the raw impact and the weighted impact so the system can inspect strong headlines without treating every source as equally reliable.

## Text Intelligence And Similar Events

`discover-text-intelligence` now writes an audit registry for optional text bases: sentence-transformer/BGE-style embeddings, transformer event classifiers, PyTorch text runtimes, FAISS/LanceDB vector stores, and local Qwen/DeepSeek summary paths. These are deliberately marked as evidence/retrieval aids only. They cannot enter trusted event factors until PIT labels and walk-forward evidence prove value.

The event layer also includes a local PIT-safe similar-event retrieval report:

- `build-event-store` writes `similar_events.csv/json/md`.
- `report-stock --with-news`, `predict-stock --with-news`, `predict-kline --with-news`, and `explain-stock --with-news` write `stock_similar_events.csv/json/md`.
- Retrieval uses TF-IDF character n-gram cosine similarity with a deterministic Jaccard fallback when optional sklearn text components are unavailable.
- Each query event can only match events published earlier than the query event.
- Forward returns are written only when the full return window ended before the query event, so the explanation does not look into the future.
- Similar-event evidence is explanatory only and has `can_enter_event_factors=False`; it does not issue buy/sell advice and cannot promote a forecast to `trusted`.

## Event Impact Study

`analyze-event-impact` adds a stricter news-factor validation layer. It joins structured events with future stock returns and writes:

- `event_impact_study_returns.csv`: event-level 1/5/20/60d forward returns and excess-return proxies.
- `event_impact_study_cohorts.csv`: cohorts by event type, sentiment, event type + sentiment, event type + source reliability, and source category.
- `event_impact_study_pit_priors.csv`: for each event, prior cohort evidence using only earlier events whose outcome window was already complete before the query event.
- `event_impact_study.md/json`: summary, PIT guardrails, sample sufficiency, and evidence status.

Stock reports with `--with-news` also write `stock_event_impact_study.*`, `stock_event_impact_returns.csv`, and `stock_event_impact_pit_priors.csv`, with the summary embedded in `stock_report_manifest.json`.

For stock-level reports, event-impact diagnostics are bounded by default with `--max-event-impact-symbols` and `--max-event-impact-events`. This bound applies to the historical outcome study only; the raw event store, stock event store, event factors, news evidence, and forecast event features are still written from the full linked event context. The selected diagnostic scope is recorded in `news_summary.event_impact_scope` so any truncation is auditable.

PIT priors are computed with cohort-level cumulative lookup instead of repeated full-table filtering. This preserves the rule that only outcomes known before the query event may enter prior evidence, while keeping large stock reports operational.

This layer is deliberately skeptical. Small cohorts become `data_insufficient`; weak reliability or weak entity links stay `weak`; even stronger-looking cohorts are only `candidate_for_walk_forward`, never directly trusted. The event factor can affect trusted predictions only after large-universe walk-forward validation beats the baseline.

## Event Factor Quality Gate

News and event features now have two explicit quality gates:

- `event_factor_quality.csv/md` audits the event evidence before modeling. It checks event rows, event-factor rows, symbol coverage, source URL coverage, published/fetched timestamps, related symbols, event type, impact/confidence, raw hash, source reliability, and entity-link confidence.
- `event_feature_quality.csv` audits the merged model matrix during `train-walk-forward`. It checks each event feature's coverage, non-zero ratio, mean absolute value, distinct values, and quarantine/watchlist/approved status.

CLI commands pass the requested universe into `event_factor_quality.csv`, so `requested_symbols`, `linked_symbols`, and `symbol_coverage` are measured against the actual stock pool rather than only the symbols that happened to receive linked events.

The walk-forward trusted gate consumes `event_feature_quality_passed`. If event features are enabled and their matrix is all zero, constant, too sparse, or otherwise quarantined, the run remains `weak` even if the model produces predictions. This prevents a model from claiming news awareness merely because event columns exist.

## Event Types

Current rule-based classifier covers:

- performance beat/miss
- order contract
- M&A/restructuring
- shareholder changes
- buyback/dividend
- regulatory inquiry
- regulatory penalty
- litigation risk
- capacity/operation
- export control
- monetary liquidity
- macro indicator
- commodity shock
- industry policy
- fund flow
- public opinion risk
- general news

## Commodity And Industry Chain Events

For metals and energy-chain stocks, the event bus now generates structured `commodity_shock` events directly from domestic futures data:

- It pulls main continuous futures daily bars through AKShare/Sina.
- It detects 1-day and 5-day price shocks.
- It maps commodities to related stocks using the curated hot-sector universe plus fallback mappings.
- It writes stock-linked events with `source=akshare_futures_main_sina`, `quality_flag=commodity_shock:<commodity>:<contract>`, signed `impact_score`, and a source URL.

Examples:

- `000630` Tongling Nonferrous receives copper/gold/silver shock events.
- `600362` Jiangxi Copper receives copper/gold/silver shock events.
- `601899` Zijin Mining receives copper/gold/lithium shock events.

The mapping is transparent but still approximate; it is a research factor, not proof that a stock must follow the commodity.

## Outputs

```text
raw_events.csv
event_store.csv
event_factors.csv
event_factor_quality.csv
event_factor_quality.md
news_evidence.md
event_warnings.json
event_feature_quality.csv
stock_event_store.csv
stock_event_factors.csv
stock_news_evidence.md
free_source_coverage.csv
source_gap_report.csv
source_gap_report.md
```

The event engine is a research input layer. It does not issue trading instructions.

## Source Coverage And Gaps

`discover-sources --domestic-only` writes a broader source matrix for market data, announcements, exchange/regulator pages, macro policy sources, public finance news, commodity exchanges, and QMT read-only state.

The matrix intentionally separates:

- implemented sources that may enter event factors
- partial sources with explicit limitations
- candidate direct adapters that are not allowed to influence stock-level factors yet
- credential/local-client limited sources

Current critical gaps are now narrower but still material: official SSE/SZSE/BSE/CSRC/NDRC/MIIT/MOFCOM/PBC/customs/NBS index-page adapters exist with bounded generic pagination and optional body-text audit, but still need site-specific pagination calibration, source-specific field extraction, and stronger PIT release-calendar handling. Richer direct commodity exchange inventory/notice feeds, direct Sina/Tencent/NetEase finance adapters, Tushare token permissions, and QMT local-client state also remain explicit follow-up items. These gaps are recorded in `source_gap_report.md` instead of being filled with fake events.

Rule: a source may influence stock-level event factors only when it has timestamps, source URLs, entity links, and an implemented or explicitly partial adapter.

## Event Risk Guardrail

Structured event factors now feed a conservative risk-control layer:

- `event_risk_count`, `negative_event_count`, `event_impact_score`, `event_weighted_impact_score`, `event_confidence_mean`, and `event_reliability_mean` can reduce target weights.
- Recent severe negative events can block a new simulated buy before an order plan is submitted.
- Positive or low-confidence events are kept in the risk report as evidence but are not hard trading blockers.
- The guard uses a recency window, default 30 days, so old events do not permanently suppress a stock.

Generated outputs include:

- `event_guarded_rebalance_targets.csv`
- `event_risk_guard_report.csv`
- `event_risk_guard_report.md`
- `event_risk_guard_summary.json`
- `event_guarded_metrics.json` for portfolio backtests with news

This is still a simulation guardrail. It is not a live trading permission path.

## Event Factors Used By Models

The current event-aware feature set adds these PIT numeric columns:

- `event_count_3d`
- `event_count_20d`
- `positive_event_count`
- `negative_event_count`
- `event_risk_count`
- `event_impact_score`
- `event_weighted_impact_score`
- `event_confidence_mean`
- `event_reliability_mean`
- `event_high_reliability_count`
- `event_entity_link_confidence_mean`
- `latest_event_source_reliability`
- `latest_entity_link_confidence`
- `latest_event_source`
- `latest_event_source_category`
- `latest_entity_link_method`
- `latest_entity_link_keywords`

These columns are joined by `date,symbol` into:

- `build-feature-store --with-news`
- `train-walk-forward --model event_aware_ensemble`
- `predict-stock --with-news`
- `predict-kline --with-news`
- `explain-stock --with-news`
- `report-stock --with-news --with-kline`
- `audit-news`
- `backtest-portfolio --with-news`
- `paper-trade --with-news --no-live`

## Source Isolation

Sample-mode events are only written to the command output directory and are not written into the shared event warehouse. Real/public events can be cached in `raw_events`, `event_store`, and `event_factor`. This prevents demo news from contaminating real predictions.

## Verification

Latest smoke outputs:

- `reports/aquant_v04_final/verify_feature_store_event_sample`
- `reports/aquant_v04_final/verify_walk_forward_event_sample`
- `reports/aquant_v04_final/verify_news_coverage_sample`
- `reports/aquant_v04_final/verify_event_guard_backtest_sample`
- `reports/aquant_v04_final/verify_event_guard_paper_trade_sample`
- `reports/aquant_v04_final/verify_commodity_news_metals`
- `reports/aquant_v04_final/verify_commodity_event_store_metals`
- `reports/aquant_v04_final/verify_event_reliability_weighting_sample`
- `reports/aquant_v04_final/verify_discover_sources_cninfo_direct`
- `reports/aquant_v04_final/verify_source_gap_matrix`
- `reports/aquant_v04_final/verify_sync_announcements_cninfo_direct_000630`
- `reports/aquant_v04_final/verify_event_store_cninfo_direct_000630`
- `reports/aquant_v04_final/verify_sync_announcements_cninfo_text_000630`
- `reports/aquant_v04_final/verify_event_store_cninfo_text_000630`
- `reports/aquant_v04_final/verify_official_public_sync_csrc`
- `reports/aquant_v04_final/verify_official_public_event_store_csrc`
- `reports/aquant_v04_final/verify_official_public_sync_csrc_text`
- `reports/aquant_v04_final/verify_official_public_event_store_csrc_text`
- `reports/aquant_v04_final/verify_official_public_sync_csrc_structured`
- `reports/aquant_v04_final/verify_official_public_event_store_csrc_structured`
- `reports/aquant_v04_final/verify_text_intelligence_registry`
- `reports/aquant_v04_final/verify_event_store_text_intelligence_sample`
- `reports/aquant_v04_final/verify_similar_event_store_sample`
- `reports/aquant_v04_final/verify_report_stock_similar_events_000630`
- `reports/aquant_v04_final/verify_event_impact_study_sample`
- `reports/aquant_v04_final/verify_report_stock_event_impact_000630`
- `reports/aquant_v04_final/verify_event_major_announcement_summary_sample`
- `reports/aquant_v04_final/verify_theme_entity_link_sample`
- `reports/aquant_v04_final/verify_feature_store_theme_entity_link_sample`
- `reports/aquant_v04_final/stocks/000630/04_full_report_source_isolated`

The 000630 isolated report includes `stock_event_store.csv`, `stock_event_factors.csv`, `stock_news_evidence.md`, and event factors inside `stock_forecast.csv`.

`audit-news` writes `news_coverage_audit.csv` and `news_coverage_summary.json`, exposing symbols with `ok`, `sparse`, or `no_linked_news` coverage.
