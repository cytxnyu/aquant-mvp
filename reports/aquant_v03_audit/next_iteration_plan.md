# AQuant v0.3 Next Iteration Plan

## Phase 1: Bigger Free Universe

- Run `build-universe --themes all-a-free` and `build-universe --themes mega-hot`.
- Use `sync-free-all --source baostock --universe mega-hot --max-symbols 300` first, then expand to 1000+.
- Keep every failed source request in `source_audit`; do not silently create fake data.

## Phase 2: Trusted Prediction Gate

- Train on at least 200 symbols, preferably 500-1200 hot-sector symbols.
- Run `train-walk-forward --model ensemble --horizons 1,5,20,60`.
- Only allow `trusted` when validation beats baseline on RankIC/Brier/directional metrics and no strict data issues exist.

## Phase 3: K-line Backtest

- Add path-level validation: compare predicted p10/p50/p90 bands with realized future closes.
- Report band hit rate, median absolute error, direction accuracy, and regime split.
- Keep K-line chart language probabilistic.

## Phase 4: Data Expansion

- Add historical industry/concept snapshots where free sources expose them.
- Add moneyflow, dragon-tiger, margin, and announcement ingestion with announce/effective dates.
- Generate coverage reports by symbol, table, date range, and source.

## Phase 5: Simulation

- Run PaperBroker for 20 trading days from generated signals.
- Keep `live-trade` blocked.
- QMT remains read-only until paper-trade, reconciliation, risk, and manual confirmation are all proven.

## Phase 6: Optional Paid Upgrade

Free domestic sources can build a strong research system. For institution-grade stability, use Wind/iFinD/JoinQuant/RiceQuant or broker-authorized QMT data. No foreign network access is required for core A-share research.
