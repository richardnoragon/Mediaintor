import unittest
from unittest.mock import patch,Mock
from PyQt6.QtCore import QObject,pyqtSignal,QRect
from tests.test_workspace_restore import RestoreTests
from mediainator.workspace_ui import capture
from mediainator.workspace_restore import bounded_rect
from mediainator.workspaces import WorkspaceError

class Loader(QObject):
    loaded=pyqtSignal(object);failed=pyqtSignal(str)
    active=False
    def shutdown(self):pass

class FailureTests(RestoreTests):
    def test_busy_autosave_is_quiet_but_explicit_restore_is_blocked(self):
        h=self.hub();c=h.workspaces;target=capture(h)
        h.statusBar().showMessage('Saved metadata.')
        before=c.store.path.read_bytes()
        with patch.object(h.bookinator,'import_active',return_value=True):
            self.assertFalse(c.flush())
            self.assertEqual(h.statusBar().currentMessage(),'Saved metadata.')
            with self.assertRaises(WorkspaceError):c.restore(target)
        self.assertEqual(c.store.path.read_bytes(),before)
        self.assertTrue(c.flush())

    def test_success_replaces_old_warning_only_after_restore_finishes(self):
        h=self.hub();c=h.workspaces;target=capture(h);p=h.bookinator
        c.fail('old workspace failure')
        books=p.books;p.books=();p.loader=Loader()
        c.restore(target)
        self.assertIn('old workspace failure',h.statusBar().currentMessage())
        p.books=books;p.loader.loaded.emit(books)
        self.assertIsNone(c.transaction)
        self.assertEqual(h.statusBar().currentMessage(),'Workspace restored.')
        self.assertEqual(c.last_error,'')
        p.loader=None

    def test_restore_failure_is_not_replaced_by_success(self):
        h=self.hub();c=h.workspaces;target=capture(h)
        with patch.object(c.store,'save_last_session',side_effect=WorkspaceError('disk full')):
            with self.assertRaises(WorkspaceError):c.restore(target)
        self.assertIn('disk full',h.statusBar().currentMessage())
        self.assertNotEqual(h.statusBar().currentMessage(),'Workspace restored.')

    def test_failed_load_rolls_back_and_late_success_ignored(self):
        h=self.hub();c=h.workspaces;p=h.bookinator;books=p.books;target=capture(h)
        p.books=();p.loader=Loader();before=c.store.path.read_bytes()
        c.restore(target);token=c.transaction['token'];self.assertIsNotNone(c.transaction)
        with self.assertRaises(WorkspaceError):c.restore(target)
        p.loader.failed.emit('test failure');self.assertIsNone(c.transaction)
        self.assertEqual(c.store.path.read_bytes(),before)
        c.catalog_complete(token,p);self.assertEqual(c.store.path.read_bytes(),before)
        p.loader=None;p.books=books
    def test_timeout_and_shutdown_cancel_pending(self):
        h=self.hub();c=h.workspaces;p=h.bookinator;books=p.books;target=capture(h);p.books=();p.loader=Loader()
        c.restore(target);token=c.transaction['token'];c.timeout(token);self.assertIsNone(c.transaction)
        c.restore(target);self.assertTrue(c.flush(closing=True));self.assertIsNone(c.transaction)
        p.loader=None;p.books=books
    def test_failed_commit_restores_layout(self):
        h=self.hub();c=h.workspaces;h.tabs.setCurrentIndex(1);target=capture(h);target['active']='hub';before=c.store.path.read_bytes()
        with patch.object(c.store,'save_last_session',side_effect=WorkspaceError('disk full')):
            with self.assertRaises(WorkspaceError):c.restore(target)
        self.assertEqual(h.tabs.currentIndex(),1);self.assertIsNone(c.transaction);self.assertEqual(c.store.path.read_bytes(),before)
    def test_rollback_settings_failure_requires_attention(self):
        h=self.hub();c=h.workspaces;target=capture(h);before=c.store.path.read_bytes()
        with patch.object(h,'persist',return_value=False):
            with self.assertRaises(WorkspaceError):c.restore(target)
        self.assertTrue(c.disabled);self.assertIn('Rollback settings',c.last_error)
        self.assertEqual(c.store.path.read_bytes(),before)
        from mediainator.workspace_ui import WorkspaceDialog
        dialog=WorkspaceDialog(h);self.assertFalse(c.disabled);dialog.close()
    def test_reload_after_repair_reenables_controller(self):
        h=self.hub();c=h.workspaces;p=c.store.path;before=p.read_bytes()
        p.write_bytes(b'{broken');c.starting=True;c.tick();self.assertTrue(c.disabled)
        from mediainator.workspace_ui import WorkspaceDialog
        dialog=WorkspaceDialog(h);self.assertTrue(c.disabled)
        p.write_bytes(before);dialog.reload();self.assertFalse(c.disabled)
        c.tick();self.assertFalse(c.starting);dialog.close()
    def test_partial_save_cannot_switch(self):
        h=self.hub();target=capture(h);target['active']='hub';h.tabs.setCurrentIndex(1)
        editor=Mock();editor.busy=False;editor.review.return_value=True;editor.dirty.return_value=True;h.bookinator.editor=editor
        with self.assertRaises(WorkspaceError):h.workspaces.restore(target)
        self.assertEqual(h.tabs.currentIndex(),1);h.bookinator.editor=None
    def test_invalid_geometry_recovery_and_screen_loss(self):
        h=self.hub();target=capture(h);target['geometry'].update(qt='aabb',normal=[90000,90000,4000,3000],screen='unplugged')
        h.workspaces.restore(target)
        self.assertTrue(h.screen().availableGeometry().contains(h.geometry()))
        h.workspaces.recover_monitor()
        self.assertTrue(h.screen().availableGeometry().contains(h.geometry()))

class GeometryTests(unittest.TestCase):
    def test_negative_coordinates_small_screen_and_oversize(self):
        for area in (QRect(-1920,0,1920,1080),QRect(0,0,800,600),QRect(100,50,1200,700)):
            for window in (QRect(90000,90000,4000,3000),QRect(-9000,-9000,400,300),QRect(100,100,400,300)):
                self.assertTrue(area.contains(bounded_rect(window,area)))
        with self.assertRaises(WorkspaceError):bounded_rect(QRect(0,0,100,100),QRect())
