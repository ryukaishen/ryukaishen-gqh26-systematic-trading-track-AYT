"""Exactly three development-era grouped daily probes; no outcomes computed."""
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def main():
    key=os.environ.get('MASSIVE_API_KEY')
    if not key:
        print('BLOCKED: missing Massive credential'); return 2
    root=Path(__file__).resolve().parents[1]
    out=root/'data/raw/massive_grouped_pilot'
    if (out/'manifest.json').exists():
        print('BLOCKED: existing pilot manifest; no automatic rerun'); return 2
    out.mkdir(parents=True,exist_ok=True)
    manifest={'acquisition_time':datetime.now(timezone.utc).isoformat(), 'requests':[],
              'retained_fields':['T','c','v','vw','t'], 'status':'in_progress'}
    def save():
        (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    opener=build_opener(NoRedirect())
    for role,day in [('low','2025-12-31'),('high','2023-06-30'),('lookback','2023-03-01')]:
        path=f'/v2/aggs/grouped/locale/us/market/stocks/{day}'
        entry={'role':role,'date':day,'path':path,'parameters':{'adjusted':'false','include_otc':'false'},'status':'attempted'}
        manifest['requests'].append(entry); save()
        req=Request('https://api.massive.com'+path+'?adjusted=false&include_otc=false',
                    headers={'Authorization':'Bearer '+key})
        try:
            with opener.open(req,timeout=30) as response:
                entry['http_status']=response.status
                body=response.read(20_000_001)
            entry['response_bytes']=len(body)
            if len(body)>20_000_000:
                entry['status']='byte_cap'; save(); continue
            payload=json.loads(body); del body
            rows=payload.get('results',[])
            if payload.get('adjusted') is not False or not isinstance(rows,list):
                entry['status']='invalid_shape_or_adjustment'; save(); continue
            if payload.get('next_url') or payload.get('resultsCount')!=len(rows):
                entry['status']='incomplete'; save(); continue
            safe=[{f:r[f] for f in manifest['retained_fields'] if f in r} for r in rows]
            del payload,rows
            encoded=''.join(json.dumps(r,sort_keys=True)+'\n' for r in safe)
            filename=day+'.jsonl'; (out/filename).write_text(encoded)
            entry.update(status='success',records=len(safe),file=filename,
                         sha256=hashlib.sha256(encoded.encode()).hexdigest())
        except HTTPError as error:
            entry.update(status='http_failure',http_status=error.code)
        except (URLError,OSError,TimeoutError,ValueError,TypeError,AttributeError):
            entry['status']='network_or_parse_failure'
        save(); print(json.dumps(entry),flush=True)
    manifest['status']='completed' if all(e['status']=='success' for e in manifest['requests']) else 'incomplete'
    manifest['total_response_bytes']=sum(e.get('response_bytes',0) for e in manifest['requests'])
    if manifest['status']=='completed':
        from math import ceil
        allowance=ceil(max(e['response_bytes'] for e in manifest['requests'])*1.5)
        b1=json.loads((root/'data/raw/fmp_stage_b1/manifest.json').read_text())
        manifest['projection']={'method':'1.5 times maximum measured response bytes per date',
           'bytes_per_date':allowance,'date_upper_bound':751,
           'grouped_projected_bytes':allowance*751,
           'cumulative_projected_bytes':b1['response_bytes']+manifest['total_response_bytes']+allowance*748,
           'cumulative_projected_requests':len(b1['requests'])+751,
           'reuse_pilot_dates':True,
           'session_semantics_status':'not_suitable_without_regular_session_volume_evidence'}
    save(); print(json.dumps({k:v for k,v in manifest.items() if k!='requests'},indent=2))
    return 0 if manifest['status']=='completed' else 2

if __name__=='__main__':
    raise SystemExit(main())
