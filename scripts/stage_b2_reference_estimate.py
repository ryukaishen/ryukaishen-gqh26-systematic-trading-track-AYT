"""Local reference-work estimate from screened candidates; no API requests."""
import json
from pathlib import Path
from collections import Counter, defaultdict

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'data/cache/stage_b2'

def main():
    summary=json.loads((CACHE/'liquidity_summary.json').read_text())
    rows=[json.loads(line) for line in (CACHE/'liquidity_survivors.jsonl').read_text().splitlines()]
    by_day=defaultdict(set)
    for r in rows: by_day[r['entry_session']].add(r['symbol'])
    symbols={r['symbol'] for r in rows}
    # List queries can validate multiple tickers at a date; 1000 is the documented page max.
    # This ideal bound excludes all noncandidate tickers that a broad query would also return.
    optimistic_pages=sum((len(v)+999)//1000 for v in by_day.values())
    direct_requests=sum(len(v) for v in by_day.values())
    # A single point per symbol is a capability/profile sample, not interval validation.
    result={'surviving_events':len(rows),'surviving_symbols':len(symbols),
            'distinct_surviving_entry_sessions':len(by_day),
            'max_surviving_symbols_on_one_session':max(map(len,by_day.values()),default=0),
            'direct_symbol_session_requests':direct_requests,
            'bulk_at_each_candidate_session_ideal_page_lower_bound':optimistic_pages,
            'single_snapshot_per_symbol_requests':len(symbols),
            'single_snapshot_limitation':'does not validate historical status for all event dates',
            'remaining_requests':summary['remaining_requests'],'remaining_bytes':summary['remaining_bytes'],
            'bulk_ideal_bound_fits_remaining_requests':optimistic_pages<=summary['remaining_requests'],
            'references_acquired':False,
            'limitations':['Bulk lower bound assumes returned pages contain only candidate records; actual all-ticker pages also include other securities.',
                           'Inactive/delisting reconciliation, ticker changes, issuer mapping, fiscal metadata, options and retrieval costs are additional.',
                           'No budget decision uses present-day status as historical status.'],
            'provider_documentation':'https://massive.com/docs/rest/stocks/tickers/all-tickers'}
    (CACHE/'reference_estimate.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return result

if __name__=='__main__': main()
