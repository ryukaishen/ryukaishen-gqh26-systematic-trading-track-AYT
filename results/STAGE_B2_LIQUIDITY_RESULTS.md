# Stage B2 acquisition and liquidity results

Status: Acquisition and operational liquidity screen completed; historical-reference acquisition blocked by remaining request budget. Stage C not executed.
Acquisition start UTC: 2026-10-04T03:41:16.845761+00:00

## Prospective amendment

EXPERIMENT.md A3 and DATA_AUDIT.md record the explicit user-authorized replacement of unavailable FMP EOD Bulk with Massive grouped daily, adjusted=false, before any strategy returns were inspected. No FMP EOD retry occurred. Massive grouped volume may include extended-hours activity, so unadjusted close × volume is an operational approximation to the originally stated regular-session dollar-volume measure. It can change membership and is disclosed prospectively rather than represented as verified regular-session volume.

Thresholds remain exactly previous unadjusted close ≥$10 and median close × volume over all preceding 20 completed exchange sessions ≥$20M, with all 20 observations required. No other hypothesis, signal, split, outcome, cost, feasibility or holdout rule was changed.

## Acquisition

All 710 required exchange-session dates from 2023-03-06 through 2025-12-31 completed. 708 new Massive requests; two cached pilot files (2023-06-30 and 2025-12-31) were hash-verified and reused. No retries, redirects or pagination expansions. Each response was checked for adjusted=false, complete record count, nonempty required-session data and absence of pagination. Only symbol/date/close/volume were retained in the new daily extracts; no adjClose or outcome fields.

New response-body bytes: **789,192,653**.
Cumulative Stage B usage, including FMP Stage B1, all three Massive pilot calls and the failed FMP EOD call: **1,005 requests and 856,847,804 bytes**.
Remaining allowance: **495 requests and 3,143,152,196 bytes** under the 1,500-request / 4 GB ceilings. These are response-body acquisition bytes, not raw header overhead or storage size.

Daily records and sanitized hashed manifest: `data/raw/massive_grouped_stage_b2/`.

## Screen and actual counts

Candidate population: exact-deduplicated FMP bmo/amc symbol/date pairs from the retained development calendar. Do not use this time-filtered subset as the denominator of a later representative timing-coverage audit. Original unfiltered Stage B1 files remain unchanged.

Map FMP bmo/amc to D using the bounded verified exchange calendar, retaining early closes as sessions and the 2025-01-09 special closure. Evaluate liquidity before loading each D's EOD file, using only its 20 strictly preceding completed sessions. Missing or invalid bars and duplicate-symbol rows fail the full-history requirement. No prices from D or subsequent sessions enter that candidate's screen. Use Decimal arithmetic and inclusive threshold comparisons.

| Stage/reason | Candidate events |
|---|---:|
| Timed deduplicated FMP input | 148,532 |
| Conflicting timing, excluded | 1 |
| Entry session outside development scope | 2 |
| Missing/invalid prior-session bar | 91,169 |
| Previous close below $10 | 23,546 |
| Median 20-session close × volume below $20M | 17,234 |
| Liquidity survivors | **16,580** |

Sequential reasons are mutually exclusive and reconcile exactly to the input count. Foreign or non-common-stock calendar candidates can fail price coverage or remain among provisional survivors; security type/locale/issuer validation is still required.

| Development split | Liquidity-surviving events |
|---|---:|
| Train | **10,017** |
| Validation | **6,563** |

**2,201 unique symbols**, across **618 distinct entry sessions**; maximum 199 surviving symbols on one session. These are provisional symbol/date liquidity candidates, not verified original quarterly events or an issuer-deduplicated primary universe. Fiscal-period mapping, then-listed common-stock validation, issuer/share-class consolidation and ten-session boundary purging remain pending. No full timestamp/feasibility gate is marked passed.

Saved outputs:
- `data/cache/stage_b2/liquidity_survivors.jsonl`
- `data/cache/stage_b2/liquidity_attrition.jsonl`
- `data/cache/stage_b2/liquidity_summary.json`
- `data/cache/stage_b2/reference_estimate.json`

## Remaining historical-reference estimate and Stage C decision

The official all-ticker route supports historical date queries and up to 1,000 records/page:
https://massive.com/docs/rest/stocks/tickers/all-tickers

For validation at every surviving entry-session date, an idealized bulk query would require at least **618 date-specific requests**, even assuming each page contains only the candidate symbols and no additional records. Actual broad all-ticker pages include other securities and may require multiple pages, plus inactive/delisting reconciliation and ticker-change/issuer/fiscal metadata. The ideal subtotal already exceeds the **495 remaining requests**; cumulative usage would reach at least **1,623** before those additions.

Direct ticker/date validation would need 16,580 requests. One snapshot per unique symbol would need 2,201 requests and would not establish historical validity at all event dates. These are reference-plan alternatives, not automatic requests or a universal lower bound for every conceivable source. A smaller plan based on documented validity intervals or an existing trusted historical reference dataset could reduce work, but cannot be assumed from a current snapshot or infrequent anchors.

No reference requests were executed after screening, and no Stage C options requests were made. The selected date-specific reference approach is outside budget. Stop rather than omit survivors, assume historical status, or use current membership to force a fit. Proceed toward Stage C only after a defensible within-budget historical-reference plan or an explicitly revised request cap, with the original chain/timestamp/schema/option-selection and spending prerequisites still in force.

## Verification and safeguards

Offline fixture checks passed for equality at both thresholds, all-20-session missingness, timing conflict exclusion and absence of D-EOD leakage. All daily extract hashes were rechecked during screening. Acquisition dates/status, actual caps and full attrition reconciliation were checked after completion; no additional tests or provider probes were needed.

No holdout data or 2026 observations were queried. No post-entry returns/P&L, reactions, X, signals, regression outcomes, performance rankings or backtest were calculated. Daily prices were used solely for the authorized historical liquidity screen. No packages, GPUs or Slurm jobs were launched.
