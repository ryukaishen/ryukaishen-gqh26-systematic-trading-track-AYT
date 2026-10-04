"""Publication-exportable Matplotlib figures from computed JSON only."""
import json,math
from pathlib import Path
from statistics import mean,stdev
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/final/figures';data=json.loads((ROOT/'results/final/plot_data.json').read_text());OUT.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':140,'savefig.bbox':'tight'})
def save(fig,name):
 for extension in ('png','svg','pdf'):fig.savefig(OUT/(name+'.'+extension))
 plt.close(fig)
fig,ax=plt.subplots(figsize=(8,4.4));labels=[]
for i,c in enumerate(data['coverage']):
 for j,(field,label,color) in enumerate([('valid_S0','S0','#64748b'),('selected_pairs','Contracts','#2563eb'),('valid_M','Valid M','#0d9488')]):
  value=c.get(field);x=i*4+j;ax.bar(x,0 if value is None else value/c['population']*100,color=color,label=label if i==0 else None)
  ax.text(x,(0 if value is None else value/c['population']*100)+2,'pending' if value is None else f'{value:,}',ha='center',fontsize=9)
 ax.text(i*4+1,-10,c['split'].title(),ha='center')
ax.axhline(80,color='#b91c1c',ls='--',label='Contract target: 80%');ax.set(ylim=(0,112),ylabel='Coverage of frozen population (%)',title='Contract feasibility failed; threshold unchanged');ax.set_xticks([]);ax.legend(ncol=2,loc='upper center');save(fig,'coverage')
fig,axes=plt.subplots(1,2,figsize=(10,4),sharey=True)
for ax,split in zip(axes,('train','validation')):
 any_entries=False
 for kind,label,color in [('directional','Modeled primary costs','#2563eb'),('doubled_cost','Doubled modeled costs','#c2410c')]:
  p=data['portfolios'][split+'|'+kind];any_entries|=bool(p['metrics']['executed_trades'])
  if p['metrics']['executed_trades']:
   curves=p['curve'];ax.plot(range(len(curves)),[100*(r['equity']/1000000-1) for r in curves],label=label,color=color,lw=1.4)
 if not any_entries:ax.text(.5,.5,'No executable entries\nPerformance unmeasured',transform=ax.transAxes,ha='center',va='center')
 else:ax.legend(fontsize=8)
 ax.axhline(0,color='grey',lw=.5);ax.set(title=('Train development' if split=='train' else '2025 OOS unavailable'),xlabel='Regular sessions (split capital reset)')
axes[0].set_ylabel('Marked portfolio return (%)');fig.suptitle('Train / 2025 separated OOS: no executable performance');save(fig,'equity_curve')
bins=[(0,.5),(.5,1),(1,1.5),(1.5,2),(2,3),(3,float('inf'))];labels=['(0,0.5]','(0.5,1]','(1,1.5]','(1.5,2]','(2,3]','>3'];fig,axes=plt.subplots(1,2,figsize=(11,4),sharey=True)
for ax,split in zip(axes,('train','validation')):
 rows=[r for r in data['events'] if r['split']==split and r.get('research_status')=='measured']
 if rows:
  for i,(lo,hi) in enumerate(bins):
   vals=[r['Y_research']*100 for r in rows if lo<r['X']<=hi]
   if vals:
    v=mean(vals);err=1.96*stdev(vals)/math.sqrt(len(vals)) if len(vals)>1 else 0;ax.bar(i,v,color='#0d9488');ax.errorbar(i,v,yerr=err,color='#1e293b',capsize=3);ax.annotate('n='+str(len(vals)),(i,v),xytext=(0,5 if v>=0 else -12),textcoords='offset points',ha='center',fontsize=8)
 else:ax.text(.5,.5,'No measurable research outcomes\nNo daily-price substitution',transform=ax.transAxes,ha='center',va='center')
 ax.axvline(1.5,color='#b91c1c',ls='--',lw=1,label='X>1 boundary');ax.legend(fontsize=8);ax.axhline(0,color='grey',lw=.6);ax.set_xticks(range(6),labels,rotation=35);ax.set(title=split.title(),xlabel='Fixed X bucket')
axes[0].set_ylabel('Mean direction-adjusted beta-residual 10-session return (%)');fig.suptitle('Exploratory available-event outcome; error bars are descriptive ±1.96 SE');save(fig,'x_buckets')
fig,ax=plt.subplots(figsize=(8,4))
for split,color in [('train','#2563eb'),('validation','#c2410c')]:
 vals=[r['M']*100 for r in data['M'] if r['split']==split and r.get('M') is not None]
 if vals:ax.hist(vals,bins=30,alpha=.45,label=split,color=color)
if not any(r.get('M') is not None for r in data['M']):ax.text(.5,.5,'No valid synchronized M observations',transform=ax.transAxes,ha='center')
else:ax.legend()
ax.set(xlabel='Straddle-premium move proxy M (%)',ylabel='Available events',title='Historical standard-contract synchronized M');save(fig,'M_distribution')

# Compact, submission-ready note PDF, built from the same computed summary.
from matplotlib.backends.backend_pdf import PdfPages
import textwrap
summary=json.loads((ROOT/'results/final/summary.json').read_text())
def value(v,percentage=False):return 'unmeasured' if v is None else f'{100*v:.2f}%' if percentage else f'{v:.3f}' if isinstance(v,float) else str(v)
def paragraph(fig,text,y,fontsize=9.2):
 lines=textwrap.wrap(text,102)
 fig.text(.075,y,'\n'.join(lines),va='top',fontsize=fontsize,linespacing=1.45)
 return y-.016*len(lines)-.02
def page(title,number):
 fig=plt.figure(figsize=(8.27,11.69));fig.text(.075,.955,title,fontsize=17,weight='bold',va='top');fig.text(.075,.035,'Gator Quant Hacks 2026 | Frozen rules; failed feasibility disclosed',fontsize=8,color='#64748b');fig.text(.92,.035,str(number),ha='right',fontsize=8);return fig
def image_on(fig,name,box):
 ax=fig.add_axes(box);ax.imshow(plt.imread(OUT/(name+'.png')));ax.axis('off')
def table_on(fig,headers,rows,box):
 ax=fig.add_axes(box);ax.axis('off');tbl=ax.table(cellText=rows,colLabels=headers,cellLoc='center',loc='center');tbl.auto_set_font_size(False);tbl.set_fontsize(7.4);tbl.scale(1,1.4)
 for (i,j),cell in tbl.get_celld().items():
  if i==0:cell.set_facecolor('#e2e8f0');cell.set_text_props(weight='bold')
with PdfPages(ROOT/'results/final/QUANT_NOTE.pdf') as pdf:
 fig=page('Earnings moves beyond the implied range',1)
 y=paragraph(fig,'Preregistered continuation hypothesis; transparent feasibility study and exploratory implementation demonstration. The historical-contract feasibility gate FAILED in both development splits. We preserve the 80% threshold and do not replace failed events or claim confirmatory strategy success.',.895)
 y=paragraph(fig,'Economic rationale: a completed earnings reaction exceeding the pre-event ATM straddle-premium move proxy may reflect incomplete information incorporation. Overreaction is an alternative; remaining option time value and risk premia confound the proxy. Historical information, fixed windows and simple interpretable rules avoid future-price signal inputs.',y)
 y=paragraph(fig,'S0 is the median valid pre-event underlying NBBO midpoint. Select the earliest standard unadjusted 100-share expiry from D+7 through D+21 inclusive, nearest matching call/put strike, lower strike on a tie. M is the median straddle-midpoint/underlying ratio at at least three shared valid completed minutes in [15:50,15:55) ET. Positive two-sided prices/sizes, unlocked/uncrossed books, <=20% relative option spreads and valid feed timestamps are required.',y)
 table_on(fig,['Split','Population','Valid S0','Pairs','Contract %','Valid M'],[[c['split'],str(c['population']),str(c['valid_S0']),str(c['selected_pairs']),value(c['contract_coverage'],True),value(c.get('valid_M'))] for c in summary['coverage']],[.075,.47,.85,.12])
 image_on(fig,'coverage',[.055,.075,.89,.36]);pdf.savefig(fig);plt.close(fig)
 fig=page('Frozen trading and cost implementation',2)
 y=paragraph(fig,'At D, complete stock/SPY reaction measurement in [10:00,10:05) ET. r is the split-comparable stock price reaction; a is its total-return reaction minus clipped beta times SPY total-return reaction. Beta is intercept OLS over the preceding 120 sessions with >=100 paired returns, clipped to [0,2]. X=abs(r)/M; require finite nonzero sign-consistent r and a. Trade only X>1 in sign(a).',.895)
 y=paragraph(fig,'Enter in [10:10,10:20) ET; exit in the same window ten regular sessions later, D=session zero. Size 1% of initial $1 million reference equity per issuer, 50% aggregate stock allocation cap, proportional simultaneous sizing, fixed shares except actions. Known S1 sets order intentions. All same-security orders share 1% observed execution-window volume. Missing/partial scheduled exits remain unresolved exposures.',y)
 y=paragraph(fig,'Modeled fills pay half median NBBO spread plus 2 bps adverse slippage and $0.001/share commission. Report doubled modeled friction and $0.005/share/$1-min commissions separately. Historical sell-side SEC/FINRA fees and action cashflows are included; exchange/CAT route pass-through remains unresolved. Missing historical borrow excludes shorts and short hedge legs from executable returns, not research observations. Reference fills are benchmarks, not guaranteed execution.',y)
 metric_rows=[[('Train' if r['split']=='train' else '2025 OOS'),('Base' if r['implementation']=='directional' else '2x costs'),str(r['executed_trades']),value(r['annualized_return'],True),value(r['annualized_volatility'],True),value(r['sharpe_zero_risk_free']),value(r['max_drawdown'],True),value(r['annualized_turnover'])] for r in summary['performance'] if r['implementation'] in ('directional','doubled_cost')]
 table_on(fig,['Split','Costs','Entries','Ann. return','Ann. vol.','Sharpe','Max DD','Ann. turnover'],metric_rows,[.075,.365,.85,.18]);image_on(fig,'equity_curve',[.035,.075,.93,.27]);pdf.savefig(fig);plt.close(fig)
 fig=page('Available-event outcomes and limitations',3)
 y=paragraph(fig,'The full-universe S0/contracts/M population remains intact. The fixed outcome-blind 20-event NBBO benchmark is only an exploratory downstream demonstration because the shared request ceiling cannot fund full-universe reaction/outcome windows. No failed event is backfilled. Calendar boundary crossings are purged before outcome analysis.',.895)
 y=paragraph(fig,'Research Y is direction-adjusted stock-minus-beta-SPY total return between prescribed NBBO entry/exit references. Both X groups remain eligible regardless of borrow, allocation or execution. Primary OLS uses I(X>1), abs(r), and RV20 with two-way issuer/date clustering. Missing groups/rank deficiency are inconclusive; fewer than 30 clusters in either dimension is unreliable. No outcome-based thresholds, trimming or tuning.',y)
 table_on(fig,['Split','Fixed events','Signal measurable','Outcomes','X>1','X<=1'],[[r['split'],'10',str(r['signal_measurable']),str(r['research_outcomes']),str(r['X_gt_1']),str(r['X_le_1'])] for r in summary['development']],[.075,.62,.85,.10])
 image_on(fig,'x_buckets',[.035,.285,.93,.32])
 y=paragraph(fig,'2025 OOS: used for feasibility/coverage checks, with no recorded return-based tuning. Zero benchmark signals/outcomes/trades; performance unavailable. Prior reports already processed exclusions; final rendering does not reevaluate outcomes. Full confirmatory 2026 acquisition was not completed under the fixed budget. The max-three pilot is exploratory only, with zero outcomes; it is not confirmatory OOS.',.265,8.5)
 paragraph(fig,'Limitations: FMP original-release/vendor vintage and uninterrupted common-stock status between reference brackets are unproven. Minute sampling does not prove continuous liquidity. Complex corporate actions, exchange/CAT costs, historical borrow and execution attainability constrain interpretation. Full CSV ledgers, metrics, frozen source hashes and source links accompany this PDF in results/final/ and README.md.',y,8.5)
 pdf.savefig(fig);plt.close(fig)
