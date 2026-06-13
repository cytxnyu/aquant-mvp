# Theme Coverage Audit

This audit checks whether the stock pool is broad enough for cross-sectional research and theme-level validation. It is not evidence of forecast accuracy.

## Summary

- Requested themes: `mega-hot`
- Unique symbols: `1200`
- Minimum symbols before any trusted prediction can be considered: `200`
- Theme rows audited: `38`
- Themes that can support trusted evidence after model/data gates: `38`
- Coverage status counts: `{'ready': 30, 'broad': 8}`

## Thin Or Blocked Themes

- No theme coverage blockers found. Predictive trust still depends on data, factor, model, and walk-forward gates.

## Guardrail

- A broad theme universe only removes the small-pool bottleneck. It must still pass PIT data audit, factor trust audit, walk-forward, calibration, event evidence, and risk gates before any stock forecast can be marked `trusted`.
