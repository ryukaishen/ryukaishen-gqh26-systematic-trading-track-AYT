"""Local full-window request lower bound; no API calls."""
import json
from collections import Counter
from pathlib import Path
from development_calendar import SESSIONS, EARLY_CLOSES

ROOT = Path(__file__).resolve().parents[1]
rows = [json.loads(line) for line in
        (ROOT/'data/cache/reference_bracketing/eligible_events.jsonl').read_text().splitlines()]
windows = {(r['symbol'], SESSIONS[SESSIONS.index(r['entry_session'])-1]) for r in rows}
ledger = json.loads((ROOT/'data/cache/acquisition_budget.json').read_text())
result = {
    'eligible_events_by_split': dict(Counter(r['split'] for r in rows)),
    'distinct_symbol_pre_event_windows': len(windows),
    'minimum_additional_requests': len(windows),
    'minimum_cumulative_requests': ledger['cumulative_requests']+len(windows),
    'request_ceiling': ledger['request_ceiling'],
    'remaining_requests': ledger['remaining_requests'],
    'request_deficit_before_pagination_or_databento': len(windows)-ledger['remaining_requests'],
    'full_transfer_projection_bytes': None,
    'transfer_projection_limitation': 'Five-record paginated capability responses cannot estimate complete window volume; request lower bound already blocks full acquisition.',
    'pilot_response_bytes': {'MSFT': 1406, 'AAPL': 1578},
    'early_close_windows': sum(day in EARLY_CLOSES for _, day in windows),
    'early_close_rule': 'Preserve fixed [15:50,15:55) ET; do not silently move window.',
    'status': 'blocked_by_existing_total_request_ceiling',
    'S0_coverage': 'unmeasured; no complete windows acquired',
    'contract_coverage': 'unmeasured; S0 and primary contract selection unavailable',
    'synchronized_quote_coverage': 'unmeasured'
}
out = ROOT/'data/cache/stage_c_nbbo_estimate.json'
out.write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
