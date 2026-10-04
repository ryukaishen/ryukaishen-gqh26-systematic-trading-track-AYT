"""Local timing coverage from the full FMP extract; no network or outcomes."""
import hashlib
import json
from collections import Counter, defaultdict, deque
from decimal import Decimal, InvalidOperation
from pathlib import Path
from statistics import median
from development_calendar import ACQUISITION_DATES, SESSIONS, session_index

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'data/cache/stage_b2'
FISCAL_FIELDS=('fiscalPeriod','fiscalYear','fiscalDateEnding','period','year')

def normalized(r): return str(r.get('time') or '').strip().lower()
def screen(bars, symbol):
    if len(bars)!=20: return 'insufficient_calendar_history'
    values=[b.get(symbol) for _,b in bars]
    if any(v is None for v in values): return 'missing_or_invalid_prior_session_bar'
    if values[-1][0]<Decimal('10'): return 'previous_close_below_10'
    if median([c*v for c,v in values])<Decimal('20000000'): return 'median_dollar_volume_below_20M'
    return 'pass'

def main():
    fmp=ROOT/'data/raw/fmp_stage_b1'
    manifest=json.loads((fmp/'manifest.json').read_text())
    assert manifest['status']=='completed_calendar_acquisition'
    groups=defaultdict(list); raw_timing=Counter(); field_rows=Counter(); raw_rows=0
    for entry in manifest['requests']:
        if not entry.get('file'): continue
        content=(fmp/entry['file']).read_bytes()
        assert hashlib.sha256(content).hexdigest()==entry['sha256']
        for line in content.splitlines():
            r=json.loads(line); assert '2023-04-03'<=r['date']<='2025-12-31'
            groups[(r['symbol'],r['date'])].append(r); raw_rows+=1
            raw_timing[str(r.get('time'))]+=1
            field_rows.update(k for k in FISCAL_FIELDS if r.get(k) not in (None,''))
    pair_data={}; pending=defaultdict(list); all_symbols={symbol for symbol,_ in groups}
    duplicate_pairs=timing_conflicts=identity_conflicts=0
    for pair,rows in groups.items():
        values={normalized(r) for r in rows}
        fiscal={tuple(str(r.get(f)) for f in FISCAL_FIELDS) for r in rows}
        timing_conflict=len(values)>1
        identity_conflict=len(fiscal)>1
        duplicate_pairs+=len(rows)>1; timing_conflicts+=timing_conflict; identity_conflicts+=identity_conflict
        usable=len(values)==1 and next(iter(values)) in ('bmo','amc')
        times=[next(iter(values))] if usable else ['bmo','amc']
        options=[]
        for timing in times:
            i=session_index(pair[1],timing)
            day=SESSIONS[i] if i is not None else None
            if day not in options: options.append(day)
        info={'symbol':pair[0],'date':pair[1],'source_rows':len(rows),
              'timing_values':sorted(values),'usable_timing':usable,
              'has_bmo_amc':bool(values & {'bmo','amc'}),
              'timing_conflict':timing_conflict,'fiscal_conflict':identity_conflict,
              'all_rows_have_fiscal_year_period':all(r.get('fiscalYear') not in (None,'') and r.get('fiscalPeriod') not in (None,'') for r in rows),
              'fiscal_period_values':sorted({str(r.get('fiscalPeriod')) for r in rows}),
              'options':{day:{'split':'train' if day<='2024-12-31' else 'validation','liquidity':None} for day in options if day is not None},
              'outside_development_option':None in options}
        pair_data[pair]=info
        for day in info['options']: pending[day].append(pair)
    raw=ROOT/'data/raw/massive_grouped_stage_b2'
    daily_manifest=json.loads((raw/'manifest.json').read_text()); assert daily_manifest['status']=='completed'
    entries={e['date']:e for e in daily_manifest['requests']}
    history=deque(maxlen=20)
    for day in ACQUISITION_DATES:
        for pair in pending.get(day,[]): pair_data[pair]['options'][day]['liquidity']=screen(history,pair[0])
        entry=entries[day]; content=(raw/entry['file']).read_bytes()
        assert hashlib.sha256(content).hexdigest()==entry['sha256']
        bars={}; invalid=set()
        for line in content.splitlines():
            r=json.loads(line); assert r['date']==day
            symbol=r['symbol']
            if symbol not in all_symbols: continue
            try:
                c=Decimal(str(r['close'])); v=Decimal(str(r['volume']))
                if not c.is_finite() or not v.is_finite() or c<=0 or v<0:
                    invalid.add(symbol); continue
                if symbol in bars: invalid.add(symbol)
                bars[symbol]=(c,v)
            except (InvalidOperation,KeyError): invalid.add(symbol)
        for symbol in invalid: bars.pop(symbol,None)
        history.append((day,bars))
    result={'raw_rows':raw_rows,'unique_symbol_date_pairs':len(groups),
            'duplicate_pairs':duplicate_pairs,'extra_duplicate_rows':raw_rows-len(groups),
            'timing_conflicting_pairs':timing_conflicts,'fiscal_conflicting_pairs':identity_conflicts,
            'raw_timing_values':dict(raw_timing),'nonempty_fiscal_fields_raw_rows':dict(field_rows),
            'fmp_manifest_sha256':hashlib.sha256((fmp/'manifest.json').read_bytes()).hexdigest(),
            'daily_manifest_sha256':hashlib.sha256((raw/'manifest.json').read_bytes()).hexdigest(),
            'splits':{},
            'denominator_definition':'unique symbol/date pairs; quarterly and historical security validation pending',
            'missing_timing_rule':'evaluate both bmo/amc-compatible D alternatives; no imputation or inferred time credit',
            'gate_scope':'local operational timing gate only; full verified-release and historical-vintage gate remains pending'}
    output=[]
    for split in ('train','validation'):
        certain=[]; possible=[]; usable=[]
        for info in pair_data.values():
            opts=list(info['options'].values())
            eligible=[o for o in opts if o['split']==split and o['liquidity']=='pass']
            if not eligible: continue
            possible.append(info)
            if not info['outside_development_option'] and all(o['split']==split and o['liquidity']=='pass' for o in opts):
                certain.append(info)
            if info['usable_timing']: usable.append(info)
        counts={'liquidity_eligible_pairs_certain':len(certain),
                'liquidity_eligible_pairs_possible':len(possible),
                'nonconflicting_bmo_amc_count':len(usable),
                'pairs_with_any_bmo_amc_value_possible':sum(r['has_bmo_amc'] for r in possible),
                'bmo':sum(r['timing_values']==['bmo'] for r in usable),
                'amc':sum(r['timing_values']==['amc'] for r in usable),
                'unusable_timing_pairs_certain':sum(not r['usable_timing'] for r in certain),
                'unusable_timing_pairs_possible':sum(not r['usable_timing'] for r in possible),
                'eligibility_or_split_ambiguous_pairs':len(possible)-len(certain),
                'duplicate_pairs_certain':sum(r['source_rows']>1 for r in certain),
                'duplicate_pairs_possible':sum(r['source_rows']>1 for r in possible),
                'extra_duplicate_rows_possible':sum(r['source_rows']-1 for r in possible),
                'timing_conflicting_pairs_possible':sum(r['timing_conflict'] for r in possible),
                'fiscal_conflicting_pairs_possible':sum(r['fiscal_conflict'] for r in possible),
                'pairs_with_fiscal_year_period_possible':sum(r['all_rows_have_fiscal_year_period'] for r in possible),
                'other_or_missing_timing_values_possible':dict(Counter(v or '<missing/blank>' for r in possible if not r['usable_timing'] for v in r['timing_values'])),
                'fiscal_period_values_possible':dict(Counter(v for r in possible for v in r['fiscal_period_values']))}
        counts['coverage_lower_percent']=100*len(usable)/len(possible) if possible else None
        counts['coverage_upper_percent']=100*len(usable)/len(certain) if certain else None
        counts['timing_gate_passed']=bool(possible) and 10*len(usable)>=9*len(possible)
        result['splits'][split]=counts
    for info in pair_data.values():
        if any(o['liquidity']=='pass' for o in info['options'].values()): output.append(info)
    result['both_splits_pass']=all(s['timing_gate_passed'] for s in result['splits'].values())
    CACHE.mkdir(parents=True,exist_ok=True)
    (CACHE/'full_timing_gate_pairs.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in output))
    (CACHE/'full_timing_gate.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return result

if __name__=='__main__': main()
