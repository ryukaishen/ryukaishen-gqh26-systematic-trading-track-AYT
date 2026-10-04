# Stage A feasibility audit results

Date: 2026-10-03
Scope: Approved revised 15-request Stage A manifest only.
Status: Stage A completed; no continuation authorized or performed.

This run attempted all 15 approved requests: 9 succeeded, 1 was empty, 2 were entitlement-limited, and 3 were classified unsupported.

## Sanitized request results

| Request | Status | Sanitized result | Body bytes |
|---|---|---|---:|
| D1: schemas | Succeeded, HTTP 200 | `definition` and `cbbo-1m` advertised | 126 |
| D2: dataset range | Succeeded, HTTP 200 | Both required schemas advertise coverage from 2013-04-01 through 2026-10-03 | 1,201 |
| D3: definition fields | Succeeded, HTTP 200 | 64 fields, including identifiers, timestamps, activation, expiration, strike, and multiplier | 2,578 |
| D4: CBBO fields | Succeeded, HTTP 200 | 15 fields, including timestamps, bid/ask prices, displayed sizes, and flags | 496 |
| M1: MSFT earnings | Entitlement-limited, HTTP 403 | Earnings access not established | 167 |
| M2: AAPL earnings | Entitlement-limited, HTTP 403 | Earnings access not established | 167 |
| M3: historical active references | Succeeded, HTTP 200 | 3 records: A, AA, AAC; pagination present | 1,148 |
| M4: historical inactive references | Succeeded, HTTP 200 | 3 records: AABA, AACQ, AAI; pagination present | 1,223 |
| M5: historical MSFT details | Succeeded, HTTP 200 | 1 common-stock record with CIK and FIGI identifiers | 1,355 |
| M7: inactive TWTR reference | Succeeded, HTTP 200 | 1 inactive common-stock record with identifiers and delisting timestamp | 405 |
| M9: AAPL dividends | Empty, HTTP 200 | 0 records; absence of coverage is not established | 76 |
| M10: expired options | Succeeded, HTTP 200 | Call/put at strike 150, expiry 2023-05-05, 100 shares per contract; pagination present | 1,632 |
| A2-1: `expired` omitted | Unsupported, HTTP 400 | Exact query rejected; filter semantics unresolved | 110 |
| A2-2: `expired=false` | Unsupported, HTTP 400 | Exact query rejected; filter semantics unresolved | 110 |
| A2-3: `expired=true` | Unsupported, HTTP 400 | Exact query rejected; filter semantics unresolved | 110 |

Total response bodies: **10,904 bytes**. Massive returned **10 records**. No request reached its byte or record cap. No pagination was followed.

## Findings and limitations

Provider metadata supports advertised OPRA coverage spanning the required start date, but retrieval entitlement and quote timestamp semantics remain unverified. Dataset/schema range endpoints are provider-level metadata; no holdout observations were requested.

Massive earnings requests M1 and M2 returned HTTP 403 and were classified entitlement-limited. Earnings timestamp capability remains unresolved.

M9 returned a successful empty result. Dividend coverage remains unresolved; empty results alone do not establish absent coverage.

All three A2 requests returned HTTP 400 and were classified unsupported. Historical option-filter semantics remain unresolved. HTTP 400 does not identify which query parameter caused rejection.

M6 and M8 were not executed or replaced. Their intended then-listed delisted-security detail and historical split capabilities remain unresolved.

## Execution-history limitation

A previous attempted execution was aborted without output. Whether any requests from that attempt reached the providers is unknown; these 15 calls are not necessarily the only provider requests ever attempted. The totals above describe this completed run only.

## Safeguards

No Stage B–D requests or data acquisition, holdout observations, post-entry prices or returns, signal-performance analysis, backtest, package installations, GPU use, purchases, or subscription changes were performed in this run. No automatic pagination, retries, or request expansion occurred.

No Stage B–D data, holdout observations, returns, backtest results, credentials, raw headers, raw responses, Request objects, Authorization values, or raw exception objects were exposed. Authentication was constructed in process memory. No credentials or raw response/error material were printed or saved. Only sanitized allowlisted audit fields and statuses were reported.

Execution stopped after Stage A.
