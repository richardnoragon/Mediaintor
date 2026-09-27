from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from PyQt6.QtWidgets import QApplication, QMessageBox
from mediainator.activity import ActivityStore, ActivityBridge
from mediainator.recovery import RecoveryStore
from mediainator.recovery_actions import RecoveryActions
from mediainator.import_store import ImportStore, atomic_json
from mediainator.editor import MetadataEditor
from mediainator.catalog import Book

APP = QApplication.instance() or QApplication([])


def metadata(**kwargs):
    return dict(dict(title='Title', authors=['Author'], tags=[], series='', series_index=None,
                     comments='<p>Original</p>', cover=None, uuid='book'), **kwargs)


class RecoveryActionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bridge = ActivityBridge(ActivityStore(self.root/'activity', 'profile', 'device'), lambda message: None)
        self.recovery = RecoveryStore(self.root/'data', 'profile', 'device', self.bridge)
        self.actions = RecoveryActions(self.bridge, self.recovery, self.root)

    def imported(self, state='pending'):
        store = ImportStore(self.root/'imports', self.root/'library')
        path, batch = store.create(dict(library_uuid='lib', items=[dict(source='original.epub', state=state,
            operation_uuid='op', destination_uuid='book', missing=['author'], title='Title')]))
        identity = self.bridge.batch(batch, path, 'import')
        return identity, store, path, batch

    def preserved(self):
        payload = self.recovery.capture('lib', 'book', metadata(), metadata(tags=['Pending']), 1, 'save')
        path = self.recovery.preserve(payload)
        return self.bridge.store.records()[0]['id'], payload, path

    def test_dismiss_survives_restart_and_retains_payload_and_retry(self):
        identity, payload, path = self.preserved(); before = path.read_bytes()
        self.actions.dismiss(identity)
        restarted = RecoveryActions(self.bridge, self.recovery, self.root)
        self.assertTrue(restarted.record(identity)['dismissed'])
        self.assertEqual(self.bridge.store.summary()['total'], 0)
        self.assertEqual(restarted.source(restarted.record(identity))[1]['payload'], payload)
        self.assertEqual(path.read_bytes(), before)

    def test_discard_requires_review_and_exact_revision(self):
        identity, store, path, batch = self.imported()
        with self.assertRaisesRegex(ValueError, 'Review Recovery'): self.actions.discard(identity)
        self.actions.acknowledge_review(identity)
        batch['items'][0]['warning'] = 'Changed since review'; atomic_json(path, batch)
        with self.assertRaisesRegex(ValueError, 'Review Recovery'): self.actions.discard(identity)
        self.actions.acknowledge_review(identity); self.actions.discard(identity)
        self.assertEqual(json.loads(path.read_text())['items'][0]['state'], 'discarded')
        self.assertFalse(self.actions.record(identity)['pending'])

    def test_uncertain_work_cannot_be_acknowledged_or_discarded(self):
        identity, _, _, _ = self.imported('unverified')
        with self.assertRaisesRegex(ValueError, 'Reconcile'): self.actions.acknowledge_review(identity)
        with self.assertRaises(ValueError): self.actions.discard(identity)

    def test_delete_blocked_until_separate_review_and_discard(self):
        identity, payload, path = self.preserved()
        with self.assertRaises(ValueError): self.actions.delete(identity)
        self.actions.acknowledge_review(identity); self.actions.discard(identity)
        self.assertTrue(path.exists())
        self.assertFalse(self.actions.record(identity)['recovery'])
        self.assertEqual(self.actions.record(identity)['attempts'][-1]['outcome'], 'discarded')
        self.actions.delete(identity)
        self.assertFalse(path.exists()); self.assertEqual(self.recovery.discover()['records'], [])
        self.assertEqual(self.bridge.store.records(), [])
        self.recovery.sync_activity(); self.assertEqual(self.bridge.store.records(), [])

    def test_delete_preserves_independent_review_status_and_no_resurrection(self):
        identity, store, path, batch = self.imported('complete')
        self.actions.delete(identity)
        self.assertIn('book', store.review_needed()); self.assertFalse(path.exists())
        self.bridge.batch(batch, path, 'import', legacy=True)
        self.assertEqual(self.bridge.store.records(), [])

    def test_migration_failure_blocks_intent_and_file_deletion(self):
        identity, store, path, _ = self.imported('complete')
        with patch.object(ImportStore, 'review_records', side_effect=OSError('disk full')):
            with self.assertRaises(OSError): self.actions.delete(identity)
        self.assertTrue(path.exists()); self.assertNotIn('deletion', self.actions.record(identity))

    def test_interrupted_delete_keeps_intent_and_resumes_after_restart(self):
        identity, _, path, _ = self.imported('complete')
        original = Path.unlink
        def fail(target, *args, **kwargs):
            if target == path: raise OSError('read only')
            return original(target, *args, **kwargs)
        with patch.object(Path, 'unlink', fail):
            with self.assertRaises(OSError): self.actions.delete(identity)
        self.assertIn('deletion', self.actions.record(identity)); self.assertTrue(path.exists())
        restarted = RecoveryActions(self.bridge, self.recovery, self.root)
        restarted.delete(identity)
        self.assertFalse(path.exists()); self.assertEqual(self.bridge.store.records(), [])

    def test_changed_cleanup_target_retained(self):
        identity, _, path, batch = self.imported('complete')
        original = Path.unlink
        def fail(target, *args, **kwargs):
            if target == path: raise OSError('blocked')
            return original(target, *args, **kwargs)
        with patch.object(Path, 'unlink', fail):
            with self.assertRaises(OSError): self.actions.delete(identity)
        batch['items'][0]['title'] = 'New value'; atomic_json(path, batch)
        with self.assertRaisesRegex(ValueError, 'changed'): self.actions.delete(identity)
        self.assertTrue(path.exists())

    def test_wrong_journal_pointer_cannot_delete_other_files(self):
        identity, _, path, _ = self.imported('complete')
        data = self.bridge.store._read(); data['operations'][identity]['source']['journal'] = str(self.root/'other')
        atomic_json(self.bridge.store.path, data)
        with self.assertRaises(ValueError): self.actions.delete(identity)
        self.assertTrue(path.exists())

    def test_resolution_rejects_newer_revision(self):
        identity, payload, path = self.preserved()
        self.actions.acknowledge_review(identity)
        newer = deepcopy(payload); newer['revision'] = 2; newer['pending']['tags'] = ['Newer']
        self.recovery.preserve(newer)
        with self.assertRaises(ValueError): self.actions.discard(identity)
        with self.assertRaises(ValueError): self.recovery.resolve(payload, 'recovered')
        self.assertTrue(path.exists())

    def editor(self, payload):
        editor = MetadataEditor(self.root/'library', Book('lib:1', 'Title', 'Author', (), (), uuid='book'), self.root/'cover')
        editor.activity = self.bridge; editor.recovery_store = self.recovery; editor.library_uuid = 'lib'
        editor.fill(metadata()); editor.apply_pending(metadata(**payload['pending']))
        editor.recovery_context = payload; editor.recovery_id = payload['id']; editor.activity_operation = payload['operation_id']
        self.addCleanup(editor.deleteLater)
        return editor

    def test_explicit_save_resolves_recovery_only_after_verified_result(self):
        identity, payload, _ = self.preserved(); editor = self.editor(payload)
        with patch.object(editor, 'request', return_value=dict(current=metadata(tags=['Pending']), saved=['tags'])):
            self.assertTrue(editor.save_changes())
        self.assertFalse(self.actions.record(identity)['pending']); self.assertIsNone(editor.recovery_context)

    def test_partial_save_persists_only_remaining_intent(self):
        payload = self.recovery.capture('lib', 'book', metadata(), metadata(title='New', tags=['Pending']), 1, 'save')
        self.recovery.preserve(payload); editor = self.editor(payload)
        with patch.object(editor, 'request', return_value=dict(current=metadata(title='New'), saved=['title'], errors={'tags':'locked'})):
            self.assertFalse(editor.save_changes())
        found = self.recovery.discover()['records'][0]['payload']
        self.assertEqual(found['pending'], {'tags':['Pending']})
        self.assertGreater(found['revision'], payload['revision'])

    def test_failed_registration_does_not_claim_recovery_resolved(self):
        identity, payload, _ = self.preserved(); editor = self.editor(payload)
        with patch.object(editor, 'request', return_value=dict(current=metadata(tags=['Pending']), saved=['tags'])), patch.object(self.recovery, 'resolve', side_effect=OSError('disk full')):
            self.assertFalse(editor.save_changes())
        self.assertTrue(self.actions.record(identity)['recovery'])
        self.assertIn('could not be updated', editor.status.text())

    def test_noop_recovery_rereads_and_refuses_changed_values(self):
        identity, payload, _ = self.preserved(); editor = self.editor(payload)
        editor.fill(metadata(tags=['Pending']))
        with patch.object(editor, 'request', return_value=dict(current=metadata(tags=['External']), library_uuid='lib')):
            self.assertFalse(editor.save_changes())
        self.assertTrue(self.actions.record(identity)['recovery'])

    def test_local_editor_discard_keeps_durable_recovery(self):
        identity, payload, path = self.preserved(); editor = self.editor(payload)
        with patch.object(editor, 'request', return_value=dict(current=metadata(), library_uuid='lib')):
            self.assertTrue(editor.discard())
        self.assertTrue(path.exists()); self.assertTrue(self.actions.record(identity)['recovery'])

    def test_local_discard_and_background_refresh_keep_filtered_editor_open(self):
        from unittest.mock import Mock
        from PyQt6.QtWidgets import QPushButton
        from mediainator.settings import SettingsStore
        from mediainator.window import Hub
        identity, payload, path = self.preserved(); before = path.read_bytes()
        settings = SettingsStore(self.root/'settings.json')
        hub = Hub(settings, settings.load(), app_data=self.root/'hub-data')
        self.addCleanup(hub.deleteLater); hub.workspaces.timer.stop()
        books = hub.bookinator; books.refresh_timer.stop(); books.reader_timer.stop()
        books.search.setText('Different title')
        editor = self.editor(payload); books.editor = editor
        books.books = (editor.book, Book('lib:2', 'Different title', 'Other', (), (), uuid='other'))
        books.state['selected_book'] = editor.book.id
        editor.on_saved = Mock(); finished = Mock(); editor.finished.connect(finished)
        editor.show()
        button = next(b for b in editor.findChildren(QPushButton) if b.text() == 'Discard local edits')
        with patch.object(editor, 'request', return_value=dict(current=metadata(), library_uuid='lib')) as request:
            button.click()
            self.assertEqual(request.call_count, 1)
            with patch.object(books, 'refresh_progress'):
                books.loaded(books.books)
        self.assertIs(books.editor, editor); self.assertTrue(editor.isVisible())
        editor.on_saved.assert_not_called()  # A read-only discard needs no save refresh.
        finished.assert_not_called(); self.assertFalse(editor.dirty())
        self.assertEqual(editor.tags.values(), [])
        self.assertIn('preserved recovery draft remains available', editor.status.text())
        self.assertEqual(path.read_bytes(), before); self.assertTrue(self.actions.record(identity)['recovery'])
        # An explicit selection still closes the clean editor normally.
        books.select(0)
        self.assertFalse(editor.isVisible()); finished.assert_called_once()
        books.editor = None; hub.close()

    def test_hub_review_and_cancel_do_not_execute_settings_retry(self):
        from mediainator.settings import SettingsStore
        from mediainator.window import Hub
        settings = SettingsStore(self.root/'settings.json'); hub = Hub(settings, settings.load()); self.addCleanup(hub.close)
        identity = hub.activity.record('Settings save', 'settings', module='hub', outcome='failure', pending=True, source={'kind':'settings'})
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.No), patch.object(hub, 'persist') as save:
            hub.activity_controller.perform('review', identity); save.assert_not_called()
        hub.activity_panel.refresh(); hub.activity_panel.show_details(identity)
        detail = hub.activity_panel.details[0]
        self.assertFalse(detail.actions['delete'].isEnabled()); detail.close()

    def test_recovery_cleanup_tracks_generations_in_alternate_locations(self):
        identity, payload, first = self.preserved()
        new = deepcopy(payload); new['revision'] = 2
        second = self.recovery.preserve(new, self.root/'alternate')
        final = deepcopy(new); final['revision'] = 3
        third = self.recovery.preserve(final, self.root/'another')
        self.actions.acknowledge_review(identity); self.actions.discard(identity); self.actions.delete(identity)
        self.assertFalse(any(path.exists() for path in (first, second, third)))

    def test_recovery_cleanup_can_resume_after_all_payloads_unlinked(self):
        identity, payload, path = self.preserved()
        self.actions.acknowledge_review(identity); self.actions.discard(identity)
        with patch.object(self.recovery, 'forget', side_effect=OSError('index write failed')):
            with self.assertRaises(OSError): self.actions.delete(identity)
        self.assertFalse(path.exists()); self.assertIn('deletion', self.actions.record(identity))
        RecoveryActions(self.bridge, self.recovery, self.root).delete(identity)
        self.assertEqual(self.recovery.discover()['records'], [])
        self.assertEqual(self.bridge.store.records(), [])

    def test_revert_descendant_retained_when_original_history_deleted(self):
        identity, _, _, batch = self.imported('complete')
        child = self.bridge.record('Batch reverts','child',outcome='success',original=batch['id'])
        self.actions.delete(identity)
        self.assertTrue(self.actions.record(child)['original_history_deleted'])
        self.assertEqual(len(self.bridge.store.records()), 1)

    def test_discard_retains_previously_committed_imports_and_failures(self):
        identity, _, path, batch = self.imported('failed')
        batch['items'].append(dict(source='saved.epub', state='complete', operation_uuid='done'))
        atomic_json(path,batch); self.bridge.batch(batch,path,'import')
        self.actions.acknowledge_review(identity); self.actions.discard(identity)
        actual=json.loads(path.read_text())
        self.assertEqual([i['state'] for i in actual['items']], ['discarded','complete'])
        self.assertTrue(any(a['outcome']=='failure' for a in self.actions.record(identity)['attempts']))

    def test_reader_retry_cancel_never_launches(self):
        from mediainator.settings import SettingsStore
        from mediainator.window import Hub
        settings=SettingsStore(self.root/'settings.json');hub=Hub(settings,settings.load());self.addCleanup(hub.close)
        identity=hub.activity.record('Reader launch','reader',outcome='failure',pending=True,
            source=dict(kind='reader_launch',path='/book.epub'))
        with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.No), patch.object(hub.bookinator,'open_format') as launch:
            hub.activity_controller.perform('review',identity);launch.assert_not_called()
        with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Yes), patch.object(hub.bookinator,'open_format') as launch:
            hub.activity_controller.perform('review',identity);launch.assert_called_once_with('/book.epub')

    def test_cancel_discard_and_delete_preserve_everything(self):
        from mediainator.settings import SettingsStore
        from mediainator.window import Hub
        settings=SettingsStore(self.root/'settings.json');hub=Hub(settings,settings.load());self.addCleanup(hub.close)
        payload=hub.recovery_store.capture('lib','book',metadata(),metadata(tags=['New']),1,'save')
        path=hub.recovery_store.preserve(payload);identity=hub.activity.store.records()[0]['id']
        hub.activity_controller.actions.acknowledge_review(identity)
        with patch.object(QMessageBox,'warning',return_value=QMessageBox.StandardButton.No):
            hub.activity_controller.perform('discard',identity)
        self.assertTrue(hub.activity_controller.actions.record(identity)['recovery']);self.assertTrue(path.exists())
        hub.activity_controller.actions.discard(identity)
        with patch.object(QMessageBox,'warning',return_value=QMessageBox.StandardButton.No):
            hub.activity_controller.perform('delete',identity)
        self.assertTrue(path.exists());self.assertTrue(hub.activity.store.records())

    def test_cleanup_intent_remains_in_attention_counts(self):
        identity, _, path, _ = self.imported('complete')
        original=Path.unlink
        def fail(target,*args,**kwargs):
            if target==path:raise OSError('blocked')
            return original(target,*args,**kwargs)
        with patch.object(Path,'unlink',fail):
            with self.assertRaises(OSError):self.actions.delete(identity)
        self.assertEqual(self.bridge.store.summary()['total'],1)
        self.assertEqual(self.bridge.store.summary()['pending'],1)

    def test_discard_is_not_reported_as_success_for_partly_completed_batch(self):
        identity, _, path, batch=self.imported('failed')
        batch['items'].append(dict(source='saved.epub',state='complete',operation_uuid='done'))
        atomic_json(path,batch)
        self.actions.acknowledge_review(identity);self.actions.discard(identity)
        self.assertEqual(self.actions.record(identity)['attempts'][-1]['outcome'],'discarded')
        self.bridge.batch(json.loads(path.read_text()),path,'import',legacy=True)
        self.assertEqual(self.actions.record(identity)['attempts'][-1]['outcome'],'discarded')

    def test_cancelled_module_review_does_not_reuse_an_old_dialog(self):
        from mediainator.settings import SettingsStore
        from mediainator.window import Hub
        from unittest.mock import Mock
        settings=SettingsStore(self.root/'settings.json');hub=Hub(settings,settings.load());self.addCleanup(hub.close)
        hub.library=self.root/'library';hub.bookinator.library=hub.library
        store=ImportStore(self.root/'imports',hub.library)
        path,batch=store.create(dict(library_uuid='lib',items=[dict(source='a.epub',state='pending',operation_uuid='op')]))
        identity=hub.activity.batch(batch,path,'import');record=hub.activity_controller.actions.record(identity)
        stale=Mock();hub.bookinator.import_dialog=stale;stale.busy=False;stale.running=False
        with patch.object(hub.bookinator,'open_imports',return_value=None):
            hub.activity_controller.review(record)
        stale.review_batch.assert_not_called();hub.bookinator.import_dialog=None

    def test_shared_import_route_opens_requested_batch_without_execution(self):
        from mediainator.settings import SettingsStore
        from mediainator.window import Hub
        from mediainator.import_dialog import ImportDialog
        settings=SettingsStore(self.root/'settings.json');hub=Hub(settings,settings.load());self.addCleanup(hub.close)
        hub.library=self.root/'library';hub.bookinator.library=hub.library
        store=ImportStore(self.root/'imports',hub.library)
        records=[]
        for number in (1,2):
            path,batch=store.create(dict(library_uuid='lib',items=[dict(source=f'{number}.epub',state='pending',operation_uuid=str(number))]))
            records.append(hub.activity_controller.actions.record(hub.activity.batch(batch,path,'import')))
        with patch.object(ImportDialog,'request',return_value={'item':{}}),patch.object(ImportDialog,'execute_batch') as execute:
            hub.activity_controller.review(records[1])
            self.assertEqual(hub.bookinator.import_dialog.batch['id'],records[1]['source']['batch_id'])
            self.assertIn(records[1]['id'],hub.activity_controller.actions.reviewed)
            execute.assert_not_called()
            hub.bookinator.import_dialog.close()
