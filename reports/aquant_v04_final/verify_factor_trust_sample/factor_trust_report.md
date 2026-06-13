# Factor Trust Report

## Summary

- Total factors: 237
- Approved: 76
- Watchlist: 146
- Quarantine: 15

## Rules

- Factors require economic rationale and point-in-time inputs.
- Low coverage, weak empirical signal, suspected leakage, and near-duplicate/crowded factors are excluded from trusted models.
- Approval here is a research gate, not a guarantee of future profitability.

## Top Approved Candidates

- `max_drawdown_120`: category=volatility_risk, coverage=0.92, rank_ic=0.0840, monotonicity=0.700
- `price_position_120`: category=price_volume, coverage=0.92, rank_ic=0.0837, monotonicity=1.000
- `ema_alignment_score`: category=price_volume, coverage=1.00, rank_ic=0.0831, monotonicity=0.900
- `upside_tail_return_60`: category=volatility_risk, coverage=0.96, rank_ic=0.0820, monotonicity=0.900
- `cs_momentum_rank_60`: category=price_volume, coverage=0.94, rank_ic=0.0777, monotonicity=1.000
- `momentum_60`: category=price_volume, coverage=0.94, rank_ic=0.0777, monotonicity=1.000
- `ma_alignment_score`: category=price_volume, coverage=1.00, rank_ic=0.0737, monotonicity=0.800
- `close_above_ma_ratio_20`: category=price_volume, coverage=0.98, rank_ic=0.0710, monotonicity=0.900
- `close_above_ma_ratio_60`: category=price_volume, coverage=0.96, rank_ic=0.0693, monotonicity=0.900
- `breakout_high_40`: category=price_volume, coverage=0.97, rank_ic=0.0693, monotonicity=1.000
- `breakdown_low_40`: category=price_volume, coverage=0.97, rank_ic=0.0686, monotonicity=0.800
- `price_position_40`: category=price_volume, coverage=0.97, rank_ic=0.0657, monotonicity=1.000
- `bollinger_breakout_count_60`: category=price_volume, coverage=0.96, rank_ic=0.0653, monotonicity=1.000
- `cs_momentum_rank_120`: category=price_volume, coverage=0.88, rank_ic=0.0647, monotonicity=0.900
- `momentum_120`: category=price_volume, coverage=0.88, rank_ic=0.0647, monotonicity=0.900
- `bollinger_breakout_count_20`: category=price_volume, coverage=0.98, rank_ic=0.0644, monotonicity=0.700
- `max_drawdown_60`: category=volatility_risk, coverage=0.96, rank_ic=0.0642, monotonicity=1.000
- `positive_body_ratio_60`: category=trend_shape, coverage=0.96, rank_ic=0.0636, monotonicity=0.900
- `rsi_24`: category=price_volume, coverage=0.98, rank_ic=0.0614, monotonicity=0.900
- `price_position_240`: category=price_volume, coverage=0.84, rank_ic=0.0609, monotonicity=0.900

## Quarantine Examples

- `macd_hist`: weak_empirical_signal
- `limit_up_count_20`: low_observations;weak_empirical_signal
- `limit_up_count_60`: low_observations;weak_empirical_signal
- `limit_down_count_20`: low_observations;weak_empirical_signal
- `limit_down_count_60`: low_observations;weak_empirical_signal
- `limit_up_near_5`: low_observations;weak_empirical_signal
- `limit_down_near_5`: low_observations;weak_empirical_signal
- `gap_up_count_20`: low_observations;weak_empirical_signal
- `gap_up_count_60`: low_observations
- `gap_down_count_20`: low_observations;weak_empirical_signal
- `gap_down_count_60`: low_observations
- `range_compression_60`: low_observations
- `cs_liquidity_risk_score`: weak_empirical_signal
- `market_breadth`: low_observations;weak_empirical_signal
- `market_mean_return`: low_observations;weak_empirical_signal