# Portfolio Validation Report

This report challenges whether the portfolio backtest is traceable and stable enough for research review. It does not certify future returns and is not investment advice.

## Summary

- Validation status: `passed`
- Failed checks: `0`; warnings: `0`; passes: `17`
- Total/annual return: `0.1569` / `0.0358`
- Max drawdown: `-0.1103`; Sharpe: `0.5482`; Calmar: `0.3251`
- Avg turnover: `0.0542`; total cost: `14747.06`; avg cost bps: `12.85`
- Annual positive ratio: `0.7500`; worst year: `-0.0005`

## Gate Results

- `pass` `equity_curve_present` observed=`1043` threshold=`>0 rows`
- `pass` `rebalance_trace_present` observed=`208` threshold=`>0 rows`
- `pass` `trade_trace_present` observed=`384` threshold=`>0 rows`
- `pass` `costs_recorded` observed=`14747.059065140375` threshold=`>=0`
- `pass` `cost_after_metrics_available` observed=`['annual_return', 'annual_volatility', 'avg_turnover', 'calmar', 'final_equity', 'initial_cash', 'max_drawdown', 'rebalance_count', 'sharpe', 'total_return', 'total_turnover', 'trade_count', 'win_rate']` threshold=`required metrics`
- `pass` `turnover_within_config` observed=`0.054207` threshold=`<= 1.0`
- `pass` `drawdown_within_risk_budget` observed=`-0.110256` threshold=`>= -0.1500`
- `pass` `annual_stability_available` observed=`4` threshold=`>=1 year rows`
- `pass` `annual_positive_ratio` observed=`0.75` threshold=`>=0.50`
- `pass` `worst_year_not_extreme` observed=`-0.0005` threshold=`> -0.50`
- `pass` `portfolio_constraints_audited` observed=`True` threshold=`True`
- `pass` `single_name_cap_enforced` observed=`0.15` threshold=`<= 0.2`
- `pass` `theme_cap_enforced` observed=`0.45` threshold=`<= 0.45`
- `pass` `daily_turnover_cap_enforced` observed=`0.45` threshold=`<= 1.0`
- `pass` `event_attribution_available` observed=`778` threshold=`>0 when --with-news`
- `pass` `event_guard_evidence_available` observed=`True` threshold=`true when --with-news`
- `pass` `capacity_proxy_available` observed=`11479541.406` threshold=`cost table with gross/cost bps`

## Annual Stability

- `2022` return `-0.0005`, drawdown `-0.1103`, Sharpe `0.0215`, status `negative`
- `2023` return `0.0515`, drawdown `-0.0970`, Sharpe `0.6849`, status `positive`
- `2024` return `0.0855`, drawdown `-0.0591`, Sharpe `1.0317`, status `positive`
- `2025` return `0.0088`, drawdown `-0.0810`, Sharpe `0.3039`, status `positive`

## Cost Evidence

- `all` trades `384`, gross `11479541.41`, cost `14747.06`, avg bps `12.85`
- `buy` trades `180`, gross `5916115.47`, cost `4732.89`, avg bps `8.00`
- `sell` trades `204`, gross `5563425.94`, cost `10014.17`, avg bps `18.00`