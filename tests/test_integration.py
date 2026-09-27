import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from mediainator.library import MARKER, check_library, parse_catalog
from mediainator.reader import Reader, ReaderError
from mediainator.settings import defaults


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        compatible=patch('mediainator.compatibility.require_compatible');compatible.start();self.addCleanup(compatible.stop)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / 'metadata.db').touch()
        (self.root / MARKER).write_text(json.dumps({'purpose':'mediainator-disposable-test','root':str(self.root)}))

    def test_unmarked_library_and_symlink_are_rejected(self):
        self.assertEqual(check_library(self.root), self.root)
        (self.root / 'linked').symlink_to('/tmp')
        with self.assertRaises(ValueError): check_library(self.root)
        (self.root / 'linked').unlink()
        (self.root / MARKER).unlink()
        with self.assertRaises(OSError): check_library(self.root)

    def test_grouping_missing_paths_and_escape(self):
        records=[{'id':1,'title':'Title','authors':'Author','tags':['Tag'],
                  'formats':[str(self.root/'book.epub'),str(self.root/'book.pdf')]}]
        books=parse_catalog(self.root,json.dumps(records).encode())
        self.assertEqual(books[0].formats,('EPUB','PDF'))
        self.assertEqual(books[0].reading_status,'Unknown')
        records[0]['formats']=['/outside/book.epub']
        with self.assertRaises(ValueError): parse_catalog(self.root,json.dumps(records).encode())

    def test_failed_response_is_not_empty_catalog(self):
        for data in [b'not json', b'{}', b'[{"id":1},{"id":1}]']:
            with self.assertRaises(ValueError): parse_catalog(self.root,data)
        self.assertEqual(parse_catalog(self.root,b'[]'),())

    def test_missing_file_does_not_launch(self):
        reader=Reader(defaults(),lambda:True)
        with patch('mediainator.reader.subprocess.Popen') as launch:
            with self.assertRaises(ReaderError): reader.launch(self.root,self.root/'missing.epub')
            launch.assert_not_called()

    def test_saved_ownership_blocks_second_reader_and_reused_pid_does_not(self):
        state=defaults();state['reader']={'pid':42,'start_time':'100'}
        reader=Reader(state,lambda:True)
        with patch('mediainator.reader.identity',return_value='100'):
            self.assertTrue(reader.active())
            with self.assertRaises(ReaderError):reader.launch(self.root,self.root/'book.epub')
        with patch('mediainator.reader.identity',return_value='101'):
            self.assertFalse(reader.active())

    def test_launch_records_profile_and_detaches(self):
        file=self.root/'book.epub';file.write_bytes(b'test fixture')
        state=defaults();reader=Reader(state,lambda:True)
        with patch('mediainator.reader.subprocess.Popen') as launch, patch('mediainator.reader.identity',return_value='200'):
            launch.return_value.pid=123
            reader.launch(self.root,file)
            self.assertTrue(launch.call_args.kwargs['start_new_session'])
            self.assertEqual(state['reader']['profile_id'],state['profile_id'])
            self.assertEqual(state['reader']['file'],str(file))
