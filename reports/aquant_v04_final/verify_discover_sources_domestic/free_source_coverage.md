# Free Domestic Source Coverage

| source | installed | credential_ready | tables | PIT | limitations |
| --- | --- | --- | --- | --- | --- |
| akshare | True | True | daily_bar,minute_bar,industry,concept,moneyflow,northbound,dragon_tiger,announcement_proxy | partial | public endpoints can fail or change schema; PIT metadata is incomplete |
| baostock | True | True | daily_bar,adj_factor,st_flag,suspension_proxy,trade_calendar,index_member,financial | partial | requires login session; no full announcement text; minute data unavailable |
| tushare_free | True | False | stock_basic,trade_calendar,daily_bar,financial,margin,index_member,delist | partial | free quota and fields vary by token score; token required |
| cninfo | True | True | announcement,annual_report,financial_report_pdf | announce_date_available | PDF/HTML parsing is noisy; structured fields need extraction |
| eastmoney_public | True | True | moneyflow,concept,sector,valuation_proxy,northbound_proxy | partial | unofficial endpoints can change; historical depth varies |
| qmt_readonly | True | True | quote,account,position,order,trade,reconcile | runtime_snapshot | requires local MiniQMT/XtQuant and broker account; no live submit in this project |

This report is a capability map, not a guarantee of endpoint availability on a given day.