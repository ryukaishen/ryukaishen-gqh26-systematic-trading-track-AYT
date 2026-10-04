import math,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from quant_core import *
class QuantRules(unittest.TestCase):
 def window(self,p=100,volume=100000):return {'complete':True,'valid_minutes':3,'midpoint':p,'spread':0.10,'volume':volume,'minute_midpoints':{'1':p,'2':p,'3':p}}
 def row(self,d=1):
  return {'event_id':'e','issuer_cik':'1','symbol':'ABC','split':'train','entry_session':'2023-07-03','exit_session':schedule('2023-07-03')[1],'status':'signal_measurable','trade_signal':True,'direction':d,'S1':100,'beta':1,'entry_window':self.window(),'exit_window':self.window(110),'spy_entry_window':self.window(400),'spy_exit_window':self.window(410)}
 def test_signal_equality_and_sign_consistency(self):
  self.assertFalse(signal(.1,.08,.1)['trade_signal']);self.assertTrue(signal(.1001,.08,.1)['trade_signal'])
  self.assertIsNone(signal(.1,-.1,.1));self.assertIsNone(signal(.1,0,.1))
 def test_split_and_dividend_total_return(self):
  a={'ABC':{'splits':[{'execution_date':'2024-02-01','split_to':2,'split_from':1}],'dividends':[{'ex_dividend_date':'2024-02-02','cash_amount':1}]}}
  self.assertAlmostEqual(total_return('ABC',100,56,'2024-01-31','2024-02-03',a),.14)
 def test_calendar_and_purge(self):
  self.assertEqual(schedule('2026-09-18')[1],'2026-10-02')
  self.assertTrue(purged({'entry_session':'2024-12-30','split':'train'}))
  self.assertFalse(purged({'entry_session':'2026-09-18','split':'holdout'}))
 def test_beta_uses_only_prior_120_sessions_and_clips(self):
  D='2024-07-01';i=SESSIONS.index(D);days=SESSIONS[i-121:i];bars={'ABC':{},'SPY':{}};a=100;s=100
  for n,day in enumerate(days):
   change=(n%7-3)/1000;s*=1+change;a*=1+3*change
   bars['ABC'][day]={'close':a};bars['SPY'][day]={'close':s}
  beta,rv,count=estimate_beta('ABC',D,bars,{})
  self.assertEqual(count,120);self.assertEqual(beta,2)
  bars['ABC'][D]={'close':1e9};self.assertEqual(estimate_beta('ABC',D,bars,{})[0],2)
 def test_missing_borrow_excludes_short_execution(self):
  out=simulate([self.row(-1)],{}, {},'train')
  self.assertEqual(out['metrics']['executed_trades'],0);self.assertEqual(out['orders'][0]['reason'],'missing_historical_borrow')
 def test_partial_entry_and_unresolved_exit_retained(self):
  r=self.row();r['entry_window']=self.window(volume=1000);r['exit_window']=self.window(110,volume=0)
  out=simulate([r],{}, {},'train')
  self.assertEqual(out['orders'][0]['shares'],10);self.assertEqual(out['orders'][0]['status'],'partial')
  self.assertEqual(out['metrics']['unresolved_exposures'],1);self.assertIsNone(out['metrics']['mean_net_trade_return'])
 def test_doubled_costs_preserve_quantity_and_reduce_equity(self):
  r=self.row();a=simulate([r],{}, {},'train');b=simulate([r],{}, {},'train',cost_scale=2)
  self.assertEqual(a['orders'][0]['shares'],b['orders'][0]['shares']);self.assertGreater(a['curve'][-1]['equity'],b['curve'][-1]['equity'])
 def test_simultaneous_entries_share_cap_and_security_participation(self):
  rows=[{**self.row(),'event_id':str(i),'issuer_cik':str(i)} for i in range(60)]
  for r in rows:r['entry_window']=self.window(volume=100000000)
  out=simulate(rows,{}, {},'train')
  self.assertLessEqual(sum(o['shares']*100 for o in out['orders'] if o['phase']=='entry'),500000)
  rows=[{**self.row(),'event_id':str(i),'issuer_cik':str(i),'entry_window':self.window(volume=1000)} for i in range(2)]
  out=simulate(rows,{}, {},'train');self.assertLessEqual(sum(o.get('shares',0) for o in out['orders'] if o['phase']=='entry'),10)
 def test_student_distribution_and_insufficient_inference(self):
  self.assertAlmostEqual(t_pvalue(1,1),.5,places=8);self.assertAlmostEqual(t_critical(10),2.22813885,places=6)
  self.assertEqual(primary_regression([])['status'],'inconclusive')
if __name__=='__main__':unittest.main()
