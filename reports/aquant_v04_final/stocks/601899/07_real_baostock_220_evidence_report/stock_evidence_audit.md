# Stock Forecast Evidence Audit: 601899

This audit checks whether each stock forecast row contains the evidence required for a falsifiable research signal. It does not certify future returns and is not investment advice.

## Summary

- Source: `baostock`
- Horizons: `4`
- Validation status: `failed`
- Failed checks: `walk_forward_evidence`
- Warning checks: `none`
- With news: `True`

## Horizon Evidence

### 1d - `weak`
- Required evidence checks: passed

### 5d - `weak`
- Required evidence checks: passed

### 20d - `model_failed`
- Fail `walk_forward_evidence`: trusted prediction evidence requires out-of-sample walk-forward provenance (observed: `model=; status=missing; rows=0`)

### 60d - `model_failed`
- Fail `walk_forward_evidence`: trusted prediction evidence requires out-of-sample walk-forward provenance (observed: `model=; status=missing; rows=0`)