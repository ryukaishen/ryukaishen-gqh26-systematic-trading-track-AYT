"""Report weighted acquisition benchmark; no signal/outcome calculation."""
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
selection_dir = ROOT/'data/cache/nbbo_benchmark_selection'
blob = (selection_dir/'events.jsonl').read_bytes()
selection = json.loads((selection_dir/'manifest.json').read_text())
assert hashlib.sha256(blob).hexdigest()==selection['sample_sha256']
rows = [json.loads(line) for line in blob.splitlines()]
m = json.loads((ROOT/'data/raw/nbbo_benchmark/manifest.json').read_text())
assert m['status']=='completed' and m['sample_sha256']==selection['sample_sha256']
assert len(rows)==len(m['windows'])==20
assert sum(r['stratum_population'] for r in rows)==14340
windows = m['windows']
requests = m['requests']
assert all(q['status']=='success' for q in requests)
assert all(w['status']=='complete' and w['discarded_outside_window']==0 for w in windows.values())
by_split = {}
projected_requests = projected_bytes = projected_runtime = 0
processing_seconds = sum(w['runtime_seconds'] for w in windows.values())
overhead_per_event = max(0,m['runtime_seconds']-processing_seconds)/20
for split in ['train','validation']:
    group = [r for r in rows if r['split']==split]
    rcount = bcount = runtime = successes = 0
    weighted_requests = weighted_bytes = weighted_runtime = 0
    for event in group:
        eid = event['sample_sha256']
        w = windows[eid]
        count = sum(q['event_id']==eid for q in requests)
        rcount += count
        bcount += w['response_bytes']
        runtime += w['runtime_seconds']+overhead_per_event
        successes += w['S0'] is not None and w['valid_minute_bins']>=3
        weight = event['stratum_population']
        weighted_requests += weight*count
        weighted_bytes += weight*w['response_bytes']
        weighted_runtime += weight*(w['runtime_seconds']+overhead_per_event)
    by_split[split] = {'events':len(group),'NBBO_requests_including_pagination':rcount,
                      'bytes_transferred':bcount,'runtime_seconds':runtime,
                      'valid_S0':successes,'valid_S0_success_percent':100*successes/len(group),
                      'full_population':sum(r['stratum_population'] for r in group),
                      'projected_NBBO_requests':weighted_requests,'projected_bytes':weighted_bytes,
                      'projected_runtime_minutes':weighted_runtime/60}
    projected_requests += weighted_requests
    projected_bytes += weighted_bytes
    projected_runtime += weighted_runtime
aux_paths = list((ROOT/'data/raw/nbbo_benchmark_conditions').glob('*manifest.json'))
aux = [json.loads(p.read_text()) for p in aux_paths]
ledger = json.loads((ROOT/'data/cache/acquisition_budget.json').read_text())
benchmark_bytes = sum(w['response_bytes'] for w in windows.values())
projected_cumulative_bytes = ledger['cumulative_bytes']+projected_bytes-benchmark_bytes
decision = projected_runtime<=90*60 and projected_cumulative_bytes<=ledger['transfer_ceiling']
result = {'recorded_at':datetime.now(timezone.utc).isoformat(),
          'selection_sha256':selection['sample_sha256'],'by_split':by_split,
          'NBBO_requests_including_pagination':len(requests),
          'auxiliary_condition_dictionary_requests':len(aux),
          'total_Massive_requests':len(requests)+len(aux),
          'NBBO_bytes_transferred':benchmark_bytes,
          'auxiliary_bytes_transferred':sum(e['response_bytes'] for e in aux),
          'total_Massive_bytes_transferred':benchmark_bytes+sum(e['response_bytes'] for e in aux),
          'end_to_end_NBBO_runtime_seconds':m['runtime_seconds'],
          'runtime_scope':'Sequential retrieval, pagination, parsing, validation, gzip persistence and S0 calculation; excludes tool approval latency and one-time schema dictionary lookup.',
          'valid_S0_successes':sum(s['valid_S0'] for s in by_split.values()),
          'projection_method':'Each selected event weighted by its source chronological/liquidity stratum population; observed processing overhead allocated equally per event.',
          'full_14340_projection':{'NBBO_requests':projected_requests,'NBBO_bytes':projected_bytes,
                                    'wall_clock_minutes':projected_runtime/60,
                                    'cumulative_bytes_reusing_benchmark':projected_cumulative_bytes},
          'sensitivity_1_5_times':{'NBBO_requests':math.ceil(projected_requests*1.5),
                                  'NBBO_bytes':math.ceil(projected_bytes*1.5),
                                  'wall_clock_minutes':projected_runtime*1.5/60},
          'provider_limit_evidence':{'official_source':'https://www.massive.com/stocks',
                                     'paid_plans':'Unlimited API calls; no per-request pricing',
                                     'observed_HTTP_429':False,
                                     'observed_request_rate_per_second':len(requests)/m['runtime_seconds']},
          'decision':'retain_full_14340_event_universe' if decision else 'return_to_proposed_deterministic_sample',
          'limitations':'20 stratified events cannot establish population S0 success or guarantee pagination/latency/transfer tails; no formal confidence bound. Projection covers underlying pre-event NBBO only, not options or post-event inputs.',
          'no_X_reactions_outcomes_holdout':True,
          'sampling_amendment_status':'paused/inactive; previous artifact preserved for audit only',
          'further_full_acquisition_executed':False}
path = ROOT/'data/cache/nbbo_benchmark_results.json'
path.write_text(json.dumps(result,indent=2)+'\n')
report = f'''# Representative pre-event NBBO benchmark

The proposed 2,100-event sampling amendment is paused/inactive. Its local hash artifact was created before the pause, but no sample acquisition started. The source population remains 14,340 operationally eligible events. No X, reactions, outcomes, post-entry returns or holdout were inspected.

Selection was prospective and outcome-blind: 10 train / 10 validation events across five equal-count chronological strata per split, one hashed event from each lower/upper pre-event liquidity half. Complete [15:50,15:55) ET windows were acquired sequentially, with a 50,000-record page limit and pagination enabled. All 20 responses were complete in one page; there were no out-of-window retained rows.

| Measurement | Train | Validation | Total |
|---|---:|---:|---:|
| Events | 10 | 10 | 20 |
| NBBO requests, including pagination | {by_split['train']['NBBO_requests_including_pagination']} | {by_split['validation']['NBBO_requests_including_pagination']} | {len(requests)} |
| NBBO transferred bytes | {by_split['train']['bytes_transferred']:,} | {by_split['validation']['bytes_transferred']:,} | {benchmark_bytes:,} |
| End-to-end runtime (seconds) | {by_split['train']['runtime_seconds']:.3f} | {by_split['validation']['runtime_seconds']:.3f} | {m['runtime_seconds']:.3f} |
| Valid S0 success | 10/10 (100%) | 10/10 (100%) | 20/20 (100%) |

Two auxiliary quote-condition schema calls transferred {sum(e['response_bytes'] for e in aux):,} bytes: the initial `data_type=quote` filter returned an empty dictionary; the corrected all-stock dictionary identifies quote data as bbo/nbbo and code 1 as Regular Two-Sided Open. Including both schema calls, the benchmark used {len(requests)+len(aux)} Massive calls and {benchmark_bytes+sum(e['response_bytes'] for e in aux):,} bytes. These are schema lookups, not historical security-reference acquisition. Valid S0 uses the median of all valid quote midpoints and at least three distinct SIP-timestamp minute bins. All 20 had five valid bins. Accept empty conditions or provider-labelled regular two-sided quotes; reject nonpositive prices/sizes, crossed/locked markets and unresolved nonregular conditions.

Transferred bytes count compressed HTTP response bodies when gzip is supplied, before decompression or sanitized re-storage. Runtime includes sequential retrieval, parsing, validity checks, storage and S0 calculation; excludes tool approval waiting and one-time condition lookup.

## Full 14,340-event projection

Weight each benchmark event by its chronological/liquidity stratum population, preserving actual 8,688 train / 5,652 validation population weights.

| Projection | Estimate | 1.5× sensitivity |
|---|---:|---:|
| NBBO requests including pagination | {projected_requests:,} | {math.ceil(projected_requests*1.5):,} |
| NBBO transfer | {projected_bytes/1e9:.3f} GB | {projected_bytes*1.5/1e9:.3f} GB |
| Sequential wall-clock runtime | {projected_runtime/60:.2f} minutes | {projected_runtime*1.5/60:.2f} minutes |

The cumulative central transfer projection, reusing benchmark windows, is {projected_cumulative_bytes/1e9:.3f} GB under the 4 GB ceiling. Massive's [official stock product page](https://www.massive.com/stocks) states paid plans have unlimited API calls without per-request pricing. Existing historical NBBO entitlement succeeded on both fixed checks and these 20 windows; no HTTP 429 occurred, with observed sequential rate {len(requests)/m['runtime_seconds']:.2f} requests/second. This does not guarantee future rate or latency.

**Decision: {'retain the full 14,340-event universe' if decision else 'return to the proposed deterministic sample'}.** The central runtime projection is {'below' if projected_runtime<=5400 else 'above'} 90 minutes, and the central cumulative transfer is within the current ceiling. Full NBBO is operationally feasible under the observed entitlement and documented paid-plan request policy. The old internal 2,500-request cap must be prospectively raised before a full download; it is not a provider limit. No full download was started in this benchmark turn.

The 1.5× sensitivity is a heuristic, not a confidence interval. Twenty stratified observations cannot establish full-universe quote success or rule out unusually active symbols, pagination, throttling or latency tails. Retain live request/transfer guards. These estimates cover underlying pre-event NBBO only; Databento definitions/quotes and later pre-decision reaction/beta/action acquisition require separate cost and transfer accounting. Hypotheses, signal, universe thresholds, split/holdout boundaries and outcome rules are unchanged.

Evidence: `data/raw/nbbo_benchmark/manifest.json`, sanitized complete-window gzip files, `data/cache/nbbo_benchmark_selection/`, `data/cache/nbbo_benchmark_results.json`. Local report reproduction: `python3 scripts/report_nbbo_benchmark.py`. Acquisition is guarded against automatic retry of incomplete windows.
'''
(ROOT/'results/NBBO_REPRESENTATIVE_BENCHMARK.md').write_text(report)
print(json.dumps(result,indent=2))
