#!/usr/bin/env python3
"""Run the preregistered capped bonus using organizer functions directly."""
import argparse,ast,hashlib,json,os,sys,time,types,subprocess
from pathlib import Path
from urllib.parse import urlsplit,urlencode,parse_qsl,urlunsplit
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'massive_bonus'
sys.path.insert(0,str(ROOT/'scripts'))
from massive_stage_b2 import credential,NoRedirect
from submission_budget import Budget,atomic

class Stop(Exception):pass

def main():
 p=argparse.ArgumentParser();p.add_argument('--start',default='2024-01-01');p.add_argument('--end',default='2025-12-31');p.add_argument('--oos-start',default='2026-01-01');p.add_argument('--oos-end',default='2026-08-31');p.add_argument('--offline',action='store_true');args=p.parse_args()
 result_dir=HERE/'results';result_dir.mkdir(exist_ok=True)
 if args.offline:
  print((result_dir/'status.json').read_text());return
 config=json.loads((HERE/'config.json').read_text());source=HERE/'organizer_source.ipynb'
 if hashlib.sha256(source.read_bytes()).hexdigest()!=config['organizer_source_sha256']:raise Stop('organizer_source_hash_mismatch')
 # One immutable execution attempt; changes in judge windows require a separate scoped directory.
 window_hash=hashlib.sha256((args.start+'|'+args.end+'|'+args.oos_start+'|'+args.oos_end).encode()).hexdigest()[:12]
 claim=result_dir/('attempt_'+window_hash+'.json')
 with claim.open('x') as f:json.dump({'status':'claimed_before_bonus_data','config_sha256':hashlib.sha256((HERE/'config.json').read_bytes()).hexdigest(),'prereg_sha256':hashlib.sha256((HERE/'PREREG.md').read_bytes()).hexdigest(),'windows':vars(args),'RUN_PLACEBO':True},f,indent=2)
 deadline=time.monotonic()+300;budget=Budget(ROOT/'data/raw/massive_bonus');key=credential()
 if not key:raise Stop('missing_Massive_credential')
 nb=json.loads(source.read_text());mod=types.ModuleType('bonus_official');sys.modules[mod.__name__]=mod;g=mod.__dict__;g['__file__']=str(source)
 # Imports and organizer definitions only: no notebook analysis, ranking or stored outputs executed.
 for index in [8,14,16,18,20,22,24,26,40,42]:
  tree=ast.parse(''.join(nb['cells'][index]['source']))
  keep=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef,ast.ClassDef))]
  if index==22:keep=[n for n in tree.body if isinstance(n,ast.FunctionDef) or (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ['STRATEGIES','STRATEGY_LABEL'] for t in n.targets))]
  if index==24:
   keep=[n for n in tree.body if isinstance(n,ast.FunctionDef) or (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ['INK','INK2','MUTED','GRID','AXIS','SURFACE','SERIES'] for t in n.targets))]
  if index==14:
   # These are the organizer calendar assignments, needed before later function defaults.
   keep=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) or (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ['CAL','TODAY','LAST_SESSION'] for t in n.targets))]
  if index==8:
   exec(compile(ast.Module(keep,type_ignores=[]),str(source), 'exec'),g)
   exec(compile(ast.parse(''.join(nb['cells'][10]['source'])),str(source),'exec'),g)
   g.update(BASE_URL='https://api.massive.com',EVENT_TAG=config['signal_tag'],MAX_EVENTS=1,N_PLACEBO=1,RUN_PLACEBO=True,STUDY_START=args.start,STUDY_END=args.end,OOS_START=args.oos_start,OOS_END=args.oos_end,WINNER='cash_secured_put')
   g['CACHE_DIR']=ROOT/'data/raw/massive_bonus/official_cache';g['CACHE_DIR'].mkdir(parents=True,exist_ok=True)
  else:exec(compile(ast.Module(keep,type_ignores=[]),str(source),'exec'),g)
 # Exact unchanged organizer cost constant, read without executing its outcome cell.
 cost_tree=ast.parse(''.join(nb['cells'][38]['source']))
 cost_node=next(n for n in cost_tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='COST_HAIRCUT' for t in n.targets));exec(compile(ast.Module([cost_node],type_ignores=[]),str(source),'exec'),g)
 import requests,numpy as np,pandas as pd
 session=requests.Session();session.headers.update({'Authorization':'Bearer '+key});n_calls=0
 class GuardedSession:
  def get(self,url,**kwargs):
   nonlocal n_calls
   if time.monotonic()>deadline:raise Stop('five_minute_execution_timeout')
   if n_calls>=120:raise Stop('pilot_120_request_stop')
   u=urlsplit(url)
   if u.scheme!='https' or u.hostname not in ('api.massive.com','api.polygon.io'):raise Stop('unexpected_api_destination')
   q=[(k,v) for k,v in parse_qsl(u.query) if k.lower() not in ('apikey','api_key')];url=urlunsplit((u.scheme,u.netloc,u.path,urlencode(q),''))
   cap=2000000;r=budget.reserve('bonus_official_api',0,cap,{'path':u.path,'query':dict(q)});n_calls+=1;body=b''
   try:
    resp=session.get(url,timeout=15,stream=True,allow_redirects=False)
    for chunk in resp.iter_content(65536):
     body+=chunk
     if len(body)>=cap:raise Stop('response_transfer_bound')
    resp._content=body;resp._content_consumed=True
    if resp.status_code==200:
     payload=json.loads(body)
     if payload.get('next_url'):
      nxt=urlsplit(payload['next_url']);clean=[(k,v) for k,v in parse_qsl(nxt.query) if k.lower() not in ('apikey','api_key')];payload['next_url']=urlunsplit((nxt.scheme,nxt.netloc,nxt.path,urlencode(clean),''))
      resp._content=json.dumps(payload).encode()
    budget.finish(r,len(body),'complete' if resp.status_code==200 else 'http_failure',http_status=resp.status_code)
    if resp.status_code!=200:raise Stop('Massive_HTTP_'+str(resp.status_code))
    return resp
   except Exception:
    if r['status']=='in_flight':budget.finish(r,len(body) if body else cap,'incomplete')
    raise
 g['SESSION']=GuardedSession()
 contact=subprocess.run(['git','config','user.email'],cwd=ROOT,capture_output=True,text=True).stdout.strip()
 if not contact:raise Stop('missing_SEC_contact_for_public_time_verification')
 g['SEC_USER_AGENT']='GatorQuantHacks bonus '+contact
 status={'status':'running','scope':'official capped pilot; first event each split, one placebo','RUN_PLACEBO':True,'bonus_outcomes_inspected':False,'oos_claimed':False,'data_sources':'Massive market data; SEC acceptance metadata only','windows':vars(args),'eligibility_claim':False}
 atomic(result_dir/'status.json',status)
 def prepare(label,start,end):
  ev=g['build_events'](g['EVENT_TAG'],start,end,g['TOP_100']).head(1).copy();ev['event_date']=ev['filing_date'];ev.to_csv(result_dir/(label+'_selected_events.csv'),index=False)
  valid=[];drops=[]
  for _,row in ev.iterrows():
   try:
    accepted=g['fetch_acceptance_time'](row.filing_url)
    if accepted is None:raise Stop('acceptance_timestamp_missing')
    if accepted.hour>=16:row['t_0']=g['CAL'][g['CAL'].searchsorted(row['t_0'],side='right')]
    row['t_pre']=g['session_before'](row['t_0']);valid.append(row)
   except Exception as exc:drops.append({'ticker':row.ticker,'filing_date':str(row.filing_date),'reason':'public_availability_unverified_'+type(exc).__name__})
  pd.DataFrame(drops,columns=['ticker','filing_date','reason']).to_csv(result_dir/(label+'_timing_exclusions.csv'),index=False)
  if not valid:raise Stop(label+'_no_verifiable_public_entry')
  return pd.DataFrame(valid)
 def export(label,ev):
  priced,drops=g['price_events'](ev,label=label);drops.to_csv(result_dir/(label+'_pricing_exclusions.csv'),index=False)
  if not priced:raise Stop(label+'_no_priced_options')
  status['bonus_outcomes_inspected']=True;res=g['evaluate'](priced);res=res[res.entry=='post'].copy()
  columns=[c for c in res.columns if c not in ['stock','long_call','covered_call','protective_put','collar']];res=res[columns]
  prem={(pe.ticker,pe.event_date,pe.bucket):pe.marks(pe.t_0) for pe in priced}
  res['round_trip_cost']=[abs(prem[(r.ticker,r.event_date,r.bucket)][f'P_L{r.otm}'])/r.S_entry*g['COST_HAIRCUT']*2 for r in res.itertuples()]
  res['net_cash_secured_put']=res.cash_secured_put-res.round_trip_cost;res.to_csv(result_dir/(label+'_results.csv'),index=False)
  boards=[]
  for bucket in g['EXPIRY_BUCKETS']:
   for otm in g['OTM_GRID']:
    for strategy in ['cash_secured_put','net_cash_secured_put']:
     board=g['scoreboard'](res,bucket=bucket,entry='post',otm=otm,horizons=g['HORIZONS']+['exp'],strategies=[strategy]);board['bucket']=bucket;board['otm']=otm;boards.append(board)
  pd.concat(boards,ignore_index=True).to_csv(result_dir/(label+'_all_horizons_sensitivity.csv'),index=False)
  return res,priced
 try:
  train_ev=prepare('train',args.start,args.end);train,priced=export('train',train_ev)
  placebo_ev=g['sample_placebo'](train_ev,1,args.start,args.end);placebo_ev.to_csv(result_dir/'placebo_events.csv',index=False);placebo,_=export('placebo',placebo_ev)
  g['difference_board'](train,placebo,strategies=['cash_secured_put','net_cash_secured_put']).to_csv(result_dir/'placebo_comparison.csv',index=False)
  with (result_dir/'oos_once.json').open('x') as f:json.dump({'status':'claimed_before_OOS_disclosures','start':args.oos_start,'end':args.oos_end},f)
  status['oos_claimed']=True;atomic(result_dir/'status.json',status)
  oos_ev=prepare('oos',args.oos_start,args.oos_end);oos,_=export('oos',oos_ev)
  import matplotlib.pyplot as plt
  fig,ax=plt.subplots(figsize=(9,4))
  for name,res in [('train',train),('placebo',placebo),('OOS',oos)]:
   board=g['scoreboard'](res,horizons=g['HORIZONS']+['exp'],strategies=['net_cash_secured_put']);x=np.arange(len(board));ax.plot(x,board['mean']*100,marker='o',label=name);ax.fill_between(x,board.ci_lo*100,board.ci_hi*100,alpha=.12)
  ax.set_xticks(x,[str(h) for h in g['HORIZONS']]+['expiry']);ax.set_ylabel('Net P&L / synthetic entry stock spot (%)');ax.set_title('Official capped cash-secured-put pilot; CI N/A when n<5');ax.legend();fig.tight_layout();fig.savefig(result_dir/'horizons.png');plt.close(fig)
  status.update(status='completed_small_pilot',uncertainty='N/A: one event per group; official bootstrap requires five',eligibility_claim=False,limitation='Not full-window analysis; no collateral return, executed quotes or early-assignment ledger; some fixed horizons can be unavailable')
 except Exception as exc:
  status.update(status='incomplete',stop_reason=str(exc) if isinstance(exc,Stop) else type(exc).__name__,eligibility_claim=False)
 finally:
  status['api_calls']=n_calls;atomic(result_dir/'status.json',status);print(json.dumps(status),flush=True)
if __name__=='__main__':
 try:main()
 except Exception as exc:print('BONUS BLOCKED: '+(str(exc) if isinstance(exc,Stop) else type(exc).__name__),flush=True);sys.exit(2)
