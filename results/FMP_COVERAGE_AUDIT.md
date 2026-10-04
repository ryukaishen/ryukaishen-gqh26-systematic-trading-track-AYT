# FMP coverage audit execution record

Date: 2026-10-03.
Status: Execution preflight blocked; acquisition and coverage calculation not executed.
Authorization: User requested execution of FMP_COVERAGE_AUDIT.md and conditional continuation to Stage B if usable timing coverage is ≥90% in each development split.

## Preflight findings

The project file inventory contains methodology and sanitized capability reports only. No certified development-only candidate-event extract, historical security/issuer mapping, historical universe-eligibility metadata, or verified exchange-calendar artifact is present. The four FMP capability examples are recorded in results/FMP_FEASIBILITY.md; their 4/4 usable classifications cannot estimate representative coverage.

FMP_COVERAGE_AUDIT.md requires candidate original quarterly events in the historical universe, deduplication by issuer/fiscal period, and calendar-based split assignment. Without these inputs, a calendar-wide row count would change the denominator and cannot execute the protocol exactly as written. The protocol explicitly prohibits loading prices to reconstruct universe eligibility during this timing-only audit.

The acquisition protocol also requires a bounded exact request manifest, verified date bounds, completeness/pagination limits, estimated charges, and spending ceiling before acquisition. These have not been fixed for the full coverage audit. The completed four-probe limits are not a full-audit manifest or budget. The user's current instruction authorizes execution and conditional continuation; no redundant general execution approval is requested. Missing input evidence and bounded acquisition parameters remain substantive blockers.

## Coverage decision

| Split | Candidate denominator | Usable bmo/amc numerator | Coverage | ≥90% decision |
|---|---|---|---|---|
| Train: 2023-04-03–2024-12-31 entry sessions | Unavailable | Unavailable | Unmeasured | Unresolved |
| Validation: 2025-01-01–2025-12-31 entry sessions | Unavailable | Unavailable | Unmeasured | Unresolved |

Missing values are not zeros. No coverage pass or failure is asserted. Stage A remains unresolved for representative timing coverage; successful FMP capability evidence is unchanged. No hypothesis, signal, split, feasibility threshold, holdout protection, or outcome rule was changed.

## Conditional Stage B

The user's required condition for Stage B has not been satisfied, so no Stage B requests were executed. DATA_AUDIT.md additionally conditions its fixed MSFT/AAPL pre-event NBBO probes on verified after-close releases. Historical option-reference discovery also requires complete preregistered NBBO spot and resolved as_of/expired list semantics; the recorded remediation leaves list semantics unresolved. These requirements were not waived or replaced.

## Required unblock

Provide the location of a certified train/validation-only candidate-event extract and its historical issuer/fiscal-period mapping, universe-eligibility metadata, and verified calendar, or specify an approved bounded acquisition scope/budget and a source for those required inputs. No present-day universe or timing-filtered denominator will be substituted.

## Safeguards

Only project protocols, file names, and repository status were read during this execution preflight. No provider requests or additional feasibility probes were made. No holdout observations, prices, signals, returns, EPS/revenue/surprise fields, or strategy outcomes were accessed. No packages were installed and no compute jobs were launched.
