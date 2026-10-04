import sys,unittest
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from stage_c_definitions_job import choose_pair,decode_definition,Job

class ContractSelection(unittest.TestCase):
    def pair(self,expiry,strike):
        return [dict(raw_symbol=f'{expiry}{strike}{cp}',instrument_id=i,expiry=expiry,strike=str(strike),cp=cp)
                for i,cp in enumerate(('C','P'),1)]
    def test_lower_tie_and_inclusive_earliest(self):
        d=self.pair('2024-01-09',95)+self.pair('2024-01-09',105)+self.pair('2024-01-23',100)
        r=choose_pair({'entry_session':'2024-01-02'},100,d)
        self.assertEqual((r['status'],r['expiry'],r['strike']),('selected','2024-01-09','95'))
    def test_no_fallback_from_unpaired_earliest_expiry(self):
        d=self.pair('2024-01-09',100)[:1]+self.pair('2024-01-12',100)
        self.assertEqual(choose_pair({'entry_session':'2024-01-02'},100,d)['reason'],'no_matching_pair_at_earliest_expiry')
    def test_upper_expiry_inclusive(self):
        self.assertEqual(choose_pair({'entry_session':'2024-01-02'},100,self.pair('2024-01-23',100))['status'],'selected')
        self.assertEqual(choose_pair({'entry_session':'2024-01-02'},100,self.pair('2024-01-24',100))['status'],'excluded')
    def definition(self):
        return {'raw_symbol':'MSFT  240109C00100000','instrument_class':'C','ts_recv':100,
                'instrument_id':1,'publisher_id':30,'strike_price':100000000000,'expiration':int(datetime(2024,1,9,tzinfo=timezone.utc).timestamp())*10**9,
                'unit_of_measure_qty':100000000000,'security_update_action':'A'}
    def test_adjusted_deleted_late_and_non100_rejected(self):
        r=self.definition();self.assertIsNotNone(decode_definition(r,'MSFT',100))
        for field,value in [('raw_symbol','MSFT1 240109C00100000'),('security_update_action','D'),('ts_recv',101),('unit_of_measure_qty',50000000000),('strike_price',105000000000)]:
            altered={**r,field:value};self.assertIsNone(decode_definition(altered,'MSFT',100))
    def test_nested_provider_header_and_undefined_size(self):
        r=self.definition()
        r['hd']={'instrument_id':r.pop('instrument_id'),'publisher_id':r.pop('publisher_id')}
        r['unit_of_measure_qty']=str(2**63-1)
        self.assertEqual(decode_definition(r,'MSFT',100)['instrument_id'],1)
    def test_reference_cutoff_is_window_end_exclusive(self):
        # A reference update during the S0 window is available at its completion.
        end_ns=300
        r={**self.definition(),'ts_recv':end_ns-1}
        self.assertIsNotNone(decode_definition(r,'MSFT',end_ns-1))
        self.assertIsNone(decode_definition({**r,'ts_recv':end_ns},'MSFT',end_ns-1))
    def test_resume_cannot_erase_later_shared_acquisition(self):
        import json,tempfile
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            ledger=Path(tmp)/'ledger.json'
            base={'request_ceiling':20000,'transfer_ceiling':4000000000,
                  'cumulative_requests':10,'cumulative_bytes':100}
            later={**base,'cumulative_requests':11,'cumulative_bytes':200}
            ledger.write_text(json.dumps(later))
            job=Job.__new__(Job);job.path=Path(tmp)/'manifest.json'
            job.m={'base_ledger':base,'requests':[]}
            with patch('stage_c_definitions_job.LEDGER',ledger):
                with self.assertRaisesRegex(RuntimeError,'shared_ledger_changed'):job.sync()
            self.assertEqual(json.loads(ledger.read_text()),later)
    def test_partial_shards_leave_only_unretrieved_cost(self):
        from decimal import Decimal
        job=Job.__new__(Job)
        job.groups={'d':{'get_cost':{'value':0.12}}}
        job.m={'dates':{},'shard_plans':{'d':[{'cost':0.05,'size':100,'status':'complete'},
            {'cost':0.07,'size':200,'status':'pending'}]}}
        self.assertEqual(job.remaining_cost(),Decimal('0.07'))
        self.assertEqual(job.remaining_size_and_queries(),(200,1))
    def test_concatenated_zstd_shards_validate(self):
        import json,tempfile
        from compression import zstd
        r=self.definition();frame=zstd.compress((json.dumps(r)+'\n').encode())
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'frames.zst';p.write_bytes(frame+frame)
            job=Job.__new__(Job);job.zstd=zstd
            self.assertEqual(job.validate_file(p),2)
    def test_no_compute_no_initialization_or_request(self):
        import unittest.mock as mock
        with mock.patch.dict('os.environ',{},clear=True):
            with self.assertRaisesRegex(RuntimeError,'compute_node_required'):Job()
    def test_concurrent_metadata_serializes_checkpoint_updates(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier,RLock
        barrier=Barrier(4);job=Job.__new__(Job)
        job.metadata_lock=RLock();job.m={'quote_estimates':{},'requests':[]};job.auth='test-only'
        def reserve(*args):
            self.assertTrue(job.metadata_lock._is_owned())
            r={};job.m['requests'].append(r);return r
        def sync():self.assertTrue(job.metadata_lock._is_owned())
        class Response:
            status=200
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,cap):barrier.wait(timeout=5);return b'0.01'
        class Opener:
            def open(self,*args,**kwargs):return Response()
        job.reserve=reserve;job.sync=sync;job.opener=Opener()
        with ThreadPoolExecutor(max_workers=4) as pool:
            values=list(pool.map(lambda n:job.fetch_metadata(str(n),'get_cost',{}),range(4)))
        self.assertEqual(values,[0.01]*4)
        self.assertEqual(len(job.m['quote_estimates']),4)
        self.assertTrue(all(r['charged_bytes']==4 and r['status']=='success' for r in job.m['requests']))
if __name__=='__main__':unittest.main()
