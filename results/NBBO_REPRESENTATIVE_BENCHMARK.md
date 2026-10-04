# Representative pre-event NBBO benchmark

The proposed 2,100-event sampling amendment is paused/inactive. Its local hash artifact was created before the pause, but no sample acquisition started. The source population remains 14,340 operationally eligible events. No X, reactions, outcomes, post-entry returns or holdout were inspected.

Selection was prospective and outcome-blind: 10 train / 10 validation events across five equal-count chronological strata per split, one hashed event from each lower/upper pre-event liquidity half. Complete [15:50,15:55) ET windows were acquired sequentially, with a 50,000-record page limit and pagination enabled. All 20 responses were complete in one page; there were no out-of-window retained rows.

| Measurement | Train | Validation | Total |
|---|---:|---:|---:|
| Events | 10 | 10 | 20 |
| NBBO requests, including pagination | 10 | 10 | 20 |
| NBBO transferred bytes | 606,890 | 236,786 | 843,676 |
| End-to-end runtime (seconds) | 2.759 | 2.023 | 4.782 |
| Valid S0 success | 10/10 (100%) | 10/10 (100%) | 20/20 (100%) |

Two auxiliary quote-condition schema calls transferred 22,183 bytes: the initial `data_type=quote` filter returned an empty dictionary; the corrected all-stock dictionary identifies quote data as bbo/nbbo and code 1 as Regular Two-Sided Open. Including both schema calls, the benchmark used 22 Massive calls and 865,859 bytes. These are schema lookups, not historical security-reference acquisition. Valid S0 uses the median of all valid quote midpoints and at least three distinct SIP-timestamp minute bins. All 20 had five valid bins. Accept empty conditions or provider-labelled regular two-sided quotes; reject nonpositive prices/sizes, crossed/locked markets and unresolved nonregular conditions.

Transferred bytes count compressed HTTP response bodies when gzip is supplied, before decompression or sanitized re-storage. Runtime includes sequential retrieval, parsing, validity checks, storage and S0 calculation; excludes tool approval waiting and one-time condition lookup.

## Full 14,340-event projection

Weight each benchmark event by its chronological/liquidity stratum population, preserving actual 8,688 train / 5,652 validation population weights.

| Projection | Estimate | 1.5× sensitivity |
|---|---:|---:|
| NBBO requests including pagination | 14,340 | 21,510 |
| NBBO transfer | 0.661 GB | 0.991 GB |
| Sequential wall-clock runtime | 59.00 minutes | 88.50 minutes |

The cumulative central transfer projection, reusing benchmark windows, is 1.570 GB under the 4 GB ceiling. Massive's [official stock product page](https://www.massive.com/stocks) states paid plans have unlimited API calls without per-request pricing. Existing historical NBBO entitlement succeeded on both fixed checks and these 20 windows; no HTTP 429 occurred, with observed sequential rate 4.18 requests/second. This does not guarantee future rate or latency.

**Decision: retain the full 14,340-event universe.** The central runtime projection is below 90 minutes, and the central cumulative transfer is within the current ceiling. Full NBBO is operationally feasible under the observed entitlement and documented paid-plan request policy. The old internal 2,500-request cap must be prospectively raised before a full download; it is not a provider limit. No full download was started in this benchmark turn.

The 1.5× sensitivity is a heuristic, not a confidence interval. Twenty stratified observations cannot establish full-universe quote success or rule out unusually active symbols, pagination, throttling or latency tails. Retain live request/transfer guards. These estimates cover underlying pre-event NBBO only; Databento definitions/quotes and later pre-decision reaction/beta/action acquisition require separate cost and transfer accounting. Hypotheses, signal, universe thresholds, split/holdout boundaries and outcome rules are unchanged.

Evidence: `data/raw/nbbo_benchmark/manifest.json`, sanitized complete-window gzip files, `data/cache/nbbo_benchmark_selection/`, `data/cache/nbbo_benchmark_results.json`. Local report reproduction: `python3 scripts/report_nbbo_benchmark.py`. Acquisition is guarded against automatic retry of incomplete windows.
