# AQuant Full System Run

Run date: 2026-06-12

## Goal

Run the whole AQuant system end to end, fix real failures and obvious quality issues, then verify the current tree with repeatable commands.

## Plan Executed

1. Check environment, imports, compileability and tests.
2. Run discovery and registry commands.
3. Run the legacy MVP line: data check, factor analysis, prediction, backtest, sync and model training.
4. Run the advanced line: free sync, PIT audit, feature store, walk-forward training, model evaluation, stock forecast, stock backtest, stock explanation, QMT read-only and paper trading.
5. Run small real free-source smoke tests for BaoStock and AKShare.
6. Keep live trading blocked.
7. Re-run final verification after fixes.

## Fixes Made During The Full Run

- Optimized factor analysis:
  - `analyze_factors` was the bottleneck, taking about 276 seconds inside a 313 second sample run.
  - Replaced repeated factor/date correlation loops with vectorized long-table correlation.
  - Final sample `run` time is about 42 seconds.

- Fixed point-in-time audit for `source_audit`:
  - Strict audit reported `missing_point_in_time_columns` for `source_audit`.
  - `source_audit` now gets `source`, `fetched_at`, `effective_date`, `announce_date`, `quality_flag` and `raw_hash`.
  - Final strict audit reports 0 issues.

- Fixed stock forecast backtest drawdown:
  - Old `max_forward_drawdown` used cumulative simple-return sums and could go below -100%.
  - It now uses a compounded wealth curve with a safety floor.
  - Added a regression test.

- Fixed AKShare schema normalization:
  - Replaced corrupted Chinese column mapping with robust Chinese/English alias matching plus positional fallback.
  - Verified both BaoStock and AKShare single-symbol free-source smoke runs.

- Stabilized prediction signal labels:
  - Removed duplicated/garbled signal definition.
  - Runtime labels are back to the existing contract: `候选`, `观察`, `回避`.

## Final Verification

Passed:

```powershell
python -m pip check
$env:PYTHONPATH='src'; python -m compileall -q src tests run_mvp.py
python -m pytest -q
python run_mvp.py run --config configs\mvp.json --source sample --output-dir reports\full_run\99_final_run
python run_mvp.py audit-data --config configs\mvp.json --source sample --strict-pit --output-dir reports\full_run\99_final_audit
```

Observed final results:

- `pip check`: no broken requirements.
- Tests: 15 passed.
- Final sample pipeline runtime: about 42 seconds.
- Final strict PIT audit: 3 tables, 0 issues.
- BaoStock smoke: 1 symbol loaded, 243 rows.
- AKShare smoke: 1 symbol loaded, 243 rows.
- QMT read-only smoke: `xtquant` available, live submit disabled.
- Paper trade smoke: risk passed, no live trading.
- `live-trade`: intentionally returns non-zero and refuses order submission.

## Important Boundary

This run proves the engineering workflow is healthy. It does not prove live predictive accuracy. Real accuracy still requires large point-in-time data, walk-forward sample-out validation and paper trading over real market days.
