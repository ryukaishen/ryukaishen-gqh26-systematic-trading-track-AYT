# Local historical-reference bracketing

Implemented prospective amendment A5 before any strategy outcome inspection, using only the 34 completed historical Massive snapshots. No additional Massive reference requests were made. Matching requires qualifying U.S. common-stock records at both consecutive anchors, the same ticker/type, CIK, composite FIGI and share-class FIGI, and complete identity evidence. Missing, changed, or unbracketed records are unresolved/excluded. Exact-date-supported historical status remains verified.

| Historical status of liquidity-eligible candidate pairs | Train | Validation |
|---|---:|---:|
| Exact-date verified | 577 | 316 |
| Bracket-verified operationally | 8,165 | 5,375 |
| Unresolved/excluded | 1,300 | 886 |
| Total candidate pairs | 10,042 | 6,577 |

Final operational eligibility additionally requires usable nonconflicting bmo/amc timing and one fiscal-year/quarter label. Consolidation uses issuer CIK + fiscal year + fiscal quarter. Two groups with multiple release dates (four pairs) remain unresolved; 37 additional share-class/duplicate pairs were consolidated. The existing boundary purge excludes 18 train and 20 validation events, without accessing holdout observations.

| Final operational sample | Train | Validation |
|---|---:|---:|
| Eligible events | 8,688 | 5,652 |
| Of which exact-date verified | 577 | 316 |
| Of which bracket-verified | 8,111 | 5,336 |
| Unique issuers | 1,584 | 1,647 |
| Unique symbols | 1,591 | 1,647 |
| Unique entry dates | 379 | 215 |

These counts exceed the numerical event/issuer/date capacity requirements, so Stage C has begun. The preregistered signal-measurable and X-group feasibility minimums remain untested; candidate capacity alone does not pass them.

Bracketing is an operational historical-status approximation, not proof of uninterrupted listing or unchanged ownership every day. Vendor fiscal labels remain uncorroborated, and ambiguous release-date groups were excluded rather than presumed original releases. The operational FMP bmo/amc gate remains passed; full historical timestamp/vintage verification remains unproven. lastUpdated remains provenance only.

Reproduction: `python3 scripts/local_reference_bracketing.py`. Outputs: `data/cache/reference_bracketing/summary.json`, `candidate_status.jsonl`, `eligible_events.jsonl`, and `unresolved_duplicate_groups.jsonl`. No returns, P&L, or holdout data were inspected.
