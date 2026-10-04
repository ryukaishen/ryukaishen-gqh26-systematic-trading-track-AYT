"""Two fixed pre-event NBBO capability checks; no retries or outcomes."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, build_opener, HTTPRedirectHandler

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def main():
    root = Path(__file__).resolve().parents[1]
    out = root / 'data/raw/stage_c_stock_nbbo_probe'
    ledger_path = root / 'data/cache/acquisition_budget.json'
    ledger = json.loads(ledger_path.read_text())
    key = os.environ.get('MASSIVE_API_KEY')
    if not key or (out / 'manifest.json').exists():
        print('BLOCKED: missing credential or existing probe; no automatic rerun')
        return 2
    if ledger['remaining_requests'] < 2 or ledger['remaining_bytes'] < 20002:
        print('BLOCKED: insufficient acquisition budget')
        return 2
    out.mkdir(parents=True, exist_ok=True)
    manifest = {'started_at': datetime.now(timezone.utc).isoformat(),
                'requests': [], 'status': 'in_progress', 'S0_computed': False}
    opener = build_opener(NoRedirect())
    def save():
        (out / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    fields = ['bid_price', 'ask_price', 'bid_size', 'ask_size', 'sip_timestamp',
              'participant_timestamp', 'conditions', 'bid_exchange', 'ask_exchange',
              'sequence_number', 'tape']
    for symbol, date, start, end in [
        ('MSFT', '2023-04-25', 1682452200000000000, 1682452500000000000),
        ('AAPL', '2023-05-04', 1683229800000000000, 1683230100000000000)]:
        params = {'timestamp.gte': start, 'timestamp.lt': end,
                  'sort': 'timestamp', 'order': 'asc', 'limit': 5}
        entry = {'symbol': symbol, 'date': date, 'path': '/v3/quotes/'+symbol,
                 'parameters': params, 'status': 'attempted'}
        manifest['requests'].append(entry)
        save()
        body = b''
        try:
            request = Request('https://api.massive.com'+entry['path']+'?'+urlencode(params),
                              headers={'Authorization': 'Bearer '+key})
            with opener.open(request, timeout=30) as response:
                entry['http_status'] = response.status
                body = response.read(10001)
            if len(body) > 10000:
                entry['status'] = 'byte_cap'
            else:
                payload = json.loads(body)
                rows = payload.get('results', [])
                if not isinstance(rows, list) or len(rows) > 5:
                    entry['status'] = 'invalid_shape'
                else:
                    safe = [{f: r[f] for f in fields if f in r} for r in rows]
                    (out / (symbol+'.jsonl')).write_text(''.join(json.dumps(r)+'\n' for r in safe))
                    entry.update(status='success', records=len(rows),
                                 paginated=bool(payload.get('next_url')),
                                 available_fields=sorted(set().union(*(set(r) for r in safe))))
        except HTTPError as error:
            entry.update(status='http_failure', http_status=error.code)
            body = error.read(10001)
            try:
                message = json.loads(body).get('message', '')
                entry['historical_entitlement_denied'] = (
                    error.code == 403 and 'entitle' in str(message).lower())
            except (ValueError, AttributeError):
                pass
        except (URLError, OSError, TimeoutError, ValueError, TypeError):
            entry['status'] = 'network_or_parse_failure'
        entry['response_bytes'] = len(body)
        ledger['cumulative_requests'] += 1
        ledger['cumulative_bytes'] += len(body)
        ledger['remaining_requests'] = ledger['request_ceiling']-ledger['cumulative_requests']
        ledger['remaining_bytes'] = ledger['transfer_ceiling']-ledger['cumulative_bytes']
        ledger['last_action'] = 'Stage C two fixed pre-event stock NBBO capability checks'
        ledger['recorded_at'] = datetime.now(timezone.utc).isoformat()
        ledger_path.write_text(json.dumps(ledger, indent=2)+'\n')
        save()
        print(json.dumps(entry), flush=True)
    manifest['status'] = 'access_available' if all(
        r['status'] == 'success' and r.get('records', 0) > 0 for r in manifest['requests']) else 'blocked'
    save()
    return 0 if manifest['status'] == 'access_available' else 2

if __name__ == '__main__':
    raise SystemExit(main())
