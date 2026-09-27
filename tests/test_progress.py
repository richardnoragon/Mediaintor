import hashlib,json,tempfile,unittest
from pathlib import Path
from mediainator.progress import read_progress,latest_formats,capture_rename,renamed_resume_args

class ProgressTests(unittest.TestCase):
    def test_records_and_rename(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); ebook=root/'old.epub'; ebook.write_bytes(b'unchanged ebook'); ann=root/'annotations'; ann.mkdir()
            side=ann/(hashlib.sha256(str(ebook).encode()).hexdigest()+'.json')
            self.assertEqual(read_progress(ann,ebook).issue,'missing-record')
            side.write_bytes(b'[{'); self.assertEqual(read_progress(ann,ebook).issue,'unreadable-record'); self.assertEqual(side.read_bytes(),b'[{')
            rows=[{'type':'last-read','pos_type':'epubcfi','pos':'epubcfi(/2/4)','timestamp':'2020-01-01T12:00:00+02:00'}, {'type':'last-read','pos_type':'epubcfi','pos':'epubcfi(/2/6)','timestamp':'2020-01-01T10:30:00Z'}]
            side.write_text(json.dumps(rows)); p=read_progress(ann,ebook); self.assertEqual(p.position,'epubcfi(/2/6)'); self.assertIsNone(p.percentage)
            self.assertEqual(latest_formats({'EPUB':p,'PDF':p}),('EPUB','PDF'))
            handoff=capture_rename('library','uuid','epub',ebook,ann); new=root/'renamed.epub'; ebook.rename(new)
            self.assertEqual(renamed_resume_args(handoff,'library','uuid','EPUB',new,ann),['--open-at',p.position])
            with self.assertRaises(ValueError): renamed_resume_args(handoff,'other','uuid','EPUB',new,ann)
            new.write_bytes(b'replaced')
            with self.assertRaises(ValueError): renamed_resume_args(handoff,'library','uuid','EPUB',new,ann)
    def test_untrusted_shapes(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); ebook=root/'book'; side=root/(hashlib.sha256(str(ebook).encode()).hexdigest()+'.json')
            for value in ({},[{}],[{'type':'last-read','pos_type':'epubcfi','pos':'bad'}]):
                side.write_text(json.dumps(value)); self.assertIsNone(read_progress(root,ebook).position)
            side.write_bytes(b' '*(1024*1024+1)); self.assertEqual(read_progress(root,ebook).issue,'oversize-record')

class StoreTests(unittest.TestCase):
    def test_persistent_rename_and_target_precedence(self):
        from mediainator.progress import ProgressStore
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); old=root/'old.epub'; old.write_bytes(b'book'); ann=root/'ann'; ann.mkdir()
            def write(path,pos):
                (ann/(hashlib.sha256(str(path).encode()).hexdigest()+'.json')).write_text(json.dumps([dict(type='last-read',pos_type='epubcfi',pos=pos,timestamp='2020-01-01T00:00:00Z')]))
            write(old,'epubcfi(/2/4)')
            store=ProgressStore(root/'state.json','library',ann); store.refresh('uuid','EPUB',old)
            new=root/'new.epub'; old.rename(new)
            store=ProgressStore(root/'state.json','library',ann)
            self.assertEqual(store.resume_args('uuid','EPUB',new),['--open-at','epubcfi(/2/4)'])
            self.assertEqual(store.resume_args('other','EPUB',new),[])
            write(new,'epubcfi(/2/6)')
            self.assertEqual(store.resume_args('uuid','EPUB',new),[])
            self.assertEqual(store.refresh('uuid','EPUB',new).position,'epubcfi(/2/6)')
            target=ann/(hashlib.sha256(str(new).encode()).hexdigest()+'.json'); target.write_bytes(b'bad')
            self.assertIsNone(store.refresh('uuid','EPUB',new).position)
            self.assertEqual(store.resume_args('uuid','EPUB',new),[])
            self.assertEqual(target.read_bytes(),b'bad')

class RobustnessTests(unittest.TestCase):
    def test_unsafe_files_and_unreliable_times(self):
        import os
        from mediainator.progress import timestamp,ProgressStore
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); book=root/'book'; side=root/(hashlib.sha256(str(book).encode()).hexdigest()+'.json')
            os.mkfifo(side);self.assertEqual(read_progress(root,book).issue,'unsafe-record');side.unlink()
            other=root/'other';other.write_text('[]');side.symlink_to(other)
            self.assertEqual(read_progress(root,book).issue,'unsafe-record');side.unlink()
            for value in ('bad','2020-01-01T00:00:00','9999-01-01T00:00:00Z',None):self.assertIsNone(timestamp(value))
            rows=[dict(type='last-read',pos_type='epubcfi',pos=p,timestamp='2020-01-01T00:00:00Z') for p in ('epubcfi(/2/4)','epubcfi(/2/6)')]
            side.write_text(json.dumps(rows));self.assertEqual(read_progress(root,book).issue,'ambiguous-position')
            history=root/'history';history.write_text('{bad')
            with self.assertRaises(ValueError):ProgressStore(history,'lib',root)
            self.assertEqual(history.read_text(),'{bad')
