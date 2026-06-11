# Architecture

AQuant is a lightweight A-share quantitative research platform. The current stage focuses on a transparent research loop rather than a production trading stack.

## Data Flow

```text
config
  -> data provider sample/AKShare
  -> data quality checks
  -> universe filters
  -> factor panel
  -> forward-return labels
  -> factor analysis IC/RankIC/quantiles
  -> multi-factor scoring
  -> rebalance targets
  -> A-share backtest engine
  -> report artifacts CSV/JSON/PNG/Markdown
```

## Modules

- `aquant_mvp.data`: Loads normalized daily bars, writes/reads local CSV cache, checks quality.
- `aquant_mvp.universe`: Applies first-pass stock-pool filters and reserves hooks for ST, suspension, limit-up/down, delisting and industry filters.
- `aquant_mvp.factors`: Computes historical-only factor features and cross-sectional normalization helpers.
- `aquant_mvp.labels`: Generates future return and cross-sectional excess-return labels.
- `aquant_mvp.analysis`: Computes IC, RankIC, ICIR, factor coverage and quantile forward returns.
- `aquant_mvp.strategy`: Scores stocks with configurable factor weights and creates rebalance targets.
- `aquant_mvp.backtest`: Simulates a simple A-share daily strategy with next-open execution, T+1, lot size and costs.
- `aquant_mvp.reporting`: Persists run artifacts and a manifest.
- `aquant_mvp.workflow`: Stable import surface for pipeline/config orchestration.

## Design Choices

- The platform is intentionally small and readable. It avoids heavy framework lock-in.
- Sample data is deterministic, so tests and demos can run offline.
- Strategy signals are generated from historical data and executed on the next trading date.
- The reporting layer writes a `manifest.json` so each run is inspectable and reproducible.
- Qlib/LightGBM/vn.py integration is planned as a later layer, not as the current core.

## Current Limitations

- The sample data is synthetic and only validates the workflow.
- AKShare public data is convenient but not sufficient for serious point-in-time research.
- Real A-share constraints such as ST, suspension, limit-up/down and delisting are reserved interfaces until reliable data is connected.
- The backtest engine is daily and simple by design; it is not a matching engine.

