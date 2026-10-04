import json,tempfile,unittest,sys,os
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from submission_budget import Budget
class Guard(unittest.TestCase):
 def test_reservation_releases_bytes_without_rolling_back_requests(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'ledger';base={'request_ceiling':20000,'transfer_ceiling':4000000000,'cumulative_requests':19013,'cumulative_bytes':100,'databento_definition_cost_upper_bound_usd':11.59}
   p.write_text(json.dumps(base));out=Path(tmp)/'out'
   with patch('submission_budget.LEDGER',p),patch('submission_budget.ROOT',Path(tmp)),patch.dict(os.environ,{'SLURM_JOB_ID':'test'}),patch('submission_budget.socket.gethostname',return_value='compute'):
    (Path(tmp)/'data/cache').mkdir(parents=True)
    b=Budget(out);r=b.reserve('q',0.01,1000,{})
    self.assertEqual(json.loads(p.read_text())['cumulative_bytes'],1100)
    b.finish(r,50,'complete')
    self.assertEqual(json.loads(p.read_text())['cumulative_bytes'],150)
    self.assertEqual(json.loads(p.read_text())['cumulative_requests'],19014)
    later=json.loads(p.read_text());later['cumulative_requests']+=1;p.write_text(json.dumps(later))
    with self.assertRaisesRegex(RuntimeError,'shared_ledger_changed'):b.sync()
    b.global_lock.close()
 def test_refuses_login_node(self):
  with patch.dict(os.environ,{},clear=True):
   with self.assertRaisesRegex(RuntimeError,'compute_node_required'):Budget('/tmp/unused-gqh26')
if __name__=='__main__':unittest.main()
