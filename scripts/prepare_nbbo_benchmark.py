"""Pause A6 and choose a representative, outcome-blind 20-event benchmark."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    out = ROOT/'data/cache/nbbo_benchmark_selection'
    if (out/'manifest.json').exists():
        print('Benchmark selection exists; no rewrite'); return 2
    now = datetime.now(timezone.utc).isoformat()
    frozen_file = ROOT/'data/cache/frozen_development_sample/manifest.json'
    frozen = json.loads(frozen_file.read_text())
    frozen.update(status='paused', paused_at=now, operationally_active=False,
                  reason='User requests representative benchmark before population decision')
    frozen_file.write_text(json.dumps(frozen, indent=2)+'\n')
    assert not (ROOT/'data/raw/frozen_sample_nbbo/manifest.json').exists()
    with (ROOT/'EXPERIMENT.md').open('a') as f:
        f.write(f'''\n\n### Amendment A6 pause — benchmark before population decision\n\nRecorded at: {now}\nThe user paused A6 before any sample acquisition. Its local 2,100-event artifact and amendment had already been created, but are now inactive and preserved solely as an audit trail. No quotes, X, reactions, strategy outcomes or holdout data were acquired for that sample. The full 14,340-event universe remains the population for deciding between full acquisition and the proposed deterministic sample. Restore the prior 2,500-request ceiling during the 20-event benchmark; the 4 GB transfer ceiling remains.\n\nSelect 20 benchmark events independently of outcomes: 10 train and 10 validation. Within each split, sort by entry session, release date, issuer CIK and symbol and divide into five equal-count chronological strata. Within each stratum sort by the stored pre-event trailing-20-session median dollar volume, split into lower and upper halves, and select one event from each half by smallest SHA256 of issuer CIK|release date|fiscal year|quarter. No X or post-event inputs enter selection. Acquire complete fixed pre-event windows sequentially, including pagination, and measure actual transferred bytes and end-to-end runtime. Report split-specific S0 success and extrapolate by split weights to the full universe, with uncertainty and provider/transfer limits disclosed. Retain the full universe if projected acquisition is at most 90 minutes and operationally feasible; otherwise return to the proposed deterministic sample. No X, reaction, outcome or subsequent-return inspection during this benchmark.\n''')
    with (ROOT/'DATA_AUDIT.md').open('a') as f:
        f.write('\n\n## A6 paused: 20-event NBBO benchmark only\n\nThe latest user instruction pauses the 2,100-event sample and its acquisition authorization pending the representative pre-event NBBO benchmark. No sampled quotes were acquired. EXPERIMENT.md A6 pause controls population selection; do not invoke the frozen-sample acquisition while paused. No X/reactions/outcomes/holdout in the benchmark.\n')
    source = ROOT/'data/cache/reference_bracketing/eligible_events.jsonl'
    blob = source.read_bytes()
    rows = [json.loads(line) for line in blob.splitlines()]
    selected = []
    for split in ['train', 'validation']:
        ordered = sorted([r for r in rows if r['split']==split],
                         key=lambda r:(r['entry_session'], r['release_date'], r['issuer_cik'], r['symbol']))
        for index in range(5):
            group = ordered[len(ordered)*index//5:len(ordered)*(index+1)//5]
            group.sort(key=lambda r:(float(r['median20_close_times_volume']),r['issuer_cik'],r['release_date']))
            for label, half in [('lower',group[:len(group)//2]),('upper',group[len(group)//2:])]:
                def key(r):
                    text = '|'.join(str(r[f]) for f in ['issuer_cik','release_date','fiscal_year','fiscal_quarter'])
                    return hashlib.sha256(text.encode()).hexdigest(), text, r['stable_identifier'], r['symbol']
                row = min(half, key=key)
                selected.append({**row,'sample_sha256':key(row)[0],
                                 'benchmark_time_stratum':index+1,'benchmark_liquidity_half':label,
                                 'stratum_population':len(half)})
    encoded = ''.join(json.dumps(r,sort_keys=True)+'\n' for r in selected).encode()
    out.mkdir(parents=True,exist_ok=True)
    (out/'events.jsonl').write_bytes(encoded)
    manifest = {'selected_at':now,'source_sha256':hashlib.sha256(blob).hexdigest(),
                'sample_sha256':hashlib.sha256(encoded).hexdigest(), 'counts':{'train':10,'validation':10},
                'population_counts':{'train':8688,'validation':5652},
                'method':'Five equal-count chronological strata per split; one hashed event from lower and upper pre-event liquidity halves per stratum',
                'outcome_blind':True,'not_a_strategy_sample':True}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    ledger_path = ROOT/'data/cache/acquisition_budget.json'
    ledger = json.loads(ledger_path.read_text())
    ledger.update(authority='EXPERIMENT.md A6 pause / benchmark',request_ceiling=2500,
                  remaining_requests=2500-ledger['cumulative_requests'])
    ledger_path.write_text(json.dumps(ledger,indent=2)+'\n')
    print(json.dumps(manifest,indent=2)); return 0

if __name__=='__main__':
    raise SystemExit(main())
