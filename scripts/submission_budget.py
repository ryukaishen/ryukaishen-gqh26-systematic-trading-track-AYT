"""Durable shared request/transfer/spend guard. Secrets never enter receipts."""
import fcntl,hashlib,json,os,socket,threading
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal
ROOT=Path(__file__).resolve().parents[1]
LEDGER=ROOT/'data/cache/acquisition_budget.json'
def atomic(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    with temp.open('w') as f:json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(temp,path)
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
class Budget:
    def __init__(self,out):
        if not os.environ.get('SLURM_JOB_ID') or socket.gethostname().startswith('login'):
            raise RuntimeError('compute_node_required')
        self.out=Path(out);self.out.mkdir(parents=True,exist_ok=True);self.lock=threading.RLock()
        self.global_lock=(ROOT/'data/cache/submission_acquisition.lock').open('a')
        fcntl.flock(self.global_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        self.path=self.out/'manifest.json'
        self.m=json.loads(self.path.read_text()) if self.path.exists() else {'base':json.loads(LEDGER.read_text()),'requests':[],'files':{},'status':'in_progress'}
        for r in self.m['requests']:
            if r['status']=='in_flight':r['status']='interrupted_unknown';r['bytes']=r['cap']
        self.sync()
    def sync(self):
        base=self.m['base'];current=json.loads(LEDGER.read_text())
        n=base['cumulative_requests']+len(self.m['requests']);used=base['cumulative_bytes']+sum(r['bytes'] for r in self.m['requests'])
        if current['cumulative_requests']>n:raise RuntimeError('shared_ledger_changed')
        spend=Decimal(str(base.get('databento_total_cost_upper_bound_usd',base.get('databento_definition_cost_upper_bound_usd',0))))+sum((Decimal(str(r['cost'])) for r in self.m['requests']),Decimal(0))
        b={**base,'recorded_at':datetime.now(timezone.utc).isoformat(),'cumulative_requests':n,'cumulative_bytes':used,
           'remaining_requests':base['request_ceiling']-n,'remaining_bytes':base['transfer_ceiling']-used,
           'databento_total_cost_upper_bound_usd':float(spend),'last_action':'authorized submission pipeline; held-out data protected until freeze'}
        if n>base['request_ceiling'] or used>base['transfer_ceiling'] or spend>12:raise RuntimeError('budget_exceeded')
        atomic(self.path,self.m);atomic(LEDGER,b);return b
    def reserve(self,tag,cost,cap,parameters):
        with self.lock:
            b=self.sync()
            if b['remaining_requests']<1 or cap>b['remaining_bytes'] or Decimal(str(b['databento_total_cost_upper_bound_usd']))+Decimal(str(cost))>12:raise RuntimeError('budget_at_risk')
            r={'tag':tag,'cost':float(cost),'cap':int(cap),'bytes':int(cap),'status':'in_flight','parameters':parameters}
            self.m['requests'].append(r);self.sync();return r
    def finish(self,r,n,status,**extra):
        with self.lock:r.update(bytes=n,status=status,**extra);self.sync()
