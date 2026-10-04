# Stage B2 revised acquisition estimate

Date: 2026-10-03.
Status: Local filtering complete; estimate presented before any Massive download.

## Actual local counts

The completed Stage B1 manifest and each retained page hash were verified. All retained event dates are within 2023-04-03–2025-12-31. The extract contains 192,246 rows and 192,241 distinct symbol/date pairs. No outcome fields were read.

Filtering normalized time to bmo/amc and deduplicating exact symbol/date pairs yields:

- 148,534 qualifying source rows.
- 148,532 unique candidate pairs.
- 21,115 unique symbols.
- 914 unique event dates.
- 1 pair with conflicting bmo/amc values, explicitly flagged and not usable for session assignment until resolved.

Saved to data/cache/stage_b2/timed_candidates.jsonl. This subset is for acquisition/liquidity planning, not a timestamp-coverage denominator. The complete Stage B1 extract remains unchanged so missing-timing events cannot disappear from later coverage calculations. These are global calendar candidates, not yet verified U.S. common-stock original quarterly releases.

## Bulk daily acquisition estimate

Use `/v2/aggs/grouped/locale/us/market/stocks/{date}?adjusted=false&include_otc=false`, one request per required session, not per symbol or event. Official documentation: https://massive.com/docs/rest/stocks/aggregates/daily-market-summary

Planning date envelope: 2023-02-15–2025-12-31, providing a conservative pre-start lookback cushion for 20 completed sessions. Weekdays in this envelope give an upper bound of **751 requests**; verified exchange holidays should reduce it. A weekday planning list is saved in data/cache/stage_b2/grouped_weekday_bounds.json and is explicitly not a verified session calendar. No 2026 date is included. Candidate sessions outside development, including late-2025 after-close events mapping into 2026, must be excluded without querying holdout observations.

Projected daily response volume at an explicitly assumed 2,000,000 bytes/date: **1,502,000,000 bytes (1.502 GB)**. This assumption is not a measured response size or provider guarantee. Enforce actual cumulative bytes and requests at runtime and stop before any expansion. No retries, redirects, security-detail requests, or extra probes are included in this acquisition estimate.

Conservatively charging Stage B1 against the same caps:

| Item | Requests | Response bytes |
|---|---:|---:|
| Completed Stage B1 | 293 | 64,236,960 |
| Projected grouped daily upper bound | 751 | 1,502,000,000 |
| Cumulative projection | 1,044 | 1,566,236,960 |

Projected remaining allowance: **456 requests** and **433,763,040 bytes** for later reference/identity work, subject to actual daily usage. No per-event reference acquisition is planned before liquidity screening. Existing entitlement only; no subscription or purchase is authorized. Marginal monetary charges remain unverified.

## Frozen screening plan and subsequent reference estimate

For each non-conflicting candidate, determine D using a verified exchange calendar and FMP event-session classification. Require presence on the relevant pre-decision historical dates; presence in daily aggregates establishes trading observations only, not exchange-listed common-stock eligibility or stable issuer identity. Missing bars must not be replaced by the last 20 observed bars across absent sessions.

Use the previous completed session's unadjusted close ≥$10 and all 20 preceding completed regular-session dollar-volume observations, with median ≥$20M. Confirm grouped daily session semantics before treating close and volume as regular-session inputs. The cited endpoint documentation supplies daily OHLC, volume, and VWAP but does not itself resolve regular versus extended-session scope. Resolve this from authoritative provider evidence before claiming the preregistered filter is measured. Any unresolved scope must be reported, not silently substituted. Document a consistent dollar-volume calculation before filtering; no price reaction, future liquidity filter, or return calculation is permitted.

Only after screening, report survivor event and unique-symbol counts and estimate historical security-reference calls using surviving symbols and necessary historical dates/change intervals. Reusing one historical snapshot across dates requires defensible validity evidence; no present-day type/identifier substitution is allowed. The exact security-reference count cannot be known before the bulk screen. It must fit the remaining actual budget or stop before those requests.

The full daily files are acquired solely for historical universe filters. Do not calculate post-entry returns/P&L, signals, or strategy outcomes from them. Retain only required aggregate identity/date, close, volume and documented dollar-volume inputs. Holdout remains untouched.

## Current decision

The bulk-only projection is within 1,500 requests / 2 GB. It does not assert the later reference work fits. Per the user's instruction to show the estimate first, no Massive download has occurred in this turn. No liquidity-survivor count or timestamp-gate pass is asserted. No hypothesis, threshold, split, holding period, or outcome rule changed.
