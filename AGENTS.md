# Gator Quant Hacks 2026

This repository is being built during Gator Quant Hacks by a solo participant.

## Environment
- Running on UF HiPerGator.
- Project root: /blue/ai-workshop/adamtang/gqh26
- Development occurs inside a Slurm interactive compute job.
- Do not move active project data to /home or /orange.
- Never run resource-intensive work on a HiPerGator login node.

## Resource rules
- Do not request GPUs unless explicitly approved by the user.
- Ask before launching long-running or large Slurm jobs.
- Ask before installing new packages.
- Prefer efficient resource requests and parallelize only when justified.

## Security
- Never hard-code, print, commit, or expose API keys.
- Secrets belong in .env or environment variables.
- Never commit .env.
- Do not use prohibited models or services under UF HiPerGator policy.

## Project
Goal: build a rigorous systematic trading submission, potentially using options and corporate-event data, with strong economic rationale, realistic backtesting, risk analysis, and robust out-of-sample testing.

Prioritize:
1. reproducibility
2. no look-ahead/data leakage
3. realistic transaction costs
4. train/validation/holdout separation
5. robustness over headline returns
6. simple interpretable baselines before complex models

Do not invent financial results or silently alter methodology to improve performance.
