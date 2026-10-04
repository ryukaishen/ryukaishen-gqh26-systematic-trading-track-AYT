#!/bin/bash
#SBATCH --job-name=gqh26-development
#SBATCH --account=ai-workshop
#SBATCH --qos=ai-workshop
#SBATCH --partition=hpg-default
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=01:00:00
#SBATCH --chdir=/blue/ai-workshop/adamtang/gqh26
#SBATCH --output=/blue/ai-workshop/adamtang/gqh26/results/final/development-%j.log
#SBATCH --open-mode=append
set -euo pipefail
umask 077
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
/apps/conda/26.7/bin/python -u scripts/downstream_acquire.py
/apps/conda/26.7/bin/python -u run_all.py --offline
