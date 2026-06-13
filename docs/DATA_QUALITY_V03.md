# Data Quality v0.3

## Free Source Policy

Preferred domestic free route:

1. BaoStock
2. AKShare
3. Tushare free token when available
4. Public Eastmoney/CNINFO style sources as future expansion

Sample data is forbidden by default for real prediction commands unless `--allow-sample` is explicitly used.

## Required Audit Columns

Warehouse writes use source-audit metadata where available:

- `source`
- `fetched_at`
- `effective_date`
- `announce_date`
- `raw_hash`
- `quality_flag`

## Current Limits

- Free sources may have missing fields, unstable endpoints, or inconsistent adjustment logic.
- Announcement text, industry history, historical index constituents, and minute-level data are not yet complete.
- A stock report can be generated with a small universe, but trust gating should remain conservative.

## Audit Commands

```powershell
python run_mvp.py discover-sources --domestic-only
python run_mvp.py sync-free-all --source baostock --universe config --start 2020-01-01
python run_mvp.py audit-data --strict-pit
python run_mvp.py build-feature-store --point-in-time --horizons 1,5,20,60
```
