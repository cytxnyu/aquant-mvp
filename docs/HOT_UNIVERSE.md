# AQuant Mega-hot Universe

This upgrade expands the curated hot-sector seed universe from a small demo list into a broad cross-sectional pool.

Aliases:

- `hot`
- `mega-hot`
- `mega_hot`
- `all-hot`

All of the aliases above resolve to the expanded pool. `core-hot` keeps the six original strategic themes:

- `ai_compute_semiconductor`
- `robotics_highend_manufacturing`
- `metals_energy_metals`
- `power_solid_state_battery`
- `defense_ship_equipment`
- `innovative_drug_medical_device`

`professional`, `professional-hot`, and `pro-hot` resolve to the finer professional sub-sector layer:

- semiconductor equipment/materials
- advanced packaging/chiplet/PCB
- CPO optical module/data center
- humanoid robot core parts
- industrial mother machine/laser
- solid-state battery materials
- UHV/smart grid equipment
- rare earth magnetic materials
- commercial space/satellite internet
- CXO/biotech/innovative drug
- medical device/IVD/imaging
- data element/fintech/AI app
- central SOE high dividend
- shipbuilding/ocean shipping

The expanded pool is a research seed universe, not an official industry classifier. Real prediction still requires liquidity filters, ST/suspension/delist checks, point-in-time data, and sample-out validation.

Latest verified smoke output on 2026-06-12:

- `mega-hot`: 36 themes, 845 theme rows, 624 unique symbols.
- `professional`: 14 themes, 145 theme rows, 145 unique symbols.

## Commands

```powershell
python run_mvp.py build-universe --themes mega-hot --output-dir reports\mega_hot_universe
python run_mvp.py build-universe --themes professional --output-dir reports\professional_universe
python run_mvp.py sync-free-all --config configs\prod.example.json --source free_real --universe mega-hot --max-symbols 50 --output-dir reports\free_max_sync
python run_mvp.py train-walk-forward --config configs\prod.example.json --source free_real --universe mega-hot --model ensemble --horizons 1,5,20 --output-dir reports\walk_forward
python run_mvp.py predict-stock --config configs\prod.example.json --source free_real --universe mega-hot --symbol 601899 --horizons 1,5,20 --output-dir reports\stock_forecast
```

Use `--universe all-a` when BaoStock or AKShare can return the full A-share list and the network/data source is stable enough. If all-A discovery fails, the CLI falls back to the mega-hot pool.

## Output Files

`build-universe` writes:

- `theme_universe.csv`: curated theme-symbol rows.
- `theme_universe_summary.csv`: per-theme coverage.
- `symbol_theme_membership.csv`: duplicate and cross-theme membership.
- `theme_universe_manifest.json`: universe size, duplicate rows, and trust-gating notes.

`sync-free-all` now continues through per-symbol failures and records them in `source_audit`. A single bad code, vendor timeout, or free-source schema change should no longer stop the whole large-universe job.

## Trust Gate

The individual stock forecaster now reports:

- `universe_symbol_count`
- `minimum_trusted_symbols`

Sample data cannot produce `trusted` forecasts. A larger pool removes the old small-universe bottleneck, but it does not guarantee accuracy. Forecasts remain probabilistic research signals, not investment advice.
