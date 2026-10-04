"""Provider quote-condition schema lookup, not historical security validation."""
import json
import os
import sys
from pathlib import Path
from urllib.request import Request, build_opener
from urllib.error import HTTPError
from massive_grouped_pilot import NoRedirect

ROOT = Path(__file__).resolve().parents[1]
out = ROOT/'data/raw/nbbo_benchmark_conditions'
all_types = '--all-types' in sys.argv
manifest_path = out/('all_types_manifest.json' if all_types else 'manifest.json')
if manifest_path.exists():
    raise SystemExit('Existing dictionary manifest; no automatic retry')
key = os.environ.get('MASSIVE_API_KEY')
if not key:
    raise SystemExit('Missing credential')
ledger_path = ROOT/'data/cache/acquisition_budget.json'
ledger = json.loads(ledger_path.read_text())
assert ledger['remaining_requests']>=1 and ledger['remaining_bytes']>=100000
out.mkdir(parents=True, exist_ok=True)
params = {'asset_class':'stocks','limit':1000}
if not all_types:
    params['data_type'] = 'quote'
entry = {'path':'/v3/reference/conditions','parameters':params,
         'scope':'quote schema condition dictionary; no ticker/reference-status acquisition'}
body = b''
try:
    suffix = '' if all_types else '&data_type=quote'
    req = Request('https://api.massive.com/v3/reference/conditions?asset_class=stocks&limit=1000'+suffix,
                  headers={'Authorization':'Bearer '+key})
    with build_opener(NoRedirect()).open(req,timeout=30) as response:
        entry['http_status'] = response.status
        body = response.read(100000)
    payload = json.loads(body)
    assert not payload.get('next_url') and len(body)<100000
    rows = [{f:r[f] for f in ['id','name','type','description','sip_mapping','data_types','legacy'] if f in r}
            for r in payload.get('results',[])]
    (out/'conditions.json').write_text(json.dumps(rows,indent=2)+'\n')
    entry.update(status='success',records=len(rows))
except HTTPError as error:
    entry.update(status='http_failure',http_status=error.code)
    body = error.read(100000)
entry['response_bytes'] = len(body)
manifest_path.write_text(json.dumps(entry,indent=2)+'\n')
ledger['cumulative_requests'] += 1
ledger['cumulative_bytes'] += len(body)
ledger.update(remaining_requests=ledger['request_ceiling']-ledger['cumulative_requests'],
              remaining_bytes=ledger['transfer_ceiling']-ledger['cumulative_bytes'],
              last_action='NBBO benchmark quote-condition dictionary (not security reference)')
ledger_path.write_text(json.dumps(ledger,indent=2)+'\n')
print(json.dumps(entry))
if entry['status']=='success':
    print(json.dumps([{'id':r['id'],'name':r.get('name'),'data_types':r.get('data_types'),'type':r.get('type')} for r in rows if r.get('type')=='quote_condition' or 'quote' in str(r.get('data_types')) or 'bbo' in str(r.get('data_types'))],indent=2))
