# Exact-date reference execution under Amendment A4

Recorded at: 2026-10-04T00:19:27.018153-04:00
Status: Operational budget amendment recorded; hard blocker remains after bounded filter check. Exact-date completion, final event counts and Stage C are not achieved.

## Prospective amendment

EXPERIMENT.md A4 and DATA_AUDIT.md now authorize 2,500 cumulative acquisition requests, replacing 1,500, with the unchanged 4,000,000,000-byte ceiling. This is an operational budget change made before any strategy-return inspection. No hypothesis, signal, threshold, universe rule, split, holdout or outcome rule changed. The operational FMP bmo/amc gate remains passed; full historical timestamp/vintage verification remains unproven.

## Empirical exact-date acquisition estimate

The previously reported approximately 604 additional requests was explicitly an ideal one-page-per-date lower bound, not a full pagination estimate. Completed anchors actually contain 5,119–5,556 common-stock records each and require six 1,000-record pages. Full snapshots for 604 unresolved dates therefore project to 3,624 further requests.

A locally optimized greedy ticker comparison-range design, using the measured union of 6,983 historical anchor tickers and at most 900 observed reference records per range, projects to **2,771 further calls**. These ranges cover all 15,719 unresolved symbol/session combinations rather than choosing a favorable subset. The observed union estimates sizing only; no common-stock identity/status interval is inferred from it. Exact-date record changes and pagination may add requests. This is a practical projection, not a proof that every conceivable alternative source needs 2,771 requests.

Saved exact range scope: data/cache/historical_reference/exact_range_manifest.json.
Sizing evidence: data/cache/historical_reference/exact_range_estimate.json.

## Executed hard-blocker check

To test whether the exact-date work could fit one batch per date, executed exactly one bounded request against an already verified historical snapshot:

`GET /v3/reference/tickers?date=2023-04-03&market=stocks&locale=us&type=CS&active=true&limit=1000&sort=ticker&order=asc&ticker.any_of=AAPL,MSFT`

Bearer authentication existed only in memory. Expected: the two allowlisted historical identities already verified in the cached 2023-04-03 snapshot. Actual: **HTTP 200, 1,000 records, 289,094 response-body bytes**; returned scope did not match the two requested symbols. The multi-ticker filter is unsupported or ineffective for this exact endpoint/query. No returned out-of-scope records were persisted. No raw response, headers, key or pagination URL was displayed or saved. No retries, redirects or expansion occurred.

This was a targeted check prompted by the measured pagination budget blocker, not a new strategy/data-feasibility experiment. An ignored filter cannot be used as if it were a successful batch query, and a truncated first page cannot validate missing candidates.

## Current budget and hard stop

Actual cumulative acquisition: **1,210 requests / 908,939,717 bytes**. Remaining under A4: **1,290 requests / 3,091,060,283 bytes**.

The optimized range route projects to **3,981 cumulative requests**, above 2,500. The full-snapshot route projects to **4,834 cumulative requests**. The failed batch filter does not resolve that difference. Do not launch an acquisition projected to exceed the cap, use only first pages, spend the allowance on knowingly incomplete coverage, or exclude unresolved events to force completion.

Therefore no remaining full exact-date reference acquisition was executed. Completion needs a larger authorized request allowance or a supported historical batching/effective-date dataset. This is a hard acquisition blocker, not another discretionary planning approval loop.

## Counts and Stage C status

Previously acquired evidence is unchanged: 893 exact-entry-date common-stock/identifier-supported candidate pairs across 591 symbols; 15,685 reference-unresolved pairs; 41 absent from complete common-stock snapshots at their candidate dates. Exact-date vendor fiscal grouping produces 893 provisional issuer/year/quarter groups. Broader anchor associations produce 15,526 provisional groups, which are not a finalized historically valid quarterly-event universe. No final train/validation event count is claimed.

Issuer/fiscal metadata corroboration and original-release deduplication are not silently waived. Reference coverage remains insufficient; Stage C Databento options coverage was not executed. Original historical-chain/contract selection, quote/spot, schema/timestamp, entitlement and spending prerequisites remain in force.

No holdout observations, post-entry returns/P&L, reactions, X, outcomes or backtest were inspected. No package installation, GPU use or Slurm job occurred.
