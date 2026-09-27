from unittest.mock import patch
import hashlib
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from mediainator.snapshot import Snapshot, SnapshotError, inventory


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        guard=patch('mediainator.compatibility.require_compatible');guard.start();self.addCleanup(guard.stop)
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        db=sqlite3.connect(self.root/'metadata.db')
        db.execute('create table fixture(value text)');db.execute("insert into fixture values ('original')");db.commit();db.close()
        (self.root/'book.epub').write_bytes(b'ebook fixture')

    def test_source_is_unchanged_and_copy_is_independent(self):
        before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.iterdir()}
        snap=Snapshot(self.root).create(); self.addCleanup(snap.close)
        self.assertEqual((snap.root/'book.epub').read_bytes(),b'ebook fixture')
        (snap.root/'book.epub').write_bytes(b'changed')
        db=sqlite3.connect(snap.root/'metadata.db');db.execute('delete from fixture');db.commit();db.close()
        self.assertEqual(before,{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.iterdir()})

    def test_changed_source_rejects_snapshot(self):
        initial=inventory(self.root)
        with patch('mediainator.snapshot.inventory',side_effect=[initial,{}]):
            with self.assertRaises(SnapshotError):Snapshot(self.root).create()

    def test_symlink_and_missing_database_are_rejected(self):
        (self.root/'external').symlink_to('/tmp')
        with self.assertRaises(SnapshotError):Snapshot(self.root).create()
        with self.assertRaises(SnapshotError):Snapshot(self.root/'external')
