import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PyQt6.QtCore import QObject,pyqtSignal
from PyQt6.QtWidgets import QApplication
from mediainator.settings import SettingsStore
from mediainator.window import Hub
from mediainator.reader import Reader,ReaderError
from mediainator.snapshot import Snapshot,SnapshotError
import sqlite3

APP=QApplication.instance() or QApplication([])

class FakeLoader(QObject):
    loaded=pyqtSignal(object);failed=pyqtSignal(str);busy_changed=pyqtSignal(bool);progress=pyqtSignal(str)
    def __init__(self,*args):super().__init__();self.active=False
    def load(self):pass
    def cancel(self):self.active=False

    def shutdown(self):
        self.active = False

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        compatible=patch('mediainator.compatibility.require_compatible');compatible.start();self.addCleanup(compatible.stop)
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.store=SettingsStore(self.root/'settings.json')

    def test_first_selection_remembered_and_module_restored(self):
        library=self.root/'library';library.mkdir();(library/'metadata.db').touch()
        with patch('mediainator.window.SnapshotLoader',FakeLoader):
            window=Hub(self.store,self.store.load(),live=True);self.addCleanup(window.deleteLater)
            with patch('mediainator.window.QFileDialog.getExistingDirectory',return_value=str(library)):
                window.choose_library()
            self.assertEqual(self.store.load()['library'],str(library))
            window.bookinator.view.setCurrentText('List');window.close()
            again=Hub(self.store,self.store.load(),live=True);self.addCleanup(again.deleteLater)
            self.assertEqual(again.library,library);self.assertEqual(again.bookinator.view.currentText(),'List');again.close()

    def test_failed_load_retains_catalog_and_recovery(self):
        window=Hub(self.store,self.store.load());self.addCleanup(window.deleteLater)
        before=window.bookinator.books
        window.bookinator.load_failed('Library unavailable: Retry or choose library')
        self.assertEqual(window.bookinator.books,before)
        self.assertIn('out of date',window.bookinator.note.text());window.close()

    def test_external_reader_is_not_attached_or_closed_by_launch(self):
        reader=Reader(self.store.load(),lambda:True,live=True)
        with patch('mediainator.reader.external_readers',return_value=[54321]),patch('mediainator.reader.subprocess.Popen') as launch:
            with self.assertRaises(ReaderError):reader.launch(self.root,self.root/'file.epub')
            launch.assert_not_called()

    def test_snapshot_cancel_leaves_source_intact(self):
        db=sqlite3.connect(self.root/'metadata.db');db.execute('create table data(value)');db.close()
        before=(self.root/'metadata.db').read_bytes()
        with self.assertRaises(SnapshotError):Snapshot(self.root).create(lambda:True)
        self.assertEqual(before,(self.root/'metadata.db').read_bytes())

    def test_cancel_reader_close_keeps_module_and_ownership(self):
        window=Hub(self.store,self.store.load());self.addCleanup(window.deleteLater)
        with patch.object(window.reader,'active',return_value=True),patch('mediainator.window.QMessageBox') as box:
            cancel=object();box.return_value.addButton.side_effect=[object(),object(),cancel]
            box.return_value.clickedButton.return_value=cancel
            window.close_tab(1)
            self.assertIsNotNone(window.bookinator)
            self.assertTrue(window.state['bookinator_open'])
        window.close()

    def test_leave_open_closes_module_without_signalling_reader(self):
        window=Hub(self.store,self.store.load());self.addCleanup(window.deleteLater)
        with patch.object(window.reader,'active',return_value=True),patch.object(window.reader,'request_close') as close,patch('mediainator.window.QMessageBox') as box:
            keep=object();box.return_value.addButton.side_effect=[object(),keep,object()]
            box.return_value.clickedButton.return_value=keep
            window.close_tab(1)
            close.assert_not_called()
            self.assertIsNone(window.bookinator)
        window.close()

    def test_window_close_reader_choice_finishes_hub_close(self):
        from PyQt6.QtCore import QTimer
        from PyQt6.QtWidgets import QMessageBox
        window=Hub(self.store,self.store.load());self.addCleanup(window.deleteLater)
        window.show();APP.processEvents()
        running={'value':True}
        def request_close():
            QTimer.singleShot(20,lambda:running.update(value=False))
        def click_close_reader():
            dialog=APP.activeModalWidget()
            self.assertIsInstance(dialog,QMessageBox)
            next(b for b in dialog.buttons() if b.text()=='Close reader').click()
        with patch.object(window.reader,'active',side_effect=lambda:running['value']),patch.object(window.reader,'request_close',side_effect=request_close) as close:
            QTimer.singleShot(0,click_close_reader)
            self.assertTrue(window.close())
            close.assert_called_once()
        self.assertFalse(window.isVisible())
        self.assertTrue(self.store.load()['bookinator_open'])

    def test_reader_exit_alone_does_not_close_hub(self):
        window=Hub(self.store,self.store.load());self.addCleanup(window.deleteLater)
        window.show();APP.processEvents()
        with patch.object(window.reader,'active',return_value=False):
            APP.processEvents()
            self.assertTrue(window.isVisible())
        window.close()
