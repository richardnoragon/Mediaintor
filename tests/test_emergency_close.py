from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QCloseEvent
from mediainator.activity import ActivityStore, ActivityBridge
from mediainator.recovery import RecoveryStore
from mediainator.editor import MetadataEditor
from mediainator.catalog import Book
from mediainator.settings import SettingsStore, SettingsError
from mediainator.window import Hub

APP=QApplication.instance() or QApplication([])

def record(**kwargs):
    return dict(dict(title='Title',authors=['Author'],tags=[],series='',series_index=None,comments='<p>Text</p>',cover=None,uuid='book'),**kwargs)

class EmergencyCloseTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.bridge=ActivityBridge(ActivityStore(self.root/'activity','profile','device'),lambda _:None)
        self.recovery=RecoveryStore(self.root/'data','profile','device',self.bridge)
        self.editor=MetadataEditor(self.root/'library',Book('lib:1','Title','Author',(),(),uuid='book'),self.root/'cover')
        self.editor.activity=self.bridge;self.editor.recovery_store=self.recovery;self.editor.library_uuid='lib'
        self.editor.fill(record());self.editor.title.setText('Unsaved')
        self.addCleanup(self.editor.deleteLater)

    def fail_twice(self):
        with patch.object(self.editor,'request',return_value=None):
            self.assertFalse(self.editor.save_changes());self.assertFalse(self.editor.save_changes())

    def test_two_failures_preserve_and_keep_normal_editor_open(self):
        self.editor.show()
        with patch.object(self.editor,'request',return_value=None):
            self.assertFalse(self.editor.save_changes());self.assertEqual(self.recovery.discover()['records'],[])
            self.assertFalse(self.editor.save_changes())
        self.assertTrue(self.editor.isVisible());self.assertTrue(self.editor.dirty())
        self.assertTrue(self.editor.protected_current_draft())
        self.assertEqual(self.recovery.discover()['records'][0]['payload']['pending'],{'title':'Unsaved'})
        self.assertIn('not been saved to the library',self.editor.status.text())

    def test_close_save_retry_preserves_and_accepts_automatically(self):
        event=QCloseEvent()
        with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Save),patch.object(self.editor,'request',return_value=None),patch.object(self.editor,'close_failure_choice',return_value='retry') as choice:
            self.editor.closeEvent(event)
        self.assertTrue(event.isAccepted());choice.assert_called_once()
        self.assertTrue(self.editor.protected_current_draft())

    def test_cancel_initial_close_performs_no_save_or_preservation(self):
        event=QCloseEvent()
        with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Cancel),patch.object(self.editor,'request') as request:
            self.editor.closeEvent(event);request.assert_not_called()
        self.assertFalse(event.isAccepted());self.assertEqual(self.recovery.discover()['records'],[])

    def test_keep_editing_after_failed_close_has_no_latent_close(self):
        self.editor.show();event=QCloseEvent()
        with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Save),patch.object(self.editor,'request',return_value=None),patch.object(self.editor,'close_failure_choice',return_value='cancel'):
            self.editor.closeEvent(event)
            self.assertFalse(event.isAccepted())
            self.editor.save_changes()
        self.assertTrue(self.editor.isVisible());self.assertTrue(self.editor.protected_current_draft())

    def test_new_edits_reset_failure_chain_and_invalidate_old_copy(self):
        self.fail_twice();self.editor.title.setText('Newer')
        self.assertFalse(self.editor.protected_current_draft())
        with patch.object(self.editor,'request',return_value=None):self.editor.save_changes()
        self.assertEqual(self.editor.failed_saves,1)
        self.assertEqual(self.recovery.discover()['records'][0]['payload']['pending']['title'],'Unsaved')

    def test_partial_success_excluded_from_emergency_payload(self):
        self.editor.tags.addItem('Pending')
        partial=dict(current=record(title='Unsaved'),saved=['title'],errors={'tags':'locked'})
        with patch.object(self.editor,'request',side_effect=[partial,None]):
            self.editor.save_changes();self.editor.save_changes()
        payload=self.recovery.discover()['records'][0]['payload']
        self.assertEqual(payload['pending'],{'tags':['Pending']});self.assertEqual(set(payload['baseline']),{'tags'})

    def test_invalid_input_and_cancelled_conflicts_do_not_preserve(self):
        self.editor.title.setText('')
        with patch.object(self.editor,'request') as request:
            self.assertFalse(self.editor.save_changes());request.assert_not_called()
        self.editor.title.setText('Unsaved')
        with patch.object(self.editor,'request',return_value=dict(conflicts=['title'],current=record(title='External'))),patch.object(self.editor,'resolve',return_value=None):
            self.editor.save_changes();self.editor.save_changes()
        self.assertEqual(self.editor.failed_saves,0);self.assertEqual(self.recovery.discover()['records'],[])

    def test_failed_registration_keeps_close_open_even_if_file_exists(self):
        event=QCloseEvent()
        from mediainator import recovery as module
        atomic=module.atomic_json
        def fail_index(path,value):
            if path==self.recovery.index:raise OSError('registration unavailable')
            return atomic(path,value)
        with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Save),patch.object(self.editor,'request',return_value=None),patch.object(self.editor,'close_failure_choice',side_effect=['retry','cancel']),patch.object(module,'atomic_json',side_effect=fail_index):
            self.editor.closeEvent(event)
        self.assertFalse(event.isAccepted());self.assertTrue(self.editor.preservation_failed)
        self.assertTrue(list(self.recovery.folder.glob('*.json')))
        self.assertFalse(self.editor.protected_current_draft())

    def test_alternate_location_success_continues_requested_close(self):
        actual=self.recovery.preserve
        def fail_default(payload,destination=None):
            if destination is None:raise OSError('default unavailable')
            return actual(payload,destination)
        with patch.object(self.editor,'request',return_value=None),patch.object(self.editor,'close_failure_choice',side_effect=['retry','elsewhere']),patch.object(self.recovery,'preserve',side_effect=fail_default),patch('mediainator.editor.QFileDialog.getExistingDirectory',return_value=str(self.root/'alternate')):
            self.assertTrue(self.editor.save_for_close())
        found=self.recovery.discover()['records'][0]
        self.assertEqual(Path(found['path']).parent,self.root/'alternate');self.assertTrue(found['registered'])

    def test_alternate_cancel_keeps_close_open(self):
        with patch.object(self.editor,'request',return_value=None),patch.object(self.editor,'close_failure_choice',side_effect=['retry','elsewhere']),patch.object(self.recovery,'preserve',side_effect=OSError('full')),patch('mediainator.editor.QFileDialog.getExistingDirectory',return_value=''):
            self.assertFalse(self.editor.save_for_close())
        self.assertTrue(self.editor.dirty())

    def test_missing_preserved_file_no_longer_protects_close(self):
        self.fail_twice();Path(self.recovery.discover()['records'][0]['path']).unlink()
        self.assertFalse(self.editor.protected_current_draft())

    def test_successful_later_save_resolves_automatically_preserved_copy(self):
        self.fail_twice()
        with patch.object(self.editor,'request',return_value=dict(current=record(title='Unsaved'),saved=['title'])):
            self.assertTrue(self.editor.save_changes())
        self.assertEqual(self.recovery.discover()['records'][0]['state'],'recovered')

    def hub(self):
        settings=SettingsStore(self.root/'settings.json');hub=Hub(settings,settings.load())
        hub.bookinator.editor=self.editor;self.editor.on_preserved=hub.show_preservation_notice
        self.addCleanup(hub.deleteLater)
        return hub

    def test_hub_exit_and_tab_close_preserve_then_continue(self):
        hub=self.hub();event=QCloseEvent()
        with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Save),patch.object(self.editor,'request',return_value=None),patch.object(self.editor,'close_failure_choice',return_value='retry'):
            hub.closeEvent(event)
        self.assertTrue(event.isAccepted());self.assertIn('preserved',hub.preservation_notice.text())
        self.assertTrue(hub.state['bookinator_open'])
        hub.bookinator.editor=None
        hub=self.hub()  # A distinct running Hub for the tab-close scenario.
        with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Save),patch.object(self.editor,'request',return_value=None):
            hub.close_tab(1)
        self.assertIsNone(hub.bookinator);self.assertFalse(hub.state['bookinator_open'])

    def test_settings_failure_still_blocks_exit_after_preservation(self):
        hub=self.hub();event=QCloseEvent()
        with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Save),patch.object(self.editor,'request',return_value=None),patch.object(self.editor,'close_failure_choice',return_value='retry'),patch.object(hub,'save_geometry',return_value=False),patch.object(QMessageBox,'warning'):
            hub.closeEvent(event)
        self.assertFalse(event.isAccepted());self.assertTrue(self.editor.protected_current_draft())

    def test_restart_finds_preserved_work_without_running_anything(self):
        self.fail_twice()
        store=RecoveryStore(self.root/'data','profile','device',self.bridge)
        self.assertEqual(len(store.sync_activity()['records']),1)
        self.assertEqual(self.bridge.store.summary()['recovery'],1)

    def test_interactive_desktop_shutdown_uses_close_and_cancels_on_failure(self):
        from unittest.mock import Mock
        hub=self.hub();manager=Mock();manager.allowsInteraction.return_value=True
        with patch.object(hub,'close',return_value=False) as close:hub.commit_shutdown(manager)
        close.assert_called_once();manager.cancel.assert_called_once()

    def test_noninteractive_shutdown_never_discards_or_prompts_for_dirty_work(self):
        from unittest.mock import Mock
        hub=self.hub();manager=Mock();manager.allowsInteraction.return_value=False
        with patch.object(self.editor,'request') as request,patch.object(QMessageBox,'question') as prompt:
            hub.commit_shutdown(manager)
        manager.cancel.assert_called_once();request.assert_not_called();prompt.assert_not_called()

    def test_noninteractive_clean_shutdown_saves_preferences(self):
        from unittest.mock import Mock
        hub=self.hub();self.editor.fill(record());manager=Mock();manager.allowsInteraction.return_value=False
        with patch.object(hub,'save_geometry',return_value=True) as save:hub.commit_shutdown(manager)
        save.assert_called_once();manager.cancel.assert_not_called()

    def test_payload_and_registration_failure_do_not_change_identity_on_fallback(self):
        from mediainator import recovery as module
        atomic=module.atomic_json
        def fail_index(path,value):
            if path==self.recovery.index:raise OSError('index unavailable')
            return atomic(path,value)
        with patch.object(self.editor,'request',return_value=None),patch.object(module,'atomic_json',side_effect=fail_index):
            self.editor.save_changes();self.editor.save_changes()
        identity=self.editor.recovery_id
        self.assertTrue(self.editor.emergency_preserve(self.root/'alternate'))
        self.assertEqual(self.editor.recovery_id,identity)
        self.assertEqual(len(self.recovery.discover()['records']),1)

    def test_existing_reader_close_cancel_never_attempts_save(self):
        from PyQt6.QtWidgets import QDialog
        hub=self.hub()
        with patch.object(hub.reader,'active',return_value=True),patch.object(QDialog,'exec',return_value=QDialog.DialogCode.Rejected),patch.object(self.editor,'request') as request,patch.object(hub.reader,'request_close') as close:
            self.assertFalse(hub.review_close());request.assert_not_called();close.assert_not_called()

    def test_preservation_embeds_cover_bytes_and_description(self):
        import base64
        from PyQt6.QtCore import QBuffer, QIODevice
        from PyQt6.QtGui import QImage
        image=QImage(2,2,QImage.Format.Format_RGB32);image.fill(0xff112233)
        buffer=QBuffer();buffer.open(QIODevice.OpenModeFlag.WriteOnly);image.save(buffer,'PNG')
        cover=bytes(buffer.data());self.editor.set_cover(base64.b64encode(cover).decode())
        self.editor.description.insertPlainText('Pending description')
        expected=self.editor.draft()['comments'];self.fail_twice()
        payload=self.recovery.discover()['records'][0]['payload']
        self.assertEqual(base64.b64decode(payload['pending']['cover']),cover)
        self.assertEqual(payload['pending']['comments'],expected)

    def test_invalid_cover_never_counts_as_failed_write(self):
        import base64
        self.editor.set_cover(base64.b64encode(b'invalid image').decode())
        with patch.object(self.editor,'request') as request:
            self.editor.save_changes();self.editor.save_changes();request.assert_not_called()
        self.assertEqual(self.editor.failed_saves,0);self.assertEqual(self.recovery.discover()['records'],[])

    def test_successful_save_clears_prior_preservation_failure_attention(self):
        with patch.object(self.recovery,'preserve',side_effect=OSError('full')):self.fail_twice()
        self.assertGreater(self.bridge.store.summary()['pending'],0)
        with patch.object(self.editor,'request',return_value=dict(current=record(title='Unsaved'),saved=['title'])):
            self.assertTrue(self.editor.save_changes())
        self.assertEqual(self.bridge.store.summary()['pending'],0)

    def test_discard_clears_prior_preservation_failure_attention(self):
        with patch.object(self.recovery,'preserve',side_effect=OSError('full')):self.fail_twice()
        with patch.object(self.editor,'request',return_value=dict(current=record(),library_uuid='lib')):
            self.assertTrue(self.editor.discard())
        self.assertEqual(self.bridge.store.summary()['pending'],0)

    def test_approved_hub_close_does_not_prompt_again_for_editor(self):
        hub=self.hub();event=QCloseEvent()
        with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Save),patch.object(self.editor,'request',return_value=None),patch.object(self.editor,'close_failure_choice',return_value='retry'):
            hub.closeEvent(event)
        self.assertTrue(event.isAccepted())
        second=QCloseEvent()
        with patch.object(QMessageBox,'question') as question:self.editor.closeEvent(second)
        self.assertTrue(second.isAccepted());question.assert_not_called()
        self.editor.title.setText('New revision')
        with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Cancel) as question:self.editor.closeEvent(second)
        self.assertFalse(second.isAccepted());question.assert_called_once()

    def test_close_suppresses_queued_auto_refresh(self):
        from unittest.mock import Mock
        hub=self.hub();self.editor.fill(record())
        loader=Mock();loader.active=False;loader.worker=None
        hub.bookinator.loader=loader
        event=QCloseEvent()
        hub.closeEvent(event)
        hub.bookinator.auto_refresh()
        self.assertTrue(event.isAccepted());loader.shutdown.assert_called_once();loader.load.assert_not_called()

    def test_cancel_close_reenables_refresh(self):
        hub=self.hub();event=QCloseEvent()
        with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Cancel):hub.closeEvent(event)
        self.assertFalse(event.isAccepted());self.assertFalse(hub.closing);self.assertFalse(hub.bookinator.closing)

    def test_snapshot_shutdown_joins_finishing_worker_even_if_active_flag_is_false(self):
        from PyQt6.QtCore import QThread
        from mediainator.library import SnapshotLoader
        class FinishingWorker(QThread):
            def run(self):
                while not self.isInterruptionRequested():self.msleep(1)
        loader=SnapshotLoader(self.root);worker=FinishingWorker(loader);loader.worker=worker;worker.start()
        loader.active=False;loader.shutdown()
        self.assertFalse(worker.isRunning());self.assertTrue(loader.stopping)
        loader.load();self.assertFalse(loader.active)
