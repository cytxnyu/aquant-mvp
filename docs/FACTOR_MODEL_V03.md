# Factor And Model v0.3

## Factor Count

`FACTOR_COLUMNS` now contains 237 factors.

New groups include:

- Oscillators: KDJ, CCI, Williams %R, MFI.
- Volume/price flow: VWAP bias, OBV slope, volume-price correlation, return-amount correlation, signed flow, PVT.
- Crowding: amount/turnover crowding, amount shock counts, stalled-up volume.
- Shape and volatility: Bollinger breakout count, tail returns, absolute return mean, range compression, ATR contraction.
- Trend structure: close-above-MA ratio, MA/EMA alignment, shrinkage breakout, low-volume pullback.
- Cross-section: momentum, reversal, volatility, amount, turnover ranks, market breadth, market mean return.

## Model Path

- Baseline: factor score and calibrated score percentile.
- Optional model: LightGBM classifier/regressor when installed and data is large enough.
- Validation: time split and walk-forward commands remain mandatory for serious use.
- Trust: no model is marked trusted merely because it produced a number.

## Current Validation

Unit tests pass. Large-sample effectiveness still must be proven with `train-walk-forward` on 200+ symbols or all-A free data.
