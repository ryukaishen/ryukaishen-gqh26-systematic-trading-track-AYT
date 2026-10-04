"""Development-only FMP acquisition. No raw responses or outcome fields persisted."""
import hashlib
import json
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, build_opener, HTTPRedirectHandler

START, END = date(2023, 4, 3), date(2025, 12, 31)
FIELDS = ('symbol', 'date', 'time', 'lastUpdated', 'fiscalDateEnding',
          'fiscalYear', 'fiscalPeriod', 'period', 'year', 'cik', 'id')
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data' / 'raw' / 'fmp_stage_b1'
MAX_REQUESTS, MAX_BYTES, MAX_PAGE_BYTES = 1500, 2_000_000_000, 20_000_000

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def main():
    key = os.environ.get('FMP_API_KEY') or os.environ.get('FINANCIAL_MODELING_PREP_API_KEY')
    if not key:
        print('BLOCKED: FMP credential unavailable; zero provider requests.')
        return 2
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / 'manifest.json').exists():
        print('BLOCKED: existing acquisition manifest; no automatic overwrite or rerun.')
        return 2
    opener = build_opener(NoRedirect())
    manifest = {'status': 'in_progress', 'start': str(START), 'end': str(END),
                'acquired_at': datetime.now(timezone.utc).isoformat(),
                'endpoint': 'https://financialmodelingprep.com/stable/earnings-calendar',
                'requests': [], 'response_bytes': 0, 'retained_fields': FIELDS,
                'window_days': 7, 'final_exact_day': str(END),
                'discarded_out_of_window_rows': 0}
    records = []
    def save():
        (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    def stop(reason):
        manifest['status'] = 'incomplete'
        manifest['stop_reason'] = reason
        save()
        print('STOP:', reason, '; no completeness or coverage claim.')
        return 2
    d = START
    while d <= END:
        # Reserve END for its own exact-day request on every pagination page.
        e = END if d == END else min(d + timedelta(days=6), END - timedelta(days=1))
        seen_pages = set()
        for page in range(MAX_REQUESTS):
            if len(manifest['requests']) >= MAX_REQUESTS:
                return stop('request cap')
            if manifest['response_bytes'] + MAX_PAGE_BYTES > MAX_BYTES:
                return stop('transfer cap')
            params = {'from': str(d), 'to': str(e), 'page': page, 'includeReportTimes': 'true'}
            # Credential-bearing request URL exists only in process memory; never log it.
            req = Request(manifest['endpoint'] + '?' + urlencode({**params, 'apikey': key}))
            entry = {'parameters': params, 'status': 'attempted'}
            manifest['requests'].append(entry)
            save()
            try:
                with opener.open(req, timeout=30) as response:
                    body = response.read(MAX_PAGE_BYTES + 1)
                entry['bytes'] = len(body)
                manifest['response_bytes'] += len(body)
                if len(body) > MAX_PAGE_BYTES:
                    return stop('page byte cap')
                payload = json.loads(body)
                del body
            except HTTPError as error:
                entry['http_status'] = error.code
                return stop('HTTP failure')
            except (URLError, TimeoutError, OSError, ValueError):
                return stop('network or parsing failure')
            if not isinstance(payload, list):
                return stop('unexpected response shape')
            received_rows = len(payload)
            discarded_rows = 0
            safe = []
            for row in payload:
                if not isinstance(row, dict):
                    return stop('unexpected record shape')
                try:
                    event_day = date.fromisoformat(str(row.get('date', '')))
                except ValueError:
                    return stop('missing or invalid event date')
                if not d <= event_day <= e:
                    discarded_rows += 1
                    manifest['discarded_out_of_window_rows'] += 1
                    continue
                kept = {field: row[field] for field in FIELDS if field in row}
                if not isinstance(kept.get('symbol'), str) or not kept['symbol']:
                    return stop('missing event symbol')
                safe.append(kept)
            del payload
            entry.update(status='success', records=len(safe),
                         received_rows=received_rows, discarded_out_of_window_rows=discarded_rows)
            # A page containing only discarded rows is not a terminal empty page.
            if received_rows == 0:
                save()
                break
            encoded = '\n'.join(json.dumps(row, sort_keys=True) for row in safe) + '\n'
            digest = hashlib.sha256(encoded.encode()).hexdigest()
            if digest in seen_pages:
                return stop('repeated page; pagination completeness unresolved')
            seen_pages.add(digest)
            filename = f'{d}_{e}_page{page}.jsonl'
            (OUT / filename).write_text(encoded)
            entry.update(file=filename, sha256=digest)
            records.extend(safe)
            save()
            print(str(d), str(e), 'page', page, 'retained rows', len(safe), flush=True)
        else:
            return stop('pagination cap')
        d = e + timedelta(days=1)
    pairs = {(row['symbol'], row['date']) for row in records}
    symbols = {row['symbol'] for row in records}
    dates = {row['date'] for row in records}
    unique_records = {json.dumps(row, sort_keys=True) for row in records}
    # Weekdays are a request upper bound, not a verified exchange calendar.
    weekdays = sum((START + timedelta(days=i)).weekday() < 5
                   for i in range((END - START).days + 1))
    manifest.update(status='completed_calendar_acquisition', raw_rows=len(records),
                    distinct_allowlisted_rows=len(unique_records),
                    unique_symbol_dates=len(pairs), unique_symbols=len(symbols),
                    unique_dates=len(dates),
                    stage_b2_mapping_request_estimate=len(pairs),
                    stage_b2_grouped_daily_weekday_request_upper_bound=weekdays,
                    stage_b2_request_subtotal=len(pairs) + weekdays,
                    limitations=['Calendar rows are not verified original quarterly events.',
                                 'Fiscal-period and historical universe mapping pending.',
                                 'Grouped daily subtotal excludes pre-start lookback, fiscal metadata, delisting reconciliation and pagination.',
                                 'No timing-coverage or historical-vintage pass asserted.'])
    save()
    print(json.dumps({k: v for k, v in manifest.items() if k not in ('requests',)}, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
