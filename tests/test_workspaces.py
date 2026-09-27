import json,tempfile,unittest
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch
from mediainator.workspaces import WorkspaceStore,WorkspaceError
from PyQt6.QtWidgets import QApplication

SNAP=dict(modules=['hub'],active='hub',selection=None,geometry=dict(qt='',normal=[0,0,900,700],maximized=False,screen='test',available=[0,0,1920,1080]))
class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'workspaces.json';self.store=WorkspaceStore(self.path,str(uuid4()),str(uuid4()),SNAP)
    def save(self,label,**kw):return self.store.save_named(self.store.load()['revision'],label,SNAP,**kw)
    def test_capacity_replacement_and_startup(self):
        ids=[self.save(str(i)) for i in range(5)];data=self.path.read_bytes()
        with self.assertRaises(WorkspaceError):self.save('six')
        self.assertEqual(data,self.path.read_bytes())
        self.store.set_startup(self.store.load()['revision'],ids[2]);new=self.save('six',replace=ids[2]);state=self.store.load()
        self.assertEqual(state['startup'],'last_session');self.assertNotIn(ids[2],state['named']);self.assertIn(new,state['named'])
    def test_rename_overwrite_delete_and_last_session(self):
        key=self.save('Research');self.store.set_startup(1,key);stamp=self.store.load()['named'][key]['saved_at']
        self.store.rename(2,key,'Reading');self.assertEqual(self.store.load()['named'][key]['saved_at'],stamp)
        self.save('Reading',overwrite=key);self.assertEqual(self.store.load()['startup'],key)
        before=self.store.load()['named'];self.store.save_last_session(4,SNAP);self.assertEqual(before,self.store.load()['named'])
        self.store.delete(5,key);self.assertEqual(self.store.load()['startup'],'last_session')
    def test_corruption_owner_and_revision(self):
        self.save('A')
        with self.assertRaises(WorkspaceError):self.store.rename(0,next(iter(self.store.load()['named'])),'B')
        other=WorkspaceStore(self.path,str(uuid4()),str(uuid4()),SNAP)
        with self.assertRaises(WorkspaceError):other.load()
        self.path.write_bytes(b'{bad')
        with self.assertRaises(WorkspaceError):self.store.load()
        self.assertEqual(self.path.read_bytes(),b'{bad')
    def test_failed_commit_preserves_original(self):
        self.save('A');before=self.path.read_bytes()
        with patch('mediainator.workspaces.QSaveFile') as save:
            save.return_value.open.return_value=False
            with self.assertRaises(WorkspaceError):self.save('B')
        self.assertEqual(before,self.path.read_bytes())
    def test_partial_write_and_failed_commit_preserve_original(self):
        from PyQt6.QtCore import QSaveFile
        self.save('A');before=self.path.read_bytes()
        class FailingSave:
            def __init__(self,path,mode):self.real=QSaveFile(path);self.mode=mode
            def setDirectWriteFallback(self,value):self.real.setDirectWriteFallback(value)
            def open(self,mode):return self.real.open(mode)
            def write(self,data):return self.real.write(data[:3] if self.mode=='write' else data)
            def cancelWriting(self):self.real.cancelWriting()
            def commit(self):self.real.cancelWriting();return False
        for mode in ('write','commit'):
            with patch('mediainator.workspaces.QSaveFile',side_effect=lambda path:FailingSave(path,mode)):
                with self.assertRaises(WorkspaceError):self.save('B')
            self.assertEqual(before,self.path.read_bytes())

    def test_names_shapes_and_size(self):
        self.save('A')
        for value in ('a',' ', 'x'*81):
            with self.assertRaises(WorkspaceError):self.save(value)
        broken=dict(SNAP,modules=['hub','future'])
        with self.assertRaises(WorkspaceError):self.store.save_named(1,'B',broken)
        self.path.write_bytes(b' '*(1024*1024+1))
        with self.assertRaises(WorkspaceError):self.store.load()

class DialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def test_save_and_cancel_do_not_change_settings(self):
        from mediainator.settings import SettingsStore
        from mediainator.window import Hub
        with tempfile.TemporaryDirectory() as d:
            store=SettingsStore(Path(d)/'settings.json');hub=Hub(store,store.load());hub.show_workspaces();dialog=hub.workspace_dialog
            settings=dict(hub.state)
            with patch('mediainator.workspace_ui.QInputDialog.getText',return_value=('Research',True)):dialog.save_new()
            self.assertEqual(len(dialog.store.load()['named']),1)
            before=dialog.store.path.read_bytes()
            with patch('mediainator.workspace_ui.QInputDialog.getText',return_value=('',False)):dialog.save_new()
            self.assertEqual(before,dialog.store.path.read_bytes());self.assertEqual(hub.state,settings)
            hub.close();hub.deleteLater();self.app.processEvents()
