import tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from PyQt6.QtWidgets import QApplication,QWidget,QLineEdit,QComboBox
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from mediainator.catalog import Book
from mediainator.discovery_store import DiscoveryStore
from mediainator.discovery_ui import DiscoveryDialog
from mediainator.duplicate_ui import DuplicateDialog
APP=QApplication.instance() or QApplication([])

class M14UiTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        host=QWidget();self.host=host;self.addCleanup(host.close)
        self.store=DiscoveryStore(self.root/'state',self.root,'uuid',dict(profile_id='p',device_id='d'))
        host.books=(Book('1','First','Author',('EPUB',),('Red',),uuid='a',cover='cover',series='S'),Book('2','Second','Other',('EPUB',),(),uuid='b'))
        host.search=QLineEdit();host.sort=QComboBox();host.sort.addItem('Title');host.filter_values=dict(formats=set(),tags={'Red'},statuses=set());host.library=self.root;host.loader=None
        host.discovery_context=lambda:(self.store,self.store.load(),[]);host.bulk_selection=set();host.sync_bulk_checks=lambda:None;host.open_bulk=lambda:None
    def test_inherited_narrowing_saved_restore_and_debounce(self):
        d=DiscoveryDialog(self.host);self.addCleanup(d.close);d.show();APP.processEvents()
        self.assertEqual([b.uuid for b in d.model.books],['a']);d.clear_outer();self.assertEqual(len(d.model.books),2)
        d.text.setText('Second');QTest.qWait(200);self.assertEqual([b.uuid for b in d.model.books],['b'])
        with patch('mediainator.discovery_ui.QInputDialog.getText',return_value=('Second search',True)):d.save_new()
        key=d.saved.currentData();d.text.setText('First');d.refresh();d.apply_saved();self.assertEqual(d.text.text(),'Second')
        d.close();other=DiscoveryDialog(self.host);self.addCleanup(other.close);other.saved.setCurrentIndex(other.saved.findData(key));other.apply_saved();self.assertEqual([b.uuid for b in other.model.books],['b'])
    def test_bulk_targets_include_hidden_selection_and_review_facts_persist(self):
        d=DiscoveryDialog(self.host);self.addCleanup(d.close);d.clear_outer();d.select_all();d.text.setText('First');d.refresh();captured=[];self.host.open_bulk=lambda:captured.append(set(self.host.bulk_selection))
        d.bulk();self.assertEqual(captured,[{'a','b'}]);d.review_selected(False);self.assertIn('Manually flagged',d.index.reasons['a']);d.review_selected(True);self.assertFalse(d.index.reasons['a']);self.assertIn('Missing cover',d.index.reasons['b'])
    def test_reload_updates_saved_results_and_selection(self):
        d=DiscoveryDialog(self.host);self.addCleanup(d.close);d.select_all();self.host.books=(self.host.books[1],);d.reload();self.assertFalse(d.selected);self.assertFalse(d.model.books)
    def test_duplicate_close_cancels_owned_worker(self):
        # A controlled long scan checks cancellation; no timing assumption about disk speed.
        observed=[]
        def scan(root,books,cancelled,progress,missing):
            progress('Scanning test fixture')
            while not cancelled():time.sleep(.001)
            observed.append(True);return dict(exact=[],similar=[],errors=[],cancelled=True)
        d=DuplicateDialog(self.host);self.addCleanup(d.close)
        with patch('mediainator.duplicate_ui.scan_library',scan):
            d.scan();QTest.qWait(20);self.assertIsNotNone(d.worker);self.assertTrue(d.cancel.isEnabled());d.close();APP.processEvents()
        self.assertEqual(observed,[True]);self.assertEqual(d.model.rowCount(),0)
    def test_duplicate_results_survive_unchanged_snapshot_refresh(self):
        inventory={'metadata.db':(100,1,2,3),'book.epub':(50,2,3,4)}
        self.host.loader=SimpleNamespace(active=False,snapshot=SimpleNamespace(source_inventory=inventory))
        d=DuplicateDialog(self.host);self.addCleanup(d.close)
        def scan(*args):return dict(exact=[],similar=[dict(books=[dict(uuid='a',title='First',author='Author'),dict(uuid='b',title='Second',author='Other')])],errors=[],cancelled=False)
        with patch('mediainator.duplicate_ui.scan_library',scan):
            d.scan();d.worker.wait();APP.processEvents()
        self.assertEqual(d.model.rowCount(),2);message=d.status.text()
        for _ in range(3):
            self.host.loader.snapshot=SimpleNamespace(source_inventory=dict(inventory));d.catalog_refreshed()
            self.assertFalse(d.stale);self.assertEqual(d.model.rowCount(),2);self.assertEqual(d.status.text(),message)
        # File-only change must invalidate even when the catalog records are identical.
        self.host.loader.snapshot.source_inventory['book.epub']=(50,2,3,5);d.catalog_refreshed()
        self.assertTrue(d.stale);self.assertEqual(d.model.rowCount(),2);self.assertIn('stale',d.status.text())
        d.show_progress('Scan finished.');self.assertIn('stale',d.status.text())
    def test_duplicate_refresh_without_evidence_or_changed_metadata(self):
        from dataclasses import replace
        d=DuplicateDialog(self.host);self.addCleanup(d.close);message=d.status.text();d.catalog_refreshed();self.assertEqual(d.status.text(),message)
        self.host.loader=SimpleNamespace(snapshot=SimpleNamespace(source_inventory={}))
        d.scan_catalog=tuple(self.host.books);d.scan_inventory={};self.host.books=(replace(self.host.books[0],title='Changed'),self.host.books[1]);d.catalog_refreshed();self.assertTrue(d.stale)
        d.stale=False;d.scan_catalog=tuple(self.host.books);self.host.loader=None;d.catalog_refreshed();self.assertTrue(d.stale)

    def test_duplicate_load_feedback_preserves_evidence_and_allows_retry(self):
        self.host.loader=SimpleNamespace(active=True,snapshot=SimpleNamespace(source_inventory={}))
        d=DuplicateDialog(self.host);self.addCleanup(d.close);d.show();APP.processEvents()
        d.status.setText('Cancelled — incomplete. No books changed.')
        d.model.replace([('Similar 1','First','Author','a','Potential only')])
        d.scan()
        self.assertIsNone(d.worker);self.assertFalse(d.start.isEnabled())
        self.assertTrue(d.load_notice.isVisible());self.assertIn('no new scan',d.load_notice.text())
        self.assertIn('Cancelled',d.status.text());self.assertEqual(d.model.rowCount(),1)
        self.host.loader.active=False;d.library_loading(False)
        self.assertTrue(d.start.isEnabled());self.assertFalse(d.load_notice.isVisible())
        self.assertIn('Cancelled',d.status.text());self.assertIsNone(d.worker)
        with patch('mediainator.duplicate_ui.scan_library',return_value=dict(exact=[],similar=[],errors=[],cancelled=False)):
            d.scan();d.worker.wait();APP.processEvents()
        self.assertIn('Scan complete',d.status.text())
        d.library_loading(True);d.invalidate();d.library_loading(False)
        self.assertIn('stale',d.status.text());self.assertFalse(d.load_notice.isVisible())

    def test_filter_duplicate_and_hidden_count_feedback(self):
        d=DiscoveryDialog(self.host);self.addCleanup(d.close);d.clear_outer()
        d.field.setCurrentIndex(d.field.findData('tag'));d.value.setCurrentText('Red')
        d.add_condition();d.add_condition();self.assertEqual(len(d.conditions),1)
        self.assertIn('already applied',d.message.text())
        d.selected={'a','b'};d.count();self.assertIn('1 hidden',d.summary.text())
        d.review_selected(False);self.assertIn('2 selected books flagged',d.message.text())

    def test_missing_identity_error_does_not_crash_editor(self):
        from mediainator.settings import SettingsStore
        from mediainator.window import Hub
        s=SettingsStore(self.root/'settings.json');h=Hub(s,s.load());self.addCleanup(h.close)
        h.bookinator.library=self.root/'does-not-exist'
        with self.assertRaisesRegex(ValueError,'Cannot read library identity'):h.bookinator.discovery_context()
        h.bookinator.library=None

if __name__=='__main__':unittest.main()
