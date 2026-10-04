# FMP feasibility record

Date: 2026-10-03.
Evidence: Approved probe results supplied by the user; probes were not rerun for this task.
Status: Access and fixed-example session-classification capability passed; representative train/validation coverage and historical availability unresolved.

## Approved capability evidence

Endpoint for all four: `https://financialmodelingprep.com/stable/earnings-calendar`.
Query form: `?from=DATE&to=DATE&page=0&includeReportTimes=true`, with identical from/to dates for each row below.

| Probe | Target | Exact date | HTTP | Returned records | Body bytes | Target found | time | lastUpdated |
|---|---|---|---:|---:|---:|---|---|---|
| F1 | MSFT | 2023-04-25 | 200 | 347 | 115,204 | Yes | amc | 2025-04-24 |
| F2 | AAPL | 2023-05-04 | 200 | 958 | 318,314 | Yes | amc | 2026-06-04 |
| F3 | JPM | 2024-01-12 | 200 | 94 | 31,298 | Yes | bmo | 2026-02-18 |
| F4 | JPM | 2025-01-15 | 200 | 70 | 23,223 | Yes | bmo | 2026-05-07 |

Totals: 4 requests, 1,469 returned calendar records, 488,039 response-body bytes. All four fixed targets had usable bmo/amc classification (4/4). The returned calendar-row totals are not a representative candidate-event coverage denominator.

Approved limits: four requests total; exact-day train/validation dates only; at most 4,000 records and 1,000,000 response bytes per request; no pagination, retries, redirects, holdout dates, or EPS/revenue/surprise/return inspection. Each reported response was within its record and byte limits. These limits applied to the completed capability probes and do not authorize a broader acquisition.

## Interpretation and prospective decision

FMP access is working under the upgraded entitlement. The four fixed examples demonstrate access and usable event-session classification only. Full train/validation coverage remains unmeasured; no ≥90% coverage pass is asserted. Original-release verification, completeness, revision handling, and historical availability remain unresolved.

Massive/Benzinga earnings access was entitlement-limited (HTTP 403) in `results/STAGE_A_AUDIT.md`. The user selected FMP as the replacement candidate source prospectively. Amendment A1 in EXPERIMENT.md occurred before any strategy returns were inspected.

Treat FMP `time` values `bmo` and `amc` as event-session classification, not exact publication timestamps. Preserve `lastUpdated` unchanged for provenance. Its later dates do not prove historical record vintages or availability at the decision time; a 2026 update value on a development-era event is provenance metadata, not access to a holdout event. All original contemporaneous-verification and historical-availability requirements remain in force.

`FMP_COVERAGE_AUDIT.md` is prepared and has not been executed. No new provider requests, holdout observations, prices, signals, strategy returns, or outcomes were accessed during this documentation task. The full pre-return feasibility gate remains unresolved.
