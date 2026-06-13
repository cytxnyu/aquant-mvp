# Source Gap Report

This report separates implemented or partially implemented sources from sources that still need direct adapters, credentials, endpoint calibration, or non-free authorization. Missing sources are explicit gaps and must not be fabricated in event factors.

## Group Summary

| source_group | sources | ready_sources | critical_gaps | followup_sources |
| --- | ---: | ---: | ---: | --- |
| macro_policy | 6 | 6 | 5 | ndrc_public;miit_public;mofcom_public;pbc_public;customs_public |
| exchange_regulator | 3 | 3 | 2 | sse_public;szse_public |
| broker_readonly | 1 | 0 | 1 | qmt_readonly |
| multi_source_data | 2 | 1 | 1 | tushare_free |
| regulator_policy | 1 | 1 | 1 | csrc_public |
| announcement | 2 | 2 | 0 | none |
| commodity_exchange | 6 | 3 | 0 | none |
| market_data | 1 | 1 | 0 | none |
| news_capital_flow | 4 | 1 | 0 | none |

## Critical Follow-Up Sources

- `sse_public` (exchange_regulator, implemented_official_index_adapter): official SSE index-page adapter implemented with bounded generic pagination and optional body text audit; site-specific pagination calibration and structured regulatory fields still need expansion
- `szse_public` (exchange_regulator, implemented_official_index_adapter): official SZSE index-page adapter implemented with bounded generic pagination and optional body text audit; site-specific pagination calibration and structured regulatory-letter fields still need expansion
- `csrc_public` (regulator_policy, implemented_official_index_adapter): official CSRC index-page adapter implemented with bounded generic pagination and optional body text audit; site-specific pagination calibration and penalty/policy field extraction still need expansion
- `qmt_readonly` (broker_readonly, readonly_adapter_live_blocked): requires local MiniQMT/XtQuant and broker account; no live submit in this project
- `customs_public` (macro_policy, implemented_official_index_adapter): official customs index-page adapter implemented with bounded generic pagination and optional body text audit; site-specific pagination calibration and monthly import/export PIT fields still need expansion
- `miit_public` (macro_policy, implemented_official_index_adapter): official MIIT index-page adapter implemented with bounded generic pagination and optional body text audit; site-specific pagination calibration and industry-policy fields still need expansion
- `mofcom_public` (macro_policy, implemented_official_index_adapter): official MOFCOM index-page adapter implemented with bounded generic pagination and optional body text audit; site-specific pagination calibration and trade-policy fields still need expansion
- `ndrc_public` (macro_policy, implemented_official_index_adapter): official NDRC index-page adapter implemented with bounded generic pagination and optional body text audit; site-specific pagination calibration and PIT release calendar still need expansion
- `pbc_public` (macro_policy, implemented_official_index_adapter): official PBC index-page adapter implemented with bounded generic pagination and optional body text audit; site-specific pagination calibration and structured liquidity-operation fields still need expansion
- `tushare_free` (multi_source_data, implemented_if_token_ready): free quota and fields vary by token score; token required

## Rule

A source may influence stock-level event factors only when it has timestamps, source URLs, entity links, and an implemented or explicitly partial adapter. Otherwise it stays in the gap report.