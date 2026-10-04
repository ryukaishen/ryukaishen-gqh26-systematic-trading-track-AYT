"""Authorized EOD liquidity acquisition/screen; no return or outcome calculations."""
import csv
import hashlib
import io
import json
import math
import os
import shlex
from bisect import bisect_left
from collections import Counter, deque
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from statistics import median
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener
from development_calendar import ACQUISITION_DATES, SESSIONS, SOURCES, EARLY_CLOSES, session_index

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw/fmp_eod_bulk'
CACHE=ROOT/'data/cache/stage_b2'
MAX_REQUESTS=1500
MAX_BYTES=4_000_000_000
MAX_FILE_BYTES=15_000_000

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def credential():
    key=os.environ.get('FMP_API_KEY') or os.environ.get('FINANCIAL_MODELING_PREP_API_KEY')
    if key: return key
    path=ROOT/'.env'
    if path.is_file():
        for line in path.read_text().splitlines():
            line=line.strip()
            if line.startswith('export '): line=line[7:].strip()
            name,sep,value=line.partition('=')
            if sep and name.strip()=='FMP_API_KEY':
                parts=shlex.split(value,comments=True)
                if len(parts)==1: return parts[0]
    return None

def prior_usage():
    manifests=[ROOT/'data/raw/fmp_stage_b1/manifest.json',
               ROOT/'data/raw/massive_grouped_pilot/manifest.json']
    count=0; size=0
    for p in manifests:
        m=json.loads(p.read_text()); count+=len(m['requests'])
        size+=m.get('total_response_bytes',m.get('response_bytes',0))
    return count,size

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
             'reference_per_symbol_planning_lower_bound':unique_symbols,
             'reference_per_symbol_session_conservative_estimate':unique_symbol_sessions,
             'reference_status':'needs_historical_validity_and_delisting_plan; no calls executed',
             'limitations':['FMP volume is not explicitly regular-session-only.',
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
        print('BLOCKED: FMP credential unavailable; zero requests.'); return 2
    previous_count,previous_bytes=prior_usage()
    if previous_count+len(ACQUISITION_DATES)>MAX_REQUESTS or previous_bytes+len(ACQUISITION_DATES)*4_000_000>MAX_BYTES:
        print('BLOCKED: initial projection exceeds cap.'); return 2
    RAW.mkdir(parents=True,exist_ok=True)
    path=RAW/'manifest.json'
    if path.exists():
        manifest=json.loads(path.read_text())
        if manifest.get('status')=='completed':
            screen(manifest); return 0
        print('BLOCKED: existing incomplete manifest; no automatic retry.'); return 2
    manifest={'status':'in_progress','acquisition_time':datetime.now(timezone.utc).isoformat(),
              'endpoint':'https://financialmodelingprep.com/stable/eod-bulk',
              'fields':['symbol','date','close','volume'], 'calendar_sources':SOURCES,
              'calendar_dates':ACQUISITION_DATES,'early_closes':sorted(EARLY_CLOSES),
              'transfer_ceiling':MAX_BYTES,'request_ceiling':MAX_REQUESTS,
              'prior_requests':previous_count,'prior_bytes':previous_bytes,
              'requests':[],'response_bytes':0,'discarded_out_of_date_rows':0}
    def save(): path.write_text(json.dumps(manifest,indent=2)+'\n')
    def stop(reason):
        manifest.update(status='incomplete',stop_reason=reason); save()
        print('STOP:',reason,flush=True); return 2
    save(); opener=build_opener(NoRedirect())
    for day in ACQUISITION_DATES:
        used=previous_bytes+manifest['response_bytes']
        if previous_count+len(manifest['requests'])>=MAX_REQUESTS:
            return stop('request cap')
        if used+MAX_FILE_BYTES>MAX_BYTES:
            return stop('transfer cap')
        entry={'date':day,'parameters':{'date':day},'status':'attempted'}
        manifest['requests'].append(entry); save()
        req=Request(manifest['endpoint']+'?'+urlencode({'date':day,'apikey':key}))
        try:
            with opener.open(req,timeout=30) as response:
                entry['http_status']=response.status
                body=response.read(MAX_FILE_BYTES+1)
            entry['response_bytes']=len(body); manifest['response_bytes']+=len(body)
            if len(body)>MAX_FILE_BYTES: return stop('file byte cap')
            text=body.decode('utf-8-sig'); del body
            if text.lstrip().startswith('['):
                payload=json.loads(text)
                if not isinstance(payload,list): return stop('unexpected JSON shape')
                rows=iter(payload)
            else:
                rows=csv.DictReader(io.StringIO(text))
                if not set(manifest['fields']).issubset(rows.fieldnames or []):
                    return stop('missing allowlisted CSV fields')
            safe=[]; discarded=0
            for row in rows:
                if not isinstance(row,dict): return stop('unexpected row shape')
                if str(row.get('date',''))!=day:
                    discarded+=1; continue
                if not all(f in row for f in manifest['fields']):
                    return stop('missing required fields')
                safe.append({f:row[f] for f in manifest['fields']})
            del text,rows
            if not safe: return stop('empty required session')
            encoded=''.join(json.dumps(r,sort_keys=True)+'\n' for r in safe)
            name=day+'.jsonl'; (RAW/name).write_text(encoded)
            entry.update(status='success',records=len(safe),discarded_out_of_date_rows=discarded,
                         file=name,sha256=hashlib.sha256(encoded.encode()).hexdigest())
            manifest['discarded_out_of_date_rows']+=discarded
        except HTTPError as error:
            entry.update(http_status=error.code, status='http_failure')
            # Count response-body bytes without displaying or retaining error material.
            size=len(error.read(MAX_FILE_BYTES+1))
            entry['response_bytes']=size; manifest['response_bytes']+=size
            return stop('HTTP failure')
        except (URLError,OSError,TimeoutError,ValueError,TypeError):
            return stop('network or parsing failure')
        save()
        if len(manifest['requests'])%25==0 or len(manifest['requests'])==len(ACQUISITION_DATES):
            print('Completed',len(manifest['requests']),'/',len(ACQUISITION_DATES),
                  'dates; response bytes',manifest['response_bytes'],flush=True)
    manifest['status']='completed'; save(); screen(manifest); return 0

if __name__=='__main__':
    raise SystemExit(main())
