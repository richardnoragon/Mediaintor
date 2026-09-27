import base64
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from PyQt6.QtWidgets import QApplication, QMessageBox
from mediainator.catalog import Book
from mediainator.editor import MetadataEditor
from mediainator.metadata_rules import changes, conflicts, validate
from mediainator.settings import SettingsStore
from mediainator.window import Hub

APP=QApplication.instance() or QApplication([])
RECORD=dict(title='Foundation',authors=['Asimov, Isaac'],tags=['Science fiction'],series='Foundation',series_index=3.0,comments='<p class="keep">Exact <b>HTML</b></p>',cover=None,uuid='test')

class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.editor=MetadataEditor(Path(self.temp.name),Book('library:32','Foundation','Isaac',('EPUB',),(),uuid='test'),Path(self.temp.name)/'recovery')
        self.addCleanup(self.editor.deleteLater);self.editor.fill(deepcopy(RECORD))

    def test_untouched_html_draft_exact(self):
        self.editor.title.setText('Changed')
        self.assertEqual(self.editor.draft()['comments'],RECORD['comments'])
        self.assertEqual(changes(RECORD,self.editor.draft()),{'title':'Changed'})

    def test_clear_series_and_new_default(self):
        self.editor.series.clear()
        self.assertIsNone(self.editor.draft()['series_index'])
        self.assertTrue(self.editor.number.isHidden())
        self.editor.series.setText('New series')
        self.assertEqual(self.editor.draft()['series_index'],1)

    def test_tag_validation_and_finite_numbers(self):
        for number in (-1,float('nan'),float('inf'),'abc'):
            with self.assertRaises(ValueError):validate(dict(RECORD,series_index=number))
        for number in (0,1,2.5):validate(dict(RECORD,series_index=number))
        with self.assertRaisesRegex(ValueError,'commas'):validate(dict(RECORD,tags=['Science, Fiction']))

    def test_tag_order_ignored_author_order_significant(self):
        baseline=dict(RECORD,tags=['A','B'],authors=['First','Second'])
        draft=dict(baseline,tags=['B','A'],authors=['Second','First'])
        self.assertEqual(set(changes(baseline,draft)),{'authors'})

    def test_three_way_conflict_and_convergence(self):
        current=dict(RECORD,title='External',tags=['External'])
        self.assertEqual(conflicts(RECORD,current,{'title':'Local'}),['title'])
        self.assertEqual(conflicts(RECORD,current,{'title':'External'}),[])
        self.assertEqual(conflicts(RECORD,current,{'comments':'Local'}),[])

    def test_partial_save_retains_only_failed_fields(self):
        self.editor.title.setText('Saved');self.editor.tags.addItem('Pending')
        response={'current':dict(RECORD,title='Saved'),'saved':['title'],'errors':{'tags':'Injected failure'}}
        with patch.object(self.editor,'request',return_value=response):self.assertFalse(self.editor.save_changes())
        self.assertEqual(changes(self.editor.baseline,self.editor.draft()),{'tags':['Science fiction','Pending']})
        with patch.object(self.editor,'request',return_value={'current':dict(RECORD,title='Saved',tags=['External'])}):self.assertTrue(self.editor.discard())
        self.assertFalse(self.editor.dirty());self.assertEqual(self.editor.title.text(),'Saved')

    def test_failed_result_preserves_draft(self):
        self.editor.title.setText('Keep me')
        with patch.object(self.editor,'request',return_value=None):self.assertFalse(self.editor.save_changes())
        self.assertEqual(self.editor.title.text(),'Keep me');self.assertTrue(self.editor.dirty())

    def test_cancel_exit_preserves_draft(self):
        self.editor.title.setText('Keep me')
        with patch('mediainator.editor.QMessageBox.question',return_value=QMessageBox.StandardButton.Cancel):self.assertFalse(self.editor.review())
        self.assertTrue(self.editor.dirty())

    def test_clean_review_never_prompts(self):
        with patch('mediainator.editor.QMessageBox.question') as question:
            self.assertTrue(self.editor.review());question.assert_not_called()

    def test_dirty_refresh_defers_and_reports_detected_change(self):
        store=SettingsStore(Path(self.temp.name)/'settings.json');hub=Hub(store,store.load());self.addCleanup(hub.deleteLater)
        from unittest.mock import Mock
        module=hub.bookinator;module.loader=Mock(active=False);module.editor=self.editor
        self.editor.title.setText('Pending')
        with patch.object(module,'signature',return_value=('changed',)):
            module.auto_refresh()
        module.loader.load.assert_not_called();self.assertIn('Refresh pending',module.note.text())
        module.editor=None;module.loader=None;hub.close()

    def test_busy_operation_prevents_exit(self):
        self.editor.busy=True
        self.assertFalse(self.editor.review())
        self.editor.busy=False

    def test_invalid_tags_prevent_any_save_call(self):
        self.editor.tags.addItem('Invalid, tag')
        with patch.object(self.editor,'request') as call:self.assertFalse(self.editor.save_changes());call.assert_not_called()

    def test_authors_reorder(self):
        self.editor.authors.addItem('Second');self.editor.authors.setCurrentRow(1);self.editor.authors.move(-1)
        self.assertEqual(self.editor.draft()['authors'],['Second','Asimov, Isaac'])

    def test_description_formatting_marks_dirty(self):
        self.editor.description.selectAll();self.editor.format_text('italic')
        self.assertTrue(self.editor.description.document().isModified());self.assertIn('comments',changes(RECORD,self.editor.draft()))

    def test_conflict_dialog_global_choices_and_cancel(self):
        from PyQt6.QtCore import QTimer
        from PyQt6.QtWidgets import QPushButton
        draft=dict(RECORD,title='Mine',tags=['Mine'])
        result={'current':dict(RECORD,title='External',tags=['External']),'conflicts':['title','tags']}
        def choose_external():
            dialog=APP.activeModalWidget()
            next(b for b in dialog.findChildren(QPushButton) if b.text()=='Use All Calibre Values').click()
            dialog.accept()
        QTimer.singleShot(0,choose_external)
        resolved=self.editor.resolve(result,draft)
        self.assertEqual(resolved['title'],'External');self.assertEqual(resolved['tags'],['External'])
        self.editor.fill(RECORD)
        QTimer.singleShot(0,lambda:APP.activeModalWidget().reject())
        self.assertIsNone(self.editor.resolve(result,draft));self.assertEqual(self.editor.baseline,RECORD)

    def test_combined_exit_cancel_preserves_everything(self):
        from PyQt6.QtCore import QTimer
        store=SettingsStore(Path(self.temp.name)/'settings.json');hub=Hub(store,store.load());self.addCleanup(hub.deleteLater)
        hub.bookinator.editor=self.editor;self.editor.title.setText('Pending')
        with patch.object(hub.reader,'active',return_value=True),patch.object(hub.reader,'request_close') as close:
            QTimer.singleShot(0,lambda:APP.activeModalWidget().reject())
            self.assertFalse(hub.review_close());close.assert_not_called();self.assertTrue(self.editor.dirty())
        hub.bookinator.editor=None;hub.close()

    def test_combined_exit_discard_leave_reader(self):
        from PyQt6.QtCore import QTimer
        from PyQt6.QtWidgets import QComboBox
        store=SettingsStore(Path(self.temp.name)/'settings.json');hub=Hub(store,store.load());self.addCleanup(hub.deleteLater)
        hub.bookinator.editor=self.editor;self.editor.title.setText('Pending')
        def accept():
            dialog=APP.activeModalWidget()
            for combo in dialog.findChildren(QComboBox):combo.setCurrentIndex(1)
            dialog.accept()
        with patch.object(hub.reader,'active',return_value=True),patch.object(hub.reader,'request_close') as close,patch.object(self.editor,'discard',return_value=True) as discard:
            QTimer.singleShot(0,accept)
            self.assertTrue(hub.review_close());close.assert_not_called();discard.assert_called_once()
        hub.bookinator.editor=None;hub.close()

    def test_clean_refresh_and_busy_access(self):
        from unittest.mock import Mock
        store=SettingsStore(Path(self.temp.name)/'settings.json');hub=Hub(store,store.load());self.addCleanup(hub.deleteLater)
        module=hub.bookinator;module.loader=Mock(active=False);module.editor=self.editor
        with patch('mediainator.reader.external_readers',return_value=[99]):module.auto_refresh()
        module.loader.load.assert_not_called();self.assertIn('Waiting for library access',module.note.text())
        with patch('mediainator.reader.external_readers',return_value=[]):module.auto_refresh()
        module.loader.load.assert_called_once();self.assertEqual(module.refresh_timer.interval(),30000)
        module.editor=None;module.loader=None;hub.close()
