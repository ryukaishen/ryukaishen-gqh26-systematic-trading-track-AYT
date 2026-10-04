"""Semantic taxonomy lookup only; no filings or market outcomes are queried."""
import json,sys
from pathlib import Path
from urllib.request import Request,build_opener
from urllib.parse import urlencode,urlsplit,parse_qsl
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from massive_stage_b2 import credential,NoRedirect
from submission_budget import Budget,atomic

def main():
 out=ROOT/'data/raw/massive_bonus_taxonomy';b=Budget(out);key=credential()
 if not key:raise RuntimeError('missing_MASSIVE_API_KEY')
 url='https://api.massive.com/stocks/taxonomies/vX/disclosures?'+urlencode({'limit':1000})
 request=b.reserve('bonus_taxonomy_only',0,500000,{'path':'/stocks/taxonomies/vX/disclosures','limit':1000})
 try:
  with build_opener(NoRedirect()).open(Request(url,headers={'Authorization':'Bearer '+key}),timeout=20) as r:body=r.read(500000)
  if len(body)>=500000:raise RuntimeError('response_cap')
  data=json.loads(body)
  if data.get('next_url'):raise RuntimeError('taxonomy_pagination_incomplete')
  if not isinstance(data.get('results'),list):raise RuntimeError('taxonomy_shape')
  safe={k:data.get(k) for k in ('results','status')};atomic(out/'taxonomy.json',safe)
  b.finish(request,len(body),'complete')
  candidates=[r for r in data['results'] if any(w in json.dumps(r).lower() for w in ('repurchase','buyback','buy-back'))]
  atomic(ROOT/'massive_bonus/taxonomy_lookup.json',{'endpoint':'/stocks/taxonomies/vX/disclosures','categories':len(data['results']),'candidates':candidates,'scope':'semantic definitions only; no filings/outcomes inspected'})
  print(json.dumps({'categories':len(data['results']),'candidates':candidates}),flush=True)
 except Exception as e:
  if request['status']=='in_flight':b.finish(request,500000,'incomplete')
  print('Taxonomy lookup blocked: '+type(e).__name__,flush=True);raise SystemExit(2)
if __name__=='__main__':main()
