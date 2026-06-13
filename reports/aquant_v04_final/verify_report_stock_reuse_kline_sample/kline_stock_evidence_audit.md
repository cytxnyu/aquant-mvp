# Stock Forecast Evidence Audit: 000630

This audit checks whether each stock forecast row contains the evidence required for a falsifiable research signal. It does not certify future returns and is not investment advice.

## Summary

- Source: `sample`
- Horizons: `5`
- Validation status: `failed`
- Failed checks: `walk_forward_evidence`
- Warning checks: `sample_source_warning`
- With news: `True`

## Horizon Evidence

### 1d - `data_insufficient`
- Required evidence checks: passed
- Warn `sample_source_warning`: sample data can verify plumbing but cannot prove a real signal (observed: `sample`)

### 5d - `data_insufficient`
- Required evidence checks: passed
- Warn `sample_source_warning`: sample data can verify plumbing but cannot prove a real signal (observed: `sample`)

### 8d - `data_insufficient`
- Fail `walk_forward_evidence`: trusted prediction evidence requires out-of-sample walk-forward provenance (observed: `model=; status=missing; rows=0`)
- Warn `sample_source_warning`: sample data can verify plumbing but cannot prove a real signal (observed: `sample`)

### 20d - `data_insufficient`
- Fail `walk_forward_evidence`: trusted prediction evidence requires out-of-sample walk-forward provenance (observed: `model=; status=missing; rows=0`)
- Warn `sample_source_warning`: sample data can verify plumbing but cannot prove a real signal (observed: `sample`)

### 60d - `data_insufficient`
- Fail `walk_forward_evidence`: trusted prediction evidence requires out-of-sample walk-forward provenance (observed: `model=; status=missing; rows=0`)
- Warn `sample_source_warning`: sample data can verify plumbing but cannot prove a real signal (observed: `sample`)