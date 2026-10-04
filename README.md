# Earnings reaction beyond the implied-move proxy

A preregistered, interpretable earnings continuation study for Gator Quant Hacks 2026. The economic hypothesis compares a completed earnings stock reaction with a historical ATM straddle-premium move proxy, then trades in the beta-residual reaction direction when `X = abs(r)/M > 1`.

**The original feasibility gate failed.** Historical call/put-pair coverage is 73.94% in train and 63.55% in validation, below the unchanged 80% target. Available-event results are exploratory. Failed events are never replaced, and no profitable or statistically significant result is implied by runnable code.

Start with [the submission PDF](results/final/QUANT_NOTE.pdf), [the editable note](results/final/QUANT_NOTE.md), [machine-readable summary](results/final/summary.json), and [approved specification](EXPERIMENT.md). The note, CSV tables, ledgers, and PNG/PDF/SVG figures regenerate automatically under `results/final/`.

## Environment and dependencies

Use UF HiPerGator Slurm compute nodes for retrieval and substantial processing. No GPUs are required. Acquisition/core analysis uses Python 3.14's standard library. Figures use Matplotlib in an existing Python environment; this workspace uses `/apps/python/3.12/bin/python`, while acquisition uses `/apps/conda/26.7/bin/python`. No packages were installed. `requirements.txt` records the optional plotting dependency for another environment; obtain permission before installing packages on HiPerGator.

Set `DATABENTO_API_KEY`, `MASSIVE_API_KEY`, and `FMP_API_KEY` in the environment or an uncommitted `.env` as appropriate. Never place keys in source, output, command arguments, or commits. Raw licensed data is not redistributed; reproducibility uses local hash-checked receipts and inputs.

## Reproduce from checkpoints

Inside a Slurm compute allocation:

```bash
/apps/conda/26.7/bin/python run_all.py --offline
/apps/conda/26.7/bin/python -m unittest discover -s tests -p 'test_*.py'
```

`--offline` performs no API calls and reads development checkpoints only. It generates coverage, available-event observations, train/validation summary, primary/doubled-cost/conservative-commission/physical-hedge portfolios, annualized metrics, turnover, equity curves, X-bucket research returns, and a quant note. Missing outcomes stay missing; daily closes cannot replace prescribed NBBO references.

## Checkpointed acquisition

The approved quote estimate is $0.029263496349 and 15,710,720 billable bytes, with a 624,933,376-byte transfer bound for 581 selected-symbol batches. Conservative definitions plus quotes remain below $12. The cumulative shared caps are 20,000 requests and 4 GB, including retries and failures.

```bash
sbatch --export=ALL slurm/stage_c_quotes.sbatch
sbatch --export=ALL --dependency=afterok:QUOTE_JOB_ID slurm/submission_development.sbatch
```

Do not submit a duplicate active job. Workers take a global acquisition lock and reserve request, transfer and cost budgets before requests. Completed files and selection identities are reused; incomplete responses retain conservative reservations. Quote acquisition uses four bounded workers and only selected-pair `OPRA.PILLAR cbbo-1m` for `[15:50,15:55)` ET. CBBO timestamps mark completed interval ends; alignment uses the preceding underlying minute bin and requires at least three shared valid observations. The final interval outside the half-open query window is not added. Invalid flags, nonpositive prices/sizes, locked/crossed books and spreads above 20% are rejected.

The downstream demonstration uses the existing fixed outcome-blind 20-event benchmark, without replacement. It is **not** a full-universe strategy sample. The full-universe S0/contract/M population remains intact. The remaining 406 requests before early recovery overhead cannot fund all full-universe stock/SPY reaction and ten-session NBBO windows. The demonstration's exclusions, capacity and borrow limitations must accompany any reported results.

## Frozen holdout, one attempt

Only after development implementation, tests and limitations are complete:

```bash
/apps/conda/26.7/bin/python run_all.py --offline --freeze --holdout-once
```

The freeze records hashes of every script/test/batch file, README, dependencies and specification, plus fixed splits, timing/cost rules and failed feasibility findings. The runner refuses changed code and atomically claims a single holdout state **before** reading any 2026 input or calling its calendar API. It cannot rerun or overwrite the claim. No tuning follows holdout access.

When validated holdout inputs exist at `data/raw/final_holdout/inputs.json`, the one-shot runner evaluates the same frozen observation, regression and portfolio code. The input includes `preregistered_input_validation: true`, events, historical M, windows, bars, actions and optional documented borrow. With no prepared validated holdout inputs, it acquires a bounded raw calendar after freezing and attempts at most three legacy-universe events selected by smallest outcome-blind event SHA256 among unambiguous source bmo/amc and provided fiscal-quarter/year records. Historical reference/identity, liquidity, S0, original option selection, quote quality, reaction, beta/actions and outcome rules are enforced without replacing failures. The pilot is exploratory; an insufficient, blocked or empty sample is inconclusive. Raw calendar counts are not eligible-event counts and never become fabricated performance. Full historical holdout preparation would require separate funded reference/S0/definition/quote/reaction/outcome acquisition. The maximum-three pilot is not described as a full confirmatory holdout evaluation. It cannot reopen, extend dates, replace failures or tune afterward.

## Fixed implementation and disclosure

- Train: 2023-04-03 through 2024-12-31; validation: 2025; holdout entry: 2026-01-01 through 2026-09-18, scheduled last exit 2026-10-02. Purge development holding periods crossing boundaries.
- Beta: intercept OLS over prior 120 sessions, at least 100 paired total returns, clipped to [0,2]. All 20 prior returns are required for RV20. Signal and research inclusion do not depend on execution/borrow status.
- Primary fills: historical execution-window midpoint plus adverse half-spread and 2 bps. Intended shares use completed S1 available before execution. $0.001/share commission; separately report doubled modeled costs and $0.005/share/$1-min orders.
- Capital: $1 million accounting reference, 1% initial equity per issuer, 50% stock gross allocation cap, fixed shares, no discretionary exits; all orders in a security/window share 1% observed volume. Preserve partial/unfilled orders and unresolved exposure.
- Cash dividends/splits are action-adjusted. Historical short borrow is mandatory; absent evidence excludes executable shorts and short hedge legs, not predictive observations. No fictitious borrow availability or short-proceeds interest.
- Modeled SEC/FINRA sell fees are date-based. Exchange/CAT route pass-through is unresolved, so results are net of modeled costs, not every possible fee. Complex action completeness, true attainability and minute-sampled liquidity remain limitations.
- Primary inference: OLS `Y_research ~ 1 + I(X>1) + abs(r) + RV20`, two-way issuer/date clustering. Fewer than 30 clusters in either dimension is unreliable; absent groups/rank deficiency are inconclusive. No threshold tuning, outcome trimming or portfolio-based predictive exclusions.
- FMP original-release timestamps/vendor vintage and uninterrupted common-stock status between historical reference brackets are not proven. Do not infer that operational eligibility verifies these facts.

Main-track submission takes priority; no Massive 8-K bonus work is included.
