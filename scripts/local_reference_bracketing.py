"""Local A5 bracketing and conservative issuer-quarter consolidation."""
import hashlib
import json
from pathlib import Path
from bisect import bisect_left
from collections import defaultdict, Counter
from decimal import Decimal
from development_calendar import SESSIONS, session_index
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/cache/reference_bracketing'

def qualifies(r):
    return (r and r.get('type')=='CS' and r.get('market')=='stocks' and r.get('locale')=='us'
            and r.get('active') is True and r.get('primary_exchange') and r.get('cik')
            and (r.get('share_class_figi') or r.get('composite_figi')))

def main():
    raw=ROOT/'data/raw/historical_reference';m=json.loads((raw/'manifest.json').read_text())
    assert m['status']=='completed'
    snapshots=defaultdict(dict)
    for e in m['requests']:
        b=(raw/e['file']).read_bytes();assert hashlib.sha256(b).hexdigest()==e['sha256']
        for line in b.splitlines():
            r=json.loads(line);snapshots[e['date']][r['ticker']]=r
    anchors=sorted(snapshots)
    pairs=[json.loads(l) for l in (ROOT/'data/cache/stage_b2/full_timing_gate_pairs.jsonl').read_text().splitlines()]
    keys={(r['symbol'],r['date']) for r in pairs};fiscal=defaultdict(set)
    fmp=ROOT/'data/raw/fmp_stage_b1';fm=json.loads((fmp/'manifest.json').read_text())
    for e in fm['requests']:
        if not e.get('file'):continue
        b=(fmp/e['file']).read_bytes();assert hashlib.sha256(b).hexdigest()==e['sha256']
        for line in b.splitlines():
            r=json.loads(line);k=(r['symbol'],r['date'])
            if k in keys:fiscal[k].add((str(r.get('fiscalYear')),str(r.get('fiscalPeriod'))))
    liquidity={(r['symbol'],r['date']):r for r in map(json.loads,(ROOT/'data/cache/stage_b2/liquidity_survivors.jsonl').read_text().splitlines())}
    records=[];status_by_split=defaultdict(Counter);accepted=[]
    for info in pairs:
        opts=[]
        for day,o in info['options'].items():
            if o['liquidity']!='pass':continue
            j=bisect_left(anchors,day);a=b=None
            if j<len(anchors) and anchors[j]==day:
                a=b=day;r=snapshots[day].get(info['symbol'])
                status='exact_date_verified' if qualifies(r) else 'unresolved_or_nonqualifying_exact_date'
            elif 0<j<len(anchors):
                a,b=anchors[j-1],anchors[j];r=snapshots[a].get(info['symbol']);right=snapshots[b].get(info['symbol'])
                status='unresolved_missing_or_nonqualifying_bracket'
                if qualifies(r) and qualifies(right):
                    fields=('ticker','type','cik','composite_figi','share_class_figi')
                    if all(r.get(f)==right.get(f) for f in fields):status='bracket_verified_operationally'
                    else:status='unresolved_ticker_type_identifier_change'
            else:r=None;status='unresolved_unbracketed'
            opts.append({'entry_session':day,'split':o['split'],'reference_status':status,'left_anchor':a,'right_anchor':b,
                         'issuer_cik':str(r['cik']).zfill(10) if qualifies(r) else None,
                         'stable_identifier':(r.get('share_class_figi') or r.get('composite_figi')) if qualifies(r) else None})
        statuses={o['reference_status'] for o in opts};ids={o['issuer_cik'] for o in opts}
        known=statuses.issubset({'exact_date_verified','bracket_verified_operationally'}) and len(ids)==1
        split_set={o['split'] for o in opts}
        final_status=('exact_date_verified' if statuses=={'exact_date_verified'} else 'bracket_verified_operationally') if known else 'unresolved_excluded'
        if len(split_set)!=1:final_status='unresolved_excluded'
        item={**info,'fiscal_labels':[list(v) for v in sorted(fiscal[(info['symbol'],info['date'])])],
              'bracket_status':final_status,'reference_options':opts}
        records.append(item)
        for split in split_set:status_by_split[split][final_status]+=1
        if final_status=='unresolved_excluded' or not info['usable_timing'] or len(fiscal[(info['symbol'],info['date'])])!=1:continue
        year,quarter=next(iter(fiscal[(info['symbol'],info['date'])]))
        if not year.isdigit() or quarter not in ('Q1','Q2','Q3','Q4'):continue
        liq=liquidity.get((info['symbol'],info['date']))
        if liq is None:continue
        accepted.append({'symbol':info['symbol'],'release_date':info['date'],'time':info['timing_values'][0],
                         'entry_session':opts[0]['entry_session'],'split':opts[0]['split'],
                         'issuer_cik':opts[0]['issuer_cik'],'stable_identifier':opts[0]['stable_identifier'],
                         'fiscal_year':year,'fiscal_quarter':quarter,'reference_status':final_status,
                         'median20_close_times_volume':liq['median20_close_times_volume']})
    groups=defaultdict(list)
    for r in accepted:groups[(r['issuer_cik'],r['fiscal_year'],r['fiscal_quarter'])].append(r)
    events=[];duplicate_unresolved=[];consolidated=0;purged=Counter()
    for key,rows in groups.items():
        release_dates={r['release_date'] for r in rows}
        if len(release_dates)>1:
            duplicate_unresolved.append({'issuer_cik':key[0],'fiscal_year':key[1],'fiscal_quarter':key[2],
                                         'status':'unresolved_original_release_multiple_dates','members':rows});continue
        chosen=sorted(rows,key=lambda r:(-Decimal(r['median20_close_times_volume']),r['stable_identifier']))[0]
        consolidated+=len(rows)-1
        i=SESSIONS.index(chosen['entry_session'])
        if i+10>=len(SESSIONS):
            purged[chosen['split']]+=1;continue
        exit_day=SESSIONS[i+10]
        if chosen['split']=='train' and exit_day>'2024-12-31':
            purged['train']+=1;continue
        events.append({**chosen,'scheduled_exit_session':exit_day,
                       'status':'operational_eligible; release_and_fiscal_vintage_verification_pending'})
    summary={'candidate_status_by_split':{k:dict(v) for k,v in status_by_split.items()},
             'historical_status_supported_pairs':sum(c['exact_date_verified']+c['bracket_verified_operationally'] for c in status_by_split.values()),
             'timed_single_fiscal_supported_pairs':len(accepted),'issuer_fiscal_groups_before_ambiguity':len(groups),
             'multiple_release_date_unresolved_groups':len(duplicate_unresolved),
             'multiple_release_date_unresolved_pairs':sum(len(g['members']) for g in duplicate_unresolved),
             'share_class_or_exact_duplicate_pairs_consolidated':consolidated,'boundary_purged':dict(purged),
             'splits':{},'operational_timing_gate':'passed; unchanged','timestamp_vintage_verification':'unproven',
             'bracketing_limitation':'consistent endpoints do not prove uninterrupted daily listing/type/ownership',
             'fiscal_release_limitation':'vendor quarter labels are not corroborated; no primary executable claim'}
    for split in ('train','validation'):
        v=[r for r in events if r['split']==split]
        issuer_count=len({r['issuer_cik'] for r in v});day_count=len({r['entry_session'] for r in v})
        summary['splits'][split]={'final_operational_eligible_events':len(v),'unique_issuers':issuer_count,
                'unique_symbols':len({r['symbol'] for r in v}),'unique_entry_dates':day_count,
                'final_exact_date_events':sum(r['reference_status']=='exact_date_verified' for r in v),
                'final_bracket_events':sum(r['reference_status']=='bracket_verified_operationally' for r in v),
                'candidate_capacity_sufficient':len(v)>=(600 if split=='train' else 200) and issuer_count>=(50 if split=='train' else 30) and day_count>=(60 if split=='train' else 30),
                'signal_measurable_X_group_minimums':'not measured; no feasibility pass inferred'}
    OUT.mkdir(parents=True,exist_ok=True)
    for filename,data in [('candidate_status.jsonl',records),('eligible_events.jsonl',events),('unresolved_duplicate_groups.jsonl',duplicate_unresolved)]:
        (OUT/filename).write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in data))
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
