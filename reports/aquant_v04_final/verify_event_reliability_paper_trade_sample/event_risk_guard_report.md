# Event Risk Guard Report

This guard uses structured, timestamped event factors to reduce or block target weights before simulated order generation. It is a risk control, not trading advice.

## Summary

- Enabled: `True`
- Adjusted rows: `13`
- Blocked symbols: `000858`
- Reduced symbols: `000001, 000858, 002594, 300750, 600519, 601888`
- Weight removed: `1.4000`

## Latest Adjustments

- `2025-12-19` `002594` reduce_weight: 0.200 -> 0.100; impact=-0.550, weighted=-0.156, reliability=0.40, risk_events=1, reason=event_risk_count_threshold;negative_event_count
- `2025-12-19` `300750` reduce_weight: 0.200 -> 0.100; impact=-0.096, weighted=-0.031, reliability=0.40, risk_events=1, reason=event_risk_count_threshold;negative_event_count
- `2025-12-19` `601888` reduce_weight: 0.200 -> 0.100; impact=-0.550, weighted=-0.156, reliability=0.40, risk_events=1, reason=event_risk_count_threshold;negative_event_count
- `2025-12-26` `000001` reduce_weight: 0.200 -> 0.100; impact=-0.550, weighted=-0.156, reliability=0.40, risk_events=1, reason=event_risk_count_threshold;negative_event_count
- `2025-12-26` `000858` block_new_buy: 0.200 -> 0.000; impact=-0.096, weighted=-0.031, reliability=0.40, risk_events=1, reason=event_risk_count_threshold;negative_event_count
- `2025-12-26` `002594` reduce_weight: 0.200 -> 0.100; impact=0.215, weighted=0.059, reliability=0.40, risk_events=1, reason=event_risk_count_threshold
- `2025-12-26` `300750` reduce_weight: 0.200 -> 0.100; impact=0.215, weighted=0.059, reliability=0.40, risk_events=1, reason=event_risk_count_threshold
- `2025-12-26` `600519` reduce_weight: 0.200 -> 0.100; impact=-0.550, weighted=-0.156, reliability=0.40, risk_events=1, reason=event_risk_count_threshold;negative_event_count
- `2025-12-31` `000001` reduce_weight: 0.200 -> 0.100; impact=0.215, weighted=0.059, reliability=0.40, risk_events=1, reason=event_risk_count_threshold
- `2025-12-31` `000858` reduce_weight: 0.200 -> 0.100; impact=0.215, weighted=0.059, reliability=0.40, risk_events=1, reason=event_risk_count_threshold
- `2025-12-31` `002594` reduce_weight: 0.200 -> 0.100; impact=0.215, weighted=0.059, reliability=0.40, risk_events=1, reason=event_risk_count_threshold
- `2025-12-31` `300750` reduce_weight: 0.200 -> 0.100; impact=0.215, weighted=0.059, reliability=0.40, risk_events=1, reason=event_risk_count_threshold
- `2025-12-31` `600519` reduce_weight: 0.200 -> 0.100; impact=0.215, weighted=0.059, reliability=0.40, risk_events=1, reason=event_risk_count_threshold