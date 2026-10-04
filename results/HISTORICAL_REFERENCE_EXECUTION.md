# Historical-reference execution results

Date: 2026-10-04.
Status: Authorized bulk snapshots completed; full reference validation blocked by interval-evidence and request-budget constraints. No Stage C requests.

## Execution and budget

Executed the approved 34 development-only historical common-stock anchors using `/v3/reference/tickers`, market=stocks, locale=us, type=CS, active=true, date=anchor, limit=1000, sort=ticker, order=asc. Each anchor completed in six pages, below its eight-page cap, with every page below 1,000,000 bytes. Pagination was restricted to the expected HTTPS host/path, credential parameters removed, original date/filter scope preserved and response fields checked. No retries, redirects, unsupported filter substitutions or silently truncated snapshots.

Actual acquisition: **204 requests / 51,802,819 response-body bytes**. All 34 snapshots are complete. Cumulative Stage B acquisition: **1,209 requests / 908,650,623 bytes**. Remaining: **291 requests / 3,091,349,377 bytes** under 1,500 requests / 4 GB. No extra event-history, inactive, statement/SEC or options calls were made after the budget blocker was established.

Raw allowlisted reference pages and hashed manifest: `data/raw/historical_reference/`.

## Resulting counts and evidence strength

Input retains all possibly liquidity-eligible candidates, including missing timing: **16,619 symbol/date pairs / 2,207 symbols**. No current-survival filter or timed-only denominator substitution.

| Reference status | Candidate pairs |
|---|---:|
| Exact entry-date common-stock status and identifiers supported | **893** |
| Not present in the complete common-stock snapshot on their eligible entry date(s) | 41 |
| Unresolved historical interval or missing identifiers | **15,685** |
| Total | **16,619** |

Exact-date supported subset: **591 unique symbols**, 577 train pairs and 316 validation pairs. These records establish provider common-stock/type/locale/exchange and CIK/FIGI at their actual candidate entry date; they do not independently verify original quarterly release timing or historical vendor availability.

Applying available FMP fiscalYear/fiscalPeriod to this exact-reference subset produces **893 provisional issuer/fiscal-year/fiscal-quarter groups**. Fiscal metadata corroboration and original-release identification remain pending; this is not a final primary event count.

For descriptive reconciliation only, unique-CIK associations observed at anchors map **15,570 candidate pairs / 2,034 symbols** to **15,526 provisional issuer/fiscal-year/fiscal-quarter groups**. **44 groups** contain multiple symbol/date candidates. Group members are retained rather than choosing a later update, preferred timing or earliest date as the original release without evidence. Matching snapshot identifiers are not treated as historical intervals. These groups are not promoted into the primary universe.

Exception flags across candidate symbols (overlapping categories): 151 absent at all anchors; 336 absent at some anchors; 53 with changing identifier fingerprints; 22 with changing issuer CIK; 54 with missing identifiers on an exact queried entry date. Absent anchors never justify excluding an intervening event. Conflicting fiscal/timing rows remain unresolved and no latest-lastUpdated rule is applied.

Outputs:
- data/cache/historical_reference/candidate_reference_status.jsonl
- data/cache/historical_reference/provisional_issuer_fiscal_groups.jsonl
- data/cache/historical_reference/exact_date_issuer_fiscal_groups.jsonl
- data/cache/historical_reference/summary.json

## Hard blocker and stop decision

The acquired snapshots have point-in-time observations, not documented continuous validity intervals. The approved plan explicitly prohibits inferring uninterrupted common-stock status or ticker ownership from matching anchors, trading continuity, CIK consistency or last_updated timestamps.

Provider documentation for the experimental ticker-events endpoint states that ticker_change is the only supported event type. This could assist symbol-history reconciliation but does not certify complete common-stock/type/listing validity intervals; no request was issued merely to obtain a ticker-change timeline that cannot resolve the prerequisite:
https://massive.com/docs/rest/stocks/corporate-actions/ticker-events?assetClass=stocks&display=all&license=personal

There are **15,719 unresolved symbol/session combinations across 604 entry dates**. A date-specific fallback needs at least **604 additional calls** even in an ideal one-page-per-date scenario, beyond the **291 remaining**. The cumulative lower estimate is **1,813 requests**, before further pages, fiscal-period corroboration, inactive/delisting reconciliation or options work. Missing-ID cases may require additional targeted evidence; the optimistic estimate is not a completeness guarantee.

Therefore full historically validated common-stock/issuer/fiscal-period deduplication cannot be claimed under this plan and current remaining request budget. Stop under the plan's explicit hard-blocker rule. Do not issue blanket per-event calls, spend the remaining budget on a knowingly incomplete fallback, exclude unresolved candidates or infer snapshot intervals to force coverage. No final eligible primary event/symbol count is asserted. A trusted effective-date history source or revised acquisition budget is needed to finish the unresolved reference work.

## Timing and Stage C status

The local operational FMP bmo/amc gate remains **passed**: train conservative coverage ≥99.751046%; validation 99.787137%. Full historical release timestamp/vintage verification is still **unproven**. Reference incompleteness does not relabel that operational timing gate as failed or promote it into full timestamp feasibility.

Stage C was not started because reference coverage is insufficient under the approved rules. Original historical options-chain semantics, pre-event spot/quote requirements and Databento entitlement/timestamp/cost gates also remain in force. No signal, hypothesis, split, purging rule, threshold or outcome rule changed.

## Verification and safeguards

All retained page hashes were verified during reconciliation. Snapshot ticker uniqueness, field scope, cap usage and exact candidate-status reconciliation were checked. Pagination tests rejected wrong-host and changed-date links without network calls. No tests calculated market returns.

No holdout observations, 2026 event/reference snapshots, post-entry returns/P&L, reactions, X, backtest or strategy outcomes were accessed. No raw credentials, raw headers, raw responses or credential-bearing pagination URLs were printed or persisted. No package installation, GPU request or Slurm job was launched.
