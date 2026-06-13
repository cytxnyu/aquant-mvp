# Portfolio Constraint Report

This report audits executable portfolio constraints applied after signal generation and before backtest or paper-trade order planning. It is a research risk-control report, not investment advice.

## Summary

- Target dates: `209`
- Symbols: `3`
- Adjustment rows: `1254`
- Constraints triggered: `max_single_weight, max_theme_weight`
- Max gross weight after constraints: `0.4500`
- Max single weight after constraints: `0.1500`
- Max theme weight after constraints: `0.4500`

## Latest Daily State

- `2025-12-05` gross 0.450 -> 0.450; cash=0.550; constraints=max_single_weight;max_theme_weight
- `2025-12-12` gross 0.450 -> 0.450; cash=0.550; constraints=max_single_weight;max_theme_weight
- `2025-12-19` gross 0.450 -> 0.450; cash=0.550; constraints=max_single_weight;max_theme_weight
- `2025-12-26` gross 0.450 -> 0.450; cash=0.550; constraints=max_single_weight;max_theme_weight
- `2025-12-31` gross 0.450 -> 0.450; cash=0.550; constraints=max_single_weight;max_theme_weight

## Latest Adjustments

- `2025-12-12` `600362` max_theme_weight: 0.200 -> 0.150; reason=theme_weight_cap
- `2025-12-12` `601899` max_theme_weight: 0.200 -> 0.150; reason=theme_weight_cap
- `2025-12-19` `000630` max_single_weight: 0.300 -> 0.200; reason=single_name_weight_cap
- `2025-12-19` `600362` max_single_weight: 0.300 -> 0.200; reason=single_name_weight_cap
- `2025-12-19` `601899` max_single_weight: 0.300 -> 0.200; reason=single_name_weight_cap
- `2025-12-19` `000630` max_theme_weight: 0.200 -> 0.150; reason=theme_weight_cap
- `2025-12-19` `600362` max_theme_weight: 0.200 -> 0.150; reason=theme_weight_cap
- `2025-12-19` `601899` max_theme_weight: 0.200 -> 0.150; reason=theme_weight_cap
- `2025-12-26` `000630` max_single_weight: 0.300 -> 0.200; reason=single_name_weight_cap
- `2025-12-26` `600362` max_single_weight: 0.300 -> 0.200; reason=single_name_weight_cap
- `2025-12-26` `601899` max_single_weight: 0.300 -> 0.200; reason=single_name_weight_cap
- `2025-12-26` `000630` max_theme_weight: 0.200 -> 0.150; reason=theme_weight_cap
- `2025-12-26` `600362` max_theme_weight: 0.200 -> 0.150; reason=theme_weight_cap
- `2025-12-26` `601899` max_theme_weight: 0.200 -> 0.150; reason=theme_weight_cap
- `2025-12-31` `000630` max_single_weight: 0.300 -> 0.200; reason=single_name_weight_cap
- `2025-12-31` `600362` max_single_weight: 0.300 -> 0.200; reason=single_name_weight_cap
- `2025-12-31` `601899` max_single_weight: 0.300 -> 0.200; reason=single_name_weight_cap
- `2025-12-31` `000630` max_theme_weight: 0.200 -> 0.150; reason=theme_weight_cap
- `2025-12-31` `600362` max_theme_weight: 0.200 -> 0.150; reason=theme_weight_cap
- `2025-12-31` `601899` max_theme_weight: 0.200 -> 0.150; reason=theme_weight_cap