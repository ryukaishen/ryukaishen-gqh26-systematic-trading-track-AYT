"""Complete fixed-window NBBO acquisition for A6; no strategy outcomes."""
import argparse
import gzip
import hashlib
import json
import math
import os
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, parse_qsl
from urllib.request import Request, build_opener
from zoneinfo import ZoneInfo
from development_calendar import SESSIONS
from massive_grouped_pilot import NoRedirect

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'data/raw/frozen_sample_nbbo'
FIELDS = ['bid_price', 'ask_price', 'bid_size', 'ask_size', 'sip_timestamp',
          'participant_timestamp', 'conditions', 'bid_exchange', 'ask_exchange', 'sequence_number', 'tape']

def summarize_quotes(records, regular_codes):
    """Shared benchmark/full-universe validity and midpoint implementation."""
    mids = []
    minute = defaultdict(list)
    condition_counts = Counter()
    rejected = Counter()
    for r in records:
        conditions = r.get('conditions', [])
        condition_counts.update(str(c) for c in conditions)
        bid, ask = r.get('bid_price', 0), r.get('ask_price', 0)
        if not all(isinstance(x, (int,float)) and math.isfinite(x) for x in [bid, ask]) or bid <= 0 or ask <= bid:
            rejected['price'] += 1; continue
        if r.get('bid_size', 0) <= 0 or r.get('ask_size', 0) <= 0:
            rejected['size'] += 1; continue
        if any(c not in regular_codes for c in conditions):
            rejected['unresolved_condition'] += 1; continue
        midpoint = (bid+ask)/2
        mids.append(midpoint)
        minute[str(r['sip_timestamp']//(60*10**9))].append(midpoint)
    return {'condition_counts':dict(condition_counts), 'rejected':dict(rejected),
            'valid_quote_count':len(mids), 'valid_minute_bins':len(minute),
            'minute_midpoints':{k:median(v) for k,v in minute.items()},
            'S0':median(mids) if len(minute)>=3 else None}

def window(event):
    day = SESSIONS[SESSIONS.index(event['entry_session'])-1]
    start = datetime.fromisoformat(day+'T15:50:00').replace(tzinfo=ZoneInfo('America/New_York'))
    return day, int(start.timestamp())*10**9, int(start.timestamp()+300)*10**9

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int)
    parser.add_argument('--benchmark', action='store_true')
    args = parser.parse_args()
    global OUT
    sample_dir = ROOT/'data/cache/nbbo_benchmark_selection' if args.benchmark else ROOT/'data/cache/frozen_development_sample'
    if args.benchmark:
        OUT = ROOT/'data/raw/nbbo_benchmark'
    elif json.loads((sample_dir/'manifest.json').read_text()).get('status') == 'paused':
        print('BLOCKED: sampling amendment paused'); return 2
    blob = (sample_dir/'events.jsonl').read_bytes()
    frozen = json.loads((sample_dir/'manifest.json').read_text())
    assert hashlib.sha256(blob).hexdigest() == frozen['sample_sha256']
    events = [json.loads(line) for line in blob.splitlines()]
    key = os.environ.get('MASSIVE_API_KEY')
    if not key:
        print('BLOCKED: missing Massive credential'); return 2
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT/'manifest.json'
    m = json.loads(path.read_text()) if path.exists() else {
        'sample_sha256': frozen['sample_sha256'], 'started_at': datetime.now(timezone.utc).isoformat(),
        'windows': {}, 'requests': [], 'status': 'in_progress',
        'scope': '20-event representative benchmark, pre-event only' if args.benchmark else 'frozen sample pre-event [15:50,15:55) ET only; no backfill'}
    assert m['sample_sha256'] == frozen['sample_sha256']
    ledger_path = ROOT/'data/cache/acquisition_budget.json'
    opener = build_opener(NoRedirect())
    condition_file = ROOT/'data/raw/nbbo_benchmark_conditions/conditions.json'
    condition_map = json.loads(condition_file.read_text()) if condition_file.exists() else []
    regular_codes = {r['id'] for r in condition_map if r.get('type')=='quote_condition' and r.get('name') in (
        'Regular Quote', 'Regular', 'Regular Two-Sided Open', 'Regular Two-Sided Open Quote', 'Regular - Two-Sided Open Quote')}
    started = time.perf_counter()
    def save():
        path.write_text(json.dumps(m, indent=2)+'\n')
    for event in events[:args.limit] if args.limit else events:
        eid = event['sample_sha256']
        if eid in m['windows']:
            if m['windows'][eid]['status'] == 'complete': continue
            print('BLOCKED: prior incomplete window; no automatic retries'); return 2
        day, start, end = window(event)
        entry = {'symbol': event['symbol'], 'split': event['split'], 'pre_event_date': day,
                 'start_ns': start, 'end_ns': end, 'status': 'in_progress',
                 'records': 0, 'discarded_outside_window': 0, 'response_bytes': 0}
        window_started = time.perf_counter()
        m['windows'][eid] = entry
        url = 'https://api.massive.com/v3/quotes/'+event['symbol']+'?'+urlencode({
            'timestamp.gte': start, 'timestamp.lt': end, 'sort': 'timestamp', 'order': 'asc', 'limit': 50000})
        records = []
        seen_urls = set()
        for page in range(100):
            ledger = json.loads(ledger_path.read_text())
            if ledger['remaining_requests'] < 1 or ledger['remaining_bytes'] < 1:
                m['status'] = 'budget_blocked'; save(); print('BLOCKED: acquisition ceiling'); return 2
            if url in seen_urls:
                m['status'] = 'pagination_blocked'; save(); return 2
            seen_urls.add(url)
            req_info = {'event_id': eid, 'page': page, 'status': 'attempted'}
            m['requests'].append(req_info); save()
            max_bytes = min(20_000_000, ledger['remaining_bytes'])
            body = b''
            try:
                req = Request(url, headers={'Authorization': 'Bearer '+key, 'Accept-Encoding': 'gzip'})
                with opener.open(req, timeout=45) as response:
                    req_info['http_status'] = response.status
                    body = response.read(max_bytes)
                    more = response.read(1) if len(body) == max_bytes else b''
                    req_info['content_encoding'] = response.headers.get('Content-Encoding', '')
                if more:
                    raise ValueError('response exceeds bounded transfer allowance')
                decoded = gzip.decompress(body) if req_info['content_encoding'] == 'gzip' else body
                payload = json.loads(decoded)
                rows = payload.get('results', [])
                if not isinstance(rows, list) or len(rows) > 50000:
                    raise ValueError('invalid page shape')
                for row in rows:
                    stamp = row.get('sip_timestamp')
                    if not isinstance(stamp, int) or not start <= stamp < end:
                        entry['discarded_outside_window'] += 1
                        continue
                    records.append({f: row[f] for f in FIELDS if f in row})
                next_url = payload.get('next_url')
                if next_url:
                    parsed = urlsplit(next_url)
                    if parsed.scheme != 'https' or parsed.hostname != 'api.massive.com' or parsed.path != '/v3/quotes/'+event['symbol']:
                        raise ValueError('unsafe pagination destination')
                    # Never retain or emit credentials from provider pagination URLs.
                    clean = [(k, v) for k, v in parse_qsl(parsed.query) if k.lower() != 'apikey']
                    next_url = 'https://api.massive.com'+parsed.path+'?'+urlencode(clean)
                req_info.update(status='success', records=len(rows), paginated=bool(next_url))
            except HTTPError as error:
                body = error.read(max_bytes)
                req_info.update(status='http_failure', http_status=error.code)
            except (URLError, OSError, TimeoutError, ValueError, TypeError):
                req_info['status'] = 'network_shape_or_cap_failure'
            req_info['response_bytes'] = len(body)
            entry['response_bytes'] += len(body)
            ledger['cumulative_requests'] += 1
            ledger['cumulative_bytes'] += len(body)
            ledger.update(remaining_requests=ledger['request_ceiling']-ledger['cumulative_requests'],
                          remaining_bytes=ledger['transfer_ceiling']-ledger['cumulative_bytes'],
                          last_action='20-event pre-event NBBO benchmark; no X/outcomes' if args.benchmark else 'A6 frozen-sample pre-event NBBO; no outcomes')
            ledger_path.write_text(json.dumps(ledger, indent=2)+'\n')
            if req_info['status'] != 'success':
                entry['status'] = 'incomplete'; m['status'] = 'blocked'; save()
                print('BLOCKED:', req_info['status'], req_info.get('http_status')); return 2
            if not next_url: break
            url = next_url
        else:
            entry['status'] = 'incomplete_page_cap'; m['status'] = 'blocked'; save(); return 2
        encoded = ''.join(json.dumps(r, sort_keys=True)+'\n' for r in records).encode()
        filename = eid+'.jsonl.gz'
        (OUT/filename).write_bytes(gzip.compress(encoded, mtime=0))
        stats = summarize_quotes(records, regular_codes)
        entry.update(status='complete', records=len(records), file=filename,
                     retained_sha256=hashlib.sha256(encoded).hexdigest(),
                     **stats,
                     runtime_seconds=time.perf_counter()-window_started,
                     accepted_regular_condition_codes=sorted(regular_codes),
                     condition_limitation='Accept only absent/empty or provider-labelled regular quote conditions. Other codes unresolved/rejected, not presumed valid.')
        save()
        count = len(m['windows'])
        if count <= 10 or count % 50 == 0:
            print(json.dumps({'complete_windows':count, 'latest_records':len(records),
                              'latest_response_bytes':entry['response_bytes'],
                              'latest_valid_minutes':stats['valid_minute_bins']}), flush=True)
    m['status'] = 'completed' if len(m['windows']) == len(events) else 'pilot_complete'
    m['runtime_seconds'] = m.get('runtime_seconds', 0)+time.perf_counter()-started
    sizes = [r['response_bytes'] for r in m['windows'].values() if r['status']=='complete']
    pages = [sum(q['event_id']==eid for q in m['requests']) for eid in m['windows']]
    m['projection'] = {'measured_windows':len(sizes), 'conservative_max_times_1_5_bytes':
                       math.ceil(max(sizes)*1.5)*len(events),
                       'conservative_max_times_1_5_requests':math.ceil(max(pages)*1.5)*len(events),
                       'scope':'underlying pre-event windows only; not a guarantee or full Stage C projection'}
    save(); print(json.dumps({'status':m['status'],'projection':m['projection']}), flush=True)
    return 0

if __name__=='__main__':
    raise SystemExit(main())
