# Similar Event Evidence Report

This report retrieves earlier structured events that resemble recent query events. It is an explanation layer only: it does not issue buy/sell advice and cannot promote a forecast to `trusted` without walk-forward evidence.

## Summary

- Symbol: `601899`
- Query events: `5`
- Matches: `25`
- Retrieval model: `tfidf_char_cosine_with_jaccard_fallback`
- PIT policy: candidate events must be earlier than query events; forward returns require the return window to end before query time

## Historical Outcomes

- 1d known rows: `23`, mean=-0.1329%, positive_rate=43.48%
- 5d known rows: `17`, mean=0.0619%, positive_rate=47.06%
- 20d known rows: `17`, mean=2.8528%, positive_rate=64.71%

## Top Matches

- Query `601899` 2026-06-10T00:00:00 commodity_shock: matched `601899` 2026-03-23T00:00:00 commodity_shock score=0.643, same_symbol=True, returns=(1d=5.30%, 5d=7.19%, 20d=16.61%); 沪金主连价格下跌触发商品冲击
- Query `601899` 2026-06-10T00:00:00 commodity_shock: matched `601899` 2026-06-08T00:00:00 commodity_shock score=0.635, same_symbol=True, returns=(1d=1.50%, 5d=NA, 20d=NA); 沪金主连价格下跌触发商品冲击
- Query `601899` 2026-06-10T00:00:00 commodity_shock: matched `601899` 2025-04-23T00:00:00 commodity_shock score=0.634, same_symbol=True, returns=(1d=-0.67%, 5d=-1.85%, 20d=4.33%); 沪金主连价格下跌触发商品冲击
- Query `601899` 2026-06-10T00:00:00 commodity_shock: matched `601899` 2024-06-11T00:00:00 commodity_shock score=0.631, same_symbol=True, returns=(1d=1.24%, 5d=-0.47%, 20d=10.71%); 沪金主连价格下跌触发商品冲击
- Query `601899` 2026-06-10T00:00:00 commodity_shock: matched `601899` 2026-03-25T00:00:00 commodity_shock score=0.628, same_symbol=True, returns=(1d=-3.46%, 5d=2.74%, 20d=3.49%); 沪金主连价格下跌触发商品冲击
- Query `601899` 2026-06-09T00:00:00 general_news: matched `601899` 2026-06-06T00:00:00 general_news score=1.000, same_symbol=True, returns=(1d=NA, 5d=NA, 20d=NA); 紫金矿业集团股份有限公司第九届董事会临时会议决议公告
- Query `601899` 2026-06-09T00:00:00 general_news: matched `601899` 2026-05-09T00:00:00 general_news score=1.000, same_symbol=True, returns=(1d=0.90%, 5d=-8.67%, 20d=-18.15%); 紫金矿业集团股份有限公司第九届董事会临时会议决议公告
- Query `601899` 2026-06-09T00:00:00 general_news: matched `601899` 2026-03-21T00:00:00 general_news score=0.776, same_symbol=True, returns=(1d=5.30%, 5d=7.19%, 20d=16.61%); 紫金矿业集团股份有限公司第九届董事会第二次会议决议公告
- Query `601899` 2026-06-09T00:00:00 general_news: matched `601899` 2026-04-22T00:00:00 general_news score=0.768, same_symbol=True, returns=(1d=-3.18%, 5d=-3.91%, 20d=-11.76%); 紫金矿业集团股份有限公司第九届董事会第三次会议决议公告
- Query `601899` 2026-06-09T00:00:00 general_news: matched `601899` 2026-03-21T00:00:00 general_news score=0.565, same_symbol=True, returns=(1d=5.30%, 5d=7.19%, 20d=16.61%); 紫金矿业集团股份有限公司2025年年度报告
- Query `601899` 2026-06-09T00:00:00 commodity_shock: matched `601899` 2026-06-04T00:00:00 commodity_shock score=0.701, same_symbol=True, returns=(1d=-2.34%, 5d=NA, 20d=NA); 碳酸锂主连价格下跌触发商品冲击
- Query `601899` 2026-06-09T00:00:00 commodity_shock: matched `601899` 2026-03-13T00:00:00 commodity_shock score=0.692, same_symbol=True, returns=(1d=-2.85%, 5d=-11.52%, 20d=-5.90%); 碳酸锂主连价格下跌触发商品冲击
- Query `601899` 2026-06-09T00:00:00 commodity_shock: matched `601899` 2026-04-16T00:00:00 commodity_shock score=0.691, same_symbol=True, returns=(1d=-1.61%, 5d=-2.55%, 20d=-11.73%); 碳酸锂主连价格上涨触发商品冲击
- Query `601899` 2026-06-09T00:00:00 commodity_shock: matched `601899` 2026-02-09T00:00:00 commodity_shock score=0.683, same_symbol=True, returns=(1d=0.47%, 5d=1.79%, 20d=-9.66%); 碳酸锂主连价格上涨触发商品冲击
- Query `601899` 2026-06-09T00:00:00 commodity_shock: matched `601899` 2026-06-03T00:00:00 commodity_shock score=0.679, same_symbol=True, returns=(1d=-2.97%, 5d=NA, 20d=NA); 碳酸锂主连价格下跌触发商品冲击
- Query `601899` 2026-06-08T00:00:00 commodity_shock: matched `601899` 2026-06-02T00:00:00 commodity_shock score=0.708, same_symbol=True, returns=(1d=-0.98%, 5d=NA, 20d=NA); 碳酸锂主连价格下跌触发商品冲击
- Query `601899` 2026-06-08T00:00:00 commodity_shock: matched `601899` 2026-06-05T00:00:00 commodity_shock score=0.708, same_symbol=True, returns=(1d=NA, 5d=NA, 20d=NA); 碳酸锂主连价格下跌触发商品冲击
- Query `601899` 2026-06-08T00:00:00 commodity_shock: matched `601899` 2026-06-04T00:00:00 commodity_shock score=0.684, same_symbol=True, returns=(1d=-2.34%, 5d=NA, 20d=NA); 碳酸锂主连价格下跌触发商品冲击
- Query `601899` 2026-06-08T00:00:00 commodity_shock: matched `601899` 2026-01-28T00:00:00 commodity_shock score=0.683, same_symbol=True, returns=(1d=2.72%, 5d=-7.42%, 20d=-10.95%); 碳酸锂主连价格下跌触发商品冲击
- Query `601899` 2026-06-08T00:00:00 commodity_shock: matched `601899` 2026-06-03T00:00:00 commodity_shock score=0.672, same_symbol=True, returns=(1d=-2.97%, 5d=NA, 20d=NA); 碳酸锂主连价格下跌触发商品冲击
- Query `601899` 2026-06-08T00:00:00 commodity_shock: matched `601899` 2026-03-25T00:00:00 commodity_shock score=0.667, same_symbol=True, returns=(1d=-3.46%, 5d=2.74%, 20d=3.49%); 沪金主连价格下跌触发商品冲击
- Query `601899` 2026-06-08T00:00:00 commodity_shock: matched `601899` 2026-03-23T00:00:00 commodity_shock score=0.657, same_symbol=True, returns=(1d=5.30%, 5d=7.19%, 20d=16.61%); 沪金主连价格下跌触发商品冲击
- Query `601899` 2026-06-08T00:00:00 commodity_shock: matched `601899` 2026-03-20T00:00:00 commodity_shock score=0.635, same_symbol=True, returns=(1d=-3.38%, 5d=2.59%, 20d=10.02%); 沪金主连价格下跌触发商品冲击
- Query `601899` 2026-06-08T00:00:00 commodity_shock: matched `601899` 2026-03-19T00:00:00 commodity_shock score=0.631, same_symbol=True, returns=(1d=-2.07%, 5d=-0.71%, 20d=7.46%); 沪金主连价格下跌触发商品冲击
- Query `601899` 2026-06-08T00:00:00 commodity_shock: matched `601899` 2024-06-11T00:00:00 commodity_shock score=0.629, same_symbol=True, returns=(1d=1.24%, 5d=-0.47%, 20d=10.71%); 沪金主连价格下跌触发商品冲击

## Guardrails

- Matches are restricted to events published before the query event.
- Forward returns are omitted when they would not have been known at query time.
- Retrieval evidence is not a trading signal.
