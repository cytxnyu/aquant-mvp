# Event Risk Guard Report

This guard uses structured, timestamped event factors to reduce or block target weights before simulated order generation. It is a risk control, not trading advice.

## Summary

- Enabled: `True`
- Adjusted rows: `6`
- Blocked symbols: `none`
- Reduced symbols: `000630, 600362, 601899`
- Weight removed: `0.9000`

## Latest Adjustments

- `2025-12-26` `000630` reduce_weight: 0.300 -> 0.150; impact=-0.550, risk_events=1, reason=event_risk_count_threshold;negative_event_impact_threshold;negative_event_count
- `2025-12-26` `600362` reduce_weight: 0.300 -> 0.150; impact=-0.096, risk_events=1, reason=event_risk_count_threshold;negative_event_count
- `2025-12-26` `601899` reduce_weight: 0.300 -> 0.150; impact=-0.550, risk_events=1, reason=event_risk_count_threshold;negative_event_impact_threshold;negative_event_count
- `2025-12-31` `000630` reduce_weight: 0.300 -> 0.150; impact=0.215, risk_events=1, reason=event_risk_count_threshold
- `2025-12-31` `600362` reduce_weight: 0.300 -> 0.150; impact=0.215, risk_events=1, reason=event_risk_count_threshold
- `2025-12-31` `601899` reduce_weight: 0.300 -> 0.150; impact=0.215, risk_events=1, reason=event_risk_count_threshold