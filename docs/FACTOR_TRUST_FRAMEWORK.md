# Factor Trust Framework

## Registry Fields

`factor_registry.csv` contains:

- `factor_id`
- `name`
- `category`
- `data_dependency`
- `effective_lag`
- `economic_rationale`
- `direction`
- `owner`
- `tests`
- `status`
- `pit_rule`

## Audit Metrics

`factor_trust_audit.csv` contains:

- coverage
- missing ratio
- IC / RankIC / ICIR
- quantile monotonicity
- yearly stability
- maximum absolute correlation
- most-correlated factor id
- VIF proxy
- half-life proxy
- rank turnover proxy
- gross top-bottom spread
- estimated cost drag
- cost-adjusted spread
- regime count
- regime positive ratio
- worst regime RankIC
- regime stability note
- crowding flag
- leakage suspicion
- cost drag flag
- regime unstable flag
- quarantine reason

Cost and regime checks are first-class trust gates. A factor with apparently positive IC can still be downgraded when turnover makes the top-bottom spread negative after estimated trading cost, or when the factor only works in one market regime and fails in bullish, sideways, or bearish slices.

## Trust Status

- `approved`: passes minimum data and empirical gates.
- `watchlist`: useful but crowded, redundant, unstable, or expensive.
- `quarantine`: low coverage, weak evidence, suspected leakage, or too little history.

Approved factors are still not a guarantee. They only pass the current research gate.

## Current Evidence

The latest cost/regime verification is:

```powershell
python run_mvp.py analyze-factor-trust --config configs\mvp.json --source sample --allow-sample --universe 000630,601899,600362 --horizons 5 --output-dir reports\aquant_v04_final\verify_factor_trust_cost_regime_sample
```

It produced 237 audited factors:

- approved: 67
- watchlist: 157
- quarantine: 13

The report now includes a `Cost/Regime Watchlist` section. This is intentionally conservative: short-horizon reversal, volatility, downside-volatility, liquidity-size proxies, and market-state fields can be quarantined or watched when their net spread is negative after cost or their worst regime RankIC is negative.

## Command

```powershell
python run_mvp.py analyze-factor-trust --config configs\mvp.json --source sample --horizons 5 --output-dir reports\aquant_v04_final\verify_factor_trust_sample
```
