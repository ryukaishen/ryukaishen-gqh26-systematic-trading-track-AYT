# Optimized historical-reference design after local timing-gate pass

Status: Design only; no provider requests executed.
The local full-candidate bmo/amc coverage threshold passed separately in train and validation. Preserve the possibly eligible missing-timing candidates in this reference population: 16,619 pairs / 2,207 symbols. Do not validate only the timed subset to inflate future coverage.

## Bulk-first acquisition design

Use historical `/v3/reference/tickers` pages with market=stocks, locale=us, type=CS, active=true, date=anchor, limit=1000, sort=ticker, order=asc. These filters describe listing status on the queried historical date, not current survival. The native route supports point-in-time date queries and up to 1,000 records/page:
https://massive.com/docs/rest/stocks/tickers/all-tickers

Choose the earliest possible liquidity-eligible entry date in each development month, plus 2025-12-31 as a final development anchor: **34 snapshots**. The exact parameter manifest is saved at data/cache/stage_b2/optimized_reference_plan.json. This covers candidate identity screening through bulk pages, avoiding blanket per-event lookups.

Retain only historical ticker, market, locale, type, primary exchange, currency, active, CIK, composite/share-class FIGI, delisted_utc and update provenance, with anchor/query/acquisition identity. Join candidate symbols locally. Preserve multiple share classes and issuer relationships. Never interpret a record update timestamp as a historical vintage or a snapshot as an interval guarantee.

Bound each snapshot at eight pages and 1,000,000 response bytes/page; fail completeness on a remaining next page or byte limit. No silent truncation. Following a provider next_url must be restricted to the expected HTTPS host/path and query scope, stripped of credential parameters, then authenticated in process memory; never log raw URLs. No redirects or unbounded retries.

## Budget

Available acquisition budget is 495 requests and 3,143,152,196 bytes. Snapshot hard caps reserve **272 requests / 272 MB**, leaving **223 requests** and approximately 2.871 GB for targeted historical exceptions, inactive/delisting reconciliation, fiscal-period corroboration and any later stage. Actual page usage, not an assumed eight pages, controls remaining capacity. This is a bounded design, not a provider-record-count estimate or guarantee all reference work fits.

## Required validity checks and adaptive exceptions

Historical anchors establish status/identifiers only at their own dates. Matching anchors, daily trading continuity, present-day status, CIK consistency or a last_updated value cannot by themselves prove uninterrupted common-stock status or ticker ownership between anchors.

Identify symbols absent from anchors, new listings, ticker/FIGI/CIK changes, disappearing listings, multiple share classes and conflicting fiscal metadata. Resolve interval validity only from documented effective-date corporate-action/reference history or trusted historical security metadata. For unresolved events, use targeted historical ticker/date queries and inactive records as necessary, within the remaining hard cap. Exact-date fallback is an exception route, never an automatic one-request-per-event acquisition.

Absence at an anchor does not justify deleting an event between anchors; it may be a subsequently delisted or newly listed security. Keep such candidates unresolved until historical evidence is obtained. Validate U.S. exchange-listed common-stock status, ADR exclusion, stable issuer/security identity and then consolidate qualifying share classes using the already specified trailing liquidity rule. Corroborate FMP fiscalYear/fiscalPeriod and conflicting rows against contemporaneous statement/SEC metadata; retain only non-outcome identity fields.

## Honest completion gate

The strict all-event-date snapshot design previously needed at least 618 requests, beyond the current 495 remainder. This anchor-plus-effective-history design reduces acquisition only if defensible interval evidence resolves most cases. It does not waive exact historical validity. If unsupported interval cases exceed the remaining budget, stop and report their counts and required requests; do not assume types or exclude cases to force a pass.

Only after common-stock/issuer/period mapping and original-release rules are defensible, rerun the timing denominator at issuer/fiscal-period level and apply registered calendar purging. Keep historical availability separate from usable session timing. This local coverage pass does not itself authorize options-chain shortcuts or freeze the full feasibility gate.

Stage C design remains conditional on the original historical as_of/expired chain semantics, pre-event quote/spot measurement, Databento schema timestamp/entitlement checks and spending estimates. No option chains, prices or outcome windows have been requested by this design step.
