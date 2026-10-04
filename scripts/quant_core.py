"""Frozen, standard-library quantitative implementation. No API side effects."""
import math
from collections import defaultdict,Counter
from datetime import date,timedelta
from statistics import median,mean,stdev
from development_calendar import HOLIDAYS,EARLY_CLOSES
EXTRA_HOLIDAYS=set('2022-01-17 2022-02-21 2022-04-15 2022-05-30 2022-06-20 2022-07-04 2022-09-05 2022-11-24 2022-12-26 2026-01-01 2026-01-19 2026-02-16 2026-04-03 2026-05-25 2026-06-19 2026-07-03 2026-09-07 2026-11-26 2026-12-25'.split())
SESSIONS=[str(date(2022,1,1)+timedelta(days=i)) for i in range((date(2026,12,31)-date(2022,1,1)).days+1) if (date(2022,1,1)+timedelta(days=i)).weekday()<5 and str(date(2022,1,1)+timedelta(days=i)) not in HOLIDAYS|EXTRA_HOLIDAYS]
SPLITS={'train':('2023-04-03','2024-12-31'),'validation':('2025-01-01','2025-12-31'),'holdout':('2026-01-01','2026-09-18')}
CAPITAL=1_000_000.0

def schedule(day):
    i=SESSIONS.index(day)
    return SESSIONS[i-1],SESSIONS[i+10]

def purged(event):
    _,exit_day=schedule(event['entry_session'])
    # Holdout outcomes through Oct 2 are specifically preregistered.
    end='2026-10-02' if event['split']=='holdout' else SPLITS[event['split']][1]
    return exit_day>end

def split_ratio(symbol,start,end,actions):
    ratio=1.0
    for r in actions.get(symbol,{}).get('splits',[]):
        if start<r['execution_date']<=end:ratio*=float(r['split_to'])/float(r['split_from'])
    return ratio

def total_return(symbol,p0,p1,start,end,actions):
    """Raw prices, changing share count, cash dividends retained without reinvestment."""
    if p0<=0 or p1<=0:raise ValueError('nonpositive_reference_price')
    events=[]
    for r in actions.get(symbol,{}).get('splits',[]):
        if start<r['execution_date']<=end:events.append((r['execution_date'],0,r))
    for r in actions.get(symbol,{}).get('dividends',[]):
        if start<r['ex_dividend_date']<=end:
            if r.get('currency','USD')!='USD':raise ValueError('unsupported_dividend_currency')
            if r.get('dividend_type','CD') not in ('CD','SC'):raise ValueError('unsupported_non_cash_action')
            events.append((r['ex_dividend_date'],1,r))
    shares=1.0;cash=0.0
    for _,kind,r in sorted(events,key=lambda x:(x[0],x[1])):
        if kind==0:shares*=float(r['split_to'])/float(r['split_from'])
        else:cash+=shares*float(r['cash_amount'])
    return (shares*p1+cash)/p0-1

def daily_returns(symbol,bars,actions,days):
    out={}
    for day in days:
        i=SESSIONS.index(day);prev=SESSIONS[i-1]
        if day in bars.get(symbol,{}) and prev in bars.get(symbol,{}):
            out[day]=total_return(symbol,float(bars[symbol][prev]['close']),float(bars[symbol][day]['close']),prev,day,actions)
    return out

def estimate_beta(symbol,D,bars,actions):
    i=SESSIONS.index(D);days=SESSIONS[i-120:i]
    stock=daily_returns(symbol,bars,actions,days);spy=daily_returns('SPY',bars,actions,days)
    common=sorted(set(stock)&set(spy));rv_days=days[-20:]
    if len(common)<100:return None,None,len(common)
    if not all(day in stock for day in rv_days):return None,None,len(common)
    x=[spy[k] for k in common];y=[stock[k] for k in common];mx=mean(x);my=mean(y)
    denom=sum((v-mx)**2 for v in x)
    if denom<=0:return None,None,len(common)
    beta=sum((a-mx)*(b-my) for a,b in zip(x,y))/denom
    return min(2,max(0,beta)),stdev(stock[k] for k in rv_days),len(common)

def signal(r,a,M):
    if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in (r,a,M)) or M<=0 or r==0 or a==0 or r*a<=0:return None
    X=abs(r)/M
    return {'X':X,'direction':1 if a>0 else -1,'trade_signal':X>1}

def wkey(symbol,day,start,end):return '|'.join((symbol,day,start,end))

def good_window(w):
    return w is not None and w.get('complete') and w.get('valid_minutes',0)>=3 and w.get('midpoint',0)>0 and w.get('spread',0)>0

def shared(w1,w2):return len(set(w1.get('minute_midpoints',{}))&set(w2.get('minute_midpoints',{}))) if w1 and w2 else 0

def observation(event,m,windows,bars,actions):
    D=event['entry_session'];pre,exit_day=schedule(D)
    r={'event_id':m['event_id'],'symbol':event['symbol'],'issuer_cik':event['issuer_cik'],'split':event['split'],'entry_session':D,'exit_session':exit_day,'M':m.get('M'),'S0':m.get('S0'),'status':'excluded'}
    if purged(event):return {**r,'reason':'ten_session_boundary_purge'}
    if m.get('M') is None:return {**r,'reason':'invalid_M'}
    s=event['symbol'];beta,rv,n=estimate_beta(s,D,bars,actions);r.update(beta=beta,RV20=rv,beta_observations=n)
    if beta is None:return {**r,'reason':'insufficient_paired_120_session_beta_or_RV20'}
    sr=windows.get(wkey(s,D,'10:00','10:05'));pr=windows.get(wkey('SPY',D,'10:00','10:05'));p0=windows.get(wkey('SPY',pre,'15:50','15:55'))
    if not all(good_window(w) for w in (sr,pr,p0)) or shared(sr,pr)<3:return {**r,'reason':'missing_synchronized_reaction_or_SPY0_NBBO'}
    S1=sr['midpoint'];ratio=split_ratio(s,pre,D,actions);raw=S1/(m['S0']/ratio)-1
    stock_total=total_return(s,m['S0'],S1,pre,D,actions);spy_total=total_return('SPY',p0['midpoint'],pr['midpoint'],pre,D,actions)
    a=stock_total-beta*spy_total;r.update(r=raw,a=a,S1=S1,SPY0=p0['midpoint'],SPY1=pr['midpoint'])
    sig=signal(raw,a,m['M'])
    if sig is None:return {**r,'reason':'zero_nonfinite_or_sign_inconsistent_reaction'}
    r.update(sig,status='signal_measurable',reason=None)
    se=windows.get(wkey(s,D,'10:10','10:20'));sx=windows.get(wkey(s,exit_day,'10:10','10:20'));pe=windows.get(wkey('SPY',D,'10:10','10:20'));px=windows.get(wkey('SPY',exit_day,'10:10','10:20'))
    r.update(entry_window=se,exit_window=sx,spy_entry_window=pe,spy_exit_window=px)
    if all(good_window(w) for w in (se,sx,pe,px)) and shared(se,pe)>=3 and shared(sx,px)>=3:
        Rstock=total_return(s,se['midpoint'],sx['midpoint'],D,exit_day,actions);Rspy=total_return('SPY',pe['midpoint'],px['midpoint'],D,exit_day,actions)
        r.update(research_status='measured',R_stock_10d=Rstock,R_SPY_10d=Rspy,Y_research=r['direction']*(Rstock-beta*Rspy))
    else:r.update(research_status='unresolved',research_reason='missing_prescribed_reference_NBBO')
    return r

def regulatory_fee(day,shares,notional):
    # Agency modeled pass-through on sells; route/CAT charges remain unresolved.
    sec=8/1e6 if day<'2024-05-22' else (27.8/1e6 if day<'2025-05-14' else 0)
    if day>='2026-01-01':return None
    taf,maximum=(0.000145,7.27) if day<'2024-01-01' else (0.000166,8.30)
    return sec*notional+min(maximum,taf*shares)

def fill_cost(window,side,shares,day,cost_scale=1,conservative_commission=False):
    adverse=(window['spread']/2+window['midpoint']*0.0002)*cost_scale
    price=window['midpoint']+side*adverse
    commission=max(1,shares*0.005) if conservative_commission else shares*0.001
    commission*=cost_scale
    fee=regulatory_fee(day,shares,shares*price) if side<0 else 0
    return price,commission,None if fee is None else fee*cost_scale

def performance(curve,trades,turnover):
    if not curve:return {'status':'unmeasured'}
    rets=[curve[i]['equity']/curve[i-1]['equity']-1 for i in range(1,len(curve))];peak=CAPITAL;dd=0
    for row in curve:peak=max(peak,row['equity']);dd=min(dd,row['equity']/peak-1)
    vol=stdev(rets)*math.sqrt(252) if len(rets)>1 else None
    ann=(curve[-1]['equity']/curve[0]['equity'])**(252/len(rets))-1 if rets and curve[-1]['equity']>0 else None
    sharpe=mean(rets)/stdev(rets)*math.sqrt(252) if len(rets)>1 and stdev(rets)>0 else None
    complete=[t for t in trades if t['status']=='closed'];unresolved=[t for t in trades if t['status']!='closed']
    return {'status':'incomplete' if unresolved else ('measured' if trades else 'no_executable_entries'),
        'annualized_return':ann if trades else None,'annualized_volatility':vol if trades else None,'sharpe_zero_risk_free':sharpe if trades else None,'max_drawdown':dd if trades else None,
        'turnover_per_initial_equity':turnover/CAPITAL,'annualized_turnover':turnover/CAPITAL*252/max(1,len(rets)),
        'executed_trades':len(trades),'completed_trades':len(complete),'unresolved_exposures':len(unresolved),
        'mean_net_trade_return':mean(t['net_return'] for t in complete) if complete and not unresolved else None,
        'mean_completed_trade_return_diagnostic':mean(t['net_return'] for t in complete) if complete else None,
        'mean_net_trade_return_ci95_descriptive':([mean(t['net_return'] for t in complete)-t_critical(len(complete)-1)*stdev(t['net_return'] for t in complete)/math.sqrt(len(complete)),mean(t['net_return'] for t in complete)+t_critical(len(complete)-1)*stdev(t['net_return'] for t in complete)/math.sqrt(len(complete))] if len(complete)>1 and not unresolved else None),
        'trade_CI_limitation':'Descriptive iid-t interval; overlapping event trades can be dependent; small demonstration is not confirmatory.',
        'long_entries':sum(t['direction']>0 for t in trades),'short_entries':sum(t['direction']<0 for t in trades),
        'cost_accounting':'net of modeled spread/slippage/commission/SEC/TAF; exchange/CAT pass-through unresolved',
        'reference_capital':CAPITAL,'max_observed_gross_fraction':max((r['gross']/CAPITAL for r in curve),default=0)}

def simulate(rows,bars,actions,split,cost_scale=1,conservative_commission=False,borrow=None,hedged=False):
    """Fixed shares, ex-ante S1 sizing, daily action-aware cash and close marking."""
    borrow=borrow or {};eligible=[r for r in rows if r['split']==split and r.get('status')=='signal_measurable' and r.get('trade_signal')]
    byday=defaultdict(list)
    for r in eligible:byday[r['entry_session']].append(r)
    start,end=SPLITS[split];end='2026-10-02' if split=='holdout' else end
    days=[d for d in SESSIONS if start<=d<=end];cash=CAPITAL;positions={};trades=[];orders=[];curve=[{'date':SESSIONS[SESSIONS.index(days[0])-1],'equity':CAPITAL,'cash':CAPITAL,'gross':0,'open_positions':0,'missing_marks':0}];turnover=0
    for day in days:
        # Actions at session start apply only to positions opened on earlier sessions.
        for issuer,p in list(positions.items()):
            for leg in p['legs']:
                for x in actions.get(leg['symbol'],{}).get('splits',[]):
                    if x['execution_date']==day:
                        ratio=float(x['split_to'])/float(x['split_from']);leg['shares']*=ratio;leg['last_price']/=ratio
                for x in actions.get(leg['symbol'],{}).get('dividends',[]):
                    if x['ex_dividend_date']==day:
                        amount=leg['shares']*float(x['cash_amount']);cash+=amount;p['dividends']+=amount
                if leg['shares']<0:
                    evidence=borrow.get(leg['symbol']+'|'+day)
                    if evidence is None:p['unresolved_borrow_accrual']=True
                    else:
                        prior_day=SESSIONS[SESSIONS.index(day)-1];elapsed=(date.fromisoformat(day)-date.fromisoformat(max(prior_day,p['entry_session']))).days
                        charge=abs(leg['shares'])*leg['last_price']*float(evidence['annual_rate'])*elapsed/365*cost_scale;cash-=charge;p['borrow_cost']+=charge
        # All security orders in this window share the participation budget.
        participation=defaultdict(float)
        # Exits precede entries. Missing/insufficient liquidity retains exposure.
        for issuer,p in list(positions.items()):
            if p['exit_session']!=day:continue
            windows=[p['row'].get('exit_window')]+([p['row'].get('spy_exit_window')] if hedged else [])
            if not all(good_window(w) and w.get('volume') is not None for w in windows):p['status']='unresolved_exit';continue
            fractions=[min(1,max(0,math.floor(0.01*w['volume']-participation[l['symbol']]))/max(1,abs(l['shares']))) for l,w in zip(p['legs'],windows)]
            fraction=min(fractions)
            if fraction<=0:p['status']='unresolved_exit';continue
            fully=True
            for leg,w in zip(p['legs'],windows):
                n=min(abs(leg['shares']),math.floor(abs(leg['shares'])*fraction));side=-1 if leg['shares']>0 else 1
                if n<=0:fully=False;continue
                px,commission,fee=fill_cost(w,side,n,day,cost_scale,conservative_commission)
                if fee is None:p['unresolved_fees']=True;fee=0
                flow=-side*n*px-commission-fee;cash+=flow;p['exit_cashflow']+=flow;turnover+=n*px
                leg['shares']+=side*n;participation[leg['symbol']]+=n;orders.append({'event_id':p['event_id'],'day':day,'phase':'exit','symbol':leg['symbol'],'shares':n,'status':'full' if leg['shares']==0 else 'partial'})
                fully &= abs(leg['shares'])<1e-9
            if fully:
                p['status']='closed';p['net_return']=(p['exit_cashflow']+p['entry_cashflow']+p['dividends']-p['borrow_cost'])/p['initial_stock_dollars'];del positions[issuer]
            else:p['status']='unresolved_partial_exit'
        candidates=[];seen_issuers=set(positions)
        for r in sorted(byday[day],key=lambda r:r['event_id']):
            reason=None
            if r['issuer_cik'] in seen_issuers:reason='existing_issuer_position'
            windows=[r.get('entry_window')]+([r.get('spy_entry_window')] if hedged else [])
            sides=[r['direction']]+([-r['direction']] if hedged and r['beta']>0 else ([0] if hedged else []))
            symbols=[r['symbol']]+(['SPY'] if hedged else [])
            for symbol,side in zip(symbols,sides):
                if side<0 and not borrow.get(symbol+'|'+day,{}).get('available'):reason='missing_historical_borrow'
            if reason:orders.append({'event_id':r['event_id'],'day':day,'phase':'entry','status':'unfilled','reason':reason});continue
            candidates.append(r);seen_issuers.add(r['issuer_cik'])
        gross=sum(abs(l['shares'])*l['last_price'] for p in positions.values() for l in p['legs'] if l['symbol']!='SPY')
        capacity=max(0,0.5*CAPITAL-gross);scale=min(1,capacity/(len(candidates)*0.01*CAPITAL)) if candidates else 0
        for r in candidates:
            windows=[r.get('entry_window')]+([r.get('spy_entry_window')] if hedged else [])
            if not all(good_window(w) and w.get('volume') is not None for w in windows):
                orders.append({'event_id':r['event_id'],'day':day,'phase':'entry','status':'unfilled','reason':'missing_entry_execution_NBBO_or_volume'});continue
            stock_w=r['entry_window'];intended=math.floor(0.01*CAPITAL*scale/r['S1']);n=min(intended,max(0,math.floor(0.01*stock_w['volume']-participation[r['symbol']])))
            if hedged and r['beta']>0:
                spy_w=r['spy_entry_window'];spy_budget=max(0,math.floor(0.01*spy_w['volume']-participation['SPY']));n=min(n,math.floor(spy_budget*r['SPY1']/(r['beta']*r['S1'])))
            if n<=0:orders.append({'event_id':r['event_id'],'day':day,'phase':'entry','status':'unfilled','reason':'allocation_or_participation'});continue
            legs=[(r['symbol'],r['direction']*n,stock_w)]
            if hedged and r['beta']>0:legs.append(('SPY',-r['direction']*math.floor(r['beta']*n*r['S1']/r['SPY1']),r['spy_entry_window']))
            p={'event_id':r['event_id'],'direction':r['direction'],'entry_session':day,'exit_session':r['exit_session'],'row':r,'legs':[],'status':'open','entry_cashflow':0,'exit_cashflow':0,'dividends':0,'borrow_cost':0,'initial_stock_dollars':n*stock_w['midpoint']}
            for symbol,signed,w in legs:
                if signed==0:continue
                side=1 if signed>0 else -1;px,commission,fee=fill_cost(w,side,abs(signed),day,cost_scale,conservative_commission)
                if fee is None:p['unresolved_fees']=True;fee=0
                flow=-signed*px-commission-fee;cash+=flow;p['entry_cashflow']+=flow;turnover+=abs(signed)*px;participation[symbol]+=abs(signed)
                p['legs'].append({'symbol':symbol,'shares':signed,'last_price':w['midpoint']})
                orders.append({'event_id':r['event_id'],'day':day,'phase':'entry','symbol':symbol,'shares':abs(signed),'intended_stock_shares':intended,'status':'full' if n==intended else 'partial'})
            positions[r['issuer_cik']]=p;trades.append(p)
        missing=0
        for p in positions.values():
            for l in p['legs']:
                close=bars.get(l['symbol'],{}).get(day,{}).get('close')
                if close is not None:l['last_price']=float(close)
                else:missing+=1
        market=sum(l['shares']*l['last_price'] for p in positions.values() for l in p['legs']);gross=sum(abs(l['shares'])*l['last_price'] for p in positions.values() for l in p['legs'])
        curve.append({'date':day,'equity':cash+market,'cash':cash,'gross':gross,'open_positions':len(positions),'missing_marks':missing})
    metrics=performance(curve,trades,turnover)
    if any(r['missing_marks'] for r in curve):metrics['daily_mark_status']='incomplete; previous mark retained on missing days'
    if any(t.get('unresolved_borrow_accrual') or t.get('unresolved_fees') for t in trades):metrics['status']='incomplete'
    return {'metrics':metrics,'curve':curve,'trades':[{k:v for k,v in t.items() if k not in ('row','legs')} for t in trades],'orders':orders}

def inverse(a):
    n=len(a);m=[list(map(float,row))+[float(i==j) for j in range(n)] for i,row in enumerate(a)]
    for c in range(n):
        p=max(range(c,n),key=lambda i:abs(m[i][c]))
        if abs(m[p][c])<1e-14:raise ValueError('rank_deficient')
        m[c],m[p]=m[p],m[c];v=m[c][c];m[c]=[x/v for x in m[c]]
        for i in range(n):
            if i!=c:
                v=m[i][c];m[i]=[x-v*y for x,y in zip(m[i],m[c])]
    return [r[n:] for r in m]

def matmul(a,b):return [[sum(x*y for x,y in zip(row,col)) for col in zip(*b)] for row in a]

def betacf(a,b,x):
    qab=a+b;qap=a+1;qam=a-1;c=1;d=1-qab*x/qap;d=1/max(1e-30,abs(d))*(1 if d>=0 else -1);h=d
    for m in range(1,201):
        aa=m*(b-m)*x/((qam+2*m)*(a+2*m));d=1+aa*d;c=1+aa/c
        if abs(d)<1e-30:d=1e-30
        if abs(c)<1e-30:c=1e-30
        d=1/d;h*=d*c;aa=-(a+m)*(qab+m)*x/((a+2*m)*(qap+2*m));d=1+aa*d;c=1+aa/c
        if abs(d)<1e-30:d=1e-30
        if abs(c)<1e-30:c=1e-30
        d=1/d;delta=d*c;h*=delta
        if abs(delta-1)<3e-12:break
    return h

def ibeta(a,b,x):
    if x<=0:return 0
    if x>=1:return 1
    bt=math.exp(math.lgamma(a+b)-math.lgamma(a)-math.lgamma(b)+a*math.log(x)+b*math.log1p(-x))
    return bt*betacf(a,b,x)/a if x<(a+1)/(a+b+2) else 1-bt*betacf(b,a,1-x)/b

def t_pvalue(t,df):return ibeta(df/2,0.5,df/(df+t*t))

def t_critical(df):
    lo=0;hi=1000
    for _ in range(80):
        mid=(lo+hi)/2
        if t_pvalue(mid,df)>0.05:lo=mid
        else:hi=mid
    return (lo+hi)/2

def primary_regression(rows):
    rs=[r for r in rows if r.get('research_status')=='measured'];n=len(rs);k=4
    counts=dict(Counter('X>1' if r['trade_signal'] else 'X<=1' for r in rs));issuers=len({r['issuer_cik'] for r in rs});dates=len({r['entry_session'] for r in rs})
    info={'n':n,'groups':counts,'issuer_clusters':issuers,'entry_date_clusters':dates,'status':'inconclusive','model':'Y_research ~ intercept + I(X>1) + abs(r) + RV20','covariance':'two-way issuer/date, finite-cluster correction; t df=min(cluster counts)-1'}
    if n<=k or len(counts)<2 or min(issuers,dates)<2:return {**info,'reason':'insufficient_observations_threshold_groups_or_clusters'}
    X=[[1,float(r['trade_signal']),abs(r['r']),r['RV20']] for r in rs];y=[r['Y_research'] for r in rs]
    try:bread=inverse([[sum(row[i]*row[j] for row in X) for j in range(k)] for i in range(k)])
    except ValueError:return {**info,'reason':'rank_deficient'}
    beta=[sum(bread[i][j]*sum(row[j]*v for row,v in zip(X,y)) for j in range(k)) for i in range(k)]
    resid=[v-sum(a*b for a,b in zip(row,beta)) for row,v in zip(X,y)]
    def meat(keys):
        groups=defaultdict(lambda:[0.0]*k)
        for key,row,e in zip(keys,X,resid):
            for i in range(k):groups[key][i]+=row[i]*e
        g=len(groups);factor=g/(g-1)*(n-1)/(n-k)
        return [[factor*sum(s[i]*s[j] for s in groups.values()) for j in range(k)] for i in range(k)]
    a=meat([r['issuer_cik'] for r in rs]);b=meat([r['entry_session'] for r in rs]);c=meat([(r['issuer_cik'],r['entry_session']) for r in rs]);cov=matmul(matmul(bread,[[a[i][j]+b[i][j]-c[i][j] for j in range(k)] for i in range(k)]),bread)
    if cov[1][1]<=0:return {**info,'gamma':beta[1],'reason':'nonpositive_cluster_variance'}
    se=math.sqrt(cov[1][1]);df=min(issuers,dates)-1;p=t_pvalue(beta[1]/se,df);critical=t_critical(df)
    reliable=min(issuers,dates)>=30
    return {**info,'gamma':beta[1],'standard_error':se,'ci95':[beta[1]-critical*se,beta[1]+critical*se],'p_value_two_sided':p,'df':df,'status':'evaluated' if reliable else 'inconclusive','reason':None if reliable else 'fewer_than_30_clusters_in_either_dimension','positive_evidence':reliable and beta[1]>0 and p<0.05}
