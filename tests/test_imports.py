import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from PyQt6.QtWidgets import QApplication,QMessageBox
from mediainator.import_store import ImportStore,discover,atomic_json
from mediainator.import_dialog import ImportDialog
from mediainator.editor import MetadataEditor
from mediainator.catalog import Book

APP=QApplication.instance() or QApplication([])
class ImportTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.store=ImportStore(self.root/'state',self.root/'library')
        self.item=dict(source=str(self.root/'a.epub'),state='pending',operation_uuid='op',format='EPUB',title='Fallback',authors=['Unknown'],hash='hash',missing=['title','authors'],warning='',action='new')
        self.plan=dict(library_uuid='lib',catalog_token='token',items=[self.item],records=[])
    def test_discovery_nested_and_unique(self):
        (self.root/'nested').mkdir();(self.root/'nested/a.epub').write_text('a')
        self.assertEqual(discover([self.root,self.root/'nested/a.epub']),[str(self.root/'nested/a.epub')])
    def test_journal_restart_and_review_independence(self):
        path,batch=self.store.create(self.plan);self.assertEqual(len(self.store.pending()),1)
        batch['items'][0].update(state='complete',destination_uuid='book');atomic_json(path,batch)
        other=ImportStore(self.root/'state',self.root/'library');self.assertEqual(other.review_needed(),{'book'})
        other.mark_reviewed('book');self.assertFalse(other.review_needed());self.assertEqual(json.loads(path.read_text())['items'][0]['missing'],['title','authors'])
    def test_corrupt_recovery_is_not_overwritten(self):
        p=self.store.folder/'bad.json';p.write_text('{')
        with self.assertRaises(ValueError):self.store.pending()
        self.assertEqual(p.read_text(),'{')
    def test_preview_does_not_create_journal(self):
        d=ImportDialog(self.root/'library',self.root/'state');self.addCleanup(d.deleteLater)
        with patch.object(d,'request',return_value=self.plan):d.preview(['a'])
        self.assertTrue(d.confirm.isEnabled());self.assertFalse(d.store.batches())
        d.close();self.assertFalse(d.store.batches())
    def test_similar_title_requires_action(self):
        d=ImportDialog(self.root/'library',self.root/'state');self.addCleanup(d.deleteLater)
        self.item['similar']=[1];d.plan=self.plan;d.render();d.execute_batch()
        self.assertIn('Choose an action',d.status.text());self.assertFalse(d.store.batches())
    def test_attachment_collision_blocks_confirmation(self):
        d=ImportDialog(self.root/'library',self.root/'state');self.addCleanup(d.deleteLater)
        self.plan['records']=[dict(id=1,uuid='b',title='Book',authors=['A'],formats=['EPUB'])]
        d.plan=self.plan;d.render();d.choices[0][0].setCurrentText('Attach to existing book');d.choices[0][1].setCurrentIndex(1);d.execute_batch()
        self.assertIn('already has',d.status.text());self.assertFalse(d.store.batches())
    def test_discard_pending_preserves_completed(self):
        path,batch=self.store.create(self.plan);batch['items'].append(dict(self.item,state='complete',destination_uuid='b'));atomic_json(path,batch)
        d=ImportDialog(self.root/'library',self.root/'state');self.addCleanup(d.deleteLater)
        with patch('mediainator.import_dialog.QMessageBox.question',return_value=QMessageBox.StandardButton.Yes):d.discard_pending()
        result=json.loads(path.read_text());self.assertEqual([i['state'] for i in result['items']],['discarded','complete'])
    def test_running_close_requests_stop(self):
        d=ImportDialog(self.root/'library',self.root/'state');self.addCleanup(d.deleteLater);d.running=True;d.reject();self.assertTrue(d.stop_requested)
    def test_review_completeness_separate(self):
        path,batch=self.store.create(self.plan);batch['items'][0].update(state='complete',destination_uuid='b');atomic_json(path,batch)
        editor=MetadataEditor(self.root/'library',Book('library:1','Fallback','Unknown',(),(),uuid='b'),self.root/'backup');self.addCleanup(editor.deleteLater);editor.review_store=self.store
        editor.fill(dict(title='Corrected',authors=['Author'],tags=[],series='',series_index=None,comments='',cover=None,uuid='b'))
        self.assertIn('Completeness: Complete',editor.review_status.text());self.assertIn('Needs Metadata Review',editor.review_status.text())
        editor.mark_reviewed();self.assertIn('Review Status: Reviewed',editor.review_status.text())
