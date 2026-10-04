"""Submission tables and note from actual checkpoints; missing results stay missing."""
import csv,json,sys,subprocess,os
from collections import Counter
from pathlib import Path
from datetime import datetime,timezone
from submission_budget import ROOT,atomic
from quant_core import observation,simulate,primary_regression
from full_universe_nbbo import event_id
FINAL=ROOT/'results/final'
def csvwrite(name,rows,fields=None):
    fields=fields or sorted(set().union(*(r.keys() for r in rows))) if rows else (fields or ['status'])
    with (FINAL/name).open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader()
        for r in rows:writer.writerow({k:json.dumps(v) if isinstance(v,(dict,list)) else v for k,v in r.items()})
def pct(v):return 'unmeasured' if v is None else f'{100*v:.2f}%'
def fmt(v):return 'unmeasured' if v is None else f'{v:.4f}' if isinstance(v,float) else str(v)
def generate():
    if (FINAL/'submission_seal.json').exists():
        raise RuntimeError('submission_sealed_use_run_all_offline_for_cached_rendering')
    FINAL.mkdir(parents=True,exist_ok=True);(FINAL/'figures').mkdir(exist_ok=True)
    definition=json.loads((ROOT/'data/raw/stage_c_definitions/manifest.json').read_text())
    mp=ROOT/'data/raw/stage_c_quotes/M.json';ms=json.loads(mp.read_text()) if mp.exists() else {}
    coverage_path=ROOT/'data/raw/stage_c_quotes/coverage.json';mcov=json.loads(coverage_path.read_text()) if coverage_path.exists() else {}
    inp=ROOT/'data/raw/downstream_development/inputs.json';inputs=json.loads(inp.read_text()) if inp.exists() else {'windows':{},'bars':{},'actions':{}}
    events=[json.loads(line) for line in (ROOT/'data/cache/nbbo_benchmark_selection/events.jsonl').read_text().splitlines()];rows=[]
    for e in events:
        eid=event_id(e)
        if eid not in ms:rows.append({'event_id':eid,'symbol':e['symbol'],'issuer_cik':e['issuer_cik'],'entry_session':e['entry_session'],'split':e['split'],'status':'excluded','reason':'no_selected_contract_or_M_not_acquired'});continue
        try:rows.append(observation(e,ms[eid],inputs['windows'],inputs['bars'],inputs['actions']))
        except (ValueError,KeyError,TypeError) as exc:rows.append({'event_id':eid,'symbol':e['symbol'],'issuer_cik':e['issuer_cik'],'entry_session':e['entry_session'],'split':e['split'],'status':'excluded','reason':'unsupported_or_missing_action_input'})
    portfolios={};metrics=[];development=[]
    for split in ('train','validation'):
        splitrows=[r for r in rows if r['split']==split];measurable=[r for r in splitrows if r.get('status')=='signal_measurable'];research=[r for r in measurable if r.get('research_status')=='measured']
        development.append({'split':split,'fixed_demonstration_events':10,'signal_measurable':len(measurable),'research_outcomes':len(research),'X_gt_1':sum(r['trade_signal'] for r in measurable),'X_le_1':sum(not r['trade_signal'] for r in measurable),'issuers':len({r['issuer_cik'] for r in measurable}),'entry_dates':len({r['entry_session'] for r in measurable}),'exclusions':dict(Counter(r.get('reason') for r in splitrows if r.get('status')!='signal_measurable')),'regression':primary_regression(splitrows),'sample_scope':'exploratory fixed benchmark; not full-universe predictive test'})
        for name,scale,commission,hedged in [('directional',1,False,False),('doubled_cost',2,False,False),('conservative_commission',1,True,False),('physical_hedge',1,False,True)]:
            p=simulate(rows,inputs['bars'],inputs['actions'],split,scale,commission,hedged=hedged);portfolios[split+'|'+name]=p;metrics.append({'split':split,'implementation':name,**p['metrics']})
            csvwrite(f'{split}_{name}_equity.csv',p['curve']);csvwrite(f'{split}_{name}_trades.csv',p['trades']);csvwrite(f'{split}_{name}_orders.csv',p['orders'])
    if mcov:
        stage_path=ROOT/'data/raw/full_universe_stage_c/manifest.json'
        stage=json.loads(stage_path.read_text());stage.update(status='selected_pair_quotes_and_M_complete',quote_coverage=mcov,M='computed; data/raw/stage_c_quotes/M.json',stop_reason=None)
        atomic(stage_path,stage)
    cov=[]
    for split in ('train','validation'):
        c=definition['contract_coverage'][split];m=mcov.get(split,{});n=c['population'];valid=m.get('valid_M')
        cov.append({'split':split,'population':n,'valid_S0':c['valid_S0'],'S0_coverage':c['valid_S0']/n,'selected_pairs':c['selected_contract_events'],'contract_coverage':c['selected_contract_events']/n,'contract_target':.8,'contract_feasibility':'failed','valid_M':valid,'M_coverage_population':valid/n if valid is not None else None,'M_coverage_selected_pairs':valid/c['selected_contract_events'] if valid is not None else None,'quote_target_conditional':.75,'quote_feasibility':'unresolved' if valid is None else ('passed' if valid/c['selected_contract_events']>=.75 else 'failed')})
    csvwrite('full_universe_coverage.csv',cov);csvwrite('development_summary.csv',[{k:v for k,v in r.items() if k!='regression'} for r in development]);csvwrite('performance.csv',metrics)
    csvwrite('events.csv',[{k:v for k,v in r.items() if not k.endswith('_window')} for r in rows]);csvwrite('full_universe_M.csv',[{k:r.get(k) for k in ('event_id','symbol','split','entry_session','S0','M','shared_valid_minutes','M_status','M_exclusion','expiry','strike')} for r in ms.values()])
    budget=json.loads((ROOT/'data/cache/acquisition_budget.json').read_text());holdout_path=FINAL/'holdout_result.json';holdout=json.loads(holdout_path.read_text()) if holdout_path.exists() else {'status':'sealed_pending_implementation_freeze','evaluations':0}
    summary={'generated_at':datetime.now(timezone.utc).isoformat(),'feasibility':'failed: historical-contract coverage below unchanged 80% minimum in both splits','analysis_scope':'full-universe S0/contracts/M; exploratory fixed 20-event downstream demonstration','coverage':cov,'development':development,'performance':metrics,'budget':budget,'holdout':holdout,'limitations':['Historical release timestamps/vendor vintage not proven.','A5 reference bracketing does not prove uninterrupted listing.','Finite CBBO minute sampling does not prove continuous liquidity.','Benchmark demonstration is not a replacement preregistered strategy sample.','Missing borrow excludes executable shorts, not predictive observations.','Exchange/CAT route pass-through fees unresolved; no claim net of every applicable cost.','Complex corporate-action feed completeness unproven.']}
    atomic(FINAL/'summary.json',summary);atomic(FINAL/'plot_data.json',{'coverage':cov,'portfolios':portfolios,'events':rows,'M':[{k:r.get(k) for k in ('split','M')} for r in ms.values()], 'holdout':holdout, 'holdout_portfolio':json.loads((FINAL/'holdout_portfolio.json').read_text()) if (FINAL/'holdout_portfolio.json').exists() else None})
    table='\n'.join(f"| {r['split']} | {r['population']:,} | {r['valid_S0']:,} | {r['selected_pairs']:,} | {pct(r['contract_coverage'])} — failed | {fmt(r['valid_M'])} | {pct(r['M_coverage_selected_pairs'])} |" for r in cov)
    devtable='\n'.join(f"| {r['split']} | 10 | {r['signal_measurable']} | {r['research_outcomes']} | {r['X_gt_1']} | {r['X_le_1']} |" for r in development)
    metrictable='\n'.join(f"| {r['split']} | {r['implementation']} | {r['executed_trades']} | {pct(r['annualized_return'])} | {pct(r['annualized_volatility'])} | {fmt(r['sharpe_zero_risk_free'])} | {pct(r['max_drawdown'])} | {r['status']} |" for r in metrics)
    note=f'''# Earnings moves beyond the option-implied range: a transparent feasibility study

**Submission status: failed preregistered feasibility threshold.** This submission reports that failure and a budget-bounded implementation demonstration. It does not claim a successful confirmatory strategy or change the 80% threshold.

## Economic hypothesis and frozen signal

An earnings price reaction larger than the historical ATM straddle-premium move proxy may indicate incomplete information incorporation and continuation in the residual reaction direction. The alternative is overreaction; option time value and risk premia confound a pure surprise interpretation. At the completed pre-event [15:50,15:55) ET window, S0 is the median valid underlying NBBO midpoint. Select the earliest standard 100-share expiry from D+7 through D+21 inclusive, nearest matching call/put strike, lower strike on a tie. At three or more shared valid completed minutes, M is the median of (call midpoint + put midpoint)/underlying midpoint. No contract substitutions repair a failure.

At D's completed [10:00,10:05) ET reaction window, r=S1/S0−1 on comparable split bases; a is the total-return reaction less the frozen clipped [0,2] beta times SPY's total-return reaction. Beta uses an intercept and the preceding 120 sessions, at least 100 paired returns; RV20 requires all preceding 20. X=abs(r)/M; finite nonzero sign-consistent r and a are required. Only X>1 trades in sign(a); X=1 does not qualify. No future price enters X.

## Full-universe feasibility and attrition

| Split | Population | Valid S0 | Selected pairs | Contract coverage / 80% target | Valid M | M / selected pairs |
|---|---:|---:|---:|---|---:|---:|
{table}

The population is the frozen operational train/validation sample. Unresolved roots are exclusions; failed events are not backfilled. Timestamp/vendor vintage and reference-bracketing limitations remain unresolved. Contract feasibility is failed independently of subsequent returns.

![Coverage](figures/coverage.png)

## Available-event demonstration

The existing outcome-blind, chronological/liquidity-stratified 20-event NBBO benchmark is used only as an exploratory implementation demonstration. Its original selection was not a strategy sample. The request ceiling prevents full-universe post-event/reference/execution NBBO acquisition; this demonstration cannot establish full-population predictive performance. Every selected benchmark event is retained in the attrition log; invalid events are not replaced. Ten-session split-boundary crossings are purged by calendar, not returns.

| Split | Fixed events | Signal measurable | Research outcomes | X>1 | X≤1 |
|---|---:|---:|---:|---:|---:|
{devtable}

Research outcomes use direction-adjusted stock-minus-beta-SPY total returns between median valid NBBO references in [10:10,10:20) ET on D and D+10 sessions. Both signal groups remain eligible irrespective of borrow, allocation or executable capacity. Missing reference observations remain unresolved; daily closes never substitute for these reference windows.

![X buckets](figures/x_buckets.png)

The frozen primary regression is Y_research ~ intercept + I(X>1) + abs(r) + RV20 with two-way issuer/date clustering. Small or absent threshold groups, rank deficiency and fewer than 30 clusters prevent a confirmatory claim; exact diagnostics are in summary.json. No thresholds, buckets, costs or model parameters were chosen from performance.

## Executable accounting and sensitivity

Initial allocation is 1% of $1 million reference equity per issuer, with a 50% stock gross allocation cap and proportional simultaneous-entry scaling. S1 known at signal completion determines intended whole-share quantities. Scheduled exits precede new entries; shares stay fixed except corporate actions. All security orders in a window share 1% observed window-volume capacity. Reference midpoint fills pay half the contemporaneous median spread plus 2 bps adversely, $0.001/share commission, modeled historical sell-side SEC/FINRA charges, and action cashflows. Doubled-cost sensitivity doubles modeled friction; conservative commissions are $0.005/share with $1/order minimum. Exchange/CAT fee pass-through remains unresolved; these are net-of-modeled-cost results, not net of every possible route fee. VWAP/midpoint execution benchmarks do not guarantee attainable fills. Missing historical borrow evidence excludes shorts and physical short-SPY hedges from executable returns, while retaining measurable research observations. No short-proceeds interest is assumed. Long stock allocations require no leverage under the capital convention.

| Split | Implementation | Entries | Annualized return | Annualized volatility | Sharpe (rf=0) | Max drawdown | Status |
|---|---|---:|---:|---:|---:|---:|---|
{metrictable}

![Equity curves](figures/equity_curve.png)

Annualization uses 252 sessions and daily action-aware close marking. Turnover, drift, orders, partial fills, missing marks and unresolved exposures are exported. Unresolved exits remain in the portfolio and invalidate complete executable performance rather than disappearing from the trade sample. No-entry plots and metrics are explicitly labeled, not evidence of profitability. The primary executable metric is mean net ten-session trade P&L per initial executed stock dollar; uncertainty is insufficient for small demonstration samples.

## Holdout and reproducibility

Holdout status: **{holdout['status']}**. Holdout access is prohibited until source/specification hashes, splits, processing rules, feasibility findings and cost assumptions are frozen. The one-shot runner claims a durable state before any holdout acquisition/evaluation; it will not rerun or tune afterward. Budget/entitlement/data shortages yield an inconclusive result, not new dates or modified signals.

Run `python run_all.py --offline` on a compute node to regenerate artifacts from checkpoints. See README.md for acquisition, freeze and one-shot holdout commands. All submission artifacts are in results/final/; all plots are in results/final/figures/. No API keys enter receipts or artifacts. Current shared usage is {budget['cumulative_requests']:,}/20,000 requests and {budget['cumulative_bytes']:,}/4,000,000,000 bytes; conservative Databento spend is ${budget.get('databento_total_cost_upper_bound_usd',budget.get('databento_definition_cost_upper_bound_usd',0)):.8f} under $12. Budget guards include failed attempts and bounded retries.

Sources: [approved specification](../../EXPERIMENT.md), [OPRA schema](https://databento.com/docs/venues-and-datasets/opra-pillar), [SEC historical fee change](https://www.sec.gov/rules-regulations/fee-rate-advisories/2025-2), [FINRA fee schedule](https://www.finra.org/sites/default/files/2024-11/sr-finra-2024-019.pdf), [NYSE calendar](https://www.nyse.com/publicdocs/nyse/ICE_NYSE_2026_Yearly_Trading_Calendar.pdf).
'''
    (FINAL/'QUANT_NOTE.md').write_text(note)
    # Existing HiPerGator plotting interpreter; no package installation.
    plot_python=Path('/apps/python/3.12/bin/python')
    env={**os.environ,'MPLCONFIGDIR':str(FINAL/'.matplotlib'),'MPLBACKEND':'Agg'}
    result=subprocess.run([str(plot_python) if plot_python.exists() else sys.executable,str(ROOT/'scripts/plot_final.py')],env=env,capture_output=True,text=True)
    atomic(FINAL/'plot_status.json',{'exit_code':result.returncode,'success':result.returncode==0})
    if result.returncode:print('Plot generation failed; see plot_status.json',flush=True)
    print(json.dumps({'artifacts':str(FINAL),'coverage':cov,'development':[{'split':r['split'],'signal_measurable':r['signal_measurable'],'outcomes':r['research_outcomes']} for r in development],'plots_success':result.returncode==0}),flush=True)
