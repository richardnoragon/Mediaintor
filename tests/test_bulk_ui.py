import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from mediainator.catalog import Book
from mediainator.settings import SettingsStore
from mediainator.window import Hub
from mediainator.bulk_dialog import BulkDialog
from mediainator.bulk import plan

APP=QApplication.instance() or QApplication([])
BOOKS=tuple(Book('calibre:'+str(i),title,author,(),(),uuid='uuid-'+str(i)) for i,title,author in [(1,'Alpha','Zed'),(2,'Beta','Yen'),(3,'Gamma','Ann')])

class BulkUiTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=SettingsStore(Path(self.temp.name)/'settings.json')

    def test_selection_survives_filter_sort_view_and_clears_on_module_close(self):
        hub=Hub(self.store,self.store.load());self.addCleanup(hub.deleteLater)
        books=hub.bookinator;books.books=BOOKS;books.render()
        books.grid.item(0).setCheckState(Qt.CheckState.Checked)
        books.search.setText('Beta');books.select_all_bulk()
        self.assertEqual(books.bulk_selection,{'uuid-1','uuid-2'})
        books.search.clear();books.sort.setCurrentIndex(2);books.view.setCurrentText('List')
        self.assertEqual(books.bulk_selection,{'uuid-1','uuid-2'})
        self.assertEqual(books.bulk_count.text(),'2 selected')
        row=next(i for i,b in enumerate(books.visible) if b.uuid=='uuid-1')
        books.table.item(row,0).setCheckState(Qt.CheckState.Unchecked)
        self.assertEqual(books.bulk_selection,{'uuid-2'})
        hub.close_tab(1);hub.open_books();self.assertEqual(hub.bookinator.bulk_selection,set());hub.close()

    def test_preview_invalidation_and_reorder(self):
        dialog=BulkDialog(Path(self.temp.name)/'library',Path(self.temp.name)/'bulk',BOOKS)
        self.addCleanup(dialog.deleteLater)
        dialog.order.setCurrentRow(2);dialog.move(-1)
        self.assertEqual([i['uuid'] for i in dialog.identities()],['uuid-1','uuid-3','uuid-2'])
        records={b.uuid:dict(title=b.title,authors=[b.author],tags=[],series='',series_index=None,uuid=b.uuid) for b in BOOKS}
        response=dict(library_uuid='lib',records=records,errors={})
        dialog.operation.setCurrentText('Set Series');dialog.series.setText('Sequence');dialog.mode.setCurrentText('Sequential');dialog.start.setText('0');dialog.increment.setText('0.5')
        with patch.object(dialog,'request',return_value=response):dialog.preview()
        self.assertTrue(dialog.confirm.isEnabled());self.assertFalse(dialog.settings.isEnabled());self.assertEqual(dialog.store.batches(),[])
        self.assertEqual([i['desired']['series_index'] for i in dialog.batch['items']],[0,0.5,1])
        dialog.back();self.assertIsNone(dialog.batch);self.assertFalse(dialog.confirm.isEnabled());self.assertTrue(dialog.settings.isEnabled())
        dialog.close()

    def test_pending_history_deletion_requires_confirmation_and_resolution(self):
        dialog=BulkDialog(Path(self.temp.name)/'library',Path(self.temp.name)/'bulk',BOOKS);self.addCleanup(dialog.deleteLater)
        records={b.uuid:dict(title=b.title,authors=[b.author],tags=[],series='',series_index=None,uuid=b.uuid) for b in BOOKS}
        batch=plan(dialog.store,dialog.identities(),dict(library_uuid='lib',records=records,errors={}),'Add Tags',dict(tags=['New']))
        dialog.store.save(batch);dialog.refresh_history()
        with patch.object(QMessageBox,'warning',return_value=QMessageBox.StandardButton.Yes):dialog.delete_history()
        self.assertEqual(len(dialog.store.batches()),1)
        with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Yes):dialog.discard()
        with patch.object(QMessageBox,'warning',return_value=QMessageBox.StandardButton.No):dialog.delete_history()
        self.assertEqual(len(dialog.store.batches()),1)
        with patch.object(QMessageBox,'warning',return_value=QMessageBox.StandardButton.Yes):dialog.delete_history()
        self.assertEqual(dialog.store.batches(),[]);dialog.close()

    def test_completed_results_dismissal_preserves_history(self):
        dialog=BulkDialog(Path(self.temp.name)/'library',Path(self.temp.name)/'bulk',BOOKS)
        self.addCleanup(dialog.deleteLater)
        records={b.uuid:dict(title=b.title,authors=[b.author],tags=[],series='',series_index=None,uuid=b.uuid) for b in BOOKS}
        batch=plan(dialog.store,dialog.identities(),dict(library_uuid='lib',records=records,errors={}),'Add Tags',dict(tags=['New']))
        for item in batch['items']:item['state']='complete'
        dialog.store.save(batch);before=dialog.store.batches()
        dialog.batch=batch;dialog.set_phase('Completed');dialog.back()
        self.assertEqual(dialog.phase,'Ready');self.assertIn('Completed changes remain saved',dialog.status.text())
        self.assertEqual(dialog.store.batches(),before);self.assertFalse(dialog.confirm.isEnabled());dialog.close()
