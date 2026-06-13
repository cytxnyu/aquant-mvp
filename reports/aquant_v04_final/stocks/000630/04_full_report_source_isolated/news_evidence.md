# News And Event Evidence Report

## Summary

- Events: 9
- Symbols: 3
- Event factors are structured research inputs, not direct trading advice.

## Latest Event Factor Snapshot

- `600362` 2025-12-29 00:00:00: impact=0.215, positive=2, negative=1, risk=1
- `601899` 2025-12-30 00:00:00: impact=0.215, positive=2, negative=1, risk=1
- `000630` 2025-12-31 00:00:00: impact=0.215, positive=2, negative=1, risk=1

## Evidence Items

- `000630` 2025-12-31 00:00:00 [sample_announcement] order_contract/positive impact=0.55: 公告: 000630 发布经营进展公告，订单合同和产能信息需要继续跟踪。 (no_url)
- `601899` 2025-12-30 00:00:00 [sample_announcement] order_contract/positive impact=0.55: 公告: 601899 发布经营进展公告，订单合同和产能信息需要继续跟踪。 (no_url)
- `600362` 2025-12-29 00:00:00 [sample_announcement] order_contract/positive impact=0.55: 公告: 600362 发布经营进展公告，订单合同和产能信息需要继续跟踪。 (no_url)
- `000630` 2025-12-28 00:00:00 [sample_industry_news] commodity_shock/positive impact=0.20: 行业: 有色金属与新能源产业链价格波动，对相关股票形成商品价格冲击。 (no_url)
- `601899` 2025-12-27 00:00:00 [sample_industry_news] commodity_shock/positive impact=0.20: 行业: 有色金属与新能源产业链价格波动，对相关股票形成商品价格冲击。 (no_url)
- `600362` 2025-12-26 00:00:00 [sample_industry_news] commodity_shock/positive impact=0.20: 行业: 有色金属与新能源产业链价格波动，对相关股票形成商品价格冲击。 (no_url)
- `000630` 2025-12-25 00:00:00 [sample_risk_news] public_opinion_risk/negative impact=-0.55: 风险: 000630 出现舆情风险提示，需降低事件置信度。 (no_url)
- `601899` 2025-12-24 00:00:00 [sample_risk_news] public_opinion_risk/negative impact=-0.55: 风险: 601899 出现舆情风险提示，需降低事件置信度。 (no_url)
- `600362` 2025-12-23 00:00:00 [sample_risk_news] public_opinion_risk/negative impact=-0.55: 风险: 600362 出现舆情风险提示，需降低事件置信度。 (no_url)

## Guardrails

- Unlinked news is excluded from individual-stock event factors.
- Source failures must be written as warnings, not silently filled with fake events.