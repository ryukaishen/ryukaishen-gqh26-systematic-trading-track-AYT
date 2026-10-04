import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from stage_c_quotes import valid_option,normalize_quote,synchronized_value
class QuoteRules(unittest.TestCase):
 def row(self,t):return {'hd':{'instrument_id':1,'publisher_id':30,'ts_event':t-1},'ts_recv':str(t),'flags':192,'levels':[{'bid_px':'1000000000','ask_px':'1100000000','bid_sz':1,'ask_sz':1}]}
 def test_end_timestamp_aligns_to_completed_stock_minute(self):
  start=60*10**9*100;r=self.row(start+60*10**9)
  self.assertEqual(valid_option(r,start,start+300*10**9)[0],'100')
  self.assertIsNone(valid_option(self.row(start+300*10**9),start,start+300*10**9))
 def test_bad_flags_spread_locked_zero_size_rejected(self):
  start=60*10**9*100;r=self.row(start+60*10**9)
  for flag in (4,8):self.assertIsNone(valid_option({**r,'flags':flag},start,start+300*10**9))
  for field,value in [('bid_px','0'),('ask_px','1000000000'),('ask_px','2000000000'),('bid_sz',0)]:
   x={**r,'levels':[{**r['levels'][0],field:value}]};self.assertIsNone(valid_option(x,start,start+300*10**9))
 def test_three_shared_minutes_and_no_zero_for_missing(self):
  start=60*10**9*100;stock={str(k):100 for k in (100,101,102,103)};call={str(k):1 for k in (99,100,101,102)};put={str(k):2 for k in (99,100,101,102)}
  M,minutes=synchronized_value(stock,call,put,start,start+300*10**9)
  self.assertEqual(M,.03);self.assertEqual(len(minutes),3)
  put['102']=None;self.assertIsNone(synchronized_value(stock,call,put,start,start+300*10**9)[0])
 def test_cbbo_header_does_not_require_raw_symbol(self):self.assertEqual(normalize_quote(self.row(100))['instrument_id'],1)
if __name__=='__main__':unittest.main()
