"""A7 complete pre-event NBBO, two workers, durable page/event checkpoints."""
import argparse
import fcntl
import gzip
import hashlib
import json
import os
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from datetime import datetime,timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, parse_qsl, quote
from urllib.request import Request, build_opener
from frozen_sample_nbbo import FIELDS, window, summarize_quotes
from massive_grouped_pilot import NoRedirect

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/raw/full_universe_nbbo'
MAX_BODY=20_000_000

def atomic_json(path,value):
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,indent=2)+'\n')
    os.replace(temp,path)

def event_id(event):
    text='|'.join(str(event[f]) for f in ('issuer_cik','release_date','fiscal_year','fiscal_quarter'))
    return hashlib.sha256(text.encode()).hexdigest()

class Acquisition:
    def __init__(self):
        OUT.mkdir(parents=True,exist_ok=True)
        (OUT/'pages').mkdir(exist_ok=True)
        (OUT/'windows').mkdir(exist_ok=True)
        self.lockfile=(OUT/'process.lock').open('a')
        fcntl.flock(self.lockfile,fcntl.LOCK_EX|fcntl.LOCK_NB)
        self.lock=threading.RLock()
        self.stop=threading.Event()
        self.key=os.environ.get('MASSIVE_API_KEY')
        if not self.key:raise RuntimeError('Missing Massive credential')
        self.db=sqlite3.connect(OUT/'checkpoint.sqlite',check_same_thread=False)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript('''CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY,v TEXT);
          CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY,split TEXT,status TEXT,result TEXT);
          CREATE TABLE IF NOT EXISTS requests(id INTEGER PRIMARY KEY,event_id TEXT,page INTEGER,
             status TEXT,response_bytes INTEGER,reservation INTEGER,receipt TEXT);
        ''')
        source=ROOT/'data/cache/reference_bracketing/eligible_events.jsonl'
        blob=source.read_bytes()
        self.source_hash=hashlib.sha256(blob).hexdigest()
        self.events=[json.loads(line) for line in blob.splitlines()]
        assert len(self.events)==14340 and len({event_id(e) for e in self.events})==14340
        ledger_path=ROOT/'data/cache/acquisition_budget.json'
        existing=dict(self.db.execute('SELECT k,v FROM meta'))
        if not existing:
            ledger=json.loads(ledger_path.read_text())
            assert ledger['authority']=='EXPERIMENT.md A7' and ledger['request_ceiling']==20000
            self.db.executemany('INSERT INTO meta VALUES(?,?)',[
                ('source_sha256',self.source_hash),('base_ledger',json.dumps(ledger)),
                ('created_at',datetime.now(timezone.utc).isoformat()),('runtime_seconds','0')])
            self.db.executemany('INSERT INTO events VALUES(?,?,?,?)',[
                (event_id(e),e['split'],'pending',None) for e in self.events])
            self.db.commit()
        else:
            assert existing['source_sha256']==self.source_hash
        self.base=json.loads(self.db.execute("SELECT v FROM meta WHERE k='base_ledger'").fetchone()[0])
        self.recover()
        self.reuse_benchmark()
        self.update_ledger()

    def update_ledger(self):
        # In-flight reservations conservatively guard transfers before any worker reads bytes.
        count,used=self.db.execute('SELECT COUNT(*),COALESCE(SUM(response_bytes),0) FROM requests').fetchone()
        ledger={**self.base,'cumulative_requests':self.base['cumulative_requests']+count,
                'cumulative_bytes':self.base['cumulative_bytes']+used,
                'last_action':'A7 full-universe pre-event NBBO; no post-event/outcomes',
                'recorded_at':datetime.now(timezone.utc).isoformat()}
        ledger['remaining_requests']=ledger['request_ceiling']-ledger['cumulative_requests']
        ledger['remaining_bytes']=ledger['transfer_ceiling']-ledger['cumulative_bytes']
        atomic_json(ROOT/'data/cache/acquisition_budget.json',ledger)
        return ledger

    def recover(self):
        with self.lock:
            for rid,eid,page,reservation in self.db.execute(
                "SELECT id,event_id,page,reservation FROM requests WHERE status='in_flight'").fetchall():
                receipt=OUT/'pages'/f'{eid}.{page}.{rid}.receipt.json'
                if receipt.exists():
                    value=json.loads(receipt.read_text())
                    self.db.execute('UPDATE requests SET status=?,response_bytes=?,receipt=? WHERE id=?',
                                    (value['status'],value['response_bytes'],str(receipt),rid))
                else:
                    # A killed HTTP call may have transferred data: charge its entire reservation.
                    self.db.execute("UPDATE requests SET status='interrupted_unknown_transfer',response_bytes=? WHERE id=?",
                                    (reservation,rid))
            self.db.execute("UPDATE events SET status='pending' WHERE status='running'")
            self.db.commit()

    def reuse_benchmark(self):
        benchmark=ROOT/'data/raw/nbbo_benchmark'
        m=json.loads((benchmark/'manifest.json').read_text())
        assert m['status']=='completed'
        by_id={event_id(e):e for e in self.events}
        for eid,result in m['windows'].items():
            status=self.db.execute('SELECT status FROM events WHERE id=?',(eid,)).fetchone()
            assert status is not None
            if status[0]=='complete':continue
            day,start,end=window(by_id[eid])
            assert result['status']=='complete' and (result['pre_event_date'],result['start_ns'],result['end_ns'])==(day,start,end)
            encoded=gzip.decompress((benchmark/result['file']).read_bytes())
            assert hashlib.sha256(encoded).hexdigest()==result['retained_sha256']
            stats=summarize_quotes([json.loads(line) for line in encoded.splitlines()],{1})
            assert stats['S0']==result['S0'] and stats['valid_minute_bins']==result['valid_minute_bins']
            target=OUT/'windows'/f'{eid}.jsonl.gz'
            target.write_bytes((benchmark/result['file']).read_bytes())
            reused={**result,**stats,'file':str(target.relative_to(OUT)),
                    'benchmark_reused':True,'new_requests':0,'new_response_bytes':0}
            atomic_json(OUT/'windows'/f'{eid}.result.json',reused)
            self.db.execute('UPDATE events SET status=?,result=? WHERE id=?',('complete',json.dumps(reused),eid))
        self.db.commit()

    def reserve(self,eid,page):
        with self.lock:
            if self.stop.is_set():raise RuntimeError('Acquisition stopped')
            ledger=self.update_ledger()
            in_flight=self.db.execute("SELECT COALESCE(SUM(reservation),0) FROM requests WHERE status='in_flight'").fetchone()[0]
            available=ledger['remaining_bytes']-in_flight
            if ledger['remaining_requests']<1 or available<2:
                self.stop.set();raise RuntimeError('Acquisition budget exhausted')
            reservation=min(MAX_BODY+1,available)
            cur=self.db.execute('INSERT INTO requests(event_id,page,status,response_bytes,reservation) VALUES(?,?,?,?,?)',
                                (eid,page,'in_flight',0,reservation))
            self.db.commit()
            self.update_ledger()
            return cur.lastrowid,reservation

    def fetch(self,eid,page,url):
        rid,reservation=self.reserve(eid,page)
        info={'event_id':eid,'page':page,'request_id':rid,'status':'attempted',
              'response_bytes':0,'discarded_outside_window':0}
        body=b''
        records=[]
        try:
            request=Request(url,headers={'Authorization':'Bearer '+self.key,'Accept-Encoding':'gzip'})
            with build_opener(NoRedirect()).open(request,timeout=45) as response:
                info['http_status']=response.status
                info['content_encoding']=response.headers.get('Content-Encoding','')
                body=response.read(reservation)
            if len(body)>=reservation:raise ValueError('Page transfer reservation reached')
            decoded=gzip.decompress(body) if info['content_encoding']=='gzip' else body
            if len(decoded)>100_000_000:raise ValueError('Decoded response cap')
            payload=json.loads(decoded)
            records=payload.get('results',[])
            if not isinstance(records,list) or len(records)>50000:raise ValueError('Page shape')
            nxt=payload.get('next_url')
            if nxt:
                parsed=urlsplit(nxt)
                original=urlsplit(url)
                if parsed.scheme!='https' or parsed.hostname not in ('api.massive.com','api.polygon.io') or parsed.path!=original.path:
                    raise ValueError('Pagination destination')
                query=[(k,v) for k,v in parse_qsl(parsed.query) if k.lower()!='apikey']
                nxt='https://api.massive.com'+parsed.path+'?'+urlencode(query)
            info.update(status='success',next_url=nxt,records=len(records))
        except HTTPError as error:
            body=error.read(reservation)
            info.update(status='http_failure',http_status=error.code)
        except (URLError,OSError,TimeoutError,ValueError,TypeError):
            info['status']='network_shape_or_cap_failure'
        info['response_bytes']=len(body)
        return rid,info,records

    def acquire(self,event):
        eid=event_id(event)
        day,start,end=window(event)
        assert '2023-03-06'<=day<='2025-12-31' and end-start==300*10**9
        with self.lock:
            self.db.execute("UPDATE events SET status='running' WHERE id=?",(eid,));self.db.commit()
            receipts=self.db.execute("SELECT receipt FROM requests WHERE event_id=? AND status='success' ORDER BY page,id",(eid,)).fetchall()
        completed_pages={}
        for (name,) in receipts:
            receipt=json.loads(Path(name).read_text())
            completed_pages[receipt['page']]=receipt
        path='/v3/quotes/'+quote(event['symbol'],safe='')
        url='https://api.massive.com'+path+'?'+urlencode({'timestamp.gte':start,'timestamp.lt':end,
             'sort':'timestamp','order':'asc','limit':50000})
        started=time.perf_counter()
        all_records=[]
        total_bytes=discarded=0
        seen_urls=set()
        for page in range(100):
            if url in seen_urls:raise RuntimeError('Pagination loop')
            seen_urls.add(url)
            if page in completed_pages:
                info=completed_pages[page]
                encoded=gzip.decompress((OUT/info['file']).read_bytes())
                assert hashlib.sha256(encoded).hexdigest()==info['retained_sha256']
                rows=[json.loads(line) for line in encoded.splitlines()]
            else:
                rid,info,raw=self.fetch(eid,page,url)
                rows=[]
                if info['status']=='success':
                    for row in raw:
                        stamp=row.get('sip_timestamp')
                        if not isinstance(stamp,int) or not start<=stamp<end:
                            info['discarded_outside_window']+=1;continue
                        rows.append({f:row[f] for f in FIELDS if f in row})
                    encoded=''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows).encode()
                    filename=f'pages/{eid}.{page}.{rid}.jsonl.gz'
                    temp=OUT/(filename+'.tmp')
                    temp.write_bytes(gzip.compress(encoded,mtime=0));os.replace(temp,OUT/filename)
                    info.update(file=filename,retained_sha256=hashlib.sha256(encoded).hexdigest())
                receipt_path=OUT/'pages'/f'{eid}.{page}.{rid}.receipt.json'
                atomic_json(receipt_path,info)
                with self.lock:
                    self.db.execute('UPDATE requests SET status=?,response_bytes=?,receipt=? WHERE id=?',
                                    (info['status'],info['response_bytes'],str(receipt_path),rid))
                    self.db.commit();self.update_ledger()
                if info['status']!='success':
                    self.stop.set()
                    with self.lock:
                        self.db.execute("UPDATE events SET status='blocked' WHERE id=?",(eid,));self.db.commit()
                    raise RuntimeError('HTTP/network/shape blocker '+str(info.get('http_status','')))
            all_records.extend(rows)
            total_bytes+=info['response_bytes']
            discarded+=info['discarded_outside_window']
            url=info.get('next_url')
            if not url:break
        else:raise RuntimeError('Pagination cap')
        encoded=''.join(json.dumps(r,sort_keys=True)+'\n' for r in all_records).encode()
        filename=f'windows/{eid}.jsonl.gz'
        temp=OUT/(filename+'.tmp')
        temp.write_bytes(gzip.compress(encoded,mtime=0));os.replace(temp,OUT/filename)
        stats=summarize_quotes(all_records,{1})
        result={'symbol':event['symbol'],'split':event['split'],'pre_event_date':day,
                'start_ns':start,'end_ns':end,'status':'complete','records':len(all_records),
                'discarded_outside_window':discarded,'response_bytes':total_bytes,'pages':page+1,
                'file':filename,'retained_sha256':hashlib.sha256(encoded).hexdigest(),
                'benchmark_reused':False,'runtime_seconds':time.perf_counter()-started,**stats}
        atomic_json(OUT/'windows'/f'{eid}.result.json',result)
        with self.lock:
            self.db.execute('UPDATE events SET status=?,result=? WHERE id=?',('complete',json.dumps(result),eid))
            self.db.commit()
        return eid

    def progress(self,status,runtime):
        with self.lock:
            counts=dict(self.db.execute('SELECT status,COUNT(*) FROM events GROUP BY status'))
            request_count,transfer=self.db.execute('SELECT COUNT(*),COALESCE(SUM(response_bytes),0) FROM requests').fetchone()
            ledger=self.update_ledger()
            manifest={'status':status,'source_sha256':self.source_hash,'event_count':14340,
                      'events_by_status':counts,'reused_benchmark_windows':20,
                      'new_requests_including_pagination':request_count,'new_response_bytes':transfer,
                      'runtime_seconds_this_run':runtime,'workers':2,
                      'checkpoint':'checkpoint.sqlite + sanitized page files/receipts + complete-window hashes',
                      'request_ceiling':20000,'transfer_ceiling':4000000000,
                      'ledger_cumulative_requests':ledger['cumulative_requests'],
                      'ledger_cumulative_bytes':ledger['cumulative_bytes'],
                      'scope':'pre-event only; no post-event, X, outcomes or holdout'}
            atomic_json(OUT/'manifest.json',manifest)
            return manifest

    def run(self,limit=None):
        started=time.perf_counter()
        pending=[]
        for event in self.events:
            status=self.db.execute('SELECT status FROM events WHERE id=?',(event_id(event),)).fetchone()[0]
            if status!='complete':pending.append(event)
        if limit:pending=pending[:limit]
        iterator=iter(pending)
        last_print=time.perf_counter()
        error=False
        with ThreadPoolExecutor(max_workers=2) as pool:
            active={}
            for _ in range(2):
                event=next(iterator,None)
                if event:active[pool.submit(self.acquire,event)]=event_id(event)
            while active:
                done,_=wait(active,timeout=5,return_when=FIRST_COMPLETED)
                for future in done:
                    active.pop(future)
                    try:future.result()
                    except Exception as exc:
                        self.stop.set();error=True
                        # Never print exception text containing authenticated request URLs.
                        print('BLOCKED: acquisition task failed; inspect sanitized checkpoint status',flush=True)
                    if not self.stop.is_set():
                        event=next(iterator,None)
                        if event:active[pool.submit(self.acquire,event)]=event_id(event)
                if time.perf_counter()-last_print>=20:
                    result=self.progress('in_progress',time.perf_counter()-started)
                    print(json.dumps({k:result[k] for k in ('events_by_status','new_requests_including_pagination','new_response_bytes','runtime_seconds_this_run')}),flush=True)
                    last_print=time.perf_counter()
        completed=self.db.execute("SELECT COUNT(*) FROM events WHERE status='complete'").fetchone()[0]
        status='completed' if completed==14340 else ('blocked' if error else 'checkpointed')
        result=self.progress(status,time.perf_counter()-started)
        print(json.dumps(result,indent=2),flush=True)
        return 2 if error else 0

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--limit',type=int)
    args=parser.parse_args()
    return Acquisition().run(args.limit)

if __name__=='__main__':
    raise SystemExit(main())
