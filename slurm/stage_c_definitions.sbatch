#!/bin/bash
#SBATCH --job-name=gqh26-opra-defs
#SBATCH --account=ai-workshop
#SBATCH --qos=ai-workshop
#SBATCH --partition=hpg-default
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=02:00:00
#SBATCH --chdir=/blue/ai-workshop/adamtang/gqh26
#SBATCH --output=/blue/ai-workshop/adamtang/gqh26/data/raw/stage_c_definitions/slurm-%j.log
#SBATCH --open-mode=append
#SBATCH --signal=B:TERM@60
set -euo pipefail
umask 077
# Inherit credential through the submitted environment; never echo or pass it as argv.
if [[ -z "${DATABENTO_API_KEY:-}" ]]; then
    echo 'BLOCKED: credential absent from job environment'
    exit 2
fi
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
exec /apps/conda/26.7/bin/python -u scripts/stage_c_definitions_job.py --retry-incomplete "$@"
