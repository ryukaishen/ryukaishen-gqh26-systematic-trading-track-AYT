# Full-universe Stage C status

Historical OPRA.PILLAR definitions and preregistered contract selection are complete for train/validation valid-S0 events. Separate selected-pair cbbo-1m metadata estimates are complete. Quote retrieval is not authorized by the definition-only approval; valid M remains unmeasured.

| Split | Population | Valid S0 | S0 coverage | Selected call/put pairs | Contract coverage, population | Contract coverage, valid S0 | Valid M |
|---|---:|---:|---:|---:|---:|---:|---|
| Train | 8,688 | 8,293 | 95.45% | 6,424 | 73.94% | 77.46% | Unmeasured |
| Validation | 5,652 | 4,765 | 84.31% | 3,592 | 63.55% | 75.38% | Unmeasured |

## Definition acquisition and selection

Credential accepted by authenticated metadata and historical endpoints without exposing it. Original full-definition estimate: $11.407067812972 and 2,449,649,160 billable bytes. User authorization raised the definition cost stop to $12; cumulative ceilings remain 20,000 requests and 4,000,000,000 transferred bytes.

All 589 date groups are resolved operationally: 588 complete retrieved definition files containing 6,804,581 records and 297,011,956 compressed response bytes, plus one unresolved-root exclusion. KRUS.OPT on 2025-07-08 did not resolve and remains excluded. No root/contract substitution was used.

The conservative definition-spend upper bound is **$11.589746363452**, including full possible charges reserved for two HTTP 504 responses. This is a budget bound, not reconciled invoice spend. Failed requests, error bytes and retries remain counted. Completed files are hash verified and reused; the first downloaded file was recovered after a decoder correction without another billable request. Large remaining date groups were partitioned into disjoint subsets of at most 40 original roots, each separately estimated before retrieval. The union of requested roots and date ranges is unchanged.

Definitions were retrieved and processed exclusively in Slurm compute jobs: 1 CPU, 4 GB RAM, two-hour wall-time per checkpoint/resume job, no GPUs or new packages. Final metadata-only resume: job 44688916. Durable acquisition, subset and estimate checkpoints are in `data/raw/stage_c_definitions/manifest.json`; complete files are under `data/raw/stage_c_definitions/dates/`; selected identities and reference timestamps are in `data/raw/stage_c_definitions/selected_pairs.json`.

Selection uses the latest historical reference information available strictly before 15:55 ET, at completion of the fixed S0 window. Expiry is an OPRA UTC calendar date and lies within entry session D+7 through D+21 inclusive. The earliest eligible expiry is frozen first; within it, choose the nearest strike to S0 with matching call/put, using the lower strike on a tie. Exact nonnumeric standard OSI roots identify documented standard 100-share contracts; contradictory non-100 reference quantities, adjusted roots, deleted records and inconsistent expiry/strike/class identities are rejected. Undefined OPRA contract-size quantities rely on the documented standard-root convention, not an invented multiplier. Quote quality has not influenced selection. There is no fallback after selection failure.

Among valid-S0 events, train exclusions are 1,869 without a qualifying standard expiry; validation exclusions are 1,172 without a qualifying standard expiry and one unresolved root. The additional 395 train and 887 validation events lack valid S0 and never enter contract selection.

## Separate quote estimates and remaining authorization

All 1,162 metadata results are complete for 581 exact selected-symbol batches across 537 dates. Each batch queries only schema cbbo-1m for the fixed [15:50,15:55) ET window; metadata cost and billable-size requests are separately checkpointed. At most four nonbillable metadata calls run concurrently, with serialized cost/transfer/request reservation and checkpoint updates. No quote retrieval endpoint is enabled in this worker.

Selected-pair quote retrieval estimate: **$0.029263496349**, **15,710,720 billable bytes** (15.710720 MB decimal). Combined conservative definition-spend upper bound plus quote estimate: **$11.619009859801**, below $12 by $0.380990140199.

Future uncompressed DBN transfer bound: **624,933,376 bytes**, including 1 MiB overhead per selected-symbol batch. Current cumulative ledger: **19,013/20,000 requests** and **1,766,577,801/4,000,000,000 bytes**, leaving **987 requests** and **2,233,422,199 bytes**. One successful retrieval per batch would reach **19,594 requests**, leaving **406** for bounded retries, and at most **2,391,511,177 cumulative bytes** under this bound. Retries must reserve their cost/transfer/request budgets separately and stop before a ceiling is at risk. These metadata estimates do not authorize retrieval.

Actual quote metadata response bytes: 10,788. There were no quote metadata failures. Final compute worker status: `definitions_and_quote_estimates_completed`; zero selected-pair quote retrievals.

Valid M coverage remains unmeasured until selected-pair quote retrieval and the unchanged quote-quality/synchronization rules are applied. Databento cbbo-1m ts_recv is the interval-end timestamp and historical filtering uses ts_recv; ts_event is last-trade time. Preserve this convention when synchronizing completed stock minute bins, and do not extend the fixed half-open window or substitute contracts to repair missing coverage.

## Validation and research limitations

Eleven focused tests pass: expiry endpoints, lower-strike tie, no later-expiry fallback, adjusted/deleted/late/non-100/inconsistent-strike rejection, nested provider headers and undefined size, exclusive reference cutoff, compute-node guard, non-rollback shared ledger, partial-subset budget accounting, concatenated compressed frames, and concurrent metadata checkpoint serialization. Python compilation and batch shell syntax checks pass.

Operational FMP bmo/amc timing coverage remains passed with historical timestamp/vendor vintage unproven. Fiscal-quarter/original-release verification limitations remain. A5 common-stock status between matching reference anchors is an operational approximation and does not prove uninterrupted listing or ticker ownership. These constraints prevent treating contract coverage alone as a completed research-feasibility verdict.

No holdout, ten-day outcomes, reaction, X or P&L were acquired or inspected in this step.

Primary schema sources: [OPRA.PILLAR](https://databento.com/docs/venues-and-datasets/opra-pillar), [instrument definitions](https://databento.com/docs/schemas-and-data-formats/instrument-definitions), [BBO](https://databento.com/docs/schemas-and-data-formats/bbo).
