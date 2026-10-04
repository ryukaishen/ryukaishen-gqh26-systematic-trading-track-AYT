# Earnings reaction beyond the implied-move proxy

A preregistered, interpretable earnings continuation study for Gator Quant Hacks 2026. The economic hypothesis compares a completed earnings stock reaction with a historical ATM straddle-premium move proxy, then trades in the beta-residual reaction direction when `X = abs(r)/M > 1`.

**The original feasibility gate failed.** Historical call/put-pair coverage is 73.94% in train and 63.55% in validation, below the unchanged 80% target. Available-event results are exploratory. Failed events are never replaced, and no profitable or statistically significant result is implied by runnable code.

Start with [the submission PDF](results/final/QUANT_NOTE.pdf), [the editable note](results/final/QUANT_NOTE.md), [machine-readable summary](results/final/summary.json), and [approved specification](EXPERIMENT.md). The note, CSV tables, ledgers, and PNG/PDF/SVG figures regenerate automatically under `results/final/`.

## Environment and dependencies

Use UF HiPerGator Slurm compute nodes for retrieval and substantial processing. No GPUs are required. Acquisition/core analysis uses Python 3.14's standard library. Figures use Matplotlib in an existing Python environment; this workspace uses `/apps/python/3.12/bin/python`, while acquisition uses `/apps/conda/26.7/bin/python`. No packages were installed. `requirements.txt` records the optional plotting dependency for another environment; obtain permission before installing packages on HiPerGator.

Set `DATABENTO_API_KEY`, `MASSIVE_API_KEY`, and `FMP_API_KEY` in the environment or an uncommitted `.env` as appropriate. Never place keys in source, output, command arguments, or commits. Raw licensed data is not redistributed; reproducibility uses local hash-checked receipts and inputs.

## One-command public artifact reproduction

```bash
python run_all.py --offline
```

This renders committed derived result checkpoints into figures and the three-page PDF, without API access, raw-data dependencies or reevaluating 2025 outcomes. Python >=3.10 and Matplotlib from requirements.txt are sufficient; the existing HiPerGator plotting interpreter is used when present. This is artifact reproduction, not a fresh independent raw-data backtest. Licensed raw/cache data remains local and excluded from Git. Original acquisition scripts and receipts document the completed quote/M pipeline; the submission runner disables further acquisition or evaluation.

## Final OOS disclosure

2025 was used for data-feasibility/coverage checks, with no recorded strategy-return inspection or return-based tuning of thresholds, sizing, costs or holding period. It is the primary separated OOS period, but the fixed benchmark has zero measurable signals/outcomes and zero trades: OOS performance is unavailable. Earlier development and post-freeze reports already processed these exclusions; no further 2025 outcome evaluation is performed. Full-universe OOS performance was not acquired.

Train and 2025 base/doubled-cost results: zero entries, annualized return/volatility/Sharpe/drawdown unavailable, annualized turnover 0. No measurable X buckets exist; empty panels report this explicitly. Historical M is valid for 7 train and 917 validation events in the full universe, but none in the fixed 20-event downstream benchmark. Changing or expanding that sample would alter the analysis and has not been done.

Full confirmatory 2026 acquisition was not completed under the fixed budget. The already-completed max-three pilot is exploratory only, with zero measurable outcomes or trades. It does not satisfy confirmatory OOS. No further pilot work is authorized by the runner. Original freeze and pilot claims are preserved; the final submission seal hashes strategy code and public artifacts. No methodology is changed after freeze.

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
