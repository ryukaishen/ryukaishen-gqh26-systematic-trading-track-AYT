"""Nonbillable, checkpointed cost/size metadata for valid-S0 development roots."""
import base64,json,os,sqlite3,time
from collections import defaultdict
from datetime import date,timedelta,datetime,timezone
from pathlib import Path
from urllib.request import Request,build_opener
from urllib.parse import urlencode
from urllib.error import HTTPError
from massive_grouped_pilot import NoRedirect
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/raw/stage_c_definition_estimates'
def save(p,x):
    t=p.with_suffix('.tmp');t.write_text(json.dumps(x,indent=2)+'\n');os.replace(t,p)
def main():
    key=os.environ.get('DATABENTO_API_KEY')
    if not key: print('BLOCKED: credential absent');return 2
    db=sqlite3.connect(f'file:{ROOT}/data/raw/full_universe_nbbo/checkpoint.sqlite?mode=ro',uri=True)
    events={r['id']:r for r in []}
    groups=defaultdict(set); counts=defaultdict(int)
    for split,result in db.execute("SELECT split,result FROM events WHERE status='complete'"):
        r=json.loads(result)
        if r['S0'] is not None:
            assert split in ('train','validation') and r['pre_event_date']<'2026-01-01'
            groups[r['pre_event_date']].add(r['symbol']+'.OPT');counts[split]+=1
    OUT.mkdir(parents=True,exist_ok=True);path=OUT/'manifest.json'
    m=json.loads(path.read_text()) if path.exists() else {'status':'in_progress','valid_S0_counts':dict(counts),'date_groups':len(groups),'requests':[],'billable_retrieval':False,'estimated_cost':0,'estimated_billable_size':0}
    auth=base64.b64encode((key+':').encode()).decode();opener=build_opener(NoRedirect())
    m['status']='in_progress'
    for x in m['requests']:
        detail=x.get('provider_error',{}).get('detail',{})
        if x.get('http_status')==422 and isinstance(detail,dict) and detail.get('case')=='symbology_invalid_request' and detail.get('message')=='None of the symbols could be resolved':
            x['status']='unresolved_roots';x['value']=0
    completed={(x['date'],x['metric']) for x in m['requests'] if x['status'] in ('success','unresolved_roots')}
    for day,roots in sorted(groups.items()):
        params={'dataset':'OPRA.PILLAR','schema':'definition','stype_in':'parent','symbols':','.join(sorted(roots)),'start':day,'end':(date.fromisoformat(day)+timedelta(days=1)).isoformat()}
        for metric in ('get_cost','get_billable_size'):
            if (day,metric) in completed:continue
            ledger_path=ROOT/'data/cache/acquisition_budget.json';ledger=json.loads(ledger_path.read_text())
            if ledger['remaining_requests']<1 or ledger['remaining_bytes']<100001:raise RuntimeError('budget exhausted')
            entry={'date':day,'metric':metric,'parameters':params,'status':'attempted'};m['requests'].append(entry);save(path,m)
            body=b''
            try:
                req=Request('https://hist.databento.com/v0/metadata.'+metric+'?'+urlencode(params),headers={'Authorization':'Basic '+auth})
                with opener.open(req,timeout=30) as response:body=response.read(100001);entry['http_status']=response.status
                value=json.loads(body)
                if len(body)>100000 or isinstance(value,bool) or not isinstance(value,(int,float)):raise ValueError('shape')
                entry.update(status='success',value=value)
                m['estimated_cost' if metric=='get_cost' else 'estimated_billable_size']+=value
            except HTTPError as e:
                body=e.read(100001);entry.update(status='http_failure',http_status=e.code)
                try:
                    error=json.loads(body);entry['provider_error']={k:error[k] for k in ('detail','message','code') if k in error}
                except ValueError:pass
                detail=entry.get('provider_error',{}).get('detail',{})
                if e.code==422 and isinstance(detail,dict) and detail.get('case')=='symbology_invalid_request' and detail.get('message')=='None of the symbols could be resolved':
                    entry.update(status='unresolved_roots',value=0)
            except Exception:
                entry['status']='network_or_shape_failure'
            entry['response_bytes']=len(body)
            ledger['cumulative_requests']+=1;ledger['cumulative_bytes']+=len(body)
            ledger.update(remaining_requests=ledger['request_ceiling']-ledger['cumulative_requests'],remaining_bytes=ledger['transfer_ceiling']-ledger['cumulative_bytes'],last_action='Stage C valid-S0 definition cost/size metadata only',recorded_at=datetime.now(timezone.utc).isoformat())
            save(ledger_path,ledger);save(path,m)
            if entry['status'] not in ('success','unresolved_roots'):
                m['status']='blocked';save(path,m);print(json.dumps(entry),flush=True);return 2
            if len(m['requests'])==1 or len(m['requests'])%40==0:print(json.dumps({'requests':len(m['requests']),'estimated_cost':m['estimated_cost'],'estimated_billable_size':m['estimated_billable_size'],'credential_verified':True}),flush=True)
    m['status']='completed';save(path,m);print(json.dumps({k:v for k,v in m.items() if k!='requests'}),flush=True)
    return 0
if __name__=='__main__':raise SystemExit(main())
