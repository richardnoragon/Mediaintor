import json,tempfile,unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
from mediainator.catalog import Book
from mediainator.discovery import DiscoveryIndex,empty_query,warning_id
from mediainator.discovery_store import DiscoveryStore
from mediainator.review_service import acknowledge
from mediainator.duplicate_scan import scan_library

class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.books=(Book('1','Café','Author',('EPUB',),('Red','Blue'),uuid='a',series='Sequence',cover='cover',reading_status='Unread'),Book('2','CAFE\u0301',' author ',('PDF',),('Blue',),uuid='b',series='Sequence'),Book('3','Other','Unknown',('EPUB',),(),uuid='c',missing_fields=('title',)))
        self.store=DiscoveryStore(self.root/'state',self.root/'library','library-uuid',dict(profile_id='p',device_id='d'))
    def query(self,mode='all',text='',**fields):return dict(version=1,text=text,mode=mode,conditions=[dict(field=k,value=v) for k,v in fields.items()])
    def ids(self,index,q,review=False):return {b.uuid for b in index.query(q,review)}
    def test_and_or_text_unicode_status_and_formats(self):
        index=DiscoveryIndex(self.books)
        q=self.query(reading_status='Unread',series='sequence');self.assertEqual(self.ids(index,q),{'a'})
        q=self.query(mode='any',text='café',reading_status='Unread',missing_metadata='cover');self.assertEqual(self.ids(index,q),{'a','b'})
        q['formats']=['PDF'];self.assertEqual(self.ids(index,q),{'b'})
        self.assertEqual(self.ids(index,self.query(reading_status='Unknown')),{'b','c'})
        self.assertEqual(self.ids(index,self.query(text='Café Author')),set())
    def test_repeated_conditions_and_empty_modes(self):
        index=DiscoveryIndex(self.books);q=self.query(tag='Red');q['conditions'].append(dict(field='tag',value='Blue'))
        self.assertEqual(self.ids(index,q),{'a'});q['mode']='any';self.assertEqual(self.ids(index,q),{'a','b'})
        self.assertEqual(self.ids(index,self.query(mode='any')),{'a','b','c'})
    def test_acknowledgment_retains_facts_and_new_warning(self):
        warning=dict(destination_uuid='b',source_batch='batch',operation_uuid='op',title='CAFE\u0301',missing=['title'],reviewed=False)
        state=self.store.load();state['manual_review']['a']=True
        state=self.store.update(0,lambda d:d['manual_review'].update(a=True))
        index=DiscoveryIndex(self.books,state,[warning]);self.assertIn('a',self.ids(index,empty_query(),True))
        state=acknowledge(self.store,state,index,{'a','b'})
        index=DiscoveryIndex(self.books,state,[warning]);self.assertNotIn('a',self.ids(index,empty_query(),True));self.assertIn('Missing title',index.reasons['b']);self.assertFalse(any(r.startswith('Import warning') for r in index.reasons['b']))
        newer=dict(warning,operation_uuid='op2');self.assertTrue(any(r.startswith('Import warning') for r in DiscoveryIndex(self.books,state,[newer]).reasons['b']))
        fixed=replace(self.books[1],title='Corrected',cover='cover');self.assertFalse(DiscoveryIndex((fixed,),state,[warning]).reasons['b'])
    def test_missing_series_preference_persists_without_hiding_filter(self):
        book=replace(self.books[0],series='');self.assertFalse(DiscoveryIndex((book,)).reasons['a'])
        state=self.store.update(0,lambda d:d.update(review_missing_series=True))
        self.assertTrue(self.store.load()['review_missing_series']);self.assertEqual(DiscoveryIndex((book,),state).reasons['a'],['Missing series'])
        self.assertEqual(self.ids(DiscoveryIndex((book,)),self.query(missing_metadata='series')),{'a'})
    def test_saved_lifecycle_conflict_corruption_and_library_isolation(self):
        q=self.query(tag='Blue');s=self.store.update(0,lambda d:d['saved_searches'].update(one=dict(name='Blue',query=q)))
        self.assertEqual(self.store.load()['saved_searches']['one']['query'],q)
        with self.assertRaises(ValueError):self.store.update(0,lambda d:d.clear())
        with self.assertRaises(ValueError):self.store.update(s['revision'],lambda d:d['saved_searches'].update(two=dict(name='BLUE',query=q)))
        s=self.store.update(s['revision'],lambda d:d['saved_searches']['one'].update(name='Renamed',query=self.query(tag='Red')))
        self.assertEqual(self.ids(DiscoveryIndex(self.books),s['saved_searches']['one']['query']),{'a'})
        self.assertEqual(self.ids(DiscoveryIndex((replace(self.books[1],tags=('Red',)),)),s['saved_searches']['one']['query']),{'b'})
        other=DiscoveryStore(self.root/'state',self.root/'library','replacement-uuid',dict(profile_id='p',device_id='d'));self.assertFalse(other.load()['saved_searches'])
        self.store.update(s['revision'],lambda d:d['saved_searches'].pop('one'));self.assertFalse(self.store.load()['saved_searches'])
        self.store.path.write_text('{bad');before=self.store.path.read_bytes()
        with self.assertRaises(ValueError):self.store.update(3,lambda d:None)
        self.assertEqual(before,self.store.path.read_bytes())
    def test_invalid_queries_cannot_execute(self):
        for query in [None,dict(version=2),dict(self.query(),mode='nested'),self.query(missing_metadata='publisher'),dict(self.query(),formats='EPUB')]:
            with self.assertRaises(ValueError):DiscoveryIndex(self.books).query(query)

class DuplicateTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
    def book(self,n,data=b'same',fmt='EPUB',title='Book',author='Author'):
        p=self.root/f'{n}.{fmt.lower()}';p.write_bytes(data)
        return Book(str(n),title,author,(fmt,),(),uuid=str(n),paths=((fmt,str(p)),))
    def test_exact_format_boundaries_and_conservative_similar(self):
        books=[self.book(1),self.book(2,title=' book ',author='AUTHOR'),self.book(3,fmt='PDF'),self.book(4,b'else',title='Book 2'),self.book(5,title='Book',author='Other')]
        before={p.name:p.read_bytes() for p in self.root.iterdir()};result=scan_library(self.root,books)
        self.assertEqual(len(result['exact']),1);self.assertEqual({b['uuid'] for b in result['exact'][0]['books']},{'1','2','5'})
        self.assertEqual(len(result['similar']),1);self.assertEqual({b['uuid'] for b in result['similar'][0]['books']},{'1','2','3'})
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.root.iterdir()})
    def test_cancel_is_incomplete_and_progress_emitted(self):
        books=[self.book(1,b'x'*2000000),self.book(2,b'x'*2000000)];messages=[];cancel=[False]
        def progress(message):messages.append(message);cancel[0]='Hashing' in message
        result=scan_library(self.root,books,lambda:cancel[0],progress)
        self.assertTrue(result['cancelled']);self.assertFalse(result['exact']);self.assertGreaterEqual(len(messages),2)
    def test_links_outside_paths_and_changed_files_are_uncertain(self):
        books=[self.book(1),self.book(2)];p=Path(books[1].paths[0][1]);p.unlink();p.symlink_to(Path(books[0].paths[0][1]))
        result=scan_library(self.root,books);self.assertTrue(result['errors']);self.assertFalse(result['exact'])
        p.unlink();p.write_bytes(b'same')
        def progress(message):
            if 'Hashing' in message:p.write_bytes(b'changed')
        result=scan_library(self.root,books,progress=progress);self.assertTrue(result['errors']);self.assertFalse(result['exact'])
        result=scan_library(self.root,[replace(books[0],paths=(('EPUB','/etc/passwd'),))]);self.assertTrue(result['errors'])
    def test_unknown_and_provenance_cannot_create_similar_match(self):
        books=[self.book(1,author='Unknown'),self.book(2,author='Unknown')]
        self.assertFalse(scan_library(self.root,books)['similar'])
        books=[self.book(1),self.book(2)];self.assertFalse(scan_library(self.root,books,missing_titles={'1'})['similar'])

if __name__=='__main__':unittest.main()
