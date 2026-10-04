"""Bounded Stage C known-contract metadata; no market data, returns or ATM substitution."""
import base64
import json
import os
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,build_opener
from urllib.error import HTTPError,URLError
from massive_stage_b2 import NoRedirect

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/raw/stage_c_databento_metadata'
SYMBOLS=['MSFT  230505C00150000','MSFT  230505P00150000']
MAX_BODY=100_000

def main():
    key=os.environ.get('DATABENTO_API_KEY')
    if not key:print('BLOCKED: missing Databento credential');return 2
    budget_file=ROOT/'data/cache/acquisition_budget.json'
    budget=json.loads(budget_file.read_text())
    calls=[{'method':'POST','path':'/v0/symbology.resolve','parameters':{'dataset':'OPRA.PILLAR','symbols':','.join(SYMBOLS),'stype_in':'raw_symbol','stype_out':'instrument_id','start_date':'2023-04-25','end_date':'2023-04-26'}}]
    for schema,start,end in [('definition','2023-04-25T00:00:00Z','2023-04-26T00:00:00Z'),('cbbo-1m','2023-04-25T19:45:00Z','2023-04-25T19:55:00Z')]:
        params={'dataset':'OPRA.PILLAR','symbols':','.join(SYMBOLS),'stype_in':'raw_symbol','schema':schema,'start':start,'end':end}
        for name in ('get_record_count','get_billable_size','get_cost'):
            calls.append({'method':'GET','path':'/v0/metadata.'+name,'parameters':params})
    if budget['cumulative_requests']+len(calls)>2500 or budget['cumulative_bytes']+len(calls)*(MAX_BODY+1)>4_000_000_000:
        print('BLOCKED: acquisition caps');return 2
    OUT.mkdir(parents=True,exist_ok=True);path=OUT/'manifest.json'
    if path.exists():print('BLOCKED: existing metadata manifest; no automatic rerun');return 2
    m={'status':'in_progress','acquisition_time':datetime.now(timezone.utc).isoformat(),
       'scope':'fixed historical MSFT strike-150 capability only, not selected ATM coverage',
       'source_contract_identifiers':['O:MSFT230505C00150000','O:MSFT230505P00150000'],
       'symbols':SYMBOLS,'requests':[],'response_bytes':0,'retrieval_executed':False}
    def save():path.write_text(json.dumps(m,indent=2)+'\n')
    def update_budget():
        budget['cumulative_requests']+=1
        budget['cumulative_bytes']+=m['requests'][-1].get('response_bytes',0)
        budget.update(remaining_requests=2500-budget['cumulative_requests'],remaining_bytes=4_000_000_000-budget['cumulative_bytes'],last_action='bounded Stage C Databento metadata; no market-data retrieval')
        budget_file.write_text(json.dumps(budget,indent=2)+'\n')
    auth=base64.b64encode((key+':').encode()).decode();opener=build_opener(NoRedirect());save()
    for spec in calls:
        entry={**spec,'status':'attempted'};m['requests'].append(entry);save()
        try:
            url='https://hist.databento.com'+spec['path'];data=None
            if spec['method']=='POST':data=urlencode(spec['parameters']).encode()
            else:url+='?'+urlencode(spec['parameters'])
            req=Request(url,data=data,method=spec['method'],headers={'Authorization':'Basic '+auth,'Content-Type':'application/x-www-form-urlencoded'})
            with opener.open(req,timeout=30) as response:
                entry['http_status']=response.status;body=response.read(MAX_BODY+1)
            entry['response_bytes']=len(body);m['response_bytes']+=len(body)
            if len(body)>MAX_BODY:raise ValueError('response cap')
            value=json.loads(body);del body
            if spec['method']=='POST':
                if not isinstance(value,dict):raise ValueError('shape')
                allow={k:value[k] for k in ('result','symbols','stype_in','stype_out','start_date','end_date','partial','not_found','status') if k in value}
                (OUT/'symbology.json').write_text(json.dumps(allow,indent=2)+'\n')
                entry['resolved_symbol_count']=sum(bool(value.get('result',{}).get(s)) for s in SYMBOLS)
            else:
                if isinstance(value,bool) or not isinstance(value,(int,float)):raise ValueError('non-scalar metadata')
                entry['scalar_result']=value
            entry['status']='success';update_budget();save();print(json.dumps(entry),flush=True)
        except HTTPError as error:
            entry.update(status='http_failure',http_status=error.code)
            size=len(error.read(MAX_BODY+1));entry['response_bytes']=size;m['response_bytes']+=size
            update_budget();m['status']='incomplete';m['stop_reason']='HTTP failure';save();print('STOP: Databento HTTP',error.code,flush=True);return 2
        except (URLError,OSError,TimeoutError,ValueError,TypeError):
            entry['status']='network_or_parse_failure';update_budget();m['status']='incomplete';m['stop_reason']='network_or_parse_failure';save();print('STOP: metadata network/shape/cap failure',flush=True);return 2
    cost=sum(e.get('scalar_result',0) for e in m['requests'] if e['path'].endswith('get_cost'))
    size=sum(e.get('scalar_result',0) for e in m['requests'] if e['path'].endswith('get_billable_size'))
    m.update(status='completed',total_estimated_cost=cost,total_estimated_billable_size=size,
             tiny_pilot_metadata_budget_pass=cost<=1 and size<=1048576,
             primary_ATM_coverage_status='unresolved; selected ATM contract identities and pre-event NBBO spot unavailable')
    save();print(json.dumps({k:v for k,v in m.items() if k!='requests'},indent=2));return 0

if __name__=='__main__':raise SystemExit(main())
