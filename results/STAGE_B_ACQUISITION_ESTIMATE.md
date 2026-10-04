# Stage B acquisition projection — stopped at request ceiling

Date: 2026-10-03.
Status: Planning completed; no provider data acquired.
Authority: User authorized construction of development-only inputs, with a mandatory stop if projected acquisition exceeds 1,500 requests or 2 GB.

## Scope and candidate calendar manifest

Development event-date acquisition is restricted to 2023-04-03 through 2025-12-31 inclusive. No 2026 event observations, holdout observations, or post-entry return/P&L calculations are authorized. The newer user instruction permits daily prices/volume solely for historical universe screens and pagination restricted to development dates; it supersedes the earlier timing-only prohibition on loading prices for this purpose.

Proposed FMP endpoint: https://financialmodelingprep.com/stable/earnings-calendar
Parameters per window: from, to, page starting at 0, includeReportTimes=true. Authentication is omitted. Pagination completeness and page-size semantics still require confirmation before an executable manifest can be finalized. These windows are a plan, not executed requests.

| Window | from | to |
|---|---|---|
| 1 | 2023-04-03 | 2023-07-01 |
| 2 | 2023-07-02 | 2023-09-29 |
| 3 | 2023-09-30 | 2023-12-28 |
| 4 | 2023-12-29 | 2024-03-27 |
| 5 | 2024-03-28 | 2024-06-25 |
| 6 | 2024-06-26 | 2024-09-23 |
| 7 | 2024-09-24 | 2024-12-22 |
| 8 | 2024-12-23 | 2025-03-22 |
| 9 | 2025-03-23 | 2025-06-20 |
| 10 | 2025-06-21 | 2025-09-18 |
| 11 | 2025-09-19 | 2025-12-17 |
| 12 | 2025-12-18 | 2025-12-31 |

Retain only symbol, date, time, lastUpdated, and permitted non-outcome identity fields. Never persist EPS, revenue, estimates, or surprises. Do not assume fiscalDateEnding exists. Deduplicate through historical issuer and documented fiscal-period metadata after universe filtering, not through usable timing.

## Request projection

The documented Massive historical detail route is `/v3/reference/tickers/{ticker}?date=YYYY-MM-DD`, one ticker/date per request. A direct candidate-date mapping plan needs approximately one request per distinct candidate symbol/date. Successful historical mapping must establish common-stock type, U.S. market/locale, exchange, stable issuer/security identifiers, listing status and delisting provenance. Current reference snapshots cannot substitute for historical mapping.

Because the candidate extract has not been acquired, distinct symbols and candidate dates are unknown. The following is an explicitly assumed planning scenario, not an observed count, lower bound, or claim of representative coverage:

- 500 distinct candidate symbols.
- Eight candidate event dates per symbol over the approximately 2.75-year period.
- 4,000 historical ticker/date mapping requests.
- 500 ticker-specific daily-data requests as an optimistic batching scenario; historical ticker changes or session restrictions can require more.
- At least 12 initial FMP window requests; pagination adds requests.
- Fiscal-period/statement or SEC metadata acquisition and separate delisting reconciliation: unpriced additional requests.

Projected total: **at least 4,512 requests in this scenario**, excluding pagination and fiscal-period/delisting additions. This exceeds the 1,500-request ceiling. With 12 FMP requests and no other acquisition, only 1,488 distinct candidate-date mapping requests fit the ceiling; allowing 500 daily requests reduces that allowance to 988. No claim is made that the actual denominator exceeds either number.

The existing four exact-day FMP responses contain 1,469 calendar records and 488,039 bytes, averaging 332.23 response bytes per row. They are fixed, nonrepresentative days containing unfiltered calendar rows. Their mean of 367.25 rows/day must not be treated as an estimate of eligible U.S. quarterly events.

## Byte projection

For a transparent coarse planning scenario, applying that observed raw-row/day mean across 1,004 calendar days gives 368,719 raw calendar rows and approximately 122.50 MB of FMP response bodies. Weekend/seasonality effects and repeated rows make this highly uncertain; it is neither a confidence bound nor an eligible-event count.

Assumed 4,000 mapping responses at a conservative planning allowance of 15 KB each: 60 MB. Assumed 500 daily-history responses at 200 KB each: 100 MB. These allowances are not provider quotes or measured transfer volumes. Combined illustrative response volume is approximately **282.50 MB**, excluding pagination overhead, fiscal metadata and delisting reconciliation. The byte cap does not trigger in this scenario; the request cap does. Retained allowlisted extracts would be smaller than response bodies. Exact charges remain unverified; no purchase or subscription change is planned.

## Methodological limits to resolve before acquisition

Daily universe inputs may only support the previous unadjusted close and preceding 20 completed regular sessions. Fix the regular-session dollar-volume calculation before execution; generic aggregates must not silently include extended-hours observations. Do not use present-day split-adjusted histories for historical price eligibility. A continuous price history must not be inspected for reactions, holding-period returns, or performance.

The user's event-date lower bound omits releases before 2023-04-03 that could map to the first train entry session. Initial April events also require preceding-20-session history before that date. Such rows cannot silently be fabricated or replaced by shortened histories. Record these boundary limitations or obtain an explicit scope clarification before acquisition.

Fiscal-period mapping must use documented statement/SEC identity metadata, not invented fields or surprise/outcome data. Timing coverage remains unmeasured until the candidate universe and calendar assignment are defensible. Preserve lastUpdated for provenance without vintage claims.

## Decision and safeguards

**Stop before acquisition because projected requests exceed 1,500.** No FMP, Massive, SEC, or options acquisition requests were executed during this task; only official provider documentation was read and local planning calculations performed. No data/ candidate universe is claimed to exist. No coverage percentage was calculated and no timestamp gate was marked passed. Conditional Stage C was not started. No holdout observations or strategy returns were inspected; no packages or jobs were launched.

A future acquisition can proceed only with a revised authorized request budget or a documented batching/caching plan projected within the existing ceiling. No strategy or denominator rule was changed to force acquisition within budget.

## Documentation used

- https://www.massive.com/blog/new-point-in-time-tickers-api — historical date dimension for ticker details and all-ticker queries.
- https://massive.com/docs/rest/stocks/overview — historical ticker details and inactive-reference route.
- https://www.massive.com/docs/rest/stocks/aggregates/custom-bars — ticker-specific historical aggregates, adjustment control, and session semantics requiring care.
