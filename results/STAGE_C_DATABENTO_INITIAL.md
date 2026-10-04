# Stage C initial historical contract capability

Stage C began after local historical-status bracketing established sufficient operational candidate capacity. Seven bounded Databento OPRA.PILLAR symbology/metadata requests succeeded. No Massive reference acquisition occurred.

The two explicit capability contracts are MSFT 2023-05-05 strike-150 call and put, previously recorded in Stage A. Both resolve historically on 2023-04-25. They are capability examples; they are not the preregistered ATM selection and do not contribute to primary coverage.

| Historical metadata query | Result |
|---|---:|
| Resolved explicit contracts | 2 |
| Definition records, 2023-04-25 | 2 |
| cbbo-1m records, [19:45, 19:55) UTC on 2023-04-25 | 40 |
| Estimated combined billable data size | 3,920 bytes |
| Estimated combined retrieval cost | $0.000009313225 |
| Actual metadata response bytes | 426 |

No market-data retrieval or strategy outcome inspection was executed. Counts do not prove quote validity, timestamp suitability, entitlement to retrieval, or the required representative contract coverage. Metadata estimates are recorded separately from actual acquisition bytes.

Primary ATM coverage has a hard prerequisite blocker: no complete pre-event underlying NBBO spot or historically selected ATM contract identities are stored. The fixed strike-150 examples cannot substitute for that selection. The ≥80% historical options-contract coverage gate therefore remains unmeasured. Historical earnings timestamp/vintage verification also remains unproven.

The acquisition ledger now totals 1,217 requests and 908,940,143 response bytes, leaving 1,283 requests and 3,091,059,857 bytes under the 2,500-request / 4 GB ceilings. Reproduction and bounded parameters are in `scripts/stage_c_databento_metadata.py` and `data/raw/stage_c_databento_metadata/manifest.json`. No holdout, returns, or P&L were inspected.
