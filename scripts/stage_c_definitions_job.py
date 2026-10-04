"""Compute-only Stage C definitions, frozen contract selection, quote estimates only.
No packages required: Python 3.14 stdlib zstd. No quote retrieval endpoint exists here.
"""
import argparse,base64,fcntl,hashlib,io,json,math,os,re,signal,socket,sqlite3,time
from concurrent.futures import ThreadPoolExecutor
from threading import RLock
from collections import Counter,defaultdict
from datetime import datetime,date,timedelta,timezone
from decimal import Decimal
from pathlib import Path
from urllib.request import Request,build_opener
from urllib.parse import urlencode
from urllib.error import HTTPError
from massive_grouped_pilot import NoRedirect
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/raw/stage_c_definitions'
LEDGER=ROOT/'data/cache/acquisition_budget.json'
ESTIMATE=ROOT/'data/raw/stage_c_definition_estimates/manifest.json'
SOURCE=ROOT/'data/cache/reference_bracketing/eligible_events.jsonl'
NBBO=ROOT/'data/raw/full_universe_nbbo/checkpoint.sqlite'
LIMIT=Decimal('12')
DOC='https://databento.com/docs/venues-and-datasets/opra-pillar'

def atomic(path,value):
    temp=path.with_suffix(path.suffix+'.tmp')
    with temp.open('w') as f:
        json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(temp,path)

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()

def ident(e):
    return hashlib.sha256('|'.join(str(e[k]) for k in ('issuer_cik','release_date','fiscal_year','fiscal_quarter')).encode()).hexdigest()

def integer(x):
    if isinstance(x,bool):raise ValueError('boolean integer')
    d=Decimal(str(x))
    if not d.is_finite() or d!=int(d):raise ValueError('invalid integer')
    return int(d)

def normalize_definition(r):
    if not isinstance(r,dict):raise ValueError('definition object')
    hd=r.get('hd',{})
    if not isinstance(hd,dict):raise ValueError('definition header')
    result={**hd,**r}
    for field in ('raw_symbol','instrument_id','publisher_id','ts_recv'):
        if field not in result:raise ValueError('definition record shape')
    return result


def decode_definition(r,symbol,cutoff_ns):
    """Accept exact standard OSI root; numeric adjusted roots never match."""
    r=normalize_definition(r)
    raw=r.get('raw_symbol','')
    if len(raw)!=21 or raw[:6].strip()!=symbol or not re.fullmatch('[A-Z][A-Z.]*',symbol):return None
    tail=raw[6:]
    if not re.fullmatch(r'\d{6}[CP]\d{8}',tail):return None
    cp=tail[6]
    if r.get('instrument_class')!=cp:return None
    stamp=integer(r['ts_recv'])
    if not 0<stamp<=cutoff_ns:return None
    if r.get('security_update_action')=='D':return None
    expiry=datetime.strptime(tail[:6],'%y%m%d').date()
    # OPRA expirations have UTC date granularity; never convert midnight to ET.
    expiration=integer(r['expiration'])
    if datetime.fromtimestamp(expiration/1e9,timezone.utc).date()!=expiry:return None
    strike=Decimal(tail[7:])/1000
    if strike<=0 or integer(r['strike_price'])!=int(strike*10**9):return None
    # Contract size field may be undefined for OPRA. Standard exact nonnumeric OSI
    # root carries the documented 100-share meaning; reject any contradictory size.
    qty=r.get('unit_of_measure_qty')
    if qty is not None and integer(qty)!=2**63-1 and integer(qty)!=100*10**9:return None
    return {'raw_symbol':raw,'instrument_id':integer(r['instrument_id']),'expiry':expiry.isoformat(),
            'strike':str(strike),'cp':cp,'definition_ts_recv':stamp,
            'standard_100_share_evidence':'exact nonnumeric standard OSI root; provider adjusted-root convention',
            'unit_of_measure_qty':qty,'standard_contract_source':DOC}

def choose_pair(e,s0,definitions):
    D=date.fromisoformat(e['entry_session']);lower=D+timedelta(days=7);upper=D+timedelta(days=21)
    eligible=[x for x in definitions if lower<=date.fromisoformat(x['expiry'])<=upper]
    if not eligible:return {'status':'excluded','reason':'no_standard_expiry_in_D7_D21'}
    # Freeze the earliest eligible expiry before checking matching strikes. No fallback.
    expiry=min(x['expiry'] for x in eligible);strikes=defaultdict(lambda:defaultdict(list))
    for x in eligible:
        if x['expiry']==expiry:strikes[Decimal(x['strike'])][x['cp']].append(x)
    paired={k:v for k,v in strikes.items() if set(v)=={'C','P'}}
    if not paired:return {'status':'excluded','reason':'no_matching_pair_at_earliest_expiry','expiry':expiry}
    spot=Decimal(str(s0));strike=min(paired,key=lambda k:(abs(k-spot),k));sides=paired[strike]
    if any(len({x['raw_symbol'] for x in sides[cp]})!=1 or len({x['instrument_id'] for x in sides[cp]})!=1 for cp in ('C','P')):
        return {'status':'excluded','reason':'ambiguous_selected_contract_identity','expiry':expiry,'strike':str(strike)}
    return {'status':'selected','expiry':expiry,'strike':str(strike),'call':sides['C'][0],'put':sides['P'][0]}

class Job:
    def __init__(self,prepare=False,retry_incomplete=False):
        self.prepare=prepare
        self.retry_incomplete=retry_incomplete
        self.shutdown=False
        self.metadata_lock=RLock()
        if not prepare:signal.signal(signal.SIGTERM,lambda signum,frame:setattr(self,'shutdown',True))
        if not prepare:
            if not os.environ.get('SLURM_JOB_ID') or socket.gethostname().split('.')[0].startswith('login'):
                raise RuntimeError('compute_node_required')
            from compression import zstd
            self.zstd=zstd
            if not os.environ.get('DATABENTO_API_KEY'):raise RuntimeError('credential_missing')
        OUT.mkdir(parents=True,exist_ok=True);(OUT/'dates').mkdir(exist_ok=True)
        self.lock=(OUT/'process.lock').open('a');fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        # Prevent the existing full-universe NBBO worker from overwriting its ledger.
        self.nbbo_lock=(NBBO.parent/'process.lock').open('a');fcntl.flock(self.nbbo_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        estimate=json.loads(ESTIMATE.read_text());assert estimate['status']=='completed'
        self.groups=defaultdict(dict)
        for r in estimate['requests']:
            if r['status'] in ('success','unresolved_roots'):
                self.groups[r['date']][r['metric']]=r
        assert len(self.groups)==589 and all(set(g)=={'get_cost','get_billable_size'} for g in self.groups.values())
        assert sum(Decimal(str(g['get_cost']['value'])) for g in self.groups.values())<=LIMIT
        self.events={ident(e):e for e in map(json.loads,SOURCE.read_text().splitlines())}
        assert len(self.events)==14340 and all(e['split'] in ('train','validation') and e['entry_session']<'2026-01-01' for e in self.events.values())
        db=sqlite3.connect(f'file:{NBBO}?mode=ro',uri=True)
        self.s0={eid:json.loads(result) for eid,result in db.execute("SELECT id,result FROM events WHERE status='complete'") if json.loads(result)['S0'] is not None};db.close()
        assert Counter(self.events[eid]['split'] for eid in self.s0)=={'train':8293,'validation':4765}
        self.by_day=defaultdict(list)
        for eid,r in self.s0.items():self.by_day[r['pre_event_date']].append(eid)
        for day,g in self.groups.items():
            assert set(g['get_cost']['parameters']['symbols'].split(','))=={self.events[eid]['symbol']+'.OPT' for eid in self.by_day[day]}
        self.path=OUT/'manifest.json'
        self.m=json.loads(self.path.read_text()) if self.path.exists() else {
            'status':'prepared','source_sha256':digest(SOURCE),'estimate_sha256':digest(ESTIMATE),
            'base_ledger':json.loads(LEDGER.read_text()),'requests':[],'dates':{},'quote_estimates':{},
            'scope':'train/validation valid-S0 historical definitions and selected-pair quote metadata only',
            'databento_cost_stop_usd':12,'quote_retrieval_authorized':False}
        assert self.m['source_sha256']==digest(SOURCE) and self.m['estimate_sha256']==digest(ESTIMATE)
        assert self.m['base_ledger']['request_ceiling']==20000 and self.m['base_ledger']['transfer_ceiling']==4000000000
        for r in self.m['requests']:
            if r['status']=='in_flight':r['status']='interrupted_unknown_transfer_and_billing'
        self.sync()
        for day,r in self.m['dates'].items():
            if r['status']=='complete':assert digest(OUT/r['file'])==r['sha256']
        self.opener=build_opener(NoRedirect())
        if not prepare:self.auth='Basic '+base64.b64encode((os.environ['DATABENTO_API_KEY']+':').encode()).decode()

    def sync(self):
        atomic(self.path,self.m)
        b=dict(self.m['base_ledger'])
        costs=sum(Decimal(str(r['reserved_cost'])) for r in self.m['requests'])
        b['cumulative_requests']+=len(self.m['requests']);b['cumulative_bytes']+=sum(r['charged_bytes'] for r in self.m['requests'])
        b.update(remaining_requests=20000-b['cumulative_requests'],remaining_bytes=4000000000-b['cumulative_bytes'],
                 databento_cost_stop_usd=12,databento_definition_cost_upper_bound_usd=float(costs),
                 last_action='authorized Stage C definition job; no quotes/outcomes/holdout',recorded_at=datetime.now(timezone.utc).isoformat())
        assert b['remaining_requests']>=0 and b['remaining_bytes']>=0 and costs<=LIMIT
        current=json.loads(LEDGER.read_text())
        if current['cumulative_requests']>b['cumulative_requests']:
            raise RuntimeError('shared_ledger_changed_no_counter_rollback')
        atomic(LEDGER,b);return b

    def remaining_cost(self):
        pending=Decimal(0)
        for day,g in self.groups.items():
            if day in self.m['dates']:continue
            plan=self.m.get('shard_plans',{}).get(day)
            if plan and all('cost' in x and 'size' in x for x in plan):
                pending+=sum(Decimal(str(x['cost'])) for x in plan if x.get('status') not in ('complete','unresolved_roots'))
            else:pending+=Decimal(str(g['get_cost']['value']))
        return pending

    def definition_metadata(self,day,metric,params,tag):
        key=tag+'|'+metric
        values=self.m.setdefault('definition_shard_estimates',{})
        if key in values:return values[key]
        r=self.reserve(day,'definition_metadata_'+metric,params,0,100001);body=b''
        try:
            req=Request('https://hist.databento.com/v0/metadata.'+metric+'?'+urlencode(params),headers={'Authorization':self.auth})
            with self.opener.open(req,timeout=60) as response:body=response.read(100001);r['http_status']=response.status
            value=json.loads(body)
            if len(body)>=100001 or isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:raise ValueError('invalid scalar')
            r.update(status='success',value=value,charged_bytes=len(body));values[key]=value;self.sync();return value
        except HTTPError as e:
            body=e.read(100001)
            try:detail=json.loads(body).get('detail',{})
            except ValueError:detail={}
            if e.code==422 and isinstance(detail,dict) and detail.get('case')=='symbology_invalid_request' and detail.get('message')=='None of the symbols could be resolved':
                r.update(status='unresolved_roots',http_status=422,value=0,charged_bytes=len(body));values[key]=0;self.sync();return 0
            r.update(status='http_failure',http_status=e.code,charged_bytes=len(body));self.sync();raise RuntimeError('definition_metadata_failed') from None
        except Exception:
            r.update(status='metadata_failed',charged_bytes=100001);self.sync();raise RuntimeError('definition_metadata_failed') from None

    def stream_shard(self,day,x):
        target=OUT/'dates'/f"{day}.{x['tag'][:12]}.json.zst"
        prior=[r for r in self.m['requests'] if r.get('shard_tag')==x['tag']]
        if target.exists() and prior and prior[-1].get('http_status')==200:
            count=self.validate_file(target);r=prior[-1]
            r.update(status='success_recovered_cached',charged_bytes=target.stat().st_size,records=count)
            x.update(status='complete',file=str(target.relative_to(OUT)),sha256=digest(target),
                     records=count,response_bytes=target.stat().st_size);self.sync();return
        if prior and (not self.retry_incomplete or len(prior)>=2 or prior[-1].get('http_status') not in (None,200,500,502,503,504)):
            raise RuntimeError('incomplete_billable_request_needs_reconciliation_no_automatic_rebilling')
        if x['size']==0:
            x['status']='unresolved_roots';self.sync();return
        params={**x['parameters'],'encoding':'json','compression':'zstd','pretty_px':'false','pretty_ts':'false','map_symbols':'false'}
        cap=int(x['size'])+1048576
        remaining_size,remaining_queries=self.remaining_size_and_queries()
        if remaining_size+remaining_queries*1048576>self.sync()['remaining_bytes']:
            raise RuntimeError('remaining_definition_transfer_estimate_at_risk')
        r=self.reserve(day,'definition_shard',params,x['cost'],cap);r['shard_tag']=x['tag'];self.sync()
        partial=target.with_suffix(f'.attempt{len(prior)+1}.partial');n=0;h=hashlib.sha256()
        try:
            req=Request('https://hist.databento.com/v0/timeseries.get_range',data=urlencode(params).encode(),headers={'Authorization':self.auth,'Content-Type':'application/x-www-form-urlencoded'})
            with self.opener.open(req,timeout=120) as response,partial.open('wb') as f:
                r['http_status']=response.status
                while n<cap:
                    block=response.read(min(1048576,cap-n))
                    if not block:break
                    f.write(block);h.update(block);n+=len(block)
                if n>=cap:raise RuntimeError('definition_transfer_reservation_reached')
                f.flush();os.fsync(f.fileno())
            os.replace(partial,target);count=self.validate_file(target)
            if count==0:raise ValueError('nonzero estimate returned no records')
            r.update(status='success',charged_bytes=n,records=count)
            x.update(status='complete',file=str(target.relative_to(OUT)),sha256=h.hexdigest(),records=count,response_bytes=n)
            self.sync()
        except HTTPError as e:
            body=e.read(100001);r.update(status='http_failure',http_status=e.code,charged_bytes=len(body));self.sync();raise RuntimeError('definition_http_failure_no_automatic_retry') from None
        except Exception:
            r.update(status='incomplete_no_automatic_retry',charged_bytes=n if target.exists() else cap,partial_bytes_written=n);self.sync();raise RuntimeError('definition_stream_or_decode_failed_no_automatic_retry') from None

    def download_sharded(self,day,g):
        plans=self.m.setdefault('shard_plans',{})
        if day not in plans:
            roots=sorted(g['get_cost']['parameters']['symbols'].split(','));plan=[]
            for offset in range(0,len(roots),40):
                params={**g['get_cost']['parameters'],'symbols':','.join(roots[offset:offset+40])}
                tag=hashlib.sha256(json.dumps(params,sort_keys=True).encode()).hexdigest()
                plan.append({'tag':tag,'parameters':params,'status':'pending'})
            assert set().union(*(set(x['parameters']['symbols'].split(',')) for x in plan))==set(roots)
            assert sum(len(x['parameters']['symbols'].split(',')) for x in plan)==len(roots)
            plans[day]=plan;self.sync()
        plan=plans[day]
        # All subset estimates precede the first billable subset download.
        for x in plan:
            x['cost']=self.definition_metadata(day,'get_cost',x['parameters'],x['tag'])
            x['size']=int(self.definition_metadata(day,'get_billable_size',x['parameters'],x['tag']))
        self.sync()
        for x in plan:
            if x.get('status')=='complete':assert digest(OUT/x['file'])==x['sha256']
            elif x.get('status')!='unresolved_roots':self.stream_shard(day,x)
        target=OUT/'dates'/f'{day}.json.zst';temp=target.with_suffix('.assemble.tmp')
        count=n=0;unresolved=[]
        with temp.open('wb') as output:
            for x in plan:
                if x['status']=='unresolved_roots':
                    unresolved.extend(x['parameters']['symbols'].split(','));continue
                count+=x['records'];n+=x['response_bytes']
                with (OUT/x['file']).open('rb') as source:
                    for block in iter(lambda:source.read(1048576),b''):output.write(block)
            output.flush();os.fsync(output.fileno())
        os.replace(temp,target)
        assert self.validate_file(target)==count
        self.m['dates'][day]={'status':'complete','file':str(target.relative_to(OUT)),'sha256':digest(target),
            'records':count,'response_bytes':n,'definition_query_shards':len(plan),'unresolved_roots':unresolved}
        self.sync()

    def remaining_size_and_queries(self):
        size=queries=0
        for day,g in self.groups.items():
            if day in self.m['dates']:continue
            plan=self.m.get('shard_plans',{}).get(day)
            if plan and all('size' in x for x in plan):
                size+=sum(x['size'] for x in plan if x.get('status') not in ('complete','unresolved_roots'))
                queries+=sum(x.get('status') not in ('complete','unresolved_roots') for x in plan)
            else:
                size+=int(g['get_billable_size']['value'])
                roots=len(g['get_cost']['parameters']['symbols'].split(','))
                queries+=math.ceil(roots/40)
        return size,queries

    def reserve(self,day,kind,parameters,cost,bytes_cap):
        if self.shutdown:raise RuntimeError('scheduler_checkpoint_before_new_request')
        b=self.sync();cost=Decimal(str(cost))
        total=sum(Decimal(str(r['reserved_cost'])) for r in self.m['requests'])
        pending=self.remaining_cost()
        if total+pending>LIMIT or total+cost>LIMIT:raise RuntimeError('dollar_budget_at_risk')
        if b['remaining_requests']<1 or b['remaining_bytes']<bytes_cap:raise RuntimeError('transfer_or_request_budget_at_risk')
        r={'day':day,'kind':kind,'parameters':parameters,'reserved_cost':float(cost),'reservation_bytes':bytes_cap,
           'charged_bytes':bytes_cap,'status':'in_flight'}
        self.m['requests'].append(r);self.sync();return r

    def fetch_metadata(self,day,metric,params,chunk=0):
        name=day+'|'+str(chunk)+'|'+metric
        with self.metadata_lock:
            if name in self.m['quote_estimates']:return self.m['quote_estimates'][name]
            r=self.reserve(day,'quote_'+metric,params,0,100001)
        body=b''
        try:
            req=Request('https://hist.databento.com/v0/metadata.'+metric+'?'+urlencode(params),headers={'Authorization':self.auth})
            with self.opener.open(req,timeout=60) as response:body=response.read(100001);r['http_status']=response.status
            value=json.loads(body)
            if len(body)>=100001 or isinstance(value,bool) or not isinstance(value,(int,float)) or value<0:raise ValueError('invalid scalar')
            with self.metadata_lock:
                r.update(status='success',value=value,charged_bytes=len(body));self.m['quote_estimates'][name]=value;self.sync()
            return value
        except HTTPError as e:
            body=e.read(100001)
            with self.metadata_lock:
                r.update(status='http_failure',http_status=e.code,charged_bytes=len(body));self.sync()
            raise RuntimeError('quote_metadata_http_failure') from None
        except Exception:
            with self.metadata_lock:
                r.update(status='metadata_failed',charged_bytes=len(body));self.sync()
            raise RuntimeError('quote_metadata_failed') from None

    def validate_file(self,target):
        count=0
        with self.zstd.open(target,'rt') as f:
            for line in f:
                normalize_definition(json.loads(line));count+=1
        return count

    def download(self,day,g):
        if day in self.m['dates']:return
        prior=[r for r in self.m['requests'] if r['day']==day and r['kind']=='definition']
        if prior:
            target=OUT/'dates'/f'{day}.json.zst'
            r=prior[-1]
            # A final filename is created only after the HTTP stream reached EOF.
            # Revalidate existing bytes after decoder fixes; never repeat the request.
            if target.exists() and r.get('http_status')==200:
                count=self.validate_file(target)
                r.update(status='success_recovered_cached',records=count,charged_bytes=target.stat().st_size)
                self.m['dates'][day]={'status':'complete','file':str(target.relative_to(OUT)),
                    'sha256':digest(target),'records':count,'response_bytes':target.stat().st_size,'recovered_without_rebilling':True}
                self.sync();return
            # One explicit resume retry is permissible only when the previous
            # full possible charge plus the repeated request plus *all remaining*
            # definitions fits $12. reserve() enforces that before any network I/O.
            retryable=r.get('http_status') in (None,200,500,502,503,504)
            if not self.retry_incomplete or len(prior)>=2 or not retryable:
                raise RuntimeError('incomplete_billable_request_needs_reconciliation_no_automatic_rebilling')
        if len(g['get_cost']['parameters']['symbols'].split(','))>40:
            self.download_sharded(day,g);return
        if g['get_cost']['status']=='unresolved_roots':
            self.m['dates'][day]={'status':'unresolved_roots','symbols':g['get_cost']['parameters']['symbols']};self.sync();return
        size=int(g['get_billable_size']['value']);params={**g['get_cost']['parameters'],
            'encoding':'json','compression':'zstd','pretty_px':'false','pretty_ts':'false','map_symbols':'false'}
        # Reservation is the *uncompressed DBN billable size* plus bounded overhead,
        # not an assumed compression ratio. A compressed JSON stream that reaches
        # this bound stops; all preceding bytes and full possible cost stay charged.
        cap=size+1048576
        b=self.sync();remaining_size=sum(int(x['get_billable_size']['value']) for d,x in self.groups.items() if d not in self.m['dates'])
        if remaining_size+1048576>b['remaining_bytes']:raise RuntimeError('remaining_definition_transfer_estimate_at_risk')
        r=self.reserve(day,'definition',params,g['get_cost']['value'],cap)
        target=OUT/'dates'/f'{day}.json.zst';partial=target.with_suffix(f'.attempt{len(prior)+1}.partial');n=0;h=hashlib.sha256()
        try:
            req=Request('https://hist.databento.com/v0/timeseries.get_range',data=urlencode(params).encode(),headers={'Authorization':self.auth,'Content-Type':'application/x-www-form-urlencoded'})
            with self.opener.open(req,timeout=120) as response,partial.open('wb') as f:
                r['http_status']=response.status
                while n<cap:
                    chunk=response.read(min(1048576,cap-n))
                    if not chunk:break
                    f.write(chunk);h.update(chunk);n+=len(chunk)
                    # Durable pessimistic reservation already covers kill/OOM/network loss.
                if n>=cap:raise RuntimeError('definition_transfer_reservation_reached')
                f.flush();os.fsync(f.fileno())
            os.replace(partial,target)
            # Validate full zstd framing and all JSON records before committing success.
            count=self.validate_file(target)
            r.update(status='success',charged_bytes=n,records=count)
            self.m['dates'][day]={'status':'complete','file':str(target.relative_to(OUT)),'sha256':h.hexdigest(),'records':count,'response_bytes':n}
            self.sync()
        except HTTPError as e:
            body=e.read(min(cap,100001));n+=len(body);r.update(status='http_failure',http_status=e.code,charged_bytes=n);self.sync();raise RuntimeError('definition_http_failure_no_automatic_retry') from None
        except Exception:
            r.update(status='incomplete_no_automatic_retry',charged_bytes=n if target.exists() else cap,partial_bytes_written=n);self.sync();raise RuntimeError('definition_stream_or_decode_failed_no_automatic_retry') from None

    def select(self):
        results={}
        for day,record in sorted(self.m['dates'].items()):
            ids=self.by_day[day]
            if record['status']=='unresolved_roots':
                for eid in ids:results[eid]={'status':'excluded','reason':'unresolved_root'}
                continue
            if record['status']!='complete':continue
            symbols={self.events[eid]['symbol'] for eid in ids};latest={}
            # Selection uses completed S0: all reference information known strictly
            # before 15:55 is eligible. No post-window records enter selection.
            cutoff_ns=self.s0[ids[0]]['end_ns']-1
            with self.zstd.open(OUT/record['file'],'rt') as f:
                for line in f:
                    r=normalize_definition(json.loads(line));raw=r.get('raw_symbol','');symbol=raw[:6].strip()
                    if symbol not in symbols:continue
                    stamp=integer(r['ts_recv'])
                    if stamp<=cutoff_ns:
                        key=(raw,integer(r['publisher_id']))
                        if key not in latest or stamp>=integer(latest[key]['ts_recv']):latest[key]=r
            definitions=defaultdict(dict)
            for r in latest.values():
                symbol=r['raw_symbol'][:6].strip();x=decode_definition(r,symbol,cutoff_ns)
                if x is not None:
                    key=(x['raw_symbol'],x['instrument_id'])
                    definitions[symbol][key]=x
            for eid in ids:
                e=self.events[eid]
                if e['symbol']+'.OPT' in record.get('unresolved_roots',[]):
                    results[eid]={'status':'excluded','reason':'unresolved_root'};continue
                pair=choose_pair(e,self.s0[eid]['S0'],list(definitions[e['symbol']].values()))
                results[eid]={'event_id':eid,'split':e['split'],'symbol':e['symbol'],'entry_session':e['entry_session'],
                              'pre_event_date':day,'S0':self.s0[eid]['S0'],'start_ns':self.s0[eid]['start_ns'],
                              'end_ns':self.s0[eid]['end_ns'],'reference_cutoff_exclusive_ns':self.s0[eid]['end_ns'],**pair}
        atomic(OUT/'selected_pairs.json',results)
        coverage={}
        for split,denominator in [('train',8688),('validation',5652)]:
            rows=[r for eid,r in results.items() if self.events[eid]['split']==split]
            count=sum(r['status']=='selected' for r in rows)
            coverage[split]={'population':denominator,'valid_S0':sum(self.events[eid]['split']==split for eid in self.s0),
                             'selected_contract_events':count,'contract_coverage_population':count/denominator,
                             'exclusions':dict(Counter(r.get('reason') for r in rows if r['status']!='selected')),
                             'valid_M_coverage':'unmeasured; quote retrieval not authorized'}
        self.m['contract_coverage']=coverage;self.sync();return results

    def quote_estimate(self,results):
        groups=defaultdict(set);windows={}
        for r in results.values():
            if r['status']=='selected':
                groups[r['pre_event_date']].update([r['call']['raw_symbol'],r['put']['raw_symbol']]);windows[r['pre_event_date']]=(r['start_ns'],r['end_ns'])
        cost=Decimal(0);size=0;query_groups=0;tasks=[]
        for day,symbols in sorted(groups.items()):
            start,end=windows[day]
            ordered=sorted(symbols)
            for chunk,offset in enumerate(range(0,len(ordered),160)):
                # Bound GET URLs and metadata response sizes; same explicit pair set.
                params={'dataset':'OPRA.PILLAR','schema':'cbbo-1m','stype_in':'raw_symbol',
                        'symbols':','.join(ordered[offset:offset+160]),
                        'start':datetime.fromtimestamp(start//10**9,timezone.utc).isoformat(),
                        'end':datetime.fromtimestamp(end//10**9,timezone.utc).isoformat()}
                tasks.extend((day,metric,params,chunk) for metric in ('get_cost','get_billable_size'))
                query_groups+=1
        # Only nonbillable metadata is concurrent. Reserve/checkpoint mutations are
        # serialized, with at most four bounded responses in flight.
        pool=ThreadPoolExecutor(max_workers=4)
        try:
            for task,value in zip(tasks,pool.map(lambda t:self.fetch_metadata(*t),tasks)):
                if task[1]=='get_cost':cost+=Decimal(str(value))
                else:size+=int(value)
        except Exception:
            self.shutdown=True
            pool.shutdown(wait=True,cancel_futures=True)
            raise
        else:pool.shutdown(wait=True)
        b=self.sync();definition_cost=sum(Decimal(str(r['reserved_cost'])) for r in self.m['requests'])
        self.m['selected_pair_quote_estimate']={'estimated_cost_usd':float(cost),'estimated_billable_bytes':size,
            'uncompressed_DBN_transfer_bound_bytes':size+query_groups*1048576,
            'date_groups':len(groups),'query_groups':query_groups,'definition_spend_upper_bound_usd':float(definition_cost),
            'combined_cost_estimate_usd':float(definition_cost+cost),
            'cost_limit_pass':definition_cost+cost<=LIMIT,'remaining_transfer_bytes':b['remaining_bytes'],
            'billable_size_with_overhead_fits':size+query_groups*1048576<=b['remaining_bytes'],
            'retrieved':False,'authorization':'estimates only; no quote retrieval'}
        self.sync()

    def run(self,resume_selected_pairs_sha256=None):
        if self.prepare:
            print(json.dumps({'status':'prepared','date_groups':len(self.groups),'events':len(self.s0),
                              'definition_cost_estimate_usd':11.407067812972011,'definition_billable_bytes':2449649160,'quote_retrieval':False}));return
        self.m.pop('stop_reason',None)
        self.m.update(status='definitions_in_progress',slurm_job_id=os.environ['SLURM_JOB_ID'],compute_host=socket.gethostname());self.sync()
        for day,g in sorted(self.groups.items()):
            if day in self.m['dates']:continue
            self.download(day,g)
            if len(self.m['dates'])%10==0:print(json.dumps({'completed_dates':len(self.m['dates']),'requests':len(self.m['requests']),'cost_upper_bound':self.sync()['databento_definition_cost_upper_bound_usd']}),flush=True)
        if resume_selected_pairs_sha256:
            assert len(self.m['dates'])==589
            pair_path=OUT/'selected_pairs.json'
            assert digest(pair_path)==resume_selected_pairs_sha256
            pairs=json.loads(pair_path.read_text())
            assert set(pairs)==set(self.s0)
            for eid,r in pairs.items():
                assert r['status'] in ('selected','excluded')
                if r['status']=='selected':
                    assert r['reference_cutoff_exclusive_ns']==r['end_ns']==self.s0[eid]['end_ns']
                    assert r['start_ns']==self.s0[eid]['start_ns'] and r['S0']==self.s0[eid]['S0']
            self.m['resumed_selected_pairs_sha256']=resume_selected_pairs_sha256
        else:
            self.m['status']='contract_selection';self.sync();pairs=self.select()
        self.m['status']='selected_pair_quote_metadata';self.sync();self.quote_estimate(pairs)
        self.m['status']='definitions_and_quote_estimates_completed';self.sync()
        print(json.dumps({'status':self.m['status'],'contract_coverage':self.m['contract_coverage'],
                          'quote_estimate':self.m['selected_pair_quote_estimate']},indent=2),flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');p.add_argument('--retry-incomplete',action='store_true');p.add_argument('--resume-selected-pairs-sha256');args=p.parse_args()
    job=None
    try:
        job=Job(args.prepare,args.retry_incomplete);job.run(args.resume_selected_pairs_sha256);return 0
    except Exception as exc:
        # Only print locally controlled diagnostic identifiers, never HTTP/credential data.
        allowed=('compute_node_required','credential_missing','dollar_budget_at_risk','transfer_or_request_budget_at_risk',
          'incomplete_billable_request_needs_reconciliation_no_automatic_rebilling','remaining_definition_transfer_estimate_at_risk',
          'definition_http_failure_no_automatic_retry','definition_stream_or_decode_failed_no_automatic_retry','quote_metadata_http_failure','quote_metadata_failed','shared_ledger_changed_no_counter_rollback','scheduler_checkpoint_before_new_request','definition_metadata_failed')
        reason=str(exc) if isinstance(exc,RuntimeError) and str(exc) in allowed else type(exc).__name__
        if job is not None:
            job.m.update(status='checkpointed' if reason=='scheduler_checkpoint_before_new_request' else 'blocked',stop_reason=reason)
            if reason=='shared_ledger_changed_no_counter_rollback':atomic(job.path,job.m)
            else:job.sync()
        print(('CHECKPOINTED: ' if reason=='scheduler_checkpoint_before_new_request' else 'BLOCKED: ')+reason,flush=True)
        return 0 if reason=='scheduler_checkpoint_before_new_request' else 2
if __name__=='__main__':raise SystemExit(main())
