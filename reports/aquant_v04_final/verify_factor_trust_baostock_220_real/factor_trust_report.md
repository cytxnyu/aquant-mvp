# Factor Trust Report

## Summary

- Total factors: 237
- Approved: 11
- Watchlist: 223
- Quarantine: 3

## Rules

- Factors require economic rationale and point-in-time inputs.
- Low coverage, weak empirical signal, suspected leakage, near-duplicate/crowded factors, negative cost-adjusted spread, and regime instability are excluded or downgraded.
- Approval here is a research gate, not a guarantee of future profitability.

## Top Approved Candidates

- `amihud_illiquidity_20`: category=liquidity_flow, coverage=0.98, rank_ic=0.0310, net_spread=0.0039, regime_pos=1.00, monotonicity=1.000
- `amihud_illiquidity_60`: category=liquidity_flow, coverage=0.97, rank_ic=0.0223, net_spread=0.0035, regime_pos=1.00, monotonicity=1.000
- `downside_tail_return_20`: category=volatility_risk, coverage=0.99, rank_ic=0.0195, net_spread=-0.0009, regime_pos=0.67, monotonicity=-0.700
- `cs_reversal_rank_5`: category=price_volume, coverage=0.99, rank_ic=0.0168, net_spread=0.0005, regime_pos=1.00, monotonicity=0.000
- `long_lower_shadow_count_60`: category=trend_shape, coverage=0.97, rank_ic=0.0089, net_spread=-0.0007, regime_pos=0.67, monotonicity=-0.600
- `down_streak`: category=trend_shape, coverage=1.00, rank_ic=0.0070, net_spread=0.0008, regime_pos=0.67, monotonicity=1.000
- `return_autocorr_20`: category=technical_other, coverage=0.99, rank_ic=0.0063, net_spread=0.0020, regime_pos=1.00, monotonicity=0.900
- `body_size`: category=trend_shape, coverage=1.00, rank_ic=0.0030, net_spread=0.0001, regime_pos=0.67, monotonicity=0.700
- `upper_shadow`: category=trend_shape, coverage=1.00, rank_ic=0.0017, net_spread=0.0001, regime_pos=1.00, monotonicity=0.700
- `long_upper_shadow_count_20`: category=trend_shape, coverage=0.99, rank_ic=-0.0017, net_spread=0.0012, regime_pos=0.67, monotonicity=0.700
- `gap_down_count_60`: category=trend_shape, coverage=0.97, rank_ic=-0.0161, net_spread=0.0020, regime_pos=1.00, monotonicity=1.000

## Cost/Regime Watchlist

- `momentum_1`: net_spread=-0.0004, rank_turnover=0.330, regime_pos=0.33, worst_regime_rank_ic=-0.0518
- `momentum_2`: net_spread=-0.0011, rank_turnover=0.226, regime_pos=0.33, worst_regime_rank_ic=-0.0662
- `momentum_3`: net_spread=-0.0014, rank_turnover=0.183, regime_pos=0.00, worst_regime_rank_ic=-0.0651
- `momentum_5`: net_spread=-0.0009, rank_turnover=0.141, regime_pos=0.00, worst_regime_rank_ic=-0.0549
- `momentum_10`: net_spread=0.0001, rank_turnover=0.100, regime_pos=0.00, worst_regime_rank_ic=-0.0246
- `momentum_20`: net_spread=0.0001, rank_turnover=0.071, regime_pos=0.00, worst_regime_rank_ic=-0.0249
- `momentum_40`: net_spread=-0.0018, rank_turnover=0.052, regime_pos=0.00, worst_regime_rank_ic=-0.0495
- `momentum_60`: net_spread=0.0004, rank_turnover=0.043, regime_pos=0.00, worst_regime_rank_ic=-0.0529
- `momentum_120`: net_spread=-0.0009, rank_turnover=0.032, regime_pos=0.00, worst_regime_rank_ic=-0.0490
- `momentum_240`: net_spread=0.0021, rank_turnover=0.023, regime_pos=0.33, worst_regime_rank_ic=-0.0168
- `reversal_1`: net_spread=-0.0005, rank_turnover=0.330, regime_pos=0.67, worst_regime_rank_ic=-0.0399
- `volatility_20`: net_spread=0.0007, rank_turnover=0.031, regime_pos=0.33, worst_regime_rank_ic=-0.0273
- `volatility_40`: net_spread=0.0012, rank_turnover=0.018, regime_pos=0.33, worst_regime_rank_ic=-0.0446
- `volatility_60`: net_spread=0.0017, rank_turnover=0.013, regime_pos=0.33, worst_regime_rank_ic=-0.0404
- `volatility_120`: net_spread=0.0020, rank_turnover=0.007, regime_pos=0.00, worst_regime_rank_ic=-0.0447
- `volatility_240`: net_spread=0.0010, rank_turnover=0.004, regime_pos=0.33, worst_regime_rank_ic=-0.0294
- `upside_volatility_5`: net_spread=0.0004, rank_turnover=0.108, regime_pos=0.33, worst_regime_rank_ic=-0.0189
- `upside_volatility_10`: net_spread=0.0010, rank_turnover=0.058, regime_pos=0.33, worst_regime_rank_ic=-0.0251
- `upside_volatility_20`: net_spread=0.0004, rank_turnover=0.032, regime_pos=0.33, worst_regime_rank_ic=-0.0302
- `upside_volatility_60`: net_spread=0.0007, rank_turnover=0.014, regime_pos=0.33, worst_regime_rank_ic=-0.0521

## Quarantine Examples

- `range_compression_60`: low_observations
- `market_breadth`: low_observations
- `market_mean_return`: low_observations;regime_unstable