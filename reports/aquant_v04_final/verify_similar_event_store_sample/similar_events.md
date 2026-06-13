# Similar Event Evidence Report

This report retrieves earlier structured events that resemble recent query events. It is an explanation layer only: it does not issue buy/sell advice and cannot promote a forecast to `trusted` without walk-forward evidence.

## Summary

- Symbol: `all`
- Query events: `12`
- Matches: `33`
- Retrieval model: `tfidf_char_cosine_with_jaccard_fallback`
- PIT policy: candidate events must be earlier than query events; forward returns require the return window to end before query time

## Historical Outcomes

- 1d known rows: `0`, mean=0.0000%, positive_rate=0.00%
- 5d known rows: `0`, mean=0.0000%, positive_rate=0.00%
- 20d known rows: `0`, mean=0.0000%, positive_rate=0.00%

## Top Matches

- Query `000630` 2025-12-31T00:00:00 order_contract: matched `000630` 2025-12-25T00:00:00 public_opinion_risk score=0.353, same_symbol=True, returns=(1d=NA, 5d=NA, 20d=NA); 风险: 000630 出现舆情风险提示，需降低事件置信度。
- Query `000630` 2025-12-31T00:00:00 order_contract: matched `000630` 2025-12-28T00:00:00 commodity_shock score=0.157, same_symbol=True, returns=(1d=NA, 5d=NA, 20d=NA); 行业: 有色金属与新能源产业链价格波动，对相关股票形成商品价格冲击。
- Query `000630` 2025-12-31T00:00:00 order_contract: matched `600362` 2025-12-29T00:00:00 order_contract score=0.720, same_symbol=False, returns=(1d=NA, 5d=NA, 20d=NA); 公告: 600362 发布经营进展公告，订单合同和产能信息需要继续跟踪。
- Query `000630` 2025-12-31T00:00:00 order_contract: matched `601899` 2025-12-30T00:00:00 order_contract score=0.698, same_symbol=False, returns=(1d=NA, 5d=NA, 20d=NA); 公告: 601899 发布经营进展公告，订单合同和产能信息需要继续跟踪。
- Query `601899` 2025-12-30T00:00:00 order_contract: matched `601899` 2025-12-24T00:00:00 public_opinion_risk score=0.306, same_symbol=True, returns=(1d=NA, 5d=NA, 20d=NA); 风险: 601899 出现舆情风险提示，需降低事件置信度。
- Query `601899` 2025-12-30T00:00:00 order_contract: matched `601899` 2025-12-27T00:00:00 commodity_shock score=0.139, same_symbol=True, returns=(1d=NA, 5d=NA, 20d=NA); 行业: 有色金属与新能源产业链价格波动，对相关股票形成商品价格冲击。
- Query `601899` 2025-12-30T00:00:00 order_contract: matched `600362` 2025-12-29T00:00:00 order_contract score=0.782, same_symbol=False, returns=(1d=NA, 5d=NA, 20d=NA); 公告: 600362 发布经营进展公告，订单合同和产能信息需要继续跟踪。
- Query `601899` 2025-12-30T00:00:00 order_contract: matched `600362` 2025-12-23T00:00:00 public_opinion_risk score=0.050, same_symbol=False, returns=(1d=NA, 5d=NA, 20d=NA); 风险: 600362 出现舆情风险提示，需降低事件置信度。
- Query `600362` 2025-12-29T00:00:00 order_contract: matched `600362` 2025-12-23T00:00:00 public_opinion_risk score=0.262, same_symbol=True, returns=(1d=NA, 5d=NA, 20d=NA); 风险: 600362 出现舆情风险提示，需降低事件置信度。
- Query `600362` 2025-12-29T00:00:00 order_contract: matched `600362` 2025-12-26T00:00:00 commodity_shock score=0.124, same_symbol=True, returns=(1d=NA, 5d=NA, 20d=NA); 行业: 有色金属与新能源产业链价格波动，对相关股票形成商品价格冲击。
- Query `600362` 2025-12-29T00:00:00 order_contract: matched `601899` 2025-12-27T00:00:00 commodity_shock score=0.055, same_symbol=False, returns=(1d=NA, 5d=NA, 20d=NA); 行业: 有色金属与新能源产业链价格波动，对相关股票形成商品价格冲击。
- Query `600362` 2025-12-29T00:00:00 order_contract: matched `000630` 2025-12-28T00:00:00 commodity_shock score=0.052, same_symbol=False, returns=(1d=NA, 5d=NA, 20d=NA); 行业: 有色金属与新能源产业链价格波动，对相关股票形成商品价格冲击。
- Query `600362` 2025-12-29T00:00:00 order_contract: matched `601899` 2025-12-24T00:00:00 public_opinion_risk score=0.050, same_symbol=False, returns=(1d=NA, 5d=NA, 20d=NA); 风险: 601899 出现舆情风险提示，需降低事件置信度。
- Query `000630` 2025-12-29T00:00:00 commodity_shock: matched `000630` 2025-12-28T00:00:00 commodity_shock score=0.174, same_symbol=True, returns=(1d=NA, 5d=NA, 20d=NA); 行业: 有色金属与新能源产业链价格波动，对相关股票形成商品价格冲击。
- Query `000630` 2025-12-29T00:00:00 commodity_shock: matched `600362` 2025-12-26T00:00:00 commodity_shock score=0.175, same_symbol=False, returns=(1d=NA, 5d=NA, 20d=NA); 行业: 有色金属与新能源产业链价格波动，对相关股票形成商品价格冲击。
- Query `000630` 2025-12-29T00:00:00 commodity_shock: matched `601899` 2025-12-27T00:00:00 commodity_shock score=0.175, same_symbol=False, returns=(1d=NA, 5d=NA, 20d=NA); 行业: 有色金属与新能源产业链价格波动，对相关股票形成商品价格冲击。
- Query `600362` 2025-12-29T00:00:00 commodity_shock: matched `600362` 2025-12-26T00:00:00 commodity_shock score=0.175, same_symbol=True, returns=(1d=NA, 5d=NA, 20d=NA); 行业: 有色金属与新能源产业链价格波动，对相关股票形成商品价格冲击。
- Query `600362` 2025-12-29T00:00:00 commodity_shock: matched `601899` 2025-12-27T00:00:00 commodity_shock score=0.175, same_symbol=False, returns=(1d=NA, 5d=NA, 20d=NA); 行业: 有色金属与新能源产业链价格波动，对相关股票形成商品价格冲击。
- Query `600362` 2025-12-29T00:00:00 commodity_shock: matched `000630` 2025-12-28T00:00:00 commodity_shock score=0.174, same_symbol=False, returns=(1d=NA, 5d=NA, 20d=NA); 行业: 有色金属与新能源产业链价格波动，对相关股票形成商品价格冲击。
- Query `601899` 2025-12-29T00:00:00 commodity_shock: matched `601899` 2025-12-27T00:00:00 commodity_shock score=0.175, same_symbol=True, returns=(1d=NA, 5d=NA, 20d=NA); 行业: 有色金属与新能源产业链价格波动，对相关股票形成商品价格冲击。
- Query `601899` 2025-12-29T00:00:00 commodity_shock: matched `600362` 2025-12-26T00:00:00 commodity_shock score=0.175, same_symbol=False, returns=(1d=NA, 5d=NA, 20d=NA); 行业: 有色金属与新能源产业链价格波动，对相关股票形成商品价格冲击。
- Query `601899` 2025-12-29T00:00:00 commodity_shock: matched `000630` 2025-12-28T00:00:00 commodity_shock score=0.174, same_symbol=False, returns=(1d=NA, 5d=NA, 20d=NA); 行业: 有色金属与新能源产业链价格波动，对相关股票形成商品价格冲击。
- Query `000630` 2025-12-28T00:00:00 commodity_shock: matched `000630` 2025-12-25T00:00:00 public_opinion_risk score=0.190, same_symbol=True, returns=(1d=NA, 5d=NA, 20d=NA); 风险: 000630 出现舆情风险提示，需降低事件置信度。
- Query `000630` 2025-12-28T00:00:00 commodity_shock: matched `600362` 2025-12-26T00:00:00 commodity_shock score=0.953, same_symbol=False, returns=(1d=NA, 5d=NA, 20d=NA); 行业: 有色金属与新能源产业链价格波动，对相关股票形成商品价格冲击。
- Query `000630` 2025-12-28T00:00:00 commodity_shock: matched `601899` 2025-12-27T00:00:00 commodity_shock score=0.949, same_symbol=False, returns=(1d=NA, 5d=NA, 20d=NA); 行业: 有色金属与新能源产业链价格波动，对相关股票形成商品价格冲击。
- Query `000630` 2025-12-28T00:00:00 commodity_shock: matched `600362` 2025-12-23T00:00:00 public_opinion_risk score=0.050, same_symbol=False, returns=(1d=NA, 5d=NA, 20d=NA); 风险: 600362 出现舆情风险提示，需降低事件置信度。
- Query `601899` 2025-12-27T00:00:00 commodity_shock: matched `601899` 2025-12-24T00:00:00 public_opinion_risk score=0.161, same_symbol=True, returns=(1d=NA, 5d=NA, 20d=NA); 风险: 601899 出现舆情风险提示，需降低事件置信度。
- Query `601899` 2025-12-27T00:00:00 commodity_shock: matched `600362` 2025-12-26T00:00:00 commodity_shock score=0.968, same_symbol=False, returns=(1d=NA, 5d=NA, 20d=NA); 行业: 有色金属与新能源产业链价格波动，对相关股票形成商品价格冲击。
- Query `601899` 2025-12-27T00:00:00 commodity_shock: matched `600362` 2025-12-23T00:00:00 public_opinion_risk score=0.053, same_symbol=False, returns=(1d=NA, 5d=NA, 20d=NA); 风险: 600362 出现舆情风险提示，需降低事件置信度。
- Query `600362` 2025-12-26T00:00:00 commodity_shock: matched `600362` 2025-12-23T00:00:00 public_opinion_risk score=0.139, same_symbol=True, returns=(1d=NA, 5d=NA, 20d=NA); 风险: 600362 出现舆情风险提示，需降低事件置信度。

## Guardrails

- Matches are restricted to events published before the query event.
- Forward returns are omitted when they would not have been known at query time.
- Retrieval evidence is not a trading signal.
