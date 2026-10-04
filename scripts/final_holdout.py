"""Freeze all implementation/spec files, then claim a single holdout attempt.
Missing funded preregistered inputs yield inconclusive; never substitute prices.
"""
import base64,fcntl,gzip,hashlib,json,os,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
from urllib.request import Request,build_opener
from urllib.parse import urlencode
from urllib.error import HTTPError
from submission_budget import ROOT,Budget,atomic,sha
from massive_grouped_pilot import NoRedirect
from quant_core import observation,simulate,primary_regression,SPLITS
FINAL=ROOT/'results/final';FREEZE=FINAL/'implementation_freeze.json';STATE=FINAL/'holdout_once_state.json'
def files():
 return sorted([ROOT/'EXPERIMENT.md',ROOT/'README.md',ROOT/'requirements.txt',ROOT/'run_all.py']+list((ROOT/'scripts').glob('*.py'))+list((ROOT/'tests').glob('*.py'))+list((ROOT/'slurm').glob('*.sbatch')))
def hashes():return {str(p.relative_to(ROOT)):sha(p) for p in files()}
def freeze():
 FINAL.mkdir(parents=True,exist_ok=True)
 if STATE.exists():raise RuntimeError('holdout_already_opened_freeze_cannot_change')
 code=hashes()
 if FREEZE.exists():
  if json.loads(FREEZE.read_text())['files_sha256']!=code:raise RuntimeError('existing_freeze_differs')
  return
 result=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_*.py'],cwd=ROOT,capture_output=True,text=True)
 if result.returncode:raise RuntimeError('tests_failed_before_freeze')
 atomic(FINAL/'freeze_test_results.json',{'passed':True,'output':result.stdout+result.stderr})
 atomic(FREEZE,{'frozen_at':datetime.now(timezone.utc).isoformat(),'files_sha256':code,'splits':SPLITS,
  'holdout_last_scheduled_exit':'2026-10-02','authority':'Explicit submission-critical user authorization 2026-10-04',
  'feasibility':'failed 80% historical-contract coverage in train and validation; continue transparently as exploratory',
  'development_scope':'full-universe M and fixed 20-event exploratory downstream benchmark; not replacement primary sample',
  'timestamp_rules':'Fixed half-open ET windows; CBBO ts_recv interval end aligns completed prior stock minute; >=3 shared valid minutes; reference cutoff before 15:55',
  'costs':'1% initial equity allocations, 50% stock gross cap, 1% window participation, half median spread +2bps, .001/share commissions; doubled friction and .005/share $1-min sensitivity; historical fee schedule; missing borrow excluded',
  'unresolved':['Original-release/vendor vintage','Historical bracketing continuity','Exchange/CAT route fees','Complex corporate-action completeness','Full downstream and holdout input acquisition exceeds funded request scope'],
  'budget':json.loads((ROOT/'data/cache/acquisition_budget.json').read_text()),'no_tuning_after_holdout':True})
 print('Implementation and specification frozen.',flush=True)
def claim():
 if not FREEZE.exists():raise RuntimeError('implementation_not_frozen')
 frozen=json.loads(FREEZE.read_text())
 if frozen['files_sha256']!=hashes():raise RuntimeError('implementation_changed_since_freeze')
 state={'opened_at':datetime.now(timezone.utc).isoformat(),'status':'claimed_before_acquisition','freeze_sha256':sha(FREEZE),'attempts':1}
 try:
  fd=os.open(STATE,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 except FileExistsError:raise RuntimeError('holdout_once_already_claimed') from None
 with os.fdopen(fd,'w') as f:json.dump(state,f,indent=2);f.flush();os.fsync(f.fileno())
 return state

def acquire_calendar_once():
 """A bounded real acquisition attempt after freeze, never false strategy evaluation.
 The remaining budget cannot silently fund an entirely new historical quote/reference
 universe. Raw calendar records alone are not eligible/measurable holdout events.
 """
 from fmp_eod_stage_b2 import credential
 key=credential()
 if not key:return {'status':'missing_FMP_credential','requests':0}
 out=ROOT/'data/raw/final_holdout_calendar';b=Budget(out);b.m.update(scope='After-freeze raw 2026 calendar only; no outcomes or eligible-universe claim');b.sync()
 rows=[]
 # Entire fixed range is queried once. Store only sanitized known event fields.
 params={'from':'2026-01-01','to':'2026-09-18','includeReportTimes':'true','page':0};cap=min(8_000_000,b.sync()['remaining_bytes'])
 if b.sync()['remaining_requests']<1 or cap<1000:return {'status':'budget_blocked','requests':0}
 r=b.reserve('fixed_holdout_calendar',0,cap,params);body=b''
 try:
  url='https://financialmodelingprep.com/stable/earnings-calendar?'+urlencode({**params,'apikey':key})
  with build_opener(NoRedirect()).open(Request(url),timeout=45) as response:body=response.read(cap)
  if len(body)>=cap:raise RuntimeError('calendar_transfer_bound')
  payload=json.loads(body)
  if not isinstance(payload,list):raise RuntimeError('calendar_shape')
  allowed=('symbol','date','time','fiscalYear','fiscalPeriod','lastUpdated')
  rows=[{k:r[k] for k in allowed if k in r} for r in payload if isinstance(r,dict) and '2026-01-01'<=str(r.get('date',''))<='2026-09-18']
  atomic(out/'raw_calendar.json',rows);b.finish(r,len(body),'complete');b.m['status']='raw_calendar_only';b.sync()
  return {'status':'raw_calendar_acquired_only','requests':1,'raw_records':len(rows),'note':'Raw records do not prove quarterly eligibility, original timing or common-stock status; no strategy outcome measured.'}
 except HTTPError as e:
  raw=e.read(min(cap,100001));b.finish(r,len(raw),'http_failure',http_status=e.code)
  return {'status':'calendar_entitlement_or_API_failure','http_status':e.code,'requests':1}
 except Exception:
  b.finish(r,len(body) if body else cap,'incomplete');return {'status':'calendar_acquisition_incomplete','requests':1}

def evaluate_once():
 state=claim();inputs_path=ROOT/'data/raw/final_holdout/inputs.json';inputs=None;acquisition=None
 # No holdout record is read before durable freeze/claim.
 if inputs_path.exists():inputs=json.loads(inputs_path.read_text())
 else:
  acquisition=acquire_calendar_once()
  raw_path=ROOT/'data/raw/final_holdout_calendar/raw_calendar.json'
  if acquisition['status']=='raw_calendar_acquired_only' and raw_path.exists():
   from holdout_acquire import acquire_pilot
   try:inputs=acquire_pilot(json.loads(raw_path.read_text()))
   except Exception as exc:acquisition['pilot_status']='blocked_'+type(exc).__name__
 if inputs is None:
  result={'status':'inconclusive_unfunded_preregistered_holdout_inputs','attempts':1,'inferential_evaluations':0,'acquisition':acquisition,
   'reason':'No validated funded holdout S0/M, historical identity, reaction/beta/actions or prescribed outcome NBBO inputs. Remaining shared caps cannot be silently raised. Raw calendar alone cannot support a strategy test.',
   'holdout_outcomes_inspected':False,'freeze_sha256':sha(FREEZE)}
 else:
  assert inputs.get('preregistered_input_validation') is True
  events=inputs['events'];assert all(e['split']=='holdout' and '2026-01-01'<=e['entry_session']<='2026-09-18' for e in events)
  rows=[]
  for e in events:
   try:rows.append(observation(e,inputs['M'][e['event_id']],inputs['windows'],inputs['bars'],inputs['actions']))
   except (KeyError,ValueError,TypeError):rows.append({'event_id':e['event_id'],'symbol':e['symbol'],'split':'holdout','status':'excluded','reason':'unsupported_or_missing_action_or_reference_input'})
  regress=primary_regression(rows);p=simulate(rows,inputs['bars'],inputs['actions'],'holdout',borrow=inputs.get('borrow',{}))
  atomic(FINAL/'holdout_events.json',rows);atomic(FINAL/'holdout_portfolio.json',p)
  n=sum(r.get('research_status')=='measured' for r in rows)
  result={'status':regress['status'],'attempts':1,'inferential_evaluations':int(n>0),'acquisition':acquisition,'regression':regress,'performance':p['metrics'],
   'scope':inputs.get('pilot_scope','validated provided inputs'),'upstream_exclusions':inputs.get('pilot_exclusions',{}),
   'holdout_outcomes_inspected':n>0,'freeze_sha256':sha(FREEZE),'inputs_sha256':sha(inputs_path) if inputs_path.exists() else None,
   'full_primary_holdout':'incomplete/unfunded; exploratory maximum-three legacy-universe pilot cannot replace it'}
 state.update(status='completed_once',result_status=result['status']);atomic(STATE,state);atomic(FINAL/'holdout_result.json',result)
 print(json.dumps({'holdout_status':result['status'],'attempts':1,'inferential_evaluations':result['inferential_evaluations']}),flush=True)
