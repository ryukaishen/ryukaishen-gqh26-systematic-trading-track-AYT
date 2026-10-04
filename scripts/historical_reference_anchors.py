"""Execute the approved bounded historical reference anchors; no outcome data."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit
from urllib.request import Request, build_opener
from urllib.error import HTTPError, URLError
from massive_stage_b2 import credential, NoRedirect

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/raw/historical_reference'
FIELDS=('ticker','market','locale','type','primary_exchange','currency_name','currency_symbol',
        'active','cik','composite_figi','share_class_figi','delisted_utc','last_updated_utc')
PAGE_BYTES=1_000_000

def next_request(raw, base):
    parts=urlsplit(raw)
    if parts.scheme!='https' or parts.netloc!='api.massive.com' or parts.path!='/v3/reference/tickers' or parts.fragment:
        raise ValueError('pagination endpoint mismatch')
    query={}
    for k,v in parse_qsl(parts.query,keep_blank_values=True):
        if k.lower() in ('apikey','api_key'): continue
        if k not in set(base)|{'cursor'} or k in query:
            raise ValueError('pagination parameter mismatch')
        if k in base and str(base[k])!=v: raise ValueError('pagination scope mismatch')
        query[k]=v
    if not query.get('cursor'): raise ValueError('missing pagination cursor')
    # Keep date and original filters explicit even on cursor-only links.
    query={**base,**query}
    return 'https://api.massive.com/v3/reference/tickers?'+urlencode(query),hashlib.sha256(query['cursor'].encode()).hexdigest()

def main():
    plan=json.loads((ROOT/'data/cache/stage_b2/optimized_reference_plan.json').read_text())
    usage=json.loads((ROOT/'data/cache/stage_b2/liquidity_summary.json').read_text())
    assert plan['anchor_request_upper_bound']<=usage['remaining_requests']==495
    assert plan['anchor_transfer_upper_bound']<=usage['remaining_bytes']
    key=credential()
    if not key: print('BLOCKED: credential unavailable'); return 2
    OUT.mkdir(parents=True,exist_ok=True); file=OUT/'manifest.json'
    if file.exists():
        print('BLOCKED: existing manifest; no automatic rerun'); return 2
    manifest={'status':'in_progress','acquisition_time':datetime.now(timezone.utc).isoformat(),
       'scope':'development-only approved 34 point-in-time anchors','fields':FIELDS,
       'prior_requests':usage['cumulative_requests'],'prior_bytes':usage['cumulative_bytes'],
       'request_ceiling':1500,'byte_ceiling':4_000_000_000,'requests':[],
       'response_bytes':0,'completed_anchors':[],'plan_sha256':hashlib.sha256((ROOT/'data/cache/stage_b2/optimized_reference_plan.json').read_bytes()).hexdigest()}
    def save(): file.write_text(json.dumps(manifest,indent=2)+'\n')
    def stop(reason):
        manifest.update(status='incomplete',stop_reason=reason);save();print('STOP:',reason,flush=True);return 2
    save(); opener=build_opener(NoRedirect())
    for spec in plan['requests']:
        base=spec['parameters']; day=base['date']; url='https://api.massive.com'+spec['endpoint']+'?'+urlencode(base)
        cursor_hash=None; seen=set()
        for page in range(spec['page_cap']):
            if len(manifest['requests'])>=495: return stop('remaining request cap')
            if manifest['prior_bytes']+manifest['response_bytes']+PAGE_BYTES+1>manifest['byte_ceiling']:
                return stop('remaining transfer cap')
            entry={'date':day,'page':page,'parameters':base,'cursor_hash':cursor_hash,'status':'attempted'}
            manifest['requests'].append(entry);save()
            try:
                req=Request(url,headers={'Authorization':'Bearer '+key})
                with opener.open(req,timeout=30) as response:
                    entry['http_status']=response.status; body=response.read(PAGE_BYTES+1)
                entry['response_bytes']=len(body); manifest['response_bytes']+=len(body)
                if len(body)>PAGE_BYTES: return stop('per-page byte cap')
                payload=json.loads(body);del body
                rows=payload.get('results',[])
                if not isinstance(rows,list) or len(rows)>1000: return stop('response shape or record cap')
                if payload.get('count') is not None and payload['count']!=len(rows):
                    return stop('response count mismatch')
                safe=[]
                for r in rows:
                    if not isinstance(r,dict): return stop('unexpected reference record')
                    if r.get('market')!='stocks' or r.get('locale')!='us' or r.get('type')!='CS' or r.get('active') is not True:
                        return stop('response reference scope mismatch')
                    safe.append({k:r[k] for k in FIELDS if k in r})
                encoded=''.join(json.dumps(r,sort_keys=True)+'\n' for r in safe)
                digest=hashlib.sha256(encoded.encode()).hexdigest()
                if safe and digest in seen: return stop('repeated reference page')
                seen.add(digest)
                name=f'{day}_page{page}.jsonl';(OUT/name).write_text(encoded)
                entry.update(status='success',records=len(safe),file=name,sha256=digest)
                next_url=payload.get('next_url');del payload,rows
                save()
                if not next_url:
                    manifest['completed_anchors'].append(day);save()
                    print('Completed reference anchor',day,'pages',page+1,'total requests',len(manifest['requests']),flush=True)
                    break
                if page+1>=spec['page_cap']: return stop('snapshot page cap; incomplete anchor')
                url,cursor_hash=next_request(next_url,base);del next_url
            except HTTPError as error:
                entry.update(status='http_failure',http_status=error.code)
                size=len(error.read(PAGE_BYTES+1));entry['response_bytes']=size;manifest['response_bytes']+=size
                return stop('HTTP failure')
            except (URLError,OSError,TimeoutError,ValueError,TypeError):
                return stop('network, parsing or pagination validation failure')
    manifest['status']='completed';save()
    print(json.dumps({'status':manifest['status'],'anchors':len(manifest['completed_anchors']),
          'requests':len(manifest['requests']),'response_bytes':manifest['response_bytes'],
          'remaining_requests':495-len(manifest['requests'])},indent=2))
    return 0

if __name__=='__main__': raise SystemExit(main())
