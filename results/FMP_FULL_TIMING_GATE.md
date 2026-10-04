# Local full-candidate FMP timing-coverage gate

Recorded at: 2026-10-03T23:58:49.395784-04:00
Status: Local operational bmo/amc coverage threshold passed in train and validation. Full verified-release/historical-availability and issuer-deduplicated quarterly-event feasibility remain pending.

## Population and calculation

Read only the completed, allowlisted development-only FMP extract and previously acquired Massive liquidity files, verifying source hashes. No new API requests. Full input: 192,246 rows, 192,241 unique symbol/date pairs. Missing/non-bmo/amc timing remained eligible for liquidity screening; the prior timed-only subset was not used as the denominator.

Apply the unchanged previous unadjusted close ≥$10 and median close × volume ≥$20M over all 20 strictly preceding completed exchange sessions, using the prospectively amended Massive extended-hours-volume approximation. Candidate D's EOD record is loaded only after evaluating its prior-session screen. Do not compute reactions, returns, P&L or strategy outcomes.

For non-conflicting normalized bmo/amc, use the fixed D mapping. For missing/other/conflicting timing, evaluate both bmo-compatible and amc-compatible D alternatives without imputing a timing value or awarding timing credit. Count a pair as certainly eligible only when all compatible alternatives pass within the same split. Count it as possibly eligible when at least one alternative passes in that split. Lower coverage = known usable timings / all possibly eligible pairs; upper coverage = known usable timings / certainly eligible pairs. The gate uses the exact conservative lower ratio, not rounded percentages. No ambiguous missing pair is silently deleted.

## Per-split results

| Measure | Train | Validation |
|---|---:|---:|
| All liquidity-eligible candidate symbol/date pairs | 10,040–10,042 | 6,577 |
| Non-conflicting normalized bmo/amc pairs | 10,017 | 6,563 |
| bmo | 5,205 | 3,380 |
| amc | 4,812 | 3,183 |
| Coverage (conservative lower bound) | **99.751046%** | **99.787137%** |
| Coverage upper bound | 99.770916% | 99.787137% |
| Unusable timing pairs, certain–possible | 23–25 | 14 |
| Missing/blank timing, possibly eligible | 23 | 13 |
| Other non-bmo/amc values, possibly eligible | tas: 1 | --: 1 |
| Conflicting bmo/amc pair, possibly eligible | 1 | 0 |
| Duplicate symbol/date pairs in eligible population | 1 | 0 |
| Extra duplicate rows in eligible population | 1 | 0 |
| Fiscal-conflicting pairs in eligible population | 1 | 0 |
| All possible pairs with nonempty fiscalYear/fiscalPeriod on every source row | 10,042 / 10,042 | 6,577 / 6,577 |
| ≥90% usable-timing threshold | **Passed** | **Passed** |

Train has 10,018 possibly eligible pairs containing at least one bmo/amc value, but one conflicting pair is deliberately excluded from the usable numerator. Validation has no such conflict. Uppercase BMO/AMC and surrounding whitespace were normalized under the existing protocol; raw values remain in source files. Other timestamps were not converted into timing credit.

Two missing-timing train pairs have eligibility uncertainty: RNA 2024-05-09 and SNN 2024-10-31 fail the median-dollar-volume screen under same-day D and pass under next-session D. Both remain in the conservative train denominator. Neither ambiguity crosses split boundaries. Validation membership is unambiguous for the liquidity-eligible missing/other-timing observations. No holdout event is queried to resolve a late-development date.

Combined possible eligible population: 16,619 pairs across 2,207 symbols, with 16,617 certainly eligible. The 16,580 usable-timing numerator agrees with the previous timed-only screen exactly. Source rows beyond eligible populations are retained in the full input, not discarded from provenance.

## Duplication and quarterly identity

Across all Stage B1 rows, five symbol/date pairs each have one extra row (five extra rows total). All five have differences in retained fiscal metadata; one also has conflicting normalized timing. Of these, one duplicate/fiscal-conflicting pair is possibly liquidity eligible in train, none in validation. No conflicting fiscal identity was resolved by choosing a newer lastUpdated or favoring usable timing.

Every raw row contains nonempty fiscalYear and fiscalPeriod. fiscalDateEnding, historical issuer identifier and stable security identifier are absent. The possible liquidity-eligible population has quarter labels Q1–Q4. Train distinct-pair period labels: Q1 2,706, Q2 2,867, Q3 2,793, Q4 1,677; these total 10,043 because one pair has two conflicting quarter labels. Validation: Q1 1,583, Q2 1,683, Q3 1,721, Q4 1,590. Raw availability is 100%; correctness, original-release identity and deduplication by historical issuer/fiscal period are not thereby established. The previous statement that fields might be absent is resolved by this local read: the actual saved extract supplies fiscalYear/fiscalPeriod.

lastUpdated is preserved only for provenance; it supplies no historical-vintage evidence. No primary event is promoted solely because a calendar row has quarter labels. Type/locale/exchange, share-class consolidation, historical ticker/issuer mapping, contemporaneous verification and historical executability remain unresolved. Therefore this passes the requested local operational timing-coverage threshold while leaving the original full timestamp-feasibility requirements pending. No hypothesis, signal, split, threshold or outcome rule changed.

## Outputs and checks

- data/cache/stage_b2/full_timing_gate.json — counts, bounds and manifest hashes.
- data/cache/stage_b2/full_timing_gate_pairs.jsonl — all possibly eligible pairs, raw timing classifications, fiscal-label conflicts and both timing-compatible liquidity decisions.
- scripts/fmp_full_timing_gate.py — local reproduction code.

All source hashes and dates were verified. The usable numerator exactly reconciles to train 10,017 and validation 6,563 from the prior screen. Numerator is never greater than the certain denominator; every missing/conflicting possible pair is included in the conservative denominator. Local reading/analysis does not change cumulative acquisition usage: 1,005 requests and 856,847,804 response-body bytes.

No new API requests, holdout observations, returns/P&L, signals or outcome analyses. Historical-reference work is designed separately in results/OPTIMIZED_HISTORICAL_REFERENCE_PLAN.md and has not been executed.
