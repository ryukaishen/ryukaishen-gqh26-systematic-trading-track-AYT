"""Reconcile exact-date evidence separately from unsupported anchor intervals."""
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw/historical_reference'
OUT=ROOT/'data/cache/historical_reference'


def main():
    m=json.loads((RAW/'manifest.json').read_text()); assert m['status']=='completed'
    snapshots=defaultdict(dict); history=defaultdict(list); exchanges=Counter()
    for e in m['requests']:
        content=(RAW/e['file']).read_bytes(); assert hashlib.sha256(content).hexdigest()==e['sha256']
        for line in content.splitlines():
            r=json.loads(line); ticker=r['ticker']
            assert ticker not in snapshots[e['date']]
            snapshots[e['date']][ticker]=r
            history[ticker].append((e['date'],r))
            exchanges[r.get('primary_exchange','<missing>')]+=1
    pairs=[json.loads(l) for l in (ROOT/'data/cache/stage_b2/full_timing_gate_pairs.jsonl').read_text().splitlines()]
    candidates={(r['symbol'],r['date']) for r in pairs}; fiscal=defaultdict(set)
    fmp=ROOT/'data/raw/fmp_stage_b1'; fm=json.loads((fmp/'manifest.json').read_text())
    for e in fm['requests']:
        if not e.get('file'):continue
        content=(fmp/e['file']).read_bytes(); assert hashlib.sha256(content).hexdigest()==e['sha256']
        for line in content.splitlines():
            r=json.loads(line); key=(r['symbol'],r['date'])
            if key in candidates: fiscal[key].add((str(r.get('fiscalYear')),str(r.get('fiscalPeriod'))))
    statuses=Counter(); mapped=[]; exact=[]; association=[]; pending_dates=set(); pending_symbol_dates=set()
    exception_symbols=defaultdict(set)
    for info in pairs:
        symbol=info['symbol']; key=(symbol,info['date'])
        opts=[day for day,o in info['options'].items() if o['liquidity']=='pass']
        h=history.get(symbol,[])
        ids={str(r.get('cik','')) for _,r in h if r.get('cik')}
        fingerprints={(r.get('cik'),r.get('composite_figi'),r.get('share_class_figi')) for _,r in h}
        if not h: exception_symbols['absent_all_anchors'].add(symbol)
        elif len(h)<len(snapshots): exception_symbols['absent_some_anchors'].add(symbol)
        if len(fingerprints)>1: exception_symbols['identifier_changes'].add(symbol)
        if len(ids)>1: exception_symbols['issuer_changes'].add(symbol)
        item={'symbol':symbol,'date':info['date'],'usable_timing':info['usable_timing'],
              'fiscal_metadata':sorted([list(f) for f in fiscal[key]]),
              'fiscal_conflict':len(fiscal[key])>1,'eligible_entry_options':opts,
              'anchor_observations':len(h),'anchor_ciks':sorted(ids),
              'identifier_versions':len(fingerprints)}
        supported=[]; excluded=[]; unknown=[]
        for day in opts:
            if day not in snapshots:
                unknown.append(day); pending_dates.add(day);pending_symbol_dates.add((symbol,day));continue
            r=snapshots[day].get(symbol)
            if r is None:
                excluded.append(day);continue
            cik=r.get('cik'); sec=r.get('share_class_figi') or r.get('composite_figi')
            if not cik or not sec or not r.get('primary_exchange'):
                unknown.append(day);pending_dates.add(day);pending_symbol_dates.add((symbol,day))
                exception_symbols['missing_exact_identifiers'].add(symbol);continue
            supported.append({'entry_session':day,**{k:r[k] for k in ('cik','composite_figi','share_class_figi','primary_exchange','type','locale','market','active') if k in r}})
        if unknown: status='unresolved_historical_interval_or_identifiers'
        elif excluded and not supported: status='not_in_common_stock_snapshot_at_all_eligible_D'
        elif excluded: status='unresolved_missing_timing_security_eligibility'
        elif supported: status='exact_entry_date_reference_supported'
        else: status='unresolved'
        item.update(reference_status=status,exact_supported=supported,unknown_dates=unknown,exact_common_absent_dates=excluded)
        statuses[status]+=1; mapped.append(item)
        if status=='exact_entry_date_reference_supported': exact.append(item)
        if len(ids)==1 and not item['fiscal_conflict']:
            year,quarter=next(iter(fiscal[key]))
            if year.isdigit() and quarter in ('Q1','Q2','Q3','Q4'):
                association.append({'issuer_cik':next(iter(ids)).zfill(10),'fiscal_year':year,'fiscal_quarter':quarter,
                                    'symbol':symbol,'date':info['date'],'reference_status':status,
                                    'status':'anchor_association_only; identity_interval_and_fiscal_corroboration_pending'})
    def grouped(rows):
        g=defaultdict(list)
        for r in rows:g[(r['issuer_cik'],r['fiscal_year'],r['fiscal_quarter'])].append(r)
        return [{'issuer_cik':k[0],'fiscal_year':k[1],'fiscal_quarter':k[2],
                 'candidate_pairs':[{'symbol':r['symbol'],'date':r['date']} for r in v],
                 'status':'candidate_group_only_original_release_and_fiscal_corroboration_pending'} for k,v in sorted(g.items())]
    exact_fiscal=[]
    for item in exact:
        ids={r['cik'] for r in item['exact_supported']}
        if len(ids)!=1 or item['fiscal_conflict']:continue
        year,quarter=item['fiscal_metadata'][0]
        if year.isdigit() and quarter in ('Q1','Q2','Q3','Q4'):
            exact_fiscal.append({'issuer_cik':next(iter(ids)).zfill(10),'fiscal_year':year,'fiscal_quarter':quarter,
                                'symbol':item['symbol'],'date':item['date']})
    associated_groups=grouped(association);exact_groups=grouped(exact_fiscal)
    summary={'input_candidate_pairs':len(pairs),'input_symbols':len({r['symbol'] for r in pairs}),
             'completed_anchors':len(snapshots),'reference_requests':len(m['requests']),'reference_response_bytes':m['response_bytes'],
             'cumulative_requests':m['prior_requests']+len(m['requests']),
             'cumulative_bytes':m['prior_bytes']+m['response_bytes'],
             'remaining_requests':1500-m['prior_requests']-len(m['requests']),
             'reference_status_counts':dict(statuses),
             'exact_date_common_identifier_supported_pairs':len(exact),
             'exact_date_supported_symbols':len({r['symbol'] for r in exact}),
             'exact_date_vendor_fiscal_groups':len(exact_groups),
             'anchor_associated_pairs':len(association),'anchor_associated_symbols':len({r['symbol'] for r in association}),
             'provisional_anchor_issuer_year_quarter_groups':len(associated_groups),
             'provisional_groups_with_multiple_candidate_pairs':sum(len(g['candidate_pairs'])>1 for g in associated_groups),
             'exceptions_by_symbol':{k:len(v) for k,v in exception_symbols.items()},
             'unresolved_symbol_session_pairs':len(pending_symbol_dates),
             'unresolved_entry_dates':len(pending_dates),
             'optimistic_additional_date_specific_request_lower_bound':len(pending_dates),
             'additional_date_queries_fit_remaining_cap':len(pending_dates)<=1500-m['prior_requests']-len(m['requests']),
             'anchor_exchange_record_counts':dict(exchanges),
             'operational_fmp_timing_gate':'passed train and validation; unchanged',
             'historical_timestamp_vintage_verification':'unproven',
             'full_reference_coverage':'insufficient; anchors do not establish intervals',
             'primary_final_event_count':None,'stage_C':'not executed; prerequisites unmet'}
    OUT.mkdir(parents=True,exist_ok=True)
    for filename,data in [('candidate_reference_status.jsonl',mapped),('provisional_issuer_fiscal_groups.jsonl',associated_groups),('exact_date_issuer_fiscal_groups.jsonl',exact_groups)]:
        (OUT/filename).write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in data))
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
