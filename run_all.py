#!/usr/bin/env python3
"""Reproduce submission artifacts; acquisition and holdout require explicit modes."""
import argparse,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT/'scripts'))
def main():
 p=argparse.ArgumentParser();p.add_argument('--offline',action='store_true');p.add_argument('--freeze',action='store_true');p.add_argument('--holdout-once',action='store_true');args=p.parse_args()
 if not os.environ.get('SLURM_JOB_ID') and os.uname().nodename.startswith('login'):raise SystemExit('Run on a Slurm compute node; no substantial login-node analysis.')
 if args.freeze:
  from final_holdout import freeze
  freeze()
 if args.holdout_once:
  from final_holdout import evaluate_once
  evaluate_once()
 from final_report import generate
 generate()
if __name__=='__main__':main()
