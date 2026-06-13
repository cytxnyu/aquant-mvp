# Similar Event Evidence Report

This report retrieves earlier structured events that resemble recent query events. It is an explanation layer only: it does not issue buy/sell advice and cannot promote a forecast to `trusted` without walk-forward evidence.

## Summary

- Symbol: `000630`
- Query events: `5`
- Matches: `25`
- Retrieval model: `tfidf_char_cosine_with_jaccard_fallback`
- PIT policy: candidate events must be earlier than query events; forward returns require the return window to end before query time

## Historical Outcomes

- 1d known rows: `23`, mean=-0.0895%, positive_rate=43.48%
- 5d known rows: `21`, mean=1.3112%, positive_rate=61.90%
- 20d known rows: `19`, mean=4.3257%, positive_rate=68.42%

## Top Matches

- Query `000630` 2026-06-10T00:00:00 commodity_shock: matched `000630` 2026-03-23T00:00:00 commodity_shock score=0.639, same_symbol=True, returns=(1d=3.94%, 5d=5.90%, 20d=15.38%); 沪金主连价格下跌触发商品冲击
- Query `000630` 2026-06-10T00:00:00 commodity_shock: matched `000630` 2026-06-08T00:00:00 commodity_shock score=0.632, same_symbol=True, returns=(1d=5.40%, 5d=NA, 20d=NA); 沪金主连价格下跌触发商品冲击
- Query `000630` 2026-06-10T00:00:00 commodity_shock: matched `000630` 2025-04-23T00:00:00 commodity_shock score=0.630, same_symbol=True, returns=(1d=-0.63%, 5d=-0.63%, 20d=0.00%); 沪金主连价格下跌触发商品冲击
- Query `000630` 2026-06-10T00:00:00 commodity_shock: matched `000630` 2024-06-11T00:00:00 commodity_shock score=0.628, same_symbol=True, returns=(1d=0.27%, 5d=-4.29%, 20d=0.80%); 沪金主连价格下跌触发商品冲击
- Query `000630` 2026-06-10T00:00:00 commodity_shock: matched `000630` 2026-03-25T00:00:00 commodity_shock score=0.623, same_symbol=True, returns=(1d=-2.20%, 5d=1.18%, 20d=6.60%); 沪金主连价格下跌触发商品冲击
- Query `000630` 2026-06-10T00:00:00 commodity_shock: matched `000630` 2026-06-08T00:00:00 commodity_shock score=0.736, same_symbol=True, returns=(1d=5.40%, 5d=NA, 20d=NA); 沪银主连价格下跌触发商品冲击
- Query `000630` 2026-06-10T00:00:00 commodity_shock: matched `000630` 2026-02-11T00:00:00 commodity_shock score=0.692, same_symbol=True, returns=(1d=0.56%, 5d=5.71%, 20d=-15.32%); 沪银主连价格下跌触发商品冲击
- Query `000630` 2026-06-10T00:00:00 commodity_shock: matched `000630` 2026-04-02T00:00:00 commodity_shock score=0.691, same_symbol=True, returns=(1d=-1.37%, 5d=4.46%, 20d=11.49%); 沪银主连价格下跌触发商品冲击
- Query `000630` 2026-06-10T00:00:00 commodity_shock: matched `000630` 2026-06-09T00:00:00 commodity_shock score=0.681, same_symbol=True, returns=(1d=NA, 5d=NA, 20d=NA); 沪银主连价格下跌触发商品冲击
- Query `000630` 2026-06-10T00:00:00 commodity_shock: matched `000630` 2026-05-20T00:00:00 commodity_shock score=0.678, same_symbol=True, returns=(1d=-2.36%, 5d=9.12%, 20d=NA); 沪银主连价格下跌触发商品冲击
- Query `000630` 2026-06-09T00:00:00 commodity_shock: matched `000630` 2026-03-09T00:00:00 commodity_shock score=0.695, same_symbol=True, returns=(1d=0.55%, 5d=-8.65%, 20d=-20.05%); 沪银主连价格下跌触发商品冲击
- Query `000630` 2026-06-09T00:00:00 commodity_shock: matched `000630` 2026-06-08T00:00:00 commodity_shock score=0.692, same_symbol=True, returns=(1d=NA, 5d=NA, 20d=NA); 沪银主连价格下跌触发商品冲击
- Query `000630` 2026-06-09T00:00:00 commodity_shock: matched `000630` 2026-02-02T00:00:00 commodity_shock score=0.665, same_symbol=True, returns=(1d=5.38%, 5d=-3.09%, 20d=-1.61%); 沪银主连价格下跌触发商品冲击
- Query `000630` 2026-06-09T00:00:00 commodity_shock: matched `000630` 2026-02-09T00:00:00 commodity_shock score=0.665, same_symbol=True, returns=(1d=-1.39%, 5d=4.16%, 20d=-8.60%); 沪银主连价格下跌触发商品冲击
- Query `000630` 2026-06-09T00:00:00 commodity_shock: matched `000630` 2026-04-09T00:00:00 commodity_shock score=0.664, same_symbol=True, returns=(1d=-0.16%, 5d=3.61%, 20d=12.95%); 沪银主连价格下跌触发商品冲击
- Query `000630` 2026-06-08T00:00:00 commodity_shock: matched `000630` 2026-03-25T00:00:00 commodity_shock score=0.661, same_symbol=True, returns=(1d=-2.20%, 5d=1.18%, 20d=6.60%); 沪金主连价格下跌触发商品冲击
- Query `000630` 2026-06-08T00:00:00 commodity_shock: matched `000630` 2026-03-23T00:00:00 commodity_shock score=0.651, same_symbol=True, returns=(1d=3.94%, 5d=5.90%, 20d=15.38%); 沪金主连价格下跌触发商品冲击
- Query `000630` 2026-06-08T00:00:00 commodity_shock: matched `000630` 2026-03-20T00:00:00 commodity_shock score=0.629, same_symbol=True, returns=(1d=-6.21%, 5d=-1.68%, 20d=9.40%); 沪金主连价格下跌触发商品冲击
- Query `000630` 2026-06-08T00:00:00 commodity_shock: matched `000630` 2026-03-19T00:00:00 commodity_shock score=0.626, same_symbol=True, returns=(1d=-1.97%, 5d=-4.93%, 20d=5.76%); 沪金主连价格下跌触发商品冲击
- Query `000630` 2026-06-08T00:00:00 commodity_shock: matched `000630` 2024-06-11T00:00:00 commodity_shock score=0.624, same_symbol=True, returns=(1d=0.27%, 5d=-4.29%, 20d=0.80%); 沪金主连价格下跌触发商品冲击
- Query `000630` 2026-06-08T00:00:00 commodity_shock: matched `000630` 2026-04-02T00:00:00 commodity_shock score=0.704, same_symbol=True, returns=(1d=-1.37%, 5d=4.46%, 20d=11.49%); 沪银主连价格下跌触发商品冲击
- Query `000630` 2026-06-08T00:00:00 commodity_shock: matched `000630` 2026-04-29T00:00:00 commodity_shock score=0.697, same_symbol=True, returns=(1d=-2.84%, 5d=8.69%, 20d=7.74%); 沪银主连价格下跌触发商品冲击
- Query `000630` 2026-06-08T00:00:00 commodity_shock: matched `000630` 2026-03-18T00:00:00 commodity_shock score=0.697, same_symbol=True, returns=(1d=-6.46%, 5d=-9.08%, 20d=-2.77%); 沪银主连价格下跌触发商品冲击
- Query `000630` 2026-06-08T00:00:00 commodity_shock: matched `000630` 2026-01-08T00:00:00 commodity_shock score=0.691, same_symbol=True, returns=(1d=3.68%, 5d=7.54%, 20d=26.14%); 沪银主连价格下跌触发商品冲击
- Query `000630` 2026-06-08T00:00:00 commodity_shock: matched `000630` 2026-05-15T00:00:00 commodity_shock score=0.682, same_symbol=True, returns=(1d=-2.25%, 5d=2.25%, 20d=NA); 沪银主连价格下跌触发商品冲击

## Guardrails

- Matches are restricted to events published before the query event.
- Forward returns are omitted when they would not have been known at query time.
- Retrieval evidence is not a trading signal.
