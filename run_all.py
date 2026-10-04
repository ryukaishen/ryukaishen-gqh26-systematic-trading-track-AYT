#!/usr/bin/env python3
"""Reproduce frozen public artifacts without reopening validation outcomes."""
import os, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent

def main():
    if sys.argv[1:] not in ([], ['--offline']):
        raise SystemExit('Submission sealed. Use python run_all.py --offline; acquisition and reevaluation are disabled.')
    env = {**os.environ, 'MPLCONFIGDIR': str(ROOT/'results/final/.matplotlib'), 'MPLBACKEND': 'Agg'}
    plotting_python = Path('/apps/python/3.12/bin/python')
    subprocess.run([str(plotting_python) if plotting_python.exists() else sys.executable,
                    str(ROOT/'scripts/plot_final.py')], env=env, check=True)
    print('Reproduced figures and 3-page PDF from frozen public result checkpoints; no outcome reevaluation.')

if __name__ == '__main__':
    main()
