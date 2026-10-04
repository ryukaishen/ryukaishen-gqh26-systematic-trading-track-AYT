"""Prospective deterministic development sample; never inspect market signals."""
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'data/cache/frozen_development_sample'

def main():
    if (OUT/'manifest.json').exists():
        print('Frozen sample already exists; refusing to overwrite')
        return 2
    source = ROOT/'data/cache/reference_bracketing/eligible_events.jsonl'
    blob = source.read_bytes()
    rows = [json.loads(line) for line in blob.splitlines()]
    assert Counter(r['split'] for r in rows) == {'train': 8688, 'validation': 5652}
    now = datetime.now(timezone.utc).isoformat()
    amendment = f'''\n\n### Amendment A6 — frozen outcome-blind development sample\n\nRecorded at: {now}\nAuthorization: Explicit user instruction before any strategy returns or X values were inspected.\n\nFull-universe NBBO acquisition is operationally impractical. From the 14,340 operationally eligible events, rank independently within each split by the ascending SHA256 hex digest of the UTF-8 literal `stable_issuer_id|event_date|fiscal_year|fiscal_quarter`. Define stable_issuer_id as the stored zero-padded issuer CIK (not ticker or share-class FIGI), event_date as the ISO earnings release_date, and fiscal labels as their stored canonical strings (year and Q1–Q4). No whitespace is added around pipes. Resolve a hash tie lexicographically by that same input string, then stable share-class identifier and ticker. Freeze the first 1,500 train and 600 validation events. Failures or missing data remain exclusions within the frozen denominator; never backfill or expand after X or returns are observed. Preserve this exact deterministic ranking rule for the eventual holdout; holdout sample size remains unspecified and no holdout access is authorized now.\n\nRaise the cumulative operational acquisition request ceiling to 50,000 requests for this fixed sample, allowing quote pagination, cost metadata, historical definitions, selected-pair quotes and preregistered pre-decision stock/SPY/beta/action inputs. The 4,000,000,000-byte cumulative transfer ceiling remains unchanged. This authorization replaces pilot-only symbol restrictions with event-root Databento [ROOT].OPT historical definition queries, and authorizes only selected-pair cbbo-1m in the fixed pre-event window. Obtain provider cost/size estimates before billable retrieval; the existing USD 1.00 cost stop remains until a larger concrete estimate is approved.\n\nCompute S0, M, the completed pre-decision reaction r and residual a, X and feasibility counts only on this sample. No subsequent ten-session returns, P&L, or holdout acquisition/inspection is authorized. This amendment precedes any strategy returns or X inspection. All hypotheses, signals, price/liquidity thresholds, contract selection, beta/action treatment, quote quality, splits, boundary purging, holdout protections and outcome rules remain unchanged. FMP timing and A5 historical-status approximations and their limitations remain explicit.\n'''
    with (ROOT/'EXPERIMENT.md').open('a') as f:
        f.write(amendment)
    with (ROOT/'DATA_AUDIT.md').open('a') as f:
        f.write('\n\n## Frozen-sample execution A6\n\nEXPERIMENT.md A6 prospectively freezes 1,500 train / 600 validation by issuer-CIK/release-date/fiscal-year/quarter SHA256 ranking. It supersedes the pilot-only parent-chain prohibition for historical event-root definitions and authorizes pre-decision reaction inputs. Preserve fixed windows, historical-only selection and all signal rules. Never replace failed sampled events. Total requests: 50,000; cumulative bytes: 4 GB; existing USD 1 cost stop remains pending concrete larger-cost approval. No holdout or subsequent ten-session returns.\n')
    selected = []
    for split, count in [('train', 1500), ('validation', 600)]:
        ranked = []
        for row in rows:
            if row['split'] != split:
                continue
            text = '|'.join(str(row[f]) for f in
                            ['issuer_cik', 'release_date', 'fiscal_year', 'fiscal_quarter'])
            row = {**row, 'sample_key': text,
                   'sample_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()}
            ranked.append(row)
        ranked.sort(key=lambda r: (r['sample_sha256'], r['sample_key'], r['stable_identifier'], r['symbol']))
        selected.extend({**r, 'sample_rank': i+1} for i, r in enumerate(ranked[:count]))
    encoded = ''.join(json.dumps(r, sort_keys=True)+'\n' for r in selected).encode()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'events.jsonl').write_bytes(encoded)
    manifest = {'frozen_at': now, 'source_sha256': hashlib.sha256(blob).hexdigest(),
                'sample_sha256': hashlib.sha256(encoded).hexdigest(),
                'counts': dict(Counter(r['split'] for r in selected)),
                'ranking_fields': ['issuer_cik', 'release_date', 'fiscal_year', 'fiscal_quarter'],
                'ranking_encoding': 'UTF-8, literal pipe separators, no whitespace',
                'no_backfill': True, 'before_X_or_strategy_returns': True}
    (OUT/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    path = ROOT/'data/cache/acquisition_budget.json'
    budget = json.loads(path.read_text())
    budget.update(authority='EXPERIMENT.md A6', request_ceiling=50000,
                  remaining_requests=50000-budget['cumulative_requests'])
    path.write_text(json.dumps(budget, indent=2)+'\n')
    print(json.dumps(manifest, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
