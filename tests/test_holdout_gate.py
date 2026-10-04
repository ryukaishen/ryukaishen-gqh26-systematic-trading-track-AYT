import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import final_holdout as h
class HoldoutGate(unittest.TestCase):
 def test_cannot_open_without_freeze(self):
  with tempfile.TemporaryDirectory() as t,patch.object(h,'FREEZE',Path(t)/'freeze'):
   with self.assertRaisesRegex(RuntimeError,'implementation_not_frozen'):h.claim()
 def test_hash_change_cannot_open_and_claim_is_once(self):
  with tempfile.TemporaryDirectory() as t:
   freeze=Path(t)/'freeze.json';state=Path(t)/'state.json';freeze.write_text(json.dumps({'files_sha256':{'core':'original'}}))
   with patch.object(h,'FREEZE',freeze),patch.object(h,'STATE',state),patch.object(h,'hashes',return_value={'core':'changed'}):
    with self.assertRaisesRegex(RuntimeError,'implementation_changed'):h.claim()
    self.assertFalse(state.exists())
   with patch.object(h,'FREEZE',freeze),patch.object(h,'STATE',state),patch.object(h,'hashes',return_value={'core':'original'}):
    self.assertEqual(h.claim()['attempts'],1)
    with self.assertRaisesRegex(RuntimeError,'already_claimed'):h.claim()
 def test_missing_holdout_inputs_are_not_fabricated(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);final=root/'results/final';final.mkdir(parents=True);freeze=final/'freeze.json';state=final/'state.json';freeze.write_text(json.dumps({'files_sha256':{'core':'original'}}))
   def acquire():
    self.assertTrue(state.exists());return {'status':'budget_blocked','requests':0}
   with patch.object(h,'ROOT',root),patch.object(h,'FINAL',final),patch.object(h,'FREEZE',freeze),patch.object(h,'STATE',state),patch.object(h,'hashes',return_value={'core':'original'}),patch.object(h,'acquire_calendar_once',side_effect=acquire):
    h.evaluate_once();result=json.loads((final/'holdout_result.json').read_text())
    self.assertEqual(result['inferential_evaluations'],0);self.assertFalse(result['holdout_outcomes_inspected'])
if __name__=='__main__':unittest.main()
