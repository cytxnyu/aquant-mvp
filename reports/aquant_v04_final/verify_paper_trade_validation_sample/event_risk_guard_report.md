# Event Risk Guard Report

This guard uses structured, timestamped event factors to reduce or block target weights before simulated order generation. It is a risk control, not trading advice.

## Summary

- Enabled: `True`
- Adjusted rows: `6`
- Blocked symbols: `none`
- Reduced symbols: `000630, 600362, 601899`
- Weight removed: `0.4500`

## Latest Adjustments

- `2025-12-26` `000630` reduce_weight: 0.150 -> 0.075; impact=-0.550, weighted=-0.156, reliability=0.40, risk_events=1, reason=event_risk_count_threshold;negative_event_count
- `2025-12-26` `600362` reduce_weight: 0.150 -> 0.075; impact=-0.096, weighted=-0.031, reliability=0.40, risk_events=1, reason=event_risk_count_threshold;negative_event_count
- `2025-12-26` `601899` reduce_weight: 0.150 -> 0.075; impact=-0.550, weighted=-0.156, reliability=0.40, risk_events=1, reason=event_risk_count_threshold;negative_event_count
- `2025-12-31` `000630` reduce_weight: 0.150 -> 0.075; impact=0.211, weighted=0.064, reliability=0.40, risk_events=1, reason=event_risk_count_threshold
- `2025-12-31` `600362` reduce_weight: 0.150 -> 0.075; impact=0.210, weighted=0.065, reliability=0.40, risk_events=1, reason=event_risk_count_threshold
- `2025-12-31` `601899` reduce_weight: 0.150 -> 0.075; impact=0.211, weighted=0.064, reliability=0.40, risk_events=1, reason=event_risk_count_threshold