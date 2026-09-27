import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from PyQt6.QtWidgets import QApplication
from mediainator.settings import SettingsStore
from mediainator.window import Hub
from mediainator.workspace_ui import capture
from mediainator.workspaces import WorkspaceError

class RestoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.settings=SettingsStore(Path(self.tmp.name)/'settings.json');self.windows=[]
        self.addCleanup(self.cleanup)
    def cleanup(self):
        for w in self.windows:w.close();w.deleteLater()
        self.app.processEvents()
    def hub(self):
        h=Hub(self.settings,self.settings.load());self.windows.append(h);h.workspaces.tick();return h
    def test_named_startup_and_last_session_independent(self):
        h=self.hub();h.tabs.setCurrentIndex(0);c=h.workspaces;s=c.store
        key=s.save_named(s.load()['revision'],'Hub active',capture(h))
        s.set_startup(s.load()['revision'],key)
        h.tabs.setCurrentIndex(1);c.flush();before=s.load()['named'][key]
        h.close();h.workspaces.timer.stop()
        again=self.hub();self.assertEqual(again.tabs.currentIndex(),0)
        self.assertEqual(again.workspaces.store.load()['named'][key],before)
    def test_restore_module_without_touching_reader_and_busy_rejection(self):
        h=self.hub();target=capture(h);target.update(modules=['hub'],active='hub',selection=None)
        with patch.object(h.reader,'request_close') as close,patch.object(h.reader,'launch') as launch:
            self.assertTrue(h.workspaces.restore(target));self.assertIsNone(h.bookinator);close.assert_not_called();launch.assert_not_called()
        target.update(modules=['hub','bookinator'],active='bookinator');self.assertTrue(h.workspaces.restore(target));self.assertIsNotNone(h.bookinator)
        with patch.object(h.bookinator,'import_active',return_value=True):
            with self.assertRaises(WorkspaceError):h.workspaces.restore(target)
    def test_cancel_draft_keeps_layout(self):
        h=self.hub();target=capture(h);target.update(modules=['hub'],active='hub',selection=None)
        from unittest.mock import Mock
        editor=Mock();editor.busy=False;editor.review.return_value=False
        h.bookinator.editor=editor
        self.assertFalse(h.workspaces.restore(target));self.assertIsNotNone(h.bookinator)
        h.bookinator.editor=None
    def test_corrupt_storage_stays_preserved(self):
        h=self.hub();p=h.workspaces.store.path;p.write_bytes(b'{broken')
        self.assertFalse(h.workspaces.flush());self.assertEqual(p.read_bytes(),b'{broken')
        # Preserve the broken fixture without interactive shutdown.
        p.unlink();h.workspaces.flush()

    def test_uuid_selection_hidden_by_shared_filters(self):
        import sqlite3
        from uuid import uuid4
        from dataclasses import replace
        h=self.hub();lib=Path(self.tmp.name)/'library';lib.mkdir()
        library_uuid=str(uuid4());book_uuid=str(uuid4())
        with sqlite3.connect(lib/'metadata.db') as db:
            db.execute('create table library_id(uuid text)');db.execute('insert into library_id values (?)',(library_uuid,))
        h.library=lib;panel=h.bookinator;panel.library=lib
        book=replace(panel.books[0],uuid=book_uuid);panel.books=(book,)
        h.state['selected_book']=book.id;target=capture(h)
        panel.search.setText('not a matching book');shared=dict(h.state['catalog_search'])
        self.assertTrue(h.workspaces.restore(target));h.workspaces.resolve_selection()
        self.assertEqual(h.state['selected_book'],book.id);self.assertEqual(h.state['catalog_search'],shared)
        self.assertIn('hidden',panel.note.text());self.assertEqual(panel.visible,[])
        panel.clear_search_filters();self.assertEqual(panel.visible[0].uuid,book_uuid)
        # Avoid unrelated library operations in cleanup.
        panel.library=None;h.library=None
