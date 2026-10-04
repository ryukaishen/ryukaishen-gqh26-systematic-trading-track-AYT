# DATA_AUDIT.md — Proposed feasibility audit

Status: proposal only.
Date: 2026-10-03.

No API requests or market-data downloads have been executed for this audit.

## Scope and safeguards

Determine:

1. Massive historical earnings access and timestamp fields.
2. Massive historical security/reference/corporate-action capabilities.
3. Databento OPRA.PILLAR definition and cbbo-1m coverage from approximately April 2023 onward.
4. Provider-estimated cost of a tiny Databento pilot before downloading.
5. Historical expired-option retrieval capability.
6. Valid pre-event ATM call/put quote availability under EXPERIMENT.md.

Do not:

- Run a backtest or inspect strategy returns.
- Retrieve post-event prices or calculate reaction, entry, exit, or subsequent returns.
- Query final-holdout observations. Only provider-level coverage metadata is permitted.
- Install packages, request GPUs, launch Slurm jobs, or download substantial data.

## Authoritative preregistration and execution gate

EXPERIMENT.md is the authoritative preregistration.

No event-level API request may execute until EXPERIMENT.md has been finalized and written. This includes earnings records, historical stock quotes, option-reference discovery, contract-specific definitions, and option quotes.

Before those requests, EXPERIMENT.md must establish:

- Development and final-holdout boundaries.
- Permissible pilot dates.
- Event timestamp requirements.
- Median historical NBBO midpoint spot definition.
- Contract selection, quote validity, synchronization, and aggregation rules.

RESEARCH_IDEAS.md provides context only. It cannot override EXPERIMENT.md.

Provider-level Databento metadata requests may be reviewed separately, but none will execute before approval of their exact request list.

## Secret handling

Neither MASSIVE_API_KEY nor DATABENTO_API_KEY will be written, printed, logged, saved, or committed.

Read the existing environment variables only when approved requests execute. Construct authentication in process memory:

- Massive: Bearer authorization header.
- Databento: Basic authentication, key as username and empty password.

Never place credentials in:

- URLs or shell arguments.
- Request manifests or configuration files.
- Logs, debug traces, exception output, or saved responses.

Disable HTTP/SDK request tracing. Do not display raw headers, responses, exception strings, or pagination URLs. Retain only allowlisted audit fields and sanitized status/error categories.

## Proposed pilot and interpretation

Candidate events:

- MSFT, 2023-04-25.
- AAPL, 2023-05-04.

These are unverified request candidates. They become eligible only if EXPERIMENT.md permits their dates and their release timestamps are verified.

Do not replace missing or failed events based on quotes or returns. This convenience sample demonstrates capability; it does not estimate representative universe coverage.

Historical reference examples involving 2022 also require approval of those dates.

## Volume and cost limits

All volumes below are planning estimates, not observed responses.

Massive marginal request charges are unverified. Use existing entitlement only. No paid add-on, subscription change, or purchase is authorized.

Databento metadata calls are expected to have no market-data acquisition charge. Dollar costs for historical retrieval remain unknown until get_cost responds.

Preserve these proposed Databento ceilings:

- Total quoted pilot cost: USD 1.00.
- Total estimated billable size: 1 MiB.
- Retrieved definition records: 100 overall.
- Retrieved CBBO records: 120 overall.
- Network transfer: 5 MiB overall.

The cost and billable-size ceilings apply conservatively to the larger estimation windows. Record ceilings apply to retrieval. These limits are not spending authorization.

## Stage A: exact Massive capability requests

Base URL: https://api.massive.com
Method: GET
Authentication is omitted from this manifest intentionally.

Execute only after EXPERIMENT.md is finalized and written and dates are approved.

All requests are single-page. No automatic pagination or unbounded retries.

| ID | Exact path and query | Maximum records | Expected response volume | Estimated cost |
|---|---|---:|---:|---|
| M1 | /benzinga/v1/earnings?ticker=MSFT&date=2023-04-25&limit=2&sort=date.asc | 2 | <10 KB | Unverified; existing entitlement only |
| M2 | /benzinga/v1/earnings?ticker=AAPL&date=2023-05-04&limit=2&sort=date.asc | 2 | <10 KB | Unverified; existing entitlement only |
| M3 | /v3/reference/tickers?market=stocks&locale=us&type=CS&date=2023-04-03&active=true&limit=3&sort=ticker&order=asc | 3 | <10 KB | Unverified; existing entitlement only |
| M4 | /v3/reference/tickers?market=stocks&locale=us&type=CS&date=2023-04-03&active=false&limit=3&sort=ticker&order=asc | 3 | <10 KB | Unverified; existing entitlement only |
| M5 | /v3/reference/tickers/MSFT?date=2023-04-25 | 1 | <15 KB | Unverified; existing entitlement only |
| M6 | /v3/reference/tickers/TWTR?date=2022-10-26 | 1 | <15 KB | Unverified; existing entitlement only |
| M7 | /v3/reference/tickers?ticker=TWTR&date=2023-04-03&active=false&limit=1 | 1 | <5 KB | Unverified; existing entitlement only |
| M8 | /stocks/v1/splits?ticker=AMZN&execution_date=2022-06-06&limit=2 | 2 | <5 KB | Unverified; existing entitlement only |
| M9 | /stocks/v1/dividends?ticker=AAPL&ex_dividend_date.gte=2023-04-01&ex_dividend_date.lte=2023-05-04&limit=3&sort=ex_dividend_date.asc | 3 | <10 KB | Unverified; existing entitlement only |
| M10 | /v3/reference/options/contracts?underlying_ticker=MSFT&expiration_date=2023-05-05&expired=true&limit=2&sort=strike_price&order=asc | 2 | <10 KB | Unverified; existing entitlement only |

Total: 10 requests, at most 20 records, expected under 100 KB.

Distinguish authentication failure, entitlement restriction, unsupported filters, successful empty results, and successful nonempty results. Empty results alone do not prove absent coverage.

### Earnings timestamp assessment

Inspect only:

- Event identifier and ticker.
- Date, time, and date confirmation status.
- Fiscal period/year.
- last_updated.

Do not display or use EPS, revenue, consensus, or surprise fields.

Scheduled release time, actual release time, vendor update time, and historical availability are distinct. last_updated does not establish original publication time or historical revision vintages.

Resolve the documented EST timezone terminology explicitly. Do not silently assume fixed UTC-5 or daylight-aware America/New_York.

Verify actual release timing against contemporaneous issuer evidence. Show exact source URLs before making those requests.

### Historical reference assessment

Inspect historical identifiers, security type, listing status, effective dates, split ratios, and dividend fields.

The tiny active/inactive and delisted-name probes do not establish a complete historical universe.

Splits/dividends alone do not prove complete ticker-change, merger, spinoff, cash-delisting, or terminal-distribution coverage. Report those requirements as unresolved unless independently established.

Do not use present-day cumulative adjustment factors for historical contract selection.

## Stage A2: tiny historical option-filter semantics probe

Do not assume how as_of interacts with expired=false.

Use the same narrowly specified historical contract pair under three filter configurations:

```
GET https://api.massive.com/v3/reference/options/contracts?underlying_ticker=MSFT&expiration_date=2023-05-05&strike_price=280&as_of=2023-04-25&limit=2&sort=contract_type&order=asc

GET https://api.massive.com/v3/reference/options/contracts?underlying_ticker=MSFT&expiration_date=2023-05-05&strike_price=280&as_of=2023-04-25&expired=false&limit=2&sort=contract_type&order=asc

GET https://api.massive.com/v3/reference/options/contracts?underlying_ticker=MSFT&expiration_date=2023-05-05&strike_price=280&as_of=2023-04-25&expired=true&limit=2&sort=contract_type&order=asc
```

Per request:

- Maximum two reference records.
- Expected response under 10 KB.
- Massive marginal charge unverified; existing entitlement only.

Combined: at most six returned records, expected under 30 KB.

Compare returned call/put identities and historical characteristics. Establish historical existence separately using the subsequently approved pre-event Databento definitions/quotes; expiration after as_of alone does not prove the contract was already listed then.

Interpretation:

- Matching historical live-contract records with expired=false supports that filter configuration for this example.
- Missing or inconsistent records leave semantics unresolved.
- All three empty responses cannot distinguish nonexistent contracts from coverage/filter problems.
- Do not expand the probe or infer semantics from expiration dates alone.

The fixed 280 strike is a filter capability example, not the pilot ATM selection.

Do not proceed to historical chain discovery until the filter behavior is resolved. Any additional probe must be shown as an exact request first.

## Stage A: Databento provider-level metadata

Proposed canonical method calls:

```
client.metadata.list_schemas(dataset="OPRA.PILLAR")

client.metadata.get_dataset_range(dataset="OPRA.PILLAR")

client.metadata.list_fields(
    dataset="OPRA.PILLAR",
    schema="definition",
    encoding="json",
)

client.metadata.list_fields(
    dataset="OPRA.PILLAR",
    schema="cbbo-1m",
    encoding="json",
)
```

| Request | Expected response volume | Estimated acquisition charge |
|---|---:|---:|
| list_schemas | <10 KB | USD 0; metadata only |
| get_dataset_range | <20 KB | USD 0; metadata only |
| list_fields: definition | <50 KB | USD 0; metadata only |
| list_fields: cbbo-1m | <20 KB | USD 0; metadata only |

Inspect schema-specific start/end coverage against approximately April 2023 onward.

Dataset metadata may describe dates overlapping the holdout. No holdout observations will be requested.

Metadata visibility does not establish account retrieval entitlement. Assess successful cost estimates and approved tiny retrieval separately.

Use an existing client if installed. Otherwise verify official HTTP routing and use standard-library HTTPS. Do not install packages.

## Stage B: historical stock NBBO capability probes

Use historical stock quotes, not aggregate bars, because EXPERIMENT.md defines spot as the median NBBO midpoint.

Assuming verified after-close releases and approved dates:

```
GET https://api.massive.com/v3/quotes/MSFT?timestamp.gte=1682452200000000000&timestamp.lt=1682452500000000000&sort=timestamp&order=asc&limit=5

GET https://api.massive.com/v3/quotes/AAPL?timestamp.gte=1683229800000000000&timestamp.lt=1683230100000000000&sort=timestamp&order=asc&limit=5
```

Intervals:

- MSFT: 2023-04-25T19:50:00Z through 19:55:00Z, end exclusive.
- AAPL: 2023-05-04T19:50:00Z through 19:55:00Z, end exclusive.

Each request:

- Maximum five quote records.
- Expected response under 10 KB.
- Massive marginal charge unverified; existing entitlement only.

Inspect bid/ask, sizes, timestamps, conditions, and entitlement status without displaying raw responses.

These five-record requests test access and field availability. They do not establish the median over a full five-minute window.

If historical stock quotes are not entitled, report a data-feasibility failure. Do not substitute bars.

If the response is paginated, do not calculate the preregistered median from the first page. Show a separate bounded full-window quote-acquisition plan, its expected volume, and its exact requests before proceeding. If complete median-NBBO measurement cannot fit the small audit budget, report spot measurement as unresolved.

Any sampling or time weighting must follow EXPERIMENT.md. Do not introduce either during the audit.

## Stage B: historical option-reference discovery

Discovery remains blocked until:

- EXPERIMENT.md is finalized and written.
- Event timing and permissible dates are confirmed.
- The complete preregistered median NBBO spot is available.
- Historical as_of/expired semantics are verified.

Conditional expiry bounds:

| Event | First regular session after release, D | Eligible expiry dates |
|---|---|---|
| MSFT 2023-04-25 | 2023-04-26 | 2023-05-03 through 2023-05-17 |
| AAPL 2023-05-04 | 2023-05-05 | 2023-05-12 through 2023-05-26 |

The original expired=false discovery form will be used only if the tiny semantics probe validates it. Otherwise show a revised exact request before execution.

Conditional requests:

```
GET https://api.massive.com/v3/reference/options/contracts?underlying_ticker=MSFT&as_of=2023-04-25&expired=false&expiration_date.gte=2023-05-03&expiration_date.lte=2023-05-17&limit=100&sort=expiration_date&order=asc

GET https://api.massive.com/v3/reference/options/contracts?underlying_ticker=AAPL&as_of=2023-05-04&expired=false&expiration_date.gte=2023-05-12&expiration_date.lte=2023-05-26&limit=100&sort=expiration_date&order=asc
```

Each:

- Maximum 100 reference rows.
- Expected response under 125 KB.
- Massive marginal charge unverified; existing entitlement only.

A truncated chain cannot establish earliest expiry or nearest strike. Stop rather than select from incomplete records. Show exact targeted continuation requests for review if necessary.

Follow EXPERIMENT.md for:

- Earliest standard expiry within the 7–21-day interval after D.
- Nearest strike to median NBBO midpoint spot.
- Lower-strike tie break.
- Call/put availability.
- Standard unadjusted 100-share deliverables.

Multiplier 100 alone is insufficient to rule out adjusted deliverables.

Budget at most three neighboring strike pairs per event at the selected expiry: at most 12 contracts overall. No fallback to farther strikes or later expiries unless explicitly preregistered.

## Stage C: Databento estimation windows

Resolve literal OPRA raw symbols before estimation. Preserve symbol spacing and verify the mapping from Massive contract identifiers.

Show the fully resolved manifest before execution. Never use ALL_SYMBOLS or parent-symbol full-chain requests.

Use 24-hour definition estimation windows and 10-minute CBBO estimation windows:

| Event | Definition estimation interval | CBBO estimation interval |
|---|---|---|
| MSFT | 2023-04-25T00:00:00Z to 2023-04-26T00:00:00Z | 2023-04-25T19:45:00Z to 2023-04-25T19:55:00Z |
| AAPL | 2023-05-04T00:00:00Z to 2023-05-05T00:00:00Z | 2023-05-04T19:45:00Z to 2023-05-04T19:55:00Z |

End timestamps are exclusive.

Definition estimates encompass a full day only to satisfy estimation rules. They return scalar metadata, not post-event definitions or prices. All intervals must remain outside the final holdout.

If a candidate event occurred before the proposed CBBO estimation endpoint, stop and revise the manifest.

For each event:

```
definition_estimate = dict(
    dataset="OPRA.PILLAR",
    schema="definition",
    stype_in="raw_symbol",
    symbols=CONTRACT_SYMBOLS,  # At most six explicit contracts.
    start=DEFINITION_ESTIMATE_START,
    end=DEFINITION_ESTIMATE_END,
)

cbbo_estimate = dict(
    dataset="OPRA.PILLAR",
    schema="cbbo-1m",
    stype_in="raw_symbol",
    symbols=CONTRACT_SYMBOLS,
    start=CBBO_ESTIMATE_START,
    end=CBBO_ESTIMATE_END,
)

client.metadata.get_record_count(**definition_estimate)
client.metadata.get_billable_size(**definition_estimate)
client.metadata.get_cost(**definition_estimate)

client.metadata.get_record_count(**cbbo_estimate)
client.metadata.get_billable_size(**cbbo_estimate)
client.metadata.get_cost(**cbbo_estimate)
```

Per metadata call:

- Expected response under 1 KB.
- Expected acquisition charge USD 0.

Two events: 12 estimation calls, expected under 12 KB total.

Do not use a record limit when estimating the full query.

Report cost, record count, and billable size for each event/schema and in total. Do not scale the estimates linearly to manufacture a five-minute or partial-day price. Label them explicitly as estimates for the larger windows.

The larger-window estimates provide a conservative budget check for smaller retrievals, subject to provider billing rules. They are not an exact quote for the smaller retrieval.

Stop if combined estimated cost exceeds USD 1.00 or estimated billable size exceeds 1 MiB.

## Stage D: separately approved smaller retrievals

Retrieval remains restricted to approved pre-event windows.

| Event | Definition retrieval interval | CBBO retrieval interval |
|---|---|---|
| MSFT | 2023-04-25T00:00:00Z to 2023-04-25T19:55:00Z | 2023-04-25T19:50:00Z to 2023-04-25T19:55:00Z |
| AAPL | 2023-05-04T00:00:00Z to 2023-05-04T19:55:00Z | 2023-05-04T19:50:00Z to 2023-05-04T19:55:00Z |

Show literal symbols and final parameters again before downloading.

```
client.timeseries.get_range(
    dataset="OPRA.PILLAR",
    schema="definition",
    stype_in="raw_symbol",
    stype_out="instrument_id",
    symbols=CONTRACT_SYMBOLS,
    start=DEFINITION_RETRIEVAL_START,
    end=PRE_EVENT_WINDOW_END,
    limit=101,
)

client.timeseries.get_range(
    dataset="OPRA.PILLAR",
    schema="cbbo-1m",
    stype_in="raw_symbol",
    stype_out="instrument_id",
    symbols=CONTRACT_SYMBOLS,
    start=PRE_EVENT_WINDOW_START,
    end=PRE_EVENT_WINDOW_END,
    limit=121,
)
```

Emergency per-request limits do not override overall ceilings:

- 100 definition records.
- 120 CBBO records.
- 5 MiB total transfer.

Planning estimate:

- Five-minute CBBO retrieval: approximately 30 records per event, 60 overall.
- Ten-minute CBBO estimation: approximately 60 records per event, 120 overall.
- Definition volume: unknown until metadata estimates.
- JSON quote payloads: typically tens of KB per event.
- Actual acquisition cost: not known until estimates; use the larger-window quoted total as the proposed budget bound.

Detect truncation. Incomplete records are an unresolved audit result, not a successful selection.

Do not retrieve definitions after the pre-event endpoint. Do not download larger estimation windows merely because they were priced.

## Quote feasibility assessment

Use only completed pre-event observations and information available by the measurement endpoint.

Confirm timestamp semantics, minute labeling, and historical instrument identity before assessing quote availability.

Require, subject to EXPERIMENT.md:

- Positive bid and ask.
- Ask strictly greater than bid.
- Positive displayed sizes.
- Spread/midpoint no greater than 20%.
- At least three valid minute observations per selected call and put.
- Common strike and expiry.
- Confirmed standard unadjusted 100-share deliverables.

Preserve quality flags. Do not forward fill missing quotes or tune filters using the sample.

Report:

- Event identifier and timestamp provenance.
- Median-NBBO spot availability/completeness.
- Pre-event interval.
- Selected expiry and strike.
- Historical symbols and instrument IDs.
- Deliverable/adjustment status.
- Valid-minute counts and synchronized-pair count.
- Exclusion reasons.
- Pass, fail, or unresolved.

Keep failed events in the denominator.

Do not calculate implied move, reaction normalization, signals, returns, or performance.

## Reporting limits

| Question | Tiny-audit evidence | Remaining limitation |
|---|---|---|
| Historical earnings | Access and timestamp fields for two records | Complete coverage and historical revision provenance |
| Survivorship references/actions | Small historical listing, delisting, split and dividend examples | Complete universe and corporate-action continuity |
| OPRA coverage | Schema ranges, successful estimates and tiny retrieval | Every issuer/day's usable coverage |
| Pilot cost | Provider estimates for documented estimation windows | Exact smaller-window billing and full-experiment budget |
| Expired options | Historical filter semantics and selected expired-contract retrieval | All expired-contract availability |
| Pre-event ATM quotes | Compliance for two fixed candidate events | Representative coverage rate or profitability |

All account-specific findings remain untested.

## Official documentation references

- https://massive.com/docs/rest/partners/benzinga/earnings
- https://massive.com/docs/rest/stocks/tickers/all-tickers
- https://massive.com/docs/rest/stocks/quotes
- https://massive.com/docs/rest/options/contracts/all-contracts
- https://massive.com/docs/rest/stocks/corporate-actions/splits
- https://massive.com/docs/rest/stocks/corporate-actions/dividends
- https://databento.com/docs/api-reference-historical/metadata/metadata-get-dataset-range
- https://databento.com/docs/api-reference-historical/metadata/metadata-get-cost

## Execution sequence

1. Review this proposed DATA_AUDIT.md before writing it.
2. Finalize and write EXPERIMENT.md.
3. Confirm permissible pilot/reference dates.
4. Review and approve exact capability requests.
5. Verify historical option-filter semantics and stock NBBO entitlement.
6. Resolve complete preregistered spot measurement and contract selection.
7. Show literal Databento symbols and compatible estimation requests.
8. Present provider estimates before any Databento download.
9. Retrieve only the separately approved smaller pre-event windows.
10. Report feasibility results without inspecting returns.


## Current Stage B acquisition amendment (A2)

The user's latest instruction supersedes prior Stage B transfer estimates and session-source blockers: authorize FMP EOD Bulk `/stable/eod-bulk?date=YYYY-MM-DD` for the liquidity screen, with a 4,000,000,000-byte cumulative transfer ceiling and the unchanged 1,500-request ceiling. Count Stage B1 and the three completed Massive grouped pilot requests conservatively. Retain only symbol, date, close and volume; never adjClose or outcome fields. Use close × volume for the unchanged ≥$20M trailing-20-session median and previous close ≥$10. Record the lack of explicit regular-session-only volume guarantee as a prospective measurement limitation. EXPERIMENT.md A2 is authoritative.

Acquire only approved development dates plus the required 20-session pre-start history, ending 2025-12-31. Verify the exchange session list, including the 2025-01-09 closure, and never query holdout dates. After screening, estimate historical-reference requests from survivors; do not make per-event reference requests for the unfiltered global calendar. Historical reference/identity and fiscal-period validation remain mandatory. Stage C options requests remain subject to the original contract-selection, historical-chain, schema and cost prerequisites; successful liquidity screening does not waive them.


## Current Stage B2 source amendment (A3 supersedes A2 source only)

Use Massive grouped-daily aggregates, adjusted=false, for all 710 lookback/development sessions from 2023-03-06 through 2025-12-31. Preserve previous close ≥$10 and trailing-20-session median unadjusted close × volume ≥$20M with all 20 prior sessions required. The user explicitly accepts grouped volume's potential extended-hours inclusion as a prospective operational approximation to regular-session dollar volume, solely because the intended bulk source is unavailable and before strategy-return inspection. FMP EOD Bulk HTTP 402 is final; do not retry. Keep cumulative caps at 1,500 requests / 4 GB, counting all prior Stage B requests and bytes. Verify and reuse existing within-range Massive pilot files. Estimate reference work only after screening; no holdout or post-entry returns. EXPERIMENT.md A3 controls.


## Acquisition budget amendment A4

The latest explicit user authorization prospectively raises the total request cap from 1,500 to 2,500 while keeping 4 GB. Complete exact-date historical common-stock/reference validation using remaining local candidate gaps; reuse verified existing snapshots and bound pagination. The hypothesis, signal, liquidity thresholds, universe, splits, holdout and outcome rules remain unchanged. Operational bmo/amc coverage is passed; historical timestamp/vintage proof remains pending. Exact-date reference page estimates and actual usage control the budget; 604 dates is a request lower bound, not a guarantee of one page/date. EXPERIMENT.md A4 is authoritative.


## Current historical-status approximation A5

Stop Massive reference acquisition. Apply local matching consecutive-anchor bracketing with stable FIGI/issuer identity and qualifying common-stock type; preserve exact-date evidence and flag inconsistent/unbracketed observations. Disclose that bracketing is an operational approximation, not uninterrupted-listing proof. Compare resulting operational event/issuer/date counts with the unchanged prospective minimums without asserting unmeasured sign-consistency or X-group counts. Begin Stage C when candidate capacity is sufficient, subject to actual contract-selection/spot, Databento timestamp/entitlement/cost and no-holdout requirements. EXPERIMENT.md A5 is authoritative.


## Frozen-sample execution A6

EXPERIMENT.md A6 prospectively freezes 1,500 train / 600 validation by issuer-CIK/release-date/fiscal-year/quarter SHA256 ranking. It supersedes the pilot-only parent-chain prohibition for historical event-root definitions and authorizes pre-decision reaction inputs. Preserve fixed windows, historical-only selection and all signal rules. Never replace failed sampled events. Total requests: 50,000; cumulative bytes: 4 GB; existing USD 1 cost stop remains pending concrete larger-cost approval. No holdout or subsequent ten-session returns.


## A6 paused: 20-event NBBO benchmark only

The latest user instruction pauses the 2,100-event sample and its acquisition authorization pending the representative pre-event NBBO benchmark. No sampled quotes were acquired. EXPERIMENT.md A6 pause controls population selection; do not invoke the frozen-sample acquisition while paused. No X/reactions/outcomes/holdout in the benchmark.

Benchmark decision: retain the full 14,340-event development universe. Weighted complete-window projection is 14,340 NBBO requests / 0.661 GB / 59.00 sequential minutes, with a heuristic 1.5× runtime sensitivity of 88.50 minutes. Twenty measured windows all produced valid S0, but full-universe coverage is unmeasured. The sampling branch remains inactive. See results/NBBO_REPRESENTATIVE_BENCHMARK.md for all measurements, provider-limit evidence, transfer accounting, selection and uncertainty. This decision authorizes neither holdout nor subsequent returns. The prospective internal request-budget update is required before a full acquisition; the 4 GB cumulative transfer ceiling remains unchanged.


## A7 full-universe pre-event NBBO execution

The latest explicit user authorization raises Massive requests to 20,000 while retaining cumulative 4 GB. Use the shared benchmark validity/window implementation for all 14,340 events, reuse completed benchmark windows and checkpoint pagination. Two concurrent event windows are permitted under paid-plan request policy. Record all calls conservatively in the shared ledger. After adequate S0 coverage, proceed to historical parent definitions and selected-pair-only cbbo-1m for M/coverage, with provider cost checks. No post-event, X, outcomes, subsequent returns or holdout acquisition. EXPERIMENT.md A7 is authoritative.
