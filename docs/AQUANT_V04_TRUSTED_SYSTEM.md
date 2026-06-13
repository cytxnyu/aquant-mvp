# AQuant v0.4 Trusted System

## Goal

v0.4 upgrades AQuant from a runnable prediction system into a verifiable research system:

- factor trust registry
- news/event evidence chain
- point-in-time data audit
- walk-forward validation
- stock report with forecast, K-line, factor contribution, event evidence, and risk flags
- portfolio constraint audit for single-name caps, theme caps, volatility targeting, turnover, blacklist, and drawdown circuit breakers
- event-risk guardrail for portfolio targets and paper orders
- commodity/industry-chain shock events for metals and energy-linked stocks
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
python run_mvp.py sync-news --config configs\mvp.json --source akshare --universe 000630,601899 --start 2025-01-01
python run_mvp.py sync-news --config configs\metals.json --source akshare --universe 000630,600362,601899 --start 2025-01-01
python run_mvp.py sync-announcements --config configs\mvp.json --source akshare --universe 000630,601899 --start 2025-01-01
python run_mvp.py sync-announcements --config configs\mvp.json --source cninfo_direct --universe 000630 --start 2026-01-01 --fetch-announcement-text
python run_mvp.py build-event-store --config configs\mvp.json --source akshare --universe 000630,601899 --start 2025-01-01
python run_mvp.py audit-news --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --start 2024-01-01
python run_mvp.py build-feature-store --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --horizons 1,5,20,60 --point-in-time --with-news
python run_mvp.py train-walk-forward --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --model event_aware_ensemble --horizons 1,5,20,60
python run_mvp.py train-walk-forward --config configs\mvp.json --source sample --allow-sample --universe mega-hot --max-symbols 220 --min-symbols 200 --model factor_score --horizons 5 --train-years 1 --test-months 3 --start 2024-01-01
python run_mvp.py backtest-portfolio --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362
python run_mvp.py backtest-portfolio --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --with-news
python run_mvp.py backtest-portfolio --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --output-dir reports\aquant_v04_final\verify_portfolio_constraints_sample
python run_mvp.py paper-trade --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --days 20 --no-live --output-dir reports\aquant_v04_final\verify_portfolio_constraints_paper_trade_sample
python run_mvp.py paper-trade --config configs\mvp.json --source sample --allow-sample --with-news --no-live
python run_mvp.py report-stock --config configs\mvp.json --source sample --allow-sample --symbol 000630 --with-news --with-kline
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
- `predict-stock` now records probability calibration rows, bin coverage, ECE, and calibration status. Sparse or failed probability calibration blocks `trusted` status.
- `predict-stock` now records conformal-style return interval evidence for p10/p50/p90: method, rows, target coverage, interval half-width, and status. Sparse conformal evidence blocks direct `trusted` promotion.
- New walk-forward prediction artifacts include PIT diagnostics for liquidity and market state (`amount_mean_20`, `cs_amount_rank_20`, `market_breadth`, `market_mean_return`). Evaluation uses these fields when present and clearly marks older artifacts where they are unavailable.
- A BaoStock 220-symbol real-source walk-forward run loaded 220/220 symbols and generated 72,748 OOS rows. It correctly stayed `weak` because AUC, Brier, and RankIC gates failed, proving the system can reject an insufficient real signal instead of overstating accuracy.
- `predict-stock --source baostock --universe mega-hot --max-symbols 220 --symbol 000630` now attaches that real walk-forward evidence and outputs `weak`, not `trusted`.
- BaoStock batch loading now uses a lazy reusable session and resilient large-universe commands keep an audit trail for failed symbols.
- Unit tests pass for factor trust, event bus, event-aware feature store, event-aware forecast output, event-risk guardrails, and risk/live-trade blockers.

## Remaining Work

- Expand real event sources beyond AKShare wrappers to exchange/regulator direct pages; direct CNINFO metadata and optional text extraction are implemented but still need richer endpoint/schema handling.
- Calibrate theme-keyword entity links against historical industry/concept membership and reduce false positives in broad policy news.
- Extend event-risk guardrails with empirical severity calibration and regime-specific thresholds.
- Calibrate commodity shock thresholds by commodity and stock exposure instead of using one default threshold.
- Run 200+ symbol walk-forward on real/free data, not sample data, before any real signal can be marked `trusted`.
- Run BaoStock-heavy and shared event-warehouse write jobs sequentially unless adapters are refactored to use isolated sessions/transactional writes; parallel runs can collide at the vendor or cache layer.
