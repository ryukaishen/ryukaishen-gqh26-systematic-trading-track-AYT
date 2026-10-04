# Massive bonus: repurchase disclosures → cash-secured put

This module is separate from the sealed main DriftMaxx study. **Do not infer Massive eligibility or successful performance from the existence of this module.** Actual status: **incomplete**. The first fixed train event (CVS, 2024-01-05) was excluded when the organizer SEC acceptance-time lookup raised HTTPError. No bonus market-price returns were inspected; OOS remained unopened. Read `results/status.json` for the machine-readable record. An incomplete run must not be appended to the main quant note.

## Preregistration and provenance

- Hypothesis/tag frozen in commit `984478b`; official starter details and chronological pilot cap verified before results in `c06961d`.
- Exact Massive taxonomy tag: `share_repurchase_program`, taxonomy `1.0`, from all 119 semantic category definitions. Definition includes authorizations, expansions and updates, not exclusively new programs.
- Permitted strategy: **Cash-secured put**. No outcome-based category, strategy, horizon, OTM or expiry selection.
- `organizer_source.ipynb` is the supplied official notebook, with source unchanged and no outputs. Original and source-copy hashes are in `config.json`. The wrapper imports the organizer functions directly; it does not recreate TOP_100, contract selection, P&L, calendar, placebo or bootstrap components.

## Fixed run

In a Slurm CPU allocation with the existing Python environment and Massive key in the environment or uncommitted root `.env`:

```bash
/apps/python/3.12/bin/python massive_bonus/run_bonus.py \
  --start 2024-01-01 --end 2025-12-31 \
  --oos-start 2026-01-01 --oos-end 2026-08-31
```

A durable claim prevents rerunning the same attempt. OOS has a separate durable claim before its disclosures are read. To inspect saved status without API calls or analysis:

```bash
python massive_bonus/run_bonus.py --offline
```

The deadline pilot uses the first chronological event in each split (`max_events=1`) and **one** official sampled ordinary day (`N_PLACEBO=1`), with `RUN_PLACEBO=True`, seed 7, 30-day exclusion distance and no backfilling. This is not the default 120-placebo or full-window run. The placebo gap is relative to the capped event sample, as in the unchanged starter code, so other uncapped events may contaminate the baseline. Judge start/end arguments are supported, but use of this capped pipeline must be disclosed. No default full-universe results are implied.

Headline expiry is 3–6m and OTM 5%. All horizons (1,2,3,5,10,21,42,63 sessions and expiry) and the complete 1m/2m/3–6m × 3%/5%/10% sensitivity grid remain in exports. Unresolved/future horizons remain N/A. Official confidence intervals require at least five observations, so this one-event pilot cannot provide them. Missing data, timing failures, entitlement and budget interruptions remain exclusions or explicit stops.

## Trade realism and costs

The original cost formula is unchanged: 5% of absolute entry option premium each way (10% round trip), divided by synthetic entry stock spot. Output is marked option P&L per dollar of chain-implied stock spot, **not** annualized portfolio return or return on cash collateral. Underlying spot is inferred from option put-call parity; standard 100-share selection, the original nearest-target expiry and strike rules, and three-session stale-mark allowance remain unchanged. Aggregates are traded closes, not bid/ask quotes or proven executable fills. This starter does not supply a broker collateral/early-assignment ledger; those limitations prevent a claim of fully realistic executed cash-secured-put returns.

SEC metadata is used only to verify filing acceptance time and apply the starter's next-session correction for acceptance at/after 16:00; all market data comes from Massive. Failure to verify public availability excludes the selected event. The static September-2026 TOP_100 introduces survivorship bias. Retrospective Massive tags also do not prove point-in-time tag availability. Daily-loaded tags cannot be claimed to have been available at the filing close.

## Outputs and stopping

`results/status.json`, selected-event/exclusion CSVs, and any available train/placebo/OOS long results and all-horizon sensitivity CSVs document what actually ran. A horizon plot is written only if all three groups finish; unavailable bootstrap bands are explicitly N/A. No OOS result is manufactured if acquisition stops earlier. Shared main-project request/transfer caps remain in force; network calls have a 120-request and five-minute execution stop. No packages or GPUs are installed/requested.

`results/required_results_status.csv` preserves all 243 split × bucket × OTM × horizon slots as unavailable statuses, not performance estimates. `BONUS_SECTION.md` is a 150–250-word transparent Devpost/README draft; it was not appended to the sealed main submission. No bonus pages were appended to the main PDF.
