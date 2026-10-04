# Prepared FMP event-session timing coverage audit

Date: 2026-10-03.
Status: Prepared only; not executed. No acquisition or audit results.
Authority: EXPERIMENT.md, including prospective amendment A1.

## Scope

Measure the fraction of candidate original quarterly earnings events in the historical universe with usable FMP `time` (`bmo`/`amc`), separately for train and validation. Require ≥90% in each split, preserving the existing feasibility threshold. Do not pool splits to rescue a failure.

Train entry-session dates: 2023-04-03–2024-12-31.
Validation entry-session dates: 2025-01-01–2025-12-31.
No final-holdout observations, including event counts, may be queried or opened. No prices, reactions, X, signals, borrow data, returns, P&L, regressions, or performance are needed or permitted in this audit. No package installation, Slurm job, GPU, or significant compute is planned.

## Inputs and acquisition gate

Use only a separately approved bounded acquisition manifest or a certified train/validation-only local extract. The capability-tested endpoint is `https://financialmodelingprep.com/stable/earnings-calendar`, with exact-day `from`/`to`, `page=0`, and `includeReportTimes=true`. Four fixed probes succeeded; broader coverage is unmeasured. Before execution, fix supported filters, the exact request list, event-date bounds, pagination limits, maximum records/bytes, existing entitlement, estimated charges, and spending ceiling. No automatic execution, unbounded pagination, retries, or expansion is authorized by this document. Do not scan an all-period local file containing holdout observations to produce the extract.

Require a documented historical security/issuer mapping and then-listed universe, including subsequently delisted securities. Do not substitute present-day constituents. Universe construction retains EXPERIMENT.md's original rules; any unavailable historical eligibility inputs make representative coverage unresolved. Do not load prices in this timing-only audit; use separately documented historical eligibility metadata, or state that universe eligibility is unresolved.

Allowlist: source/event identifier if supplied, historical issuer/security identifier, historical ticker, event date, fiscal period/year, original-release/confirmation evidence, raw `time`, raw `lastUpdated`, acquisition time, and source/query-manifest identifier. Exclude EPS/revenue/surprise and price/outcome fields from retained audit data. Never retain credentials, authentication headers, credential-bearing URLs, raw error bodies, or full responses in reports.

## Frozen denominator and split assignment

1. Establish candidate original quarterly events independently of whether `time` is present. Deduplicate by historical issuer and fiscal period, preserving source-row provenance. Resolve conflicting duplicates from original-release evidence, never by preferring a record merely because its timing is usable. Unresolved timing conflicts count as unusable.
2. Exclude only documented non-quarterly/non-original events or historical-universe ineligibility under the existing rules. Missing or uncertain timing stays in the denominator. Do not condition the denominator on option coverage, quote quality, signals, borrow, or outcomes. Report every exclusion and unresolved universe/event-identity issue.
3. Map usable `bmo`/`amc` to D using the verified exchange calendar and event date, with holidays, early closes, and daylight-saving handling. Preserve raw values; trim surrounding whitespace and lowercase solely for classification. Do not infer missing classifications from exact times, `lastUpdated`, or other fields. Verified disagreement changing D makes timing unusable.
4. Missing timing can make split assignment ambiguous near boundaries. Use independently verified release evidence to assign D when available, without crediting an absent FMP timing value. Otherwise report these events separately and calculate per-split conservative lower and upper coverage bounds across all possible calendar-consistent assignments. Do not silently exclude boundary-ambiguous missing events. A pass requires the conservative lower bound ≥90% in both splits; unresolved membership otherwise prevents a definitive pass.
5. Plan bounded event-date queries to cover releases mapping into the approved entry-session dates, including necessary preceding-release dates. Verify those bounds against the calendar before approval. Cap acquisition at development-era events, never request 2026 event observations. A 2025 release potentially mapping into 2026 is logged as outside the approved development-entry scope without inspecting any holdout session observations.

## Calculation and output

For each split:

`timing coverage = unique candidate events with usable, non-conflicting bmo/amc / all unique candidate events`

Report numerator, denominator, percentage, `bmo` count, `amc` count, missing/blank count, other-value count, timing-conflict count, unresolved split-membership count, and duplicate/exclusion reconciliation. Missing acquisition pages or failed queries make coverage unresolved, not zero or an exclusion. An empty denominator is unresolved. Use the exact ratio for the ≥90% decision without rounding a failure into a pass.

Report timing coverage by split and year; issuer-level missingness may be reported within the authorized development scope. Preserve `lastUpdated` only in provenance records. Record extract/manifest hashes, acquisition time, calendar version, mapping version, and classification transformation for reproducibility.

Keep separate columns for original-release verification and evidence of availability by 10:05 ET on D. A timing-coverage pass does not prove the preregistered verified-timestamp requirement, historical vintage availability, full universe coverage, or the full feasibility gate. No `lastUpdated` value can turn those evidence columns into a pass.

Report both the raw timing-coverage population and calendar-only ten-session boundary-purge attrition. Do not use purging to remove missing timing from the raw denominator or improve its pass rate. Compute scheduled dates from calendars only; do not retrieve outcome windows.

## Decision and stop

Mark timing coverage passed, failed, or unresolved per development split. Preserve all other feasibility requirements and sample minimums. Record limitations before any subsequent analysis. Stop after the coverage report; no backtest, outcome inspection, holdout access, or automatic next-stage acquisition follows.
