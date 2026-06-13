# Stock Trust Gate Report: 000630

This report explains why each probabilistic forecast is or is not trusted. A failed block gate prevents `trusted`; warning gates are evidence gaps or risk notes. This is not investment advice.

## Summary

- Source: `sample`
- Horizons: `3`
- Final status set: `data_insufficient`
- Blocking gate count: `18`
- Blocking gates: `local_signal_quality, minimum_universe_size, probability_calibration, sample_data_block, walk_forward_evidence_present, walk_forward_rows, walk_forward_trusted`

## Horizon Gates

### 1d - `data_insufficient`
- Block `sample_data_block`: sample_source_cannot_be_trusted
- Block `minimum_universe_size`: universe_symbols=3, minimum=200
- Block `walk_forward_trusted`: walk_forward_status=data_insufficient; reasons=
- Block `walk_forward_rows`: walk_forward_rows=340
- Block `probability_calibration`: calibration_status=calibration_low_coverage; ece=0.0059; rows=627
- Block `local_signal_quality`: confidence=0.0736; sample_rank_ic=0.0000
- Warn `news_evidence_available`: with_news=False; event_rows=0; event_factor_rows=0

### 5d - `data_insufficient`
- Block `sample_data_block`: sample_source_cannot_be_trusted
- Block `minimum_universe_size`: universe_symbols=3, minimum=200
- Block `walk_forward_trusted`: walk_forward_status=weak; reasons=auc_above_052;brier_below_025;rank_ic_positive
- Block `probability_calibration`: calibration_status=calibration_low_coverage; ece=0.0132; rows=624
- Block `local_signal_quality`: confidence=0.1501; sample_rank_ic=0.0000
- Warn `news_evidence_available`: with_news=False; event_rows=0; event_factor_rows=0

### 20d - `data_insufficient`
- Block `sample_data_block`: sample_source_cannot_be_trusted
- Block `minimum_universe_size`: universe_symbols=3, minimum=200
- Block `walk_forward_evidence_present`: walk_forward_evidence_missing
- Block `walk_forward_trusted`: walk_forward_status=missing; reasons=walk_forward_evidence_missing
- Block `walk_forward_rows`: walk_forward_rows=0
- Block `probability_calibration`: calibration_status=calibration_low_coverage; ece=0.0167; rows=615
- Block `local_signal_quality`: confidence=0.2178; sample_rank_ic=0.0000
- Warn `news_evidence_available`: with_news=False; event_rows=0; event_factor_rows=0