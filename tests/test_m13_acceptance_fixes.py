"""Regression checks for defects found during installed M13 acceptance."""
import tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from PyQt6.QtWidgets import QApplication,QWidget,QMessageBox
from mediainator.import_dialog import ImportDialog
from mediainator.workspace_ui import WorkspaceDialog
from mediainator.workspaces import WorkspaceStore,WorkspaceError
from tests.test_workspaces import SNAP
APP=QApplication.instance() or QApplication([])

class AcceptanceFixTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
    def importer(self):
        d=ImportDialog(self.root/'library',self.root/'imports');self.addCleanup(d.close);return d
    def test_path_entry_spaces_folder_invalid_and_busy(self):
        d=self.importer();p=self.root/'Book with spaces.epub';p.write_text('fixture')
        with patch.object(d,'preview') as preview:
            for value in (p,self.root):
                d.path_input.setText(str(value));d.path_input.returnPressed.emit();preview.assert_called_with([str(value)])
            preview.reset_mock();d.path_input.setText('/missing-m13-path');d.preview_path();preview.assert_not_called()
            self.assertIn('existing absolute',d.status.text())
            d.path_input.setText(str(p));d.busy=True;d.preview_path();preview.assert_not_called();d.busy=False
        self.assertFalse(d.store.batches())
    def test_similar_choice_feedback_and_completed_action(self):
        d=self.importer();item=dict(source='/tmp/book.epub',state='pending',title='Book',authors=[],similar=[1],action='new',warning='Similar existing title: choose an action.; Missing metadata: title')
        d.plan=dict(items=[item],records=[]);d.render()
        action,destination=d.choices[0];self.assertEqual(action.currentText(),'Choose action…')
        action.setCurrentText('Create new book')
        self.assertNotIn('choose an action',d.table.item(0,2).text());self.assertIn('Missing metadata',d.table.item(0,2).text());self.assertFalse(destination.isEnabled())
        action.setCurrentText('Attach to existing book');self.assertTrue(destination.isEnabled())
        d.plan=None;d.batch=dict(items=[dict(item,state='complete',warning='Imported and verified.')]);d.render()
        self.assertEqual(d.choices[0][0].currentText(),'Create new book');self.assertFalse(d.choices[0][0].isEnabled())
    def workspace(self):
        h=QWidget();self.addCleanup(h.close)
        store=WorkspaceStore(self.root/'workspaces.json','11111111-1111-4111-8111-111111111111','22222222-2222-4222-8222-222222222222',SNAP)
        key=store.save_named(0,'Temporary M13',SNAP)
        h.workspaces=SimpleNamespace(store=store,disabled=False)
        d=WorkspaceDialog(h);self.addCleanup(d.close);d.list.setCurrentRow(0)
        return d,store,key
    def test_last_session_revision_can_advance_during_confirmation(self):
        d,store,key=self.workspace()
        def confirm(*args):
            self.assertIn('Temporary M13',args[2]);store.save_last_session(store.load()['revision'],SNAP)
            return QMessageBox.StandardButton.Yes
        with patch('mediainator.workspace_ui.QMessageBox.question',side_effect=confirm):d.delete()
        self.assertNotIn(key,store.load()['named'])
    def test_concurrent_named_change_still_blocks_delete(self):
        d,store,key=self.workspace();store.rename(store.load()['revision'],key,'Changed elsewhere')
        with patch('mediainator.workspace_ui.QMessageBox.question',return_value=QMessageBox.StandardButton.Yes):
            with self.assertRaises(WorkspaceError):d.delete()
        self.assertIn(key,store.load()['named'])
    def test_cancel_does_not_delete(self):
        d,store,key=self.workspace();before=store.path.read_bytes()
        with patch('mediainator.workspace_ui.QMessageBox.question',return_value=QMessageBox.StandardButton.Cancel):d.delete()
        self.assertEqual(before,store.path.read_bytes())

    def test_duplicate_only_cannot_execute_or_create_journal(self):
        d=self.importer();d.plan=dict(items=[dict(source='/tmp/a.epub',state='duplicate',warning='Identical file contents: skipped.',action='new')],records=[])
        d.render();d.preview_status()
        self.assertFalse(d.confirm.isEnabled());self.assertEqual(d.choices[0][0].currentText(),'Skipped — identical file')
        self.assertIn('nothing to import',d.windowTitle())
        with patch.object(d.store,'create') as create:d.execute_batch();create.assert_not_called()
        self.assertFalse(d.store.batches())
    def test_destination_data_shared_and_long_paths_do_not_hide_actions(self):
        d=self.importer();d.plan=dict(items=[dict(source='/'+'long/'*100,state='pending',warning='') for _ in range(30)],records=[dict(id=1,uuid='b',title='Book',authors=['A'],formats=['EPUB'])])
        d.render();self.assertTrue(all(dest.model() is d.destination_model for _,dest in d.choices))
        self.assertLessEqual(d.table.columnWidth(0),300);self.assertEqual(d.destination_model.rowCount(),2)
    def test_progress_visible_during_worker_and_cleared_on_failure(self):
        from PyQt6.QtCore import QThread,pyqtSignal,QTimer
        class Worker(QThread):
            result=pyqtSignal(object);failure=pyqtSignal(str);progress=pyqtSignal(str)
            def __init__(self,*args):super().__init__()
            def run(self):self.progress.emit('Checking fixture');self.msleep(100);self.failure.emit('Fixture failure')
        d=self.importer();observed=[];timer=QTimer();timer.setInterval(10);timer.timeout.connect(lambda:observed.append(not d.progress.isHidden()));timer.start()
        with patch('mediainator.import_dialog.ImportWorker',Worker):self.assertIsNone(d.request(dict(action='preview')))
        timer.stop();self.assertTrue(any(observed));self.assertTrue(d.progress.isHidden());self.assertFalse(d.busy)
        self.assertIn('Fixture failure',d.status.text())
