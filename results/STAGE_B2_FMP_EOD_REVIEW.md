# Stage B2 FMP EOD Bulk source review

Date: 2026-10-03 (project local date).
Status: Replacement source authorized; documentation/budget gates not satisfied; no EOD Bulk acquisition executed.

## Prospective source selection

The user replaced Massive grouped daily with FMP `/stable/eod-bulk?date=YYYY-MM-DD` for Stage B2 liquidity acquisition only. Massive remains the historical reference, corporate-action and stock-quote source; Databento remains the options source. This source selection occurred before any strategy-return inspection. Every hypothesis, signal, split, holdout and outcome rule remains unchanged. The user specified daily dollar volume as unadjusted close × volume; preserve ≥$10 previous close, ≥$20M median over all preceding 20 completed regular sessions, and no shortened or missing-session history.

If acquisition becomes permissible, retain only symbol, date, unadjusted close and volume, rejecting and counting out-of-request dates without persisting them. Never substitute adjClose or retain changes/returns or other outcomes. Preserve original FMP earnings extracts so the timing-filtered liquidity subset cannot replace the eventual coverage denominator. The conflicting pair is already flagged and cannot supply session assignment.

## Documentation findings

FMP EOD Bulk documentation:
https://site.financialmodelingprep.com/developer/docs/stable/eod-bulk
https://site.financialmodelingprep.com/developer/docs

The endpoint is described as bulk end-of-day stock price data. Its documented CSV schema includes symbol, date, open, high, low, close, adjClose and volume. The separate close/adjClose fields support selecting close rather than adjusted close, but the consulted endpoint description does not explicitly establish raw historical share-basis semantics for both close and volume or exclusive regular-session volume.

FMP FAQ:
https://site.financialmodelingprep.com/faqs
https://site.financialmodelingprep.com/it/faqs?code=marketPerformance

The FAQ says EOD data updates after market close. Its separate statement that Quote API updates during regular hours applies to Quote API and cannot establish EOD Bulk volume session scope. After-close update timing alone is not a definition of included trade hours. Consequently the regular-session suitability condition requested by the user remains unresolved, not verified or disproven.

## Published size estimate and cumulative cap

The provider FAQ estimates approximately 4 MB of bandwidth per EOD Bulk file. This is provider bandwidth accounting, not a measured response-body size or precise transport-byte quote. It is the available planning estimate; no compression assumption is used to force the acquisition under the cap.

Existing measured acquisition: 293 FMP calendar requests plus three Massive pilot requests = 296 requests and 67,654,974 response-body bytes.

At the approved planning upper bound of 751 dates:

- FMP EOD Bulk projection: 751 requests × approximately 4,000,000 bytes = 3,004,000,000 bytes.
- Cumulative projected requests: 1,047, under 1,500.
- Cumulative projected bytes: 3,071,654,974, above 2,000,000,000.
- At this estimate, at most 483 bulk files fit the remaining byte allowance. Omitting required sessions to fit that allowance would violate the screen and is not proposed.

This is an estimate, not a claim that actual transfer must exceed the cap. Verified trading dates may reduce the 751-weekday envelope, but no documented within-cap full-period acquisition is established. A measured transfer/compression plan could refine the estimate, subject to the same caps and session verification. No such extra probe was automatically added.

## Decision

Do not execute the full acquisition: both explicit regular-session suitability and a within-cap full-acquisition estimate are outstanding. No liquidity survivor count or historical-reference request count can be computed from this unacquired source. No gate is marked passed. No FMP EOD, Massive reference or options request was executed in this task. No holdout observations or post-entry return/P&L calculations were accessed; no packages or compute jobs were launched.
