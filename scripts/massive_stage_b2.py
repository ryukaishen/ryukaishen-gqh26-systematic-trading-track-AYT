"""Amendment A3 acquisition/liquidity screen; never compute strategy outcomes."""
import hashlib
import json
import os
import shlex
from collections import Counter, deque
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from statistics import median
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError
from development_calendar import ACQUISITION_DATES, SESSIONS, SOURCES, EARLY_CLOSES, session_index

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw/massive_grouped_stage_b2'
CACHE=ROOT/'data/cache/stage_b2'
MAX_REQUESTS=1500
MAX_BYTES=4_000_000_000
MAX_FILE_BYTES=10_000_000

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def credential():
    if os.environ.get('MASSIVE_API_KEY'): return os.environ['MASSIVE_API_KEY']
    p=ROOT/'.env'
    if p.is_file():
        for line in p.read_text().splitlines():
            line=line.strip()
            if line.startswith('export '): line=line[7:].strip()
            name,sep,value=line.partition('=')
            if sep and name.strip()=='MASSIVE_API_KEY':
                parts=shlex.split(value,comments=True)
                if len(parts)==1: return parts[0]
    return None

def actual_prior_usage():
    count=size=0
    for name in ['fmp_stage_b1','massive_grouped_pilot','fmp_eod_bulk']:
        m=json.loads((ROOT/'data/raw'/name/'manifest.json').read_text())
        count+=len(m['requests']); size+=m.get('total_response_bytes',m.get('response_bytes',0))
    return count,size

def prior_usage():
    # screen() adds all date entries, including reuse; subtract their prior accounting.
    count,size=actual_prior_usage()
    m=json.loads((RAW/'manifest.json').read_text())
    cached=[e for e in m['requests'] if e.get('reused')]
    return count-len(cached),size-sum(e['response_bytes'] for e in cached)
def screen(manifest):
    candidates=[json.loads(line) for line in (CACHE/'timed_candidates.jsonl').read_text().splitlines()]
    by_session={}; reasons=Counter(); survivors=[]; candidate_symbols={r['symbol'] for r in candidates}
    for r in candidates:
        if r.get('timing_conflict'):
            reasons['conflicting_timing']+=1; continue
        i=session_index(r['date'],r['time'])
        if i is None:
            reasons['outside_development_entry_scope']+=1; continue
        by_session.setdefault(SESSIONS[i],[]).append(r)
    history=deque(maxlen=20)
    logs=[]
    entries={r['date']:r for r in manifest['requests'] if r['status']=='success'}
    for day in ACQUISITION_DATES:
        # Evaluate using strictly earlier completed sessions, before loading D EOD.
        for r in by_session.get(day,[]):
            reason=None; bars=[]
            if len(history)!=20: reason='insufficient_calendar_history'
            else:
                bars=[h.get(r['symbol']) for _,h in history]
                if any(b is None for b in bars): reason='missing_or_invalid_prior_session_bar'
            if reason is None:
                previous=bars[-1][0]
                dv=median([b[0]*b[1] for b in bars])
                if previous < Decimal('10'): reason='previous_close_below_10'
                elif dv < Decimal('20000000'): reason='median_dollar_volume_below_20M'
            if reason:
                reasons[reason]+=1
                logs.append({**r,'entry_session':day,'liquidity_status':reason})
            else:
                item={**r,'entry_session':day,'previous_close':str(previous),
                      'median20_close_times_volume':str(dv),
                      'history_start':history[0][0],'history_end':history[-1][0],
                      'split':'train' if day<='2024-12-31' else 'validation',
                      'status':'liquidity_pass_only_reference_and_event_identity_pending'}
                survivors.append(item); logs.append(item)
        entry=entries[day]; p=RAW/entry['file']; content=p.read_bytes()
        if hashlib.sha256(content).hexdigest()!=entry['sha256']:
            raise ValueError('extract hash mismatch')
        bars={}; invalid=set()
        for line in content.splitlines():
            r=json.loads(line)
            if r['date']!=day: raise ValueError('extract date mismatch')
            symbol=r['symbol']
            if symbol not in candidate_symbols: continue
            try:
                c=Decimal(str(r['close'])); v=Decimal(str(r['volume']))
                if not c.is_finite() or not v.is_finite() or c<=0 or v<0:
                    invalid.add(symbol); continue
                if symbol in bars: invalid.add(symbol)
                bars[symbol]=(c,v)
            except (InvalidOperation,KeyError): invalid.add(symbol)
        for symbol in invalid: bars.pop(symbol,None)
        history.append((day,bars))
    CACHE.mkdir(parents=True,exist_ok=True)
    for filename,rows in [('liquidity_survivors.jsonl',survivors),('liquidity_attrition.jsonl',logs)]:
        (CACHE/filename).write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows))
    count,size=prior_usage()
    count+=len(manifest['requests']); size+=manifest['response_bytes']
    unique_symbols=len({r['symbol'] for r in survivors})
    unique_symbol_sessions=len({(r['symbol'],r['entry_session']) for r in survivors})
    summary={'candidate_pairs':len(candidates),'surviving_events':len(survivors),
             'surviving_symbols':unique_symbols,'surviving_symbol_entry_sessions':unique_symbol_sessions,
             'survivors_by_split':dict(Counter(r['split'] for r in survivors)),
             'exclusions':dict(reasons),'cumulative_requests':count,'cumulative_bytes':size,
             'remaining_requests':MAX_REQUESTS-count,'remaining_bytes':MAX_BYTES-size,
             'reference_single_snapshot_per_symbol_requests':unique_symbols,
             'reference_per_symbol_session_conservative_estimate':unique_symbol_sessions,
             'reference_status':'needs_historical_validity_and_delisting_plan; no calls executed',
             'limitations':['Massive grouped volume may include extended hours; prospective regular-session approximation.',
                            'Survivors are liquidity candidates, not verified U.S. common stocks.',
                            'Historical issuer/fiscal-period identity and original release verification pending.',
                            'No timing-coverage gate or options gate pass inferred.',
                            'Primary ten-session boundary purge remains a separate calendar stage.']}
    (CACHE/'liquidity_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2),flush=True)
    return summary

def main():
    key=credential()
    if not key:
        print('BLOCKED: missing Massive credential'); return 2
    RAW.mkdir(parents=True,exist_ok=True)
    path=RAW/'manifest.json'
    if path.exists():
        m=json.loads(path.read_text())
        if m['status']=='completed': screen(m); return 0
        print('BLOCKED: incomplete existing manifest; no automatic retry.'); return 2
    prior_count,prior_bytes=actual_prior_usage()
    pilot_root=ROOT/'data/raw/massive_grouped_pilot'
    pilot=json.loads((pilot_root/'manifest.json').read_text())
    cached={e['date']:e for e in pilot['requests'] if e['status']=='success' and e['date'] in ACQUISITION_DATES}
    new_count=len(ACQUISITION_DATES)-len(cached)
    allowance=1_833_275
    if prior_count+new_count>MAX_REQUESTS or prior_bytes+new_count*allowance>MAX_BYTES:
        print('BLOCKED: projection exceeds caps'); return 2
    m={'status':'in_progress','amendment':'A3','acquisition_time':datetime.now(timezone.utc).isoformat(),
       'endpoint':'https://api.massive.com/v2/aggs/grouped/locale/us/market/stocks/{date}',
       'parameters':{'adjusted':'false','include_otc':'false'},'fields':['symbol','date','close','volume'],
       'calendar_sources':SOURCES,'dates':ACQUISITION_DATES,'early_closes':sorted(EARLY_CLOSES),
       'prior_requests':prior_count,'prior_bytes':prior_bytes,'requests':[],
       'response_bytes':0,'new_response_bytes':0,'transfer_ceiling':MAX_BYTES,'request_ceiling':MAX_REQUESTS}
    def save(): path.write_text(json.dumps(m,indent=2)+'\n')
    def stop(reason):
        m.update(status='incomplete',stop_reason=reason); save(); print('STOP:',reason,flush=True); return 2
    save(); opener=build_opener(NoRedirect())
    for day in ACQUISITION_DATES:
        entry={'date':day,'status':'attempted','reused':day in cached}
        m['requests'].append(entry); save()
        if day in cached:
            old=cached[day]; content=(pilot_root/old['file']).read_bytes()
            if hashlib.sha256(content).hexdigest()!=old['sha256']: return stop('pilot hash mismatch')
            source=[json.loads(line) for line in content.splitlines()]
            entry.update(http_status=old['http_status'],response_bytes=old['response_bytes'],source_sha256=old['sha256'])
        else:
            n=sum(not e['reused'] for e in m['requests'])
            if prior_count+n>MAX_REQUESTS: return stop('request cap')
            if prior_bytes+m['new_response_bytes']+MAX_FILE_BYTES>MAX_BYTES: return stop('transfer cap')
            req=Request(m['endpoint'].format(date=day)+'?adjusted=false&include_otc=false',
                        headers={'Authorization':'Bearer '+key})
            try:
                with opener.open(req,timeout=30) as response:
                    entry['http_status']=response.status
                    body=response.read(MAX_FILE_BYTES+1)
                entry['response_bytes']=len(body); m['new_response_bytes']+=len(body)
                if len(body)>MAX_FILE_BYTES: return stop('file byte cap')
                payload=json.loads(body); del body
                source=payload.get('results',[])
                if payload.get('adjusted') is not False or not isinstance(source,list):
                    return stop('shape or adjustment mismatch')
                if payload.get('next_url') or payload.get('resultsCount')!=len(source):
                    return stop('incomplete response')
                if not source: return stop('empty required session')
                del payload
            except HTTPError as error:
                entry.update(status='http_failure',http_status=error.code)
                size=len(error.read(MAX_FILE_BYTES+1)); entry['response_bytes']=size
                m['new_response_bytes']+=size; return stop('HTTP failure')
            except (URLError,OSError,TimeoutError,ValueError,TypeError):
                return stop('network or parsing failure')
        safe=[]
        for row in source:
            if not all(k in row for k in ['T','c','v']): return stop('missing liquidity field')
            safe.append({'symbol':row['T'],'date':day,'close':row['c'],'volume':row['v']})
        del source
        encoded=''.join(json.dumps(r,sort_keys=True)+'\n' for r in safe)
        filename=day+'.jsonl'; (RAW/filename).write_text(encoded)
        entry.update(status='success',records=len(safe),file=filename,sha256=hashlib.sha256(encoded.encode()).hexdigest())
        m['response_bytes']+=entry['response_bytes']; save()
        if len(m['requests'])%25==0 or len(m['requests'])==len(ACQUISITION_DATES):
            print('Completed',len(m['requests']),'/',len(ACQUISITION_DATES),'dates;',
                  'new bytes',m['new_response_bytes'],flush=True)
    m['status']='completed'; save(); screen(m); return 0

if __name__=='__main__':
    raise SystemExit(main())
