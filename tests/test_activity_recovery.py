import base64
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from PyQt6.QtWidgets import QApplication
from mediainator.activity import ActivityStore, ActivityBridge
from mediainator.recovery import RecoveryStore
from mediainator.import_store import ImportStore, atomic_json
from mediainator.settings import SettingsStore, SettingsError
from mediainator.window import Hub
from mediainator.catalog import Book
from mediainator.editor import MetadataEditor

APP=QApplication.instance() or QApplication([])
def record(**kw):
    return dict(dict(title='Title',authors=['Author'],tags=['Old'],series='',series_index=None,comments='<p>Exact</p>',cover=None,uuid='book'),**kw)

class ActivityRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.activity=ActivityStore(self.root/'activity','profile','device')
        self.messages=[];self.bridge=ActivityBridge(self.activity,self.messages.append)
        self.recovery=RecoveryStore(self.root/'data','profile','device',self.bridge)

    def payload(self,**kw):
        return self.recovery.capture('lib','book',record(),record(tags=['New']),1,'operation',**kw)

    def test_attempt_identity_latest_outcomes_and_interruption(self):
        for outcome,attempt in [('running','a'),('failure','a'),('running','b'),('success','b'),('interrupted','c')]:
            self.activity.record('Import','op',outcome=outcome,pending=outcome!='success',attempt_id=attempt)
        records=self.activity.records();self.assertEqual(len(records),1);self.assertEqual(len(records[0]['attempts']),3)
        latest=self.activity.latest()[('bookinator','Import')]
        self.assertEqual(latest['failure']['attempt']['id'],'a');self.assertEqual(latest['success']['attempt']['id'],'b')

    def test_summary_does_not_double_count_overlapping_indicators(self):
        self.activity.record('Save','op',outcome='failure',pending=True,recovery=True)
        self.assertEqual(self.activity.summary(),dict(total=1,pending=1,failed=1,recovery=1))

    def test_owner_isolation_and_concurrent_writers(self):
        def write(i):ActivityStore(self.root/'activity','profile','device').record('Save',str(i),outcome='success')
        with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(write,range(12)))
        self.assertEqual(len(self.activity.records()),12)
        self.assertEqual(ActivityStore(self.root/'activity','other','device').records(),[])

    def test_corrupt_activity_preserved_and_bridge_failure_nonrecursive(self):
        self.activity.folder.mkdir(parents=True);self.activity.path.write_text('{')
        self.assertIsNone(self.bridge.record('Save','a',outcome='failure'))
        self.assertEqual(self.activity.path.read_text(),'{');self.assertEqual(len(self.messages),1)

    def test_restart_marks_running_without_execution(self):
        self.activity.record('Save','a',outcome='running',pending=True)
        self.activity.recover_interrupted()
        self.assertEqual(self.activity.records()[0]['attempts'][0]['outcome'],'interrupted')
        self.assertNotIn('failure',self.activity.latest().get(('bookinator','Save'),{}))

    def test_batch_projection_deduplicates_legacy_discovery(self):
        batch=dict(id='batch',library=str(self.root/'library'),library_uuid='lib',items=[dict(uuid='book',state='complete')])
        for _ in range(3):self.activity.project_batch(batch,self.root/'journal','bulk',legacy=True)
        item=self.activity.records()[0];self.assertEqual(len(item['attempts']),1);self.assertIsNone(item['attempts'][0]['time'])
        self.assertEqual(item['source']['library_uuid'],'lib')

    def test_recovery_persists_only_pending_and_readback(self):
        payload=self.payload();path=self.recovery.preserve(payload)
        self.assertEqual(self.recovery.read(path),payload)
        self.assertEqual(set(payload['pending']),{'tags'});self.assertEqual(set(payload['baseline']),{'tags'})
        self.assertEqual(self.activity.summary()['recovery'],1)
        self.assertEqual(len(self.recovery.discover()['records']),1)

    def test_generations_alternate_location_and_registration(self):
        first=self.payload();p1=self.recovery.preserve(first)
        second=deepcopy(first);second['revision']=2;second['pending']['tags']=['Latest']
        p2=self.recovery.preserve(second,self.root/'alternate')
        self.assertTrue(p1.exists());self.assertNotEqual(p1,p2)
        self.assertEqual(self.recovery.discover()['records'][0]['payload']['revision'],2)
        with self.assertRaises(ValueError):self.recovery.preserve(first)
        self.assertEqual(self.recovery.preserve(second),p2)

    def test_registry_failure_never_claims_success_and_default_copy_discoverable(self):
        from mediainator.recovery import atomic_json as original
        def fail_index(path,value):
            if Path(path)==self.recovery.index:raise OSError('disk full')
            return original(path,value)
        with patch('mediainator.recovery.atomic_json',side_effect=fail_index):
            with self.assertRaises(OSError):self.recovery.preserve(self.payload())
        found=self.recovery.discover();self.assertEqual(len(found['records']),1);self.assertFalse(found['records'][0]['registered'])
        self.assertEqual(self.activity.records(),[])

    def test_corrupt_index_recovers_default_generations_without_overwriting_index(self):
        self.recovery.preserve(self.payload());self.recovery.index.write_text('{')
        found=self.recovery.discover();self.assertEqual(len(found['records']),1);self.assertTrue(found['errors'])
        self.assertEqual(self.recovery.index.read_text(),'{')

    def test_recovery_identity_integrity_and_unknown_schema(self):
        payload=self.payload();path=self.recovery.preserve(payload)
        with self.assertRaises(ValueError):self.recovery.read(path,book_uuid='wrong')
        with self.assertRaises(ValueError):RecoveryStore(self.root/'data','other','device').read(path)
        envelope=json.loads(path.read_text());envelope['payload']['pending']['tags']=['Tampered'];path.write_text(json.dumps(envelope))
        with self.assertRaises(ValueError):self.recovery.read(path)
        self.assertTrue(path.exists())
        payload['schema']=99
        with self.assertRaises(ValueError):self.recovery.preserve(payload)

    def test_recovery_review_preserves_unrelated_changes_and_requires_choices(self):
        payload=self.payload();current=record(tags=['External'],title='External title')
        result=self.recovery.draft(payload,current,library_uuid='lib',book_uuid='book')
        self.assertIsNone(result['draft']);self.assertEqual(result['conflicts'],['tags'])
        result=self.recovery.draft(payload,current,library_uuid='lib',book_uuid='book',choices={'tags':'recovered'})
        self.assertEqual(result['draft']['title'],'External title');self.assertEqual(result['draft']['tags'],['New'])
        self.assertEqual(current['tags'],['External'])
        with self.assertRaises(ValueError):self.recovery.draft(payload,dict(current,uuid='different'),library_uuid='lib',book_uuid='book')

    def test_embedded_cover_and_html_survive(self):
        cover=base64.b64encode(b'cover bytes').decode();html='<p class="unchanged">Hi &amp; bye</p>'
        payload=self.recovery.capture('lib','book',record(),record(cover=cover,comments=html),1,'operation')
        path=self.recovery.preserve(payload);restored=self.recovery.read(path)
        self.assertEqual(restored['pending'],dict(cover=cover,comments=html))

    def import_fixture(self):
        store=ImportStore(self.root/'imports',self.root/'library')
        path,batch=store.create(dict(library_uuid='lib',items=[dict(source='a.epub',state='complete',operation_uuid='op',destination_uuid='book',missing=['title'],title='Fallback')]))
        return store,path,batch

    def test_import_review_survives_journal_deletion_and_editor_uses_it(self):
        store,path,batch=self.import_fixture();self.assertEqual(store.review_needed(),{'book'})
        store.delete_history(path);self.assertFalse(path.exists());self.assertEqual(store.review_needed(),{'book'})
        editor=MetadataEditor(self.root/'library',Book('lib:1','Fallback','Author',(),(),uuid='book'),self.root/'backups');self.addCleanup(editor.deleteLater)
        editor.review_store=store;editor.fill(record(title='Fallback'))
        self.assertIn('Completeness: Incomplete',editor.review_status.text());self.assertIn('Needs Metadata Review',editor.review_status.text())
        store.mark_reviewed('book');self.assertFalse(store.review_needed())
        editor.update_review_status();self.assertIn('Reviewed',editor.review_status.text())

    def test_review_migration_idempotent_when_journal_items_reordered(self):
        store,path,batch=self.import_fixture();store.mark_reviewed('book')
        batch['items'].insert(0,dict(source='b.epub',state='discarded',operation_uuid='other'));atomic_json(path,batch)
        self.assertFalse(store.review_needed());self.assertEqual(len(store.review_records()),1)

    def test_migration_failure_blocks_deletion_and_preserves_journal(self):
        store,path,batch=self.import_fixture()
        with patch('mediainator.import_store.atomic_json',side_effect=OSError('disk full')):
            with self.assertRaises(OSError):store.delete_history(path)
        self.assertTrue(path.exists())
        batch['items'][0]['state']='pending';atomic_json(path,batch)
        with self.assertRaises(ValueError):store.delete_history(path)

    def test_metadata_save_attempts_and_explicit_preservation_hook(self):
        editor=MetadataEditor(self.root/'library',Book('lib:1','Title','Author',(),(),uuid='book'),self.root/'backup');self.addCleanup(editor.deleteLater)
        editor.activity=self.bridge;editor.recovery_store=self.recovery;editor.library_uuid='lib';editor.fill(record());editor.title.setText('Changed')
        with patch.object(editor,'request',return_value=None):self.assertFalse(editor.save_changes())
        item=self.activity.records()[0];self.assertEqual(len(item['attempts']),1);self.assertTrue(item['pending'])
        path=editor.preserve_recovery();self.assertEqual(self.recovery.read(path)['pending'],{'title':'Changed'})
        self.assertTrue(editor.dirty())

    def test_settings_success_not_logged_failure_coalesced(self):
        store=SettingsStore(self.root/'settings.json');hub=Hub(store,store.load());self.addCleanup(hub.deleteLater)
        self.assertEqual(hub.activity.store.records(),[])
        with patch.object(store,'save',side_effect=SettingsError('read only')):
            hub.persist();hub.persist()
        records=hub.activity.store.records();self.assertEqual(len(records),1);self.assertEqual(len(records[0]['attempts']),1)
        hub.persist();self.assertFalse(hub.activity.store.records()[0]['pending']);self.assertEqual(len(hub.activity.store.records()[0]['attempts']),1)
        hub.close()

    def test_startup_import_discovery_does_not_open_dialog(self):
        store=SettingsStore(self.root/'settings.json');hub=Hub(store,store.load());self.addCleanup(hub.deleteLater)
        books=hub.bookinator;books.library=self.root/'library';imports=books.import_store()
        imports.create(dict(library_uuid='lib',items=[dict(source='a',state='pending',operation_uuid='op')]))
        with patch.object(books,'open_imports') as opened:books.loaded(());APP.processEvents();opened.assert_not_called()
        self.assertEqual(hub.activity.store.summary()['pending'],1);hub.close()

    def test_failed_bulk_before_journal_creation_is_not_left_running(self):
        from mediainator.bulk_dialog import BulkDialog
        from mediainator.bulk import plan
        book=Book('lib:1','Title','Author',(),(),uuid='book')
        dialog=BulkDialog(self.root/'library',self.root/'bulk',[book]);self.addCleanup(dialog.deleteLater)
        dialog.activity=self.bridge
        dialog.batch=plan(dialog.store,[dict(book=1,uuid='book')],dict(library_uuid='lib',records={'book':record()},errors={}), 'Add Tags',dict(tags=['New']))
        dialog.render();dialog.status.setText('Access denied')
        with patch.object(dialog,'request',return_value=None):dialog.execute()
        self.assertEqual(self.activity.records()[0]['attempts'][-1]['outcome'],'failure')
        self.assertFalse(self.activity.records()[0]['attempts'][-1]['details']['journal_available'])

    def test_conflicted_batch_is_not_an_interruption_or_actual_failure(self):
        batch=dict(id='batch',library=str(self.root/'library'),library_uuid='lib',items=[dict(uuid='book',state='conflict')])
        self.activity.project_batch(batch,self.root/'journal','bulk')
        self.assertEqual(self.activity.records()[0]['attempts'][-1]['outcome'],'conflict')
        self.assertEqual(self.activity.summary()['failed'],0)
