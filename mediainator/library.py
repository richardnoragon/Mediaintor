"""Calibre listing adapters: marked test libraries or private source snapshots."""
import json
from pathlib import Path
from PyQt6.QtCore import QObject, QProcess, QProcessEnvironment, QTimer, QThread, pyqtSignal
from .catalog import Book

MARKER = '.mediainator-disposable.json'


def check_library(root: Path) -> Path:
    root = root.resolve(strict=True)
    marker = json.loads((root / MARKER).read_text())
    if marker != {'purpose': 'mediainator-disposable-test', 'root': str(root)}:
        raise ValueError('Not a registered disposable test library.')
    if not (root / 'metadata.db').is_file():
        raise ValueError('Library metadata.db is missing.')
    # Do not allow a marked copy to redirect Calibre to live files.
    if any(p.is_symlink() for p in root.rglob('*')):
        raise ValueError('Disposable libraries cannot contain symbolic links.')
    return root


def local_path(root: Path, value: str) -> Path:
    path = Path(value).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Calibre returned a path outside the disposable library.')
    return path


def parse_catalog(root: Path, output: bytes) -> tuple[Book, ...]:
    records = json.loads(output)
    if not isinstance(records, list):
        raise ValueError('Expected a JSON catalog list.')
    books = []
    ids = set()
    for record in records:
        key = str(record['id'])
        if key in ids:
            raise ValueError('Duplicate Calibre record ID.')
        ids.add(key)
        paths = tuple((Path(p).suffix[1:].upper(), str(local_path(root, p))) for p in record.get('formats', []))
        tags = record.get('tags', [])
        if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
            raise ValueError('Invalid tag list.')
        title, author = record.get('title') or 'Untitled', record.get('authors') or 'Unknown author'
        if not isinstance(record.get('series') or '', str) or not isinstance(title, str) or not isinstance(author, str):
            raise ValueError('Invalid title or author.')
        cover = str(local_path(root, record['cover'])) if record.get('cover') else ''
        books.append(Book(f'{root}:{key}', title, author, tuple(f for f, _ in paths), tuple(tags), paths=paths, cover=cover, uuid=record.get('uuid', ''), series=record.get('series') or '', missing_fields=tuple(f for f,v in [('title',record.get('title')),('author',record.get('authors'))] if not v or not v.strip())))
    return tuple(books)


class LibraryLoader(QObject):
    loaded = pyqtSignal(object)
    failed = pyqtSignal(str)
    busy_changed = pyqtSignal(bool)
    progress = pyqtSignal(str)

    def __init__(self, root, parent=None):
        super().__init__(parent)
        self.root = root
        self.process = QProcess(self)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(30000)
        self.timer.timeout.connect(self.timeout)
        self.process.finished.connect(self.finished)
        self.process.errorOccurred.connect(self.error)
        self.active = False
        self.problem = None
        self.stopping = False

    def shutdown(self):
        self.stopping=True;self.timer.stop()
        self.cancel()
        worker=getattr(self,'worker',None)
        if worker and worker.isRunning():worker.wait()
        if self.process.state()!=QProcess.ProcessState.NotRunning:
            self.process.waitForFinished(30000)
        self.active=False

    def load(self):
        if self.stopping or self.active:
            return
        try:
            from .compatibility import require_compatible
            require_compatible()
            self.root = check_library(self.root)
        except (OSError, ValueError, RuntimeError) as exc:
            self.failed.emit(str(exc))
            return
        self.active = True
        self.problem = None
        self.busy_changed.emit(True)
        env = QProcessEnvironment.systemEnvironment()
        # Test reads must not use or mutate the user's Calibre preferences.
        env.insert('CALIBRE_CONFIG_DIRECTORY', str(self.root.parent / 'cli-config'))
        env.insert('QT_QPA_PLATFORM', 'offscreen')
        env.remove('CALIBRE_OVERRIDE_DATABASE_PATH')
        self.process.setProcessEnvironment(env)
        self.progress.emit('Reading private catalog…')
        self.process.start('/usr/bin/calibredb', ['list', '--with-library', str(self.root), '--for-machine', '--fields', 'title,authors,tags,formats,cover,uuid,series'])
        self.timer.start()

    def cancel(self):
        self.problem = 'Library loading cancelled.'
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()

    def timeout(self):
        self.problem = 'Library loading timed out. Retry when Calibre is available.'
        self.process.kill()  # Only our bounded metadata command on disposable data.

    def error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self.timer.stop()
            self.active = False
            self.busy_changed.emit(False)
            self.failed.emit(self.process.errorString())

    def finished(self, code, status):
        if self.stopping:return
        self.timer.stop()
        self.active = False
        self.busy_changed.emit(False)
        output = bytes(self.process.readAllStandardOutput())
        error = bytes(self.process.readAllStandardError()).decode(errors='replace')
        if code or status != QProcess.ExitStatus.NormalExit or self.problem:
            self.failed.emit(self.problem or error[-3000:] or 'Calibre listing failed.')
            return
        try:
            self.loaded.emit(parse_catalog(self.root, output))
        except (ValueError, TypeError, KeyError, OSError) as exc:
            self.failed.emit(f'Invalid Calibre response: {exc}')


class SnapshotWorker(QThread):
    progress = pyqtSignal(str)
    prepared = pyqtSignal(object)
    failure = pyqtSignal(str)

    def __init__(self, root, parent=None):
        super().__init__(parent)
        self.root = root

    def run(self):
        from .snapshot import Snapshot
        try:
            self.prepared.emit(Snapshot(self.root).create(self.isInterruptionRequested,self.progress.emit))
        except Exception as exc:
            self.failure.emit(str(exc))


class SnapshotLoader(LibraryLoader):
    """Runs the command against a private copy and remaps file references."""
    def __init__(self, root, parent=None):
        super().__init__(root, parent)
        self.source = Path(root).resolve()
        self.snapshot = None
        self.worker = None

    def load(self):
        if self.stopping or self.active:
            return
        from .reader import external_readers
        if external_readers(include_calibre=True):
            self.failed.emit('Close Calibre and external readers before refreshing the library, then Retry.')
            return
        self.active = True
        self.busy_changed.emit(True)
        self.worker = SnapshotWorker(self.source, self)
        self.worker.progress.connect(self.progress.emit)
        self.worker.prepared.connect(self.prepared)
        self.worker.failure.connect(self.copy_failed)
        self.worker.start()

    def cancel(self):
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
        super().cancel()

    def copy_failed(self, message):
        self.active = False
        self.busy_changed.emit(False)
        self.failed.emit(message)

    def prepared(self, snapshot):
        if self.stopping or self.worker.isInterruptionRequested():
            snapshot.close()
            self.copy_failed('Library loading cancelled.')
            return
        from .compatibility import require_compatible, CompatibilityError
        try:require_compatible()
        except CompatibilityError as exc:
            snapshot.close();self.copy_failed(str(exc));return
        from .reader import external_readers
        if external_readers(include_calibre=True):
            snapshot.close()
            self.copy_failed('Calibre or a reader opened during copying. Close it and Retry.')
            return
        if self.snapshot:
            self.snapshot.close()
        self.snapshot = snapshot
        self.root = snapshot.root
        (self.root / MARKER).write_text(json.dumps({'purpose':'mediainator-disposable-test','root':str(self.root)}))
        self.active = False
        super().load()

    def finished(self, code, status):
        if self.stopping:return
        from dataclasses import replace
        self.timer.stop()
        self.active = False
        self.busy_changed.emit(False)
        output = bytes(self.process.readAllStandardOutput())
        error = bytes(self.process.readAllStandardError()).decode(errors='replace')
        if code or status != QProcess.ExitStatus.NormalExit or self.problem:
            self.failed.emit(self.problem or error[-3000:] or 'Calibre listing failed.')
            return
        try:
            books = parse_catalog(self.root, output)
            def original(value):
                return str(local_path(self.source, str(self.source / Path(value).relative_to(self.root))))
            books = tuple(replace(b, id=b.id.replace(str(self.root), str(self.source), 1),
                                  paths=tuple((fmt, original(path)) for fmt,path in b.paths),
                                  cover=original(b.cover) if b.cover else '') for b in books)
            self.loaded.emit(books)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            self.failed.emit(f'Invalid snapshot catalog: {exc}')
