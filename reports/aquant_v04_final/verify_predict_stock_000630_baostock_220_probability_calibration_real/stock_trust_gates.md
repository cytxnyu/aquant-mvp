# Stock Trust Gate Report: 000630

This report explains why each probabilistic forecast is or is not trusted. A failed block gate prevents `trusted`; warning gates are evidence gaps or risk notes. This is not investment advice.

## Summary

- Source: `baostock`
- Horizons: `3`
- Final status set: `model_failed, weak`
- Blocking gate count: `9`
- Blocking gates: `local_signal_quality, walk_forward_evidence_present, walk_forward_rows, walk_forward_trusted`

## Horizon Gates

### 1d - `weak`
- Block `walk_forward_trusted`: walk_forward_status=weak; reasons=min_oos_rows;brier_below_025
- Block `walk_forward_rows`: walk_forward_rows=2370
- Block `local_signal_quality`: confidence=0.0376; sample_rank_ic=0.0000
- Warn `risk_flags_clear`: risk_flags=high_volatility

### 5d - `weak`
- Block `walk_forward_trusted`: walk_forward_status=weak; reasons=beats_baseline;auc_above_052;brier_below_025;calibration_ready;rank_ic_positive;top_bottom_spread_positive
- Block `local_signal_quality`: confidence=0.0278; sample_rank_ic=0.0000
- Warn `risk_flags_clear`: risk_flags=high_volatility

### 20d - `model_failed`
- Block `walk_forward_evidence_present`: walk_forward_evidence_missing
- Block `walk_forward_trusted`: walk_forward_status=missing; reasons=walk_forward_evidence_missing
- Block `walk_forward_rows`: walk_forward_rows=0
- Block `local_signal_quality`: confidence=0.0036; sample_rank_ic=0.0000
- Warn `risk_flags_clear`: risk_flags=high_volatility