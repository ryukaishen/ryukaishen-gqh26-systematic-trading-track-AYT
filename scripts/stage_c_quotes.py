"""Only frozen selected-pair CBBO windows; modest concurrency and M immediately."""
import base64,json,math,os,sqlite3,signal
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from decimal import Decimal
from statistics import median
from urllib.request import Request,build_opener
from urllib.parse import urlencode
from urllib.error import HTTPError
from compression import zstd
from submission_budget import ROOT,Budget,atomic,sha
from massive_grouped_pilot import NoRedirect

OUT=ROOT/'data/raw/stage_c_quotes'
def normalize_quote(r):
    if not isinstance(r,dict) or not isinstance(r.get('hd',{}),dict):raise ValueError('quote_shape')
    r={**r.get('hd',{}),**r}
    if not all(k in r for k in ('instrument_id','ts_recv','levels')):raise ValueError('quote_shape')
    return r

def valid_option(r,start,end):
    r=normalize_quote(r);stamp=int(r['ts_recv'])
    if not start<=stamp<end or int(r.get('flags',0))&12:return None
    levels=r.get('levels',[])
    if len(levels)!=1:return None
    l=levels[0];bid=float(l.get('bid_px',0))/1e9;ask=float(l.get('ask_px',0))/1e9
    if not all(math.isfinite(x) for x in (bid,ask)) or bid<=0 or ask<=bid or l.get('bid_sz',0)<=0 or l.get('ask_sz',0)<=0:return None
    mid=(bid+ask)/2
    if (ask-bid)/mid>0.20:return None
    # CBBO stamp is completed interval end; align to prior stock minute bin.
    if stamp%(60*10**9):return None
    return str(stamp//(60*10**9)-1),mid

def synchronized_value(stock,call,put,start,end):
    shared=sorted(k for k in set(stock)&set(call)&set(put) if call[k] is not None and put[k] is not None and start//(60*10**9)<=int(k)<end//(60*10**9))
    vals=[(call[k]+put[k])/stock[k] for k in shared]
    M=median(vals) if len(vals)>=3 else None
    return (M if M is not None and math.isfinite(M) and M>0 else None),shared

def calculate_m(pairs,files):
    db=sqlite3.connect(f'file:{ROOT}/data/raw/full_universe_nbbo/checkpoint.sqlite?mode=ro',uri=True)
    stocks={eid:json.loads(r) for eid,r in db.execute("SELECT id,result FROM events WHERE status='complete'")};db.close()
    byday=defaultdict(list)
    for eid,r in pairs.items():
        if r['status']=='selected':byday[r['pre_event_date']].append((eid,r))
    outputs={};counts=defaultdict(lambda:defaultdict(int))
    for day,events in sorted(byday.items()):
        wanted={c['instrument_id'] for _,r in events for c in (r['call'],r['put'])};quotes=defaultdict(dict)
        start,end=events[0][1]['start_ns'],events[0][1]['end_ns']
        for entry in files.values():
            if entry['day']!=day:continue
            with zstd.open(OUT/entry['file'],'rt') as f:
                for line in f:
                    row=normalize_quote(json.loads(line));iid=int(row['instrument_id'])
                    if iid not in wanted:continue
                    x=valid_option(row,start,end)
                    if x is not None:
                        minute,mid=x
                        # Multiple records for one instrument/minute are unresolved.
                        if minute in quotes[iid]:quotes[iid][minute]=None
                        else:quotes[iid][minute]=mid
        for eid,r in events:
            stock=stocks[eid]['minute_midpoints'];call=quotes[r['call']['instrument_id']];put=quotes[r['put']['instrument_id']]
            M,shared=synchronized_value(stock,call,put,start,end)
            good=M is not None and math.isfinite(M) and M>0
            outputs[eid]={**r,'M':M if good else None,'shared_valid_minutes':len(shared),'shared_minute_bins':shared,
                'M_status':'valid' if good else 'excluded','M_exclusion':None if good else 'fewer_than_three_shared_valid_minutes'}
            counts[r['split']]['selected_pairs']+=1;counts[r['split']]['valid_M']+=int(good)
    atomic(OUT/'M.json',outputs)
    coverage={split:{**counts[split],'population':n,'coverage_population':counts[split]['valid_M']/n,'contract_feasibility_80pct':'failed'} for split,n in [('train',8688),('validation',5652)]}
    atomic(OUT/'coverage.json',coverage);return coverage

def main():
    b=Budget(OUT);definition=json.loads((ROOT/'data/raw/stage_c_definitions/manifest.json').read_text());q=definition['selected_pair_quote_estimate']
    assert q['cost_limit_pass'] and q['billable_size_with_overhead_fits'] and q['query_groups']<=b.sync()['remaining_requests']+len(b.m['requests'])
    pairpath=ROOT/'data/raw/stage_c_definitions/selected_pairs.json';pairs=json.loads(pairpath.read_text());pairhash=sha(pairpath)
    if 'pair_sha256' in b.m:assert b.m['pair_sha256']==pairhash
    b.m.update(pair_sha256=pairhash,slurm_job_id=os.environ['SLURM_JOB_ID'],status='quotes_in_progress',authorization='Explicit user submission-critical authorization, 2026-10-04')
    groups=defaultdict(set);windows={}
    for r in pairs.values():
        if r['status']=='selected':groups[r['pre_event_date']].update((r['call']['raw_symbol'],r['put']['raw_symbol']));windows[r['pre_event_date']]=(r['start_ns'],r['end_ns'])
    tasks=[]
    for day,symbols in sorted(groups.items()):
        start,end=windows[day];ordered=sorted(symbols)
        for chunk,offset in enumerate(range(0,len(ordered),160)):
            tag=day+'|'+str(chunk);params={'dataset':'OPRA.PILLAR','schema':'cbbo-1m','stype_in':'raw_symbol','symbols':','.join(ordered[offset:offset+160]),'start':datetime.fromtimestamp(start//10**9,timezone.utc).isoformat(),'end':datetime.fromtimestamp(end//10**9,timezone.utc).isoformat()}
            cost=definition['quote_estimates'][tag+'|get_cost'];size=definition['quote_estimates'][tag+'|get_billable_size'];tasks.append((tag,day,params,cost,int(size)))
    # Forecast every unfinished request before starting; retries reserve prior failures.
    pending=[t for t in tasks if t[0] not in b.m['files']]
    state=b.sync()
    if sum(t[4]+1048576 for t in pending)>state['remaining_bytes'] or len(pending)>state['remaining_requests'] or Decimal(str(state['databento_total_cost_upper_bound_usd']))+sum((Decimal(str(t[3])) for t in pending),Decimal(0))>12:raise RuntimeError('remaining_quote_forecast_at_risk')
    key=os.environ['DATABENTO_API_KEY'];auth='Basic '+base64.b64encode((key+':').encode()).decode();stop=False
    def term(*args):
        nonlocal stop;stop=True
    signal.signal(signal.SIGTERM,term)
    def acquire(task):
        tag,day,params,cost,size=task
        with b.lock:
            if tag in b.m['files']:
                entry=b.m['files'][tag];assert sha(OUT/entry['file'])==entry['sha256'];return
            if stop:raise RuntimeError('scheduler_checkpoint')
        target=OUT/(day+'.'+tag.split('|')[1]+'.json.zst')
        prior=[r for r in b.m['requests'] if r['tag']==tag]
        if target.exists() and prior:
            with zstd.open(target,'rt') as f:count=sum(1 for line in f if normalize_quote(json.loads(line)))
            with b.lock:
                b.m['files'][tag]={'day':day,'file':target.name,'sha256':sha(target),'records':count}
                b.finish(prior[-1],target.stat().st_size,'complete_recovered')
            return
        if len(prior)>=2:raise RuntimeError('quote_retry_limit')
        cap=size+1048576;r=b.reserve(tag,cost,cap,params);n=0
        partial=target.with_suffix('.partial')
        try:
            query={**params,'encoding':'json','compression':'zstd','pretty_px':'false','pretty_ts':'false','map_symbols':'false'}
            req=Request('https://hist.databento.com/v0/timeseries.get_range',data=urlencode(query).encode(),headers={'Authorization':auth,'Content-Type':'application/x-www-form-urlencoded'})
            with build_opener(NoRedirect()).open(req,timeout=90) as response,partial.open('wb') as f:
                r['http_status']=response.status
                while n<cap:
                    block=response.read(min(1048576,cap-n))
                    if not block:break
                    f.write(block);n+=len(block)
                if n>=cap:raise RuntimeError('quote_transfer_bound_reached')
                f.flush();os.fsync(f.fileno())
            os.replace(partial,target)
            with zstd.open(target,'rt') as f:count=sum(1 for line in f if normalize_quote(json.loads(line)))
            with b.lock:
                b.m['files'][tag]={'day':day,'file':target.name,'sha256':sha(target),'records':count}
                b.finish(r,n,'complete',http_status=200)
        except HTTPError as e:
            body=e.read(min(cap,100001));b.finish(r,len(body),'http_failure',http_status=e.code);raise RuntimeError('quote_http_failure') from None
        except Exception:
            b.finish(r,n if target.exists() else cap,'incomplete');raise RuntimeError('quote_incomplete') from None
    pool=ThreadPoolExecutor(max_workers=4)
    try:list(pool.map(acquire,tasks))
    except Exception:
        stop=True;pool.shutdown(wait=True,cancel_futures=True);raise
    else:pool.shutdown(wait=True)
    b.m['status']='quotes_complete_computing_M';b.sync();coverage=calculate_m(pairs,b.m['files'])
    b.m.update(status='completed',coverage=coverage);b.sync();print(json.dumps(coverage),flush=True)
if __name__=='__main__':
    try:main()
    except Exception as e:print('BLOCKED:',type(e).__name__,flush=True);raise SystemExit(2)
