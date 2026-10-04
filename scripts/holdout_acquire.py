"""After-freeze, budget-bounded legacy-universe holdout pilot. No backfilling.
This is not the preregistered full-universe confirmatory holdout population.
"""
import base64,gzip,hashlib,json,math,os,re
from collections import defaultdict
from datetime import datetime,timezone
from decimal import Decimal
from pathlib import Path
from statistics import median
from urllib.request import Request,build_opener
from urllib.parse import urlencode
from urllib.error import HTTPError
from compression import zstd
from bisect import bisect_left,bisect_right
from submission_budget import ROOT,atomic,sha
from downstream_acquire import Acquire
from massive_grouped_pilot import NoRedirect
from stage_c_definitions_job import normalize_definition,decode_definition,choose_pair
from stage_c_quotes import normalize_quote,valid_option,synchronized_value
from quant_core import SESSIONS,schedule,purged,wkey
from full_universe_nbbo import event_id
from development_calendar import EARLY_CLOSES
OUT=ROOT/'data/raw/final_holdout'

def acquire_pilot(raw_calendar):
    # Called only from the durable claimed once-state after hash verification.
    assert (ROOT/'results/final/holdout_once_state.json').exists()
    legacy=[json.loads(l) for l in (ROOT/'data/cache/reference_bracketing/eligible_events.jsonl').read_text().splitlines()]
    bysymbol=defaultdict(set)
    for e in legacy:bysymbol[e['symbol']].add((e['issuer_cik'],e['stable_identifier']))
    groups=defaultdict(list)
    for r in raw_calendar:
        if r.get('symbol') in bysymbol and r.get('time') in ('bmo','amc') and str(r.get('fiscalPeriod')) in ('Q1','Q2','Q3','Q4') and r.get('fiscalYear') is not None:groups[(r['symbol'],r['date'])].append(r)
    candidates=[]
    for (symbol,release),rs in groups.items():
        identities={(r['time'],str(r['fiscalYear']),str(r['fiscalPeriod'])) for r in rs}
        if len(identities)!=1 or len(bysymbol[symbol])!=1:continue
        time,year,quarter=next(iter(identities));i=(bisect_left if time=='bmo' else bisect_right)(SESSIONS,release)
        D=SESSIONS[i]
        if not '2026-01-01'<=D<='2026-09-18':continue
        cik,figi=next(iter(bysymbol[symbol]));e={'symbol':symbol,'release_date':release,'entry_session':D,'time':time,'fiscal_year':year,'fiscal_quarter':quarter,'issuer_cik':cik,'stable_identifier':figi,'split':'holdout'}
        e['event_id']=event_id(e);candidates.append(e)
    # Fiscal-period deduplication: conflicts excluded, never select by outcomes.
    periodgroups=defaultdict(list)
    for e in candidates:periodgroups[(e['issuer_cik'],e['fiscal_year'],e['fiscal_quarter'])].append(e)
    candidates=[rs[0] for rs in periodgroups.values() if len(rs)==1]
    ordered=sorted(candidates,key=lambda e:e['event_id'])[:3]
    atomic(OUT/'pilot_selection.json',{'selected_before_market_inputs':ordered,'maximum':3,'raw_candidate_filter':'Unambiguous bmo/amc and provided fiscal year/quarter; legacy development issuer/FIGI universe; dates fixed','method':'Smallest SHA256 issuer|release|fiscal-year|quarter; no replacement','scope':'Exploratory legacy-universe holdout pilot, not full preregistered primary population'})
    if not ordered:
        return {'events':[],'M':{},'windows':{},'bars':{},'actions':{},'preregistered_input_validation':True,'pilot_exclusions':{},'pilot_scope':'No unambiguous timed quarterly legacy-universe candidates; no replacements'}
    a=Acquire(OUT/'acquisition',history_end='2026-10-02');a.b.m.update(scope='Once-claimed max-three holdout pilot; no replacement',status='in_progress');a.b.sync()
    inputs={'events':[],'M':{},'windows':{},'bars':{},'actions':{},'preregistered_input_validation':True,'pilot_exclusions':{},'pilot_scope':'Exploratory once-claimed legacy-universe max-three-event holdout pilot; full primary holdout remains unfunded'}
    key=os.environ.get('DATABENTO_API_KEY');auth='Basic '+base64.b64encode((key+':').encode()).decode() if key else None
    def databento(tag,metric,params,cost=0,size=0):
        cap=100001 if metric!='get_range' else size+1048576
        cache=a.b.m['files'].get(tag)
        if cache:
            p=a.out/cache['file'];assert sha(p)==cache['sha256']
            if metric=='get_range':
                with zstd.open(p,'rt') as f:return [json.loads(l) for l in f]
            return json.loads(p.read_text())
        r=a.b.reserve(tag,cost,cap,params);body=b''
        try:
            if metric=='get_range':
                q={**params,'encoding':'json','compression':'zstd','pretty_px':'false','pretty_ts':'false','map_symbols':'false'}
                req=Request('https://hist.databento.com/v0/timeseries.get_range',data=urlencode(q).encode(),headers={'Authorization':auth,'Content-Type':'application/x-www-form-urlencoded'})
            else:req=Request('https://hist.databento.com/v0/metadata.'+metric+'?'+urlencode(params),headers={'Authorization':auth})
            with build_opener(NoRedirect()).open(req,timeout=45) as response:body=response.read(cap)
            if len(body)>=cap:raise RuntimeError('holdout_databento_cap')
            name=hashlib.sha256(tag.encode()).hexdigest()+('.json.zst' if metric=='get_range' else '.json');p=a.out/name
            if metric=='get_range':
                payload=[json.loads(l) for l in zstd.decompress(body).splitlines()]
                p.write_bytes(body)
            else:
                payload=json.loads(body)
                if isinstance(payload,bool) or not isinstance(payload,(int,float)) or payload<0:raise RuntimeError('metadata_shape')
                p.write_text(json.dumps(payload))
            a.b.m['files'][tag]={'file':name,'sha256':sha(p)};a.b.finish(r,len(body),'complete');return payload
        except HTTPError as e:
            err=e.read(min(cap,100001));a.b.finish(r,len(err),'http_failure',http_status=e.code);raise RuntimeError('holdout_databento_http_'+str(e.code)) from None
        except Exception:
            a.b.finish(r,len(body) if body else cap,'incomplete');raise RuntimeError('holdout_databento_incomplete') from None
    try:
        if not a.key or not auth:
            for e in ordered:inputs['pilot_exclusions'][e['event_id']]='missing_market_data_credential'
            return inputs
        a.history('SPY')
        for e in ordered:
            eid=e['event_id'];symbol=e['symbol'];D=e['entry_session'];pre,exit_day=schedule(D)
            try:
                # Budget ceilings remain binding; avoid knowingly abandoning a started event.
                if a.b.sync()['remaining_requests']<24:raise RuntimeError('budget_at_risk')
                if pre in EARLY_CLOSES or purged(e):raise RuntimeError('early_close_or_boundary_purge')
                ref=a.get('reference|'+eid,'/v3/reference/tickers/'+symbol,{'date':D})['results']
                if ref.get('active') is not True or str(ref.get('currency_name','')).lower()!='usd' or ref.get('type')!='CS' or ref.get('locale')!='us' or ref.get('market')!='stocks' or ref.get('primary_exchange') not in ('XNYS','XNAS','XASE','ARCX') or str(ref.get('cik','')).zfill(10)!=str(e['issuer_cik']).zfill(10) or ref.get('share_class_figi')!=e['stable_identifier']:raise RuntimeError('historical_reference_unresolved')
                a.history(symbol);i=SESSIONS.index(D);prior=SESSIONS[i-20:i];bars=a.data['bars'][symbol]
                if len(prior)!=20 or not all(d in bars for d in prior):raise RuntimeError('missing_prior_liquidity_history')
                if bars[prior[-1]]['close']<10 or median(bars[d]['close']*bars[d]['volume'] for d in prior)<20_000_000:raise RuntimeError('liquidity_screen_failed')
                a.window(symbol,pre,'15:50','15:55');stock=a.data['windows'][wkey(symbol,pre,'15:50','15:55')]
                if stock.get('midpoint') is None:raise RuntimeError('invalid_S0')
                start=datetime.fromisoformat(pre+'T15:50:00').replace(tzinfo=__import__('zoneinfo').ZoneInfo('America/New_York'));start_ns=int(start.timestamp())*10**9;end_ns=start_ns+300*10**9
                params={'dataset':'OPRA.PILLAR','schema':'definition','stype_in':'parent','symbols':symbol+'.OPT','start':pre+'T00:00:00+00:00','end':str(__import__('datetime').date.fromisoformat(pre)+__import__('datetime').timedelta(days=1))+'T00:00:00+00:00'}
                cost=databento('defcost|'+eid,'get_cost',params);size=int(databento('defsize|'+eid,'get_billable_size',params))
                if size==0:raise RuntimeError('unresolved_option_root')
                definitions=databento('definitions|'+eid,'get_range',params,cost,size);latest={}
                for raw in definitions:
                    r=normalize_definition(raw);stamp=int(r['ts_recv']);k=(r['raw_symbol'],int(r['publisher_id']))
                    if 0<stamp<end_ns and (k not in latest or stamp>=int(latest[k]['ts_recv'])):latest[k]=r
                decoded={}
                for r in latest.values():
                    d=decode_definition(r,symbol,end_ns-1)
                    if d is not None:decoded[(d['raw_symbol'],d['instrument_id'])]=d
                pair=choose_pair(e,stock['midpoint'],list(decoded.values()))
                if pair['status']!='selected':raise RuntimeError(pair['reason'])
                qp={'dataset':'OPRA.PILLAR','schema':'cbbo-1m','stype_in':'raw_symbol','symbols':pair['call']['raw_symbol']+','+pair['put']['raw_symbol'],'start':start.astimezone(timezone.utc).isoformat(),'end':datetime.fromtimestamp(end_ns//10**9,timezone.utc).isoformat()}
                qc=databento('quotecost|'+eid,'get_cost',qp);qs=int(databento('quotesize|'+eid,'get_billable_size',qp));quotes=databento('quotes|'+eid,'get_range',qp,qc,qs)
                per=defaultdict(dict)
                for raw in quotes:
                    r=normalize_quote(raw);x=valid_option(r,start_ns,end_ns)
                    if x:
                        minute,mid=x;iid=int(r['instrument_id']);per[iid][minute]=mid if minute not in per[iid] else None
                M,shared=synchronized_value(stock['minute_midpoints'],per[pair['call']['instrument_id']],per[pair['put']['instrument_id']],start_ns,end_ns)
                m={'event_id':eid,'symbol':symbol,'split':'holdout','S0':stock['midpoint'],'M':M,'shared_valid_minutes':len(shared),'pre_event_date':pre,'start_ns':start_ns,'end_ns':end_ns,**pair}
                inputs['events'].append(e);inputs['M'][eid]=m
                if M is None:inputs['pilot_exclusions'][eid]='invalid_synchronized_M';continue
                for s,d,t,z in [('SPY',pre,'15:50','15:55'),(symbol,D,'10:00','10:05'),('SPY',D,'10:00','10:05'),(symbol,D,'10:10','10:20'),('SPY',D,'10:10','10:20'),(symbol,exit_day,'10:10','10:20'),('SPY',exit_day,'10:10','10:20')]:a.window(s,d,t,z)
            except (RuntimeError,KeyError,ValueError) as exc:
                reason=str(exc) if isinstance(exc,RuntimeError) else 'missing_or_invalid_reference_input';inputs['pilot_exclusions'][eid]=reason
                if eid in inputs['M'] and e not in inputs['events']:inputs['events'].append(e)
                if reason in ('budget_at_risk','scheduler_checkpoint'):break
        inputs.update(windows=a.data['windows'],bars=a.data['bars'],actions=a.data['actions'])
        a.b.m.update(status='completed_once_pilot',exclusions=inputs['pilot_exclusions']);a.b.sync();atomic(OUT/'inputs.json',inputs)
        return inputs
    finally:a.b.global_lock.close()
