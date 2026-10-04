"""Strict NBBO/corporate-action acquisition for the fixed exploratory benchmark.
No substituted daily prices enter signals or research reference outcomes.
"""
import gzip,json,math,os,signal,time,sqlite3
from pathlib import Path
from collections import defaultdict
from datetime import datetime,timezone
from statistics import median
from urllib.request import Request,build_opener
from urllib.parse import urlencode,urlsplit,parse_qsl,quote
from urllib.error import HTTPError
from zoneinfo import ZoneInfo
from submission_budget import Budget,ROOT,atomic,sha
from massive_grouped_pilot import NoRedirect
from full_universe_nbbo import event_id
from massive_stage_b2 import credential
from quant_core import SESSIONS,schedule,wkey,purged
OUT=ROOT/'data/raw/downstream_development'

def summarize(rows,start,end):
    mids=[];spreads=[];minute=defaultdict(list);rejected=defaultdict(int)
    for r in rows:
        t=r.get('sip_timestamp');bid=r.get('bid_price',0);ask=r.get('ask_price',0)
        if not isinstance(t,int) or not start<=t<end:rejected['timestamp']+=1;continue
        if not all(isinstance(x,(int,float)) and math.isfinite(x) for x in (bid,ask)) or bid<=0 or ask<=bid:rejected['price']+=1;continue
        if r.get('bid_size',0)<=0 or r.get('ask_size',0)<=0 or any(c!=1 for c in r.get('conditions',[])):rejected['size_or_condition']+=1;continue
        mid=(bid+ask)/2;mids.append(mid);spreads.append(ask-bid);minute[str(t//(60*10**9))].append(mid)
    return {'complete':True,'valid_minutes':len(minute),'valid_quotes':len(mids),'midpoint':median(mids) if len(minute)>=3 else None,'spread':median(spreads) if len(minute)>=3 else None,'minute_midpoints':{k:median(v) for k,v in minute.items()},'rejected':dict(rejected)}

class Acquire:
    def __init__(self,out=OUT,history_end='2025-12-31'):
        self.b=Budget(out);self.out=Path(out);self.key=credential();self.stop=False;self.history_end=history_end
        self.data_path=self.out/'inputs.json';self.data=json.loads(self.data_path.read_text()) if self.data_path.exists() else {'windows':{},'bars':{},'actions':{},'event_ids':[]}
        signal.signal(signal.SIGTERM,lambda *args:setattr(self,'stop',True))
    def checkpoint(self):atomic(self.data_path,self.data)
    def get(self,tag,path,params,cap=20_000_000):
        if self.stop:raise RuntimeError('scheduler_checkpoint')
        cached=self.b.m['files'].get(tag)
        if cached:
            p=self.out/cached['file'];assert sha(p)==cached['sha256'];return json.loads(gzip.decompress(p.read_bytes()))
        # URL/parameters never contain a credential.
        url='https://api.massive.com'+path+'?'+urlencode(params)
        r=self.b.reserve(tag,0,cap,{'path':path,'query':params});body=b''
        try:
            req=Request(url,headers={'Authorization':'Bearer '+self.key,'Accept-Encoding':'gzip'})
            with build_opener(NoRedirect()).open(req,timeout=45) as response:
                body=response.read(cap);encoding=response.headers.get('Content-Encoding','');code=response.status
            if len(body)>=cap:raise RuntimeError('response_cap_reached')
            payload=json.loads(gzip.decompress(body) if encoding=='gzip' else body)
            if payload.get('status') in ('ERROR','NOT_AUTHORIZED'):raise RuntimeError('provider_response_error')
            filename=__import__('hashlib').sha256(tag.encode()).hexdigest()+'.json.gz';p=self.out/filename
            # Strip pagination credentials before persisting any provider object.
            nxt=payload.get('next_url')
            if nxt:
                u=urlsplit(nxt)
                if u.hostname not in ('api.massive.com','api.polygon.io') or u.scheme!='https' or u.path!=path:raise RuntimeError('pagination_destination')
                clean=[(k,v) for k,v in parse_qsl(u.query) if k.lower()!='apikey'];payload['next_url']='https://api.massive.com'+u.path+'?'+urlencode(clean)
            safe={k:v for k,v in payload.items() if k in ('results','next_url','status','adjusted','resultsCount','queryCount','count','ticker')}
            p.write_bytes(gzip.compress(json.dumps(safe).encode(),mtime=0));self.b.m['files'][tag]={'file':filename,'sha256':sha(p)};self.b.finish(r,len(body),'complete',http_status=code);return safe
        except HTTPError as e:
            errorbody=e.read(min(cap,100001));self.b.finish(r,len(errorbody),'http_failure',http_status=e.code);raise RuntimeError('provider_http_'+str(e.code)) from None
        except Exception:
            self.b.finish(r,len(body) if body else cap,'incomplete');raise RuntimeError('provider_incomplete') from None
    def pages(self,tag,path,params,maxpages=30):
        rows=[]
        for page in range(maxpages):
            p=self.get(tag+'|'+str(page),path,params);rows.extend(p.get('results',[]))
            if not p.get('next_url'):return rows
            u=urlsplit(p['next_url']);params=dict(parse_qsl(u.query))
        raise RuntimeError('pagination_cap')
    def history(self,symbol):
        if symbol in self.data['bars'] and self.data['actions'].get(symbol,{}).get('complete'):return
        rows=self.pages('daily|'+symbol,'/v2/aggs/ticker/'+quote(symbol,safe='')+'/range/1/day/2022-01-01/'+self.history_end,{'adjusted':'false','sort':'asc','limit':50000})
        self.data['bars'][symbol]={datetime.fromtimestamp(r['t']/1000,timezone.utc).date().isoformat():{'close':r['c'],'volume':r['v']} for r in rows}
        splits=self.pages('splits|'+symbol,'/v3/reference/splits',{'ticker':symbol,'execution_date.gte':'2022-01-01','execution_date.lte':self.history_end,'limit':1000,'sort':'execution_date'})
        dividends=self.pages('dividends|'+symbol,'/v3/reference/dividends',{'ticker':symbol,'ex_dividend_date.gte':'2022-01-01','ex_dividend_date.lte':self.history_end,'limit':1000,'sort':'ex_dividend_date'})
        self.data['actions'][symbol]={'splits':splits,'dividends':dividends,'complete':True,'limitation':'Split/cash-dividend feed cannot establish completeness of complex reorganizations.'};self.checkpoint()
    def window(self,symbol,day,start_clock,end_clock):
        tag=wkey(symbol,day,start_clock,end_clock)
        if tag in self.data['windows']:return
        start=int(datetime.fromisoformat(day+'T'+start_clock+':00').replace(tzinfo=ZoneInfo('America/New_York')).timestamp())*10**9
        end=int(datetime.fromisoformat(day+'T'+end_clock+':00').replace(tzinfo=ZoneInfo('America/New_York')).timestamp())*10**9
        rows=self.pages('quotes|'+tag,'/v3/quotes/'+quote(symbol,safe=''),{'timestamp.gte':start,'timestamp.lt':end,'sort':'timestamp','order':'asc','limit':50000})
        self.data['windows'][tag]={**summarize(rows,start,end),'symbol':symbol,'date':day,'start':start_clock,'end':end_clock};self.checkpoint()
        if start_clock=='10:10':
            aggs=self.pages('volume|'+tag,'/v2/aggs/ticker/'+quote(symbol,safe='')+'/range/1/minute/'+str(start//10**6)+'/'+str(end//10**6-1),{'adjusted':'false','sort':'asc','limit':50000})
            self.data['windows'][tag]['volume']=sum(r['v'] for r in aggs if start//10**6<=r['t']<end//10**6) if aggs else None;self.checkpoint()
    def run(self):
        source=ROOT/'data/cache/nbbo_benchmark_selection/events.jsonl';events=[json.loads(line) for line in source.read_text().splitlines()]
        m=json.loads((ROOT/'data/raw/stage_c_quotes/M.json').read_text())
        self.data.update(sample_status='exploratory fixed 20-event implementation demonstration; not primary full universe',source_sha256=sha(source))
        self.b.m.update(scope=self.data['sample_status'],status='acquiring',slurm_job_id=os.environ['SLURM_JOB_ID']);self.b.sync()
        # All 20 events stay in the audit. Invalid M and boundary failures are not replaced.
        selected=[e for e in events if m.get(event_id(e),{}).get('M') is not None and not purged(e)]
        if selected and not self.key:
            self.data['acquisition_exclusions']={event_id(e):'missing_MASSIVE_API_KEY' for e in selected};self.checkpoint()
            self.b.m.update(status='blocked_missing_MASSIVE_API_KEY');self.b.sync();return
        if selected:self.history('SPY')
        for e in selected:
            eid=event_id(e);s=e['symbol'];D=e['entry_session'];pre,exit_day=schedule(D)
            try:
                self.history(s)
                for symbol,day,a,z in [('SPY',pre,'15:50','15:55'),(s,D,'10:00','10:05'),('SPY',D,'10:00','10:05'),(s,D,'10:10','10:20'),('SPY',D,'10:10','10:20'),(s,exit_day,'10:10','10:20'),('SPY',exit_day,'10:10','10:20')]:self.window(symbol,day,a,z)
                self.data['event_ids'].append(eid) if eid not in self.data['event_ids'] else None;self.checkpoint()
            except RuntimeError as exc:
                self.data.setdefault('acquisition_exclusions',{})[eid]=str(exc);self.checkpoint()
                if str(exc) in ('budget_at_risk','scheduler_checkpoint','response_cap_reached','pagination_cap'):break
                # Entitlement/shape problems are retained; do not flood repeated failed calls.
                self.b.m.update(status='blocked',stop_reason=str(exc));self.b.sync();return
        self.b.m.update(status='completed_or_budget_bounded',completed_events=len(self.data['event_ids']));self.b.sync()
        print(json.dumps({'sample':20,'valid_M_unpurged':len(selected),'complete_events':len(self.data['event_ids']),'remaining_requests':self.b.sync()['remaining_requests']}),flush=True)
if __name__=='__main__':
    try:Acquire().run()
    except Exception as e:print('BLOCKED:',type(e).__name__,flush=True);raise SystemExit(2)
