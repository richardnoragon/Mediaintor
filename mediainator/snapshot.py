"""Coherent, private catalog snapshots. Never run Calibre on the source DB."""
import sqlite3
import tempfile
import time
from pathlib import Path


class SnapshotError(Exception):
    pass


def inventory(root, check=lambda: None):
    entries = {}
    for path in root.rglob('*'):
        check()
        if path.is_symlink():
            raise SnapshotError('Library contains symbolic links. Choose a library with local files for M1.')
        if path.is_file():
            relative = str(path.relative_to(root))
            stat = path.stat()
            entries[relative] = (stat.st_size, stat.st_mtime_ns, stat.st_ino, stat.st_ctime_ns)
    return entries


class Snapshot:
    def __init__(self, source):
        from .compatibility import require_compatible
        require_compatible()
        self.source_inventory = None
        self.source = Path(source).resolve(strict=True)
        if not (self.source / 'metadata.db').is_file():
            raise SnapshotError('Selected folder has no Calibre metadata.db.')
        self.temp = tempfile.TemporaryDirectory(prefix='mediainator-catalog-')
        self.root = Path(self.temp.name) / 'library'

    def create(self, cancelled=lambda: False, progress=lambda message: None):
        from .compatibility import require_compatible
        require_compatible()
        deadline = time.monotonic() + 120
        def check(*_):
            if cancelled():
                raise SnapshotError('Library loading cancelled; source library unchanged.')
            if time.monotonic() > deadline:
                raise SnapshotError('Library copying timed out. Retry with the library available locally.')
        try:
            check()
            progress('Inspecting library files…')
            before = inventory(self.source, check)
            self.root.mkdir()
            progress(f'Copying {len(before)} library files…')
            last_progress=time.monotonic()
            for copied,name in enumerate(before,1):
                if time.monotonic()-last_progress>=.2:
                    progress(f'Copying library files: {copied} / {len(before)}');last_progress=time.monotonic()
                if name in ('metadata.db', 'metadata.db-wal', 'metadata.db-shm', 'metadata.db-journal'):
                    continue
                target = self.root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                check()
                with (self.source / name).open('rb') as src_file, target.open('wb') as dst_file:
                    while chunk := src_file.read(1024 * 1024):
                        check()
                        dst_file.write(chunk)
            progress('Copying and checking catalog database…')
            source = sqlite3.connect((self.source / 'metadata.db').as_uri() + '?mode=ro', uri=True, timeout=2)
            dest = sqlite3.connect(self.root / 'metadata.db')
            try:
                source.backup(dest, pages=256, progress=check)
                if dest.execute('pragma quick_check').fetchone()[0] != 'ok':
                    raise SnapshotError('Library database integrity check failed.')
            finally:
                dest.close()
                source.close()
            progress('Verifying source library remained unchanged…')
            if inventory(self.source, check) != before:
                raise SnapshotError('Library changed during copying. Close Calibre and readers, then Retry.')
            self.source_inventory = before
            return self
        except Exception:
            self.close()
            raise

    def close(self):
        self.temp.cleanup()
