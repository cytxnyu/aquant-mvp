# AQuant v0.4 System Gap Report

## Completed In This Iteration

- Added `factor_registry` and `factor_trust_audit` warehouse tables.
- Added `raw_events`, `event_store`, and `event_factor` warehouse tables.
- Added `analyze-factor-trust`, `sync-news`, `sync-announcements`, and `build-event-store` commands.
- Added `report-stock --with-news` to generate event evidence beside forecast/K-line/backtest files.
- Added event evidence markdown and stock-level event factor CSV outputs.
- Added event-aware feature fusion for `build-feature-store`, `train-walk-forward`, `predict-stock`, `predict-kline`, `explain-stock`, and `report-stock`.
- Added `event_aware_ensemble` model mode with 7 numeric event factors.
- Added `backtest-portfolio` as a portfolio backtest command that respects command-line universe selection.
- Added sample/real event source isolation so sample events do not overwrite the shared event warehouse.
- Added `audit-news` to produce per-symbol news/event coverage status.
- Fixed raw-event cache reuse so partial cached symbols trigger missing-symbol fetches instead of false `no_linked_news` audit results.
- Added portfolio event attribution for `backtest-portfolio --with-news`.
- Added event-risk guardrails that reduce/block target weights from structured news factors before paper-trade order generation.
- Added event-guarded portfolio backtest comparison outputs for `backtest-portfolio --with-news`.
- Added an audited portfolio constraint layer for `backtest-portfolio` and `paper-trade --no-live`: single-name cap, theme cap, turnover cap, volatility target, blacklist, drawdown circuit breaker, adjusted targets, daily audit, and constrained backtest metrics.
- Added domestic commodity futures shock events through AKShare/Sina main contracts and mapped them into stock-level event factors.
- Fixed source-audit preservation so event rows keep their original `source`, `quality_flag`, `fetched_at`, and `raw_hash`, while audit metadata is stored separately.
- Tightened walk-forward `trusted` gating: enough rows, baseline improvement, AUC, Brier, RankIC, and top-bottom spread must all pass.
- Added CLI controls for large validation runs: `--min-symbols`, `--train-years`, `--test-months`, and `--max-symbols` for `train-walk-forward`.
- Added registry-backed walk-forward evidence fields to `predict-stock` and `report-stock`, so stock reports cannot self-certify without matching OOS model evidence.
- Added model evaluation slices by year, theme proxy, size/liquidity availability, and ex-post market regime.
- Added probability calibration evidence to stock forecasts: calibration rows, bin coverage, ECE, and status. Sparse or failed calibration blocks `trusted`.
- Added conformal-style return interval evidence to stock forecasts: method, rows, alpha, target coverage, interval half-width, and status. Sparse conformal evidence blocks direct `trusted` promotion.
- Added audited entity linking for policy/macro/industry events: explicit symbols, provided related symbols, code/name mentions, and theme-keyword links with confidence and matched keywords.
- Added PIT diagnostic fields to new walk-forward prediction artifacts: liquidity proxies, volatility, market breadth, and market mean return.
- Upgraded model evaluation slices to distinguish PIT liquidity/regime sources from older artifacts where those fields are unavailable.
- Added resilient free-source batch loading for large-universe walk-forward/prediction jobs, with lazy BaoStock session reuse and per-symbol failure audit.
- Added `--max-symbols` handling to shared data-config construction so prediction commands can run bounded 200+ pools without accidentally loading the full 600+ seed universe.
- Added factor cost/regime trust gates: top correlated factor id, estimated transaction-cost drag, cost-adjusted top-bottom spread, bullish/sideways/bearish RankIC stability, and downgrade/quarantine flags for expensive or regime-fragile factors.
- Added source reliability weighting to event evidence: `source_category`, `source_reliability`, `weighted_impact_score`, weighted event factors, and weighted-impact risk checks.
- Added `cninfo_direct` public-source adapter for direct CNINFO announcement metadata, CLI source routing, empty-schema handling, and persisted event warning audits.
- Added optional direct announcement body extraction via `--fetch-announcement-text`, with `source_text_status`, `source_text_length`, and `source_text_hash` carried into event evidence. HTML/text are parsed directly; PDF parsing is explicit about parser availability.
- Added unit tests for factor trust, event bus, and event-risk guardrails.

## Current Verification

- `sync-news` sample: 6 raw rows for 2 symbols.
- `sync-announcements` sample: 2 rows.
- `build-event-store` sample: 2 events, 2 event-factor rows.
- `sync-news` AKShare: 174 raw rows for `000630,601899`.
- `build-event-store` AKShare: 160 structured events, 228 event-factor rows.
- `analyze-factor-trust` sample: 237 factors, with approved/watchlist/quarantine status.
- `report-stock --with-news --with-kline` sample: full stock report generated for `000630`.
- `build-feature-store --with-news` sample: 244 total features, including 7 event features.
- `train-walk-forward --model event_aware_ensemble` sample: event-aware walk-forward generated metrics for 1/5/20/60d and correctly marked the 3-symbol run `data_insufficient`.
- `backtest-portfolio` sample: loaded 3 requested symbols and generated portfolio reports.
- `report-stock --with-news --with-kline` isolated sample: complete `000630` report generated with source-isolated sample events.
- `audit-news` sample: 3 symbols audited, 9 events, 15 event-factor rows, all coverage statuses `ok`.
- Real free-source `report-stock --source baostock --symbol 000630 --with-news --with-kline`: full event-aware report generated with BaoStock daily bars and 80 linked events.
- Five key full reports generated with BaoStock daily bars, event evidence, predicted K-line, stock backtest, and manifests: `000630`, `601899`, `600362`, `300308`, `300750`.
- Key-stock `audit-news`: 5 symbols, 414 events, 521 event-factor rows, all coverage statuses `ok` after missing-symbol cache fetch fix.
- `backtest-portfolio --with-news` sample: generated daily and symbol-level portfolio event attribution reports.
- `backtest-portfolio --with-news` event guard sample: wrote event-guarded targets, trades, holdings, attribution, and metrics.
- `paper-trade --with-news --no-live` sample: event-risk guard adjusted 13 target rows, blocked/reduced affected weights, generated order/risk reports, and stayed paper-only.
- Portfolio constraint sample: wrote `portfolio_constraint_report.*`, `portfolio_constraint_daily.csv`, adjusted targets, constrained trades/holdings/equity/metrics, and showed risk-control cost transparently. In the 3-symbol sample, constrained max drawdown improved from about `-0.2103` to `-0.1103` while total return fell from about `0.9157` to `0.1569`.
- Portfolio constraint paper-trade sample: wrote `portfolio_constraint_report.*`, generated a 20-day `--no-live` order plan after constraints, and kept live orders disabled.
- Commodity news sync for `000630,600362,601899`: 705 raw rows, including 447 `akshare_futures_main_sina` futures-shock rows.
- Commodity event store for `000630,600362,601899`: 691 structured events and 810 event-factor rows, with futures source evidence preserved in `news_evidence.md`.
- 220-symbol sample walk-forward trust-gate run: 58,520 OOS rows, accuracy 0.5085, AUC 0.5132, Brier 0.2520, RankIC 0.0267, top-bottom spread 0.0035, `trust_status=weak`, failed gates `auc_above_052;brier_below_025`.
- `evaluate-models` v0.4 slices read 126,407 walk-forward prediction rows and wrote year, theme, industry-proxy, size, and regime reports.
- `predict-stock` calibration sample for `000630` wrote `calibration_rows=624`, `calibration_bins=1`, `calibration_status=calibration_low_coverage`, keeping the sample forecast `data_insufficient`.
- `predict-stock` conformal sample for `000630` wrote p10/p50/p90 plus `conformal_method=split_conformal_historical_residual_proxy`, target coverage 0.8, and `conformal_status=conformal_ready` on the sample horizons.
- PIT diagnostic walk-forward sample wrote `amount_mean_20`, `cs_amount_rank_20`, `market_breadth`, and `market_mean_return` into `walk_forward_predictions.csv`.
- PIT diagnostic evaluation read 128,765 walk-forward prediction rows and separated `cs_amount_rank_20_liquidity_proxy` / `pit_market_mean_return_and_breadth` rows from older unavailable/ex-post artifacts.
- BaoStock 20-symbol real-source smoke: loaded 20 symbols, generated 6,620 OOS rows, and correctly stayed `weak`.
- BaoStock 220-symbol real-source walk-forward: loaded 220/220 symbols, generated 72,748 OOS rows, accuracy 0.4847, AUC 0.4790, Brier 0.2567, RankIC -0.0383, `trust_status=weak`, failed gates `auc_above_052;brier_below_025;rank_ic_positive`.
- `evaluate-models` including the BaoStock 220-symbol run read 208,133 walk-forward prediction rows and produced updated year/theme/size/regime slices.
- `predict-stock` for `000630` on the BaoStock 220-symbol pool produced `trust_status=weak`, `walk_forward_rows=72748`, `walk_forward_status=weak`, and `calibration_status=calibration_low_coverage`.
- Cost/regime factor trust sample: 237 factors audited; 67 approved, 157 watchlist, 13 quarantine. The report includes a `Cost/Regime Watchlist`, and factors with negative cost-adjusted spread or unstable regime behavior are downgraded instead of entering trusted models unchecked.
- Event reliability weighting sample: 9 structured events and 15 event-factor rows generated with `source_reliability`, `weighted_impact_score`, `event_weighted_impact_score`, and reliability evidence in markdown.
- Event reliability feature-store sample: 3,129 PIT rows, 248 features, and 11 event features, including weighted impact and source reliability fields.
- Event reliability paper-trade sample: event guard adjusted 13 target rows and wrote weighted impact/reliability evidence into `event_risk_guard_report.*` while staying `--no-live`.
- 000630 event-reliability stock report: generated forecast CSV/JSON, predicted K-line HTML/PNG/CSV, explanation, backtest metrics, event evidence, and manifest; forecast rows include `event_feature_count=11` and factor contributions from event reliability fields.
- Source discovery with direct CNINFO: 7 domestic/free source rows, including `cninfo_direct`.
- Direct CNINFO 000630 smoke: `sync-announcements` completed with 0 rows and a recorded `cninfo_direct unexpected schema` warning; `build-event-store` wrote empty event outputs plus `event_warnings.json` instead of using fake data.
- Direct CNINFO text smoke: `--fetch-announcement-text` completed with the same source warning and wrote schemas containing text audit fields. The sample event-store verification now includes a `Recent Major Announcement Summary` section.
- 000630 announcement-text report smoke: refreshed full sample report with forecast CSV/JSON, prediction K-line HTML/PNG/CSV, `stock_news_evidence.md` major announcement summary, and `source_text_*` fields in `stock_event_store.csv`.
- 000630 conformal/text report smoke: refreshed full sample report with conformal interval columns, announcement summary evidence, prediction K-line artifacts, and `trust_status=data_insufficient`.
- Theme entity-link sample: unlinked AI/semiconductor policy news mapped to `300308`, metals policy news mapped to `000630`, and event factors now include 13 event features with entity-link confidence fields.
- Full tests: 35 passed; compileall passed; pip check passed; `live-trade --confirm` remains blocked.

## Engineering Notes

- BaoStock login is not safe for heavy parallel command execution in this project. Sequential BaoStock runs avoid observed `用户未登录` session collisions.
- All five key reports are still `data_insufficient`, not `trusted`, because their local free-source universes are below the 200-symbol trusted threshold.
- Current walk-forward slice reports expose unstable periods and regimes; this is expected and should be treated as evidence against overclaiming precision.
- Older walk-forward artifacts do not contain PIT diagnostics and are explicitly marked as unavailable or ex-post fallback in slice reports; regenerate important walk-forward runs after this change for cleaner diagnostics.
- The factor trust audit can produce numpy warnings on constant cross-sections; these are non-fatal, but warning cleanup and explicit constant-factor diagnostics remain useful hardening work.

## Remaining Gaps

- Direct CNINFO metadata and optional HTML/text announcement extraction are implemented. Direct exchange/regulator feeds, richer CNINFO schema handling, and robust PDF extraction still need expansion.
- Theme-keyword entity linking is implemented but still needs calibration against historical industry/concept membership and false-positive audits on large real news corpora.
- Event-risk guardrails are implemented for sample/news-aware paper-trade and comparison backtest. They still need empirical reliability calibration, direct regulator/exchange feeds, and large-universe validation.
- Portfolio constraints are implemented and audited for sample backtest/paper-trade. They still need large-universe capacity validation, industry-classification driven theme maps, and empirical volatility/drawdown parameter calibration.
- Source reliability weighting is now implemented, but direct exchange/regulator feeds and empirical reliability calibration still need expansion.
- Commodity shocks are implemented with generic thresholds and approximate stock mappings; they still need exposure weights, commodity-specific thresholds, and validation against historical stock reactions.
- `trusted` remains unavailable for real predictions: the first 220-symbol BaoStock validation failed AUC/Brier/RankIC gates. Next work should improve factor/model quality and rerun real-source validation rather than loosening gates.

## Safety

Live trading remains blocked. QMT/XtQuant is allowed only as read-only.
