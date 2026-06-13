# Paper Trade Validation Report

This report verifies that the dry-run trading path stayed paper-only and produced auditable risk/order/execution evidence. It is not live-trading permission.

## Summary

- Validation status: `passed`
- Risk passed: `True`; no-live: `True`; broker: `paper`
- Orders/executions/positions: `3` / `3` / `3`
- Failed checks: `0`; warnings: `0`; passes: `14`

## Gate Results

- `pass` `no_live_required` observed=`True` threshold=`True`
- `pass` `paper_summary_present` observed=`['event_risk_guard', 'metadata', 'no_live', 'passed', 'portfolio_constraints', 'requested_days', 'with_news']` threshold=`non-empty`
- `pass` `requested_days_recorded` observed=`20` threshold=`>= 20`
- `pass` `order_plan_present` observed=`3` threshold=`>0 rows`
- `pass` `risk_report_present` observed=`3` threshold=`>0 rows`
- `pass` `risk_report_matches_summary` observed=`True` threshold=`True`
- `pass` `executions_present_when_risk_passed` observed=`3` threshold=`>0 rows`
- `pass` `positions_present_when_risk_passed` observed=`True` threshold=`True`
- `pass` `paper_only_filled_status` observed=`['FILLED']` threshold=`FILLED`
- `pass` `execution_count_matches_orders` observed=`3` threshold=`3`
- `pass` `execution_costs_recorded` observed=`['fee', 'fill_price', 'filled_shares', 'gross_value', 'requested_shares', 'side', 'status', 'symbol', 'tax', 'trade_date']` threshold=`gross_value/fee/tax`
- `pass` `broker_is_paper` observed=`paper` threshold=`paper`
- `pass` `portfolio_constraints_recorded` observed=`dict` threshold=`dict`
- `pass` `event_guard_recorded` observed=`dict` threshold=`dict`