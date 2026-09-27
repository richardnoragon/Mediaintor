import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from mediainator.bulk import BulkStore, propose, plan, reconcile, record_result, revert_plan


def record(**values):
    return dict(title='Book', authors=['Isaac Asimov', 'John Doe'], tags=['Classic'], series='', series_index=None, uuid='book-uuid', **values) if not values else dict(record(), **values)


class BulkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.store = BulkStore(Path(self.temp.name)/'history', Path(self.temp.name)/'library')
        self.response = dict(library_uuid='library-uuid', records={'book-uuid':record()}, errors={})

    def batch(self, operation='Add Tags', **options):
        return plan(self.store, [dict(book=1, uuid='book-uuid')], self.response, operation, options or dict(tags=['New']))

    def test_author_exact_order_dedup(self):
        options=dict(old='Isaac Asimov', new='I. Asimov')
        self.assertEqual(propose(record(), 'Replace Author', options, 0)['authors'], ['I. Asimov', 'John Doe'])
        self.assertEqual(propose(record(authors=['I. Asimov','John Doe','Isaac Asimov']), 'Replace Author', options, 0)['authors'], ['I. Asimov','John Doe'])
        self.assertEqual(propose(record(authors=['isaac asimov']), 'Replace Author', options, 0), {})

    def test_number_modes_orphans_and_gaps(self):
        options=dict(series='Series', mode='Keep existing')
        self.assertEqual(propose(record(series_index=8), 'Set Series', options, 0)['series_index'], 1)
        self.assertEqual(propose(record(series='Old',series_index=0), 'Set Series', options, 0)['series_index'], 0)
        options.update(mode='Sequential', start='0', increment='0.5')
        self.assertEqual([propose(record(),'Set Series',options,i)['series_index'] for i in [0,2,3]], [0,1,1.5])
        for bad in ['0','-1','nan','inf']:
            with self.assertRaises(ValueError): propose(record(),'Set Series',dict(options,increment=bad),0)

    def test_tag_validation_and_noop(self):
        with self.assertRaises(ValueError): self.batch(tags=['a,b'])
        self.assertEqual(propose(record(),'Add Tags',dict(tags=['Classic']),0),{})
        with self.assertRaises(ValueError): propose(record(),'Add Tags + Set Series',{},0)

    def test_conflict_isolation(self):
        batch=self.batch(); response=deepcopy(self.response)
        response['records']['book-uuid']['tags']=['External']
        reconcile(batch,response)
        self.assertEqual(batch['items'][0]['state'],'conflict')
        self.assertEqual(batch['items'][0]['desired']['tags'],['Classic','New'])

    def test_lost_ack_reconciles_and_revert_preserves_unrelated(self):
        batch=self.batch(); item=batch['items'][0]; item['state']='inflight'; item['attempt_before']={'tags':['Classic']}
        response=deepcopy(self.response); response['records']['book-uuid']['tags']=['Classic','New']
        reconcile(batch,response)
        self.assertEqual(item['state'],'complete')
        response['records']['book-uuid']['title']='New title'
        reverted=revert_plan(self.store,batch,response)
        self.assertEqual(reverted['items'][0]['desired'],{'tags':['Classic']})
        self.assertEqual(reverted['items'][0]['baseline']['title'],'New title')
        response['records']['book-uuid']['tags']=['External']
        self.assertEqual(revert_plan(self.store,batch,response)['items'][0]['state'],'conflict')

    def test_partial_save_and_discard_keep_verified_fields(self):
        batch=self.batch('Set Series',series='New',mode='Fixed',fixed=3)
        item=batch['items'][0]; item['attempt_before']={'series':'','series_index':None}
        current=record(series='New',series_index=1)
        record_result(item,dict(current=current,saved=['series'],errors={'series_index':'fault'}))
        self.assertEqual(item['state'],'failed'); self.assertEqual(set(item['applied']),{'series','series_index'})
        item['state']='discarded'; self.store.save(batch)
        self.assertEqual(self.store.batches()[0]['items'][0]['applied']['series']['before'],'')

    def test_durable_history_library_isolation_delete_guard(self):
        batch=self.batch(); self.store.save(batch)
        self.assertEqual(len(self.store.pending()),1)
        with self.assertRaises(ValueError): self.store.delete(batch)
        other=BulkStore(Path(self.temp.name)/'history',Path(self.temp.name)/'other')
        self.assertEqual(other.batches(),[])
        batch['items'][0]['state']='discarded'; self.store.save(batch); self.store.delete(batch)
        self.assertEqual(self.store.batches(),[])

    def test_wrong_library_rejected(self):
        with self.assertRaises(ValueError): reconcile(self.batch(),dict(self.response,library_uuid='other'))

    def test_missing_book_isolated_during_revert(self):
        batch=self.batch();item=batch['items'][0]
        item['applied']={'tags':{'before':['Classic'],'after':['Classic','New']}};item['state']='complete'
        response=dict(self.response,records={},errors={'book-uuid':'Book missing'})
        reverted=revert_plan(self.store,batch,response)
        self.assertEqual(reverted['items'][0]['state'],'failed')
        self.assertIn('book',reverted['items'][0]['errors'])

    def test_lost_ack_on_partial_retry_retains_earliest_before(self):
        batch=self.batch('Set Series',series='New',mode='Fixed',fixed=5);item=batch['items'][0]
        item['applied']={'series':{'before':'Old','after':'New'},'series_index':{'before':3,'after':2}}
        item['baseline']=record(series='New',series_index=2);item['state']='inflight';item['attempt_before']={'series_index':2}
        response=dict(self.response,records={'book-uuid':record(series='New',series_index=5)})
        reconcile(batch,response)
        self.assertEqual(item['applied']['series_index'],{'before':3,'after':5})
        self.assertEqual(item['state'],'complete')

    def test_damaged_history_is_preserved(self):
        path=self.store.folder/'broken.json';path.write_text('{}')
        with self.assertRaises(ValueError):self.store.batches()
        self.assertEqual(path.read_text(),'{}')
