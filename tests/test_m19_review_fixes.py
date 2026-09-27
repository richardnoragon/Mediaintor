"""Preservation and responsiveness regressions discovered in the M18/M19 audit."""
import tempfile,time,threading,unittest
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch
from PyQt6.QtWidgets import QApplication,QDialog,QComboBox
from mediainator.paper_store import PaperStore,PaperStoreError
from mediainator.paper_ui import Paperinator
from mediainator.settings import defaults,SettingsStore
from mediainator.window import Hub
from mediainator.music_scan import build_unit,ScanFile
APP=QApplication.instance() or QApplication([])

class ReviewFixes(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.state=defaults()
        self.store=PaperStore(self.root/'paper',self.state['profile_id']);self.store.initialize()

    def test_foreign_recovery_preserves_staging_and_catalog(self):
        stage=self.store._staging()/'active.part';stage.write_bytes(b'keep')
        before=self.store.path.read_bytes()
        with self.assertRaises(PaperStoreError):PaperStore(self.store.root,str(uuid4())).recover()
        self.assertEqual(stage.read_bytes(),b'keep');self.assertEqual(before,self.store.path.read_bytes())

    def test_recovery_defers_live_file_operation(self):
        stage=self.store._staging()/'active.part';stage.write_bytes(b'keep')
        with self.store._file_operation():
            self.assertIn('deferred',self.store.recover()[0]);self.assertTrue(stage.exists())
        self.store.recover();self.assertFalse(stage.exists())

    def test_combined_cancel_preserves_all_drafts(self):
        panel=Paperinator(self.state,lambda:True,self.store)
        first=panel.add_item();first.title.setText('First draft')
        second=panel.new_note();second.editor.setPlainText('Second draft')
        def cancel(dialog):
            for box in dialog.findChildren(QComboBox):box.setCurrentIndex(1)
            return QDialog.DialogCode.Rejected
        with patch('mediainator.close_review.QDialog.exec',cancel):self.assertFalse(panel.review_close())
        self.assertTrue(first.dirty());self.assertTrue(second.dirty())
        self.assertEqual(first.title.text(),'First draft')
        panel.shutdown();panel.deleteLater()

    def test_suite_cancel_preserves_music_and_paper(self):
        self.state['bookinator_open']=False
        hub=Hub(SettingsStore(self.root/'settings.json'),self.state,app_data=self.root/'data',
                paper_library=self.root/'papers',music_catalog=self.root/'music.sqlite')
        hub.open_papers();hub.open_music()
        paper=hub.paperinator.add_item();paper.title.setText('Paper draft')
        hub.musicinator.add_album();music=hub.musicinator.editor;music.title.setText('Album draft')
        with patch('mediainator.close_review.QDialog.exec',return_value=QDialog.DialogCode.Rejected):
            self.assertFalse(hub.review_close())
        self.assertTrue(paper.dirty());self.assertTrue(music.dirty())
        hub.paperinator.shutdown();hub.musicinator.shutdown();hub.deleteLater()

    def test_embedded_tags_win_over_conflicting_paths(self):
        file=ScanFile('/Wrong Artist - Wrong Album (2001)/09 - Wrong title.flac',
            tags={'album':'Tagged Album','album_artist':'Tagged Artist','title':'Tagged Track','track':'2','disc':'3','date':'2020','genre':'Jazz'})
        unit=build_unit(Path(file.path).parent,[file],{file.path:7})
        self.assertEqual((unit.title,unit.artist,unit.year),('Tagged Album','Tagged Artist',2020))
        self.assertEqual((file.title,file.number,file.disc),('Tagged Track',2,3))

    def test_cancelled_copy_keeps_original_and_leaves_no_staging(self):
        source=self.root/'source.pdf';source.write_bytes(b'original')
        with self.assertRaises(PaperStoreError):self.store._stage_copy(source,None,lambda:True)
        self.assertEqual(source.read_bytes(),b'original')
        self.assertFalse(list(self.store._staging().glob('*.part')))

    def test_import_copy_runs_off_ui_thread_and_remains_responsive(self):
        from mediainator.paper_import import ImportPlan,Proposal
        from mediainator.paper_store import fingerprint
        panel=Paperinator(self.state,lambda:True,self.store)
        source=self.root/'source.pdf';source.write_bytes(b'%PDF test content')
        size,sha=fingerprint(source)
        dialog=panel.open_import()
        dialog.preview_ready(ImportPlan([Proposal(str(source),size,sha,{'title':'Worker test'}, {})],[],{}))
        dialog.managed.setChecked(True)
        entered=threading.Event();release=threading.Event();threads=[]
        original=self.store._stage_copy
        def slow(*args,**kwargs):
            threads.append(threading.get_ident());entered.set()
            if not release.wait(5):raise RuntimeError('UI never released worker')
            return original(*args,**kwargs)
        with patch.object(self.store,'_stage_copy',side_effect=slow):
            try:
                dialog.apply()
                self.assertTrue(entered.wait(2));self.assertTrue(dialog.busy())
                APP.processEvents()
                self.assertNotEqual(threads,[threading.get_ident()])
            finally:
                release.set()
                deadline=time.monotonic()+10
                while dialog.busy() and time.monotonic()<deadline:
                    APP.processEvents();time.sleep(.01)
        self.assertFalse(dialog.busy());self.assertEqual(len(self.store.load().items),1)
        panel.shutdown();panel.deleteLater()
