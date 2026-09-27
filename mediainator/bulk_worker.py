"""Serial, interruptible-between-books execution; each write uses Calibre's lock."""
import json
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal
from .bulk import FINAL, FIELDS, remaining
from .metadata import run_request
from .snapshot import Snapshot
from .reader import external_readers


class BulkWorker(QThread):
    result = pyqtSignal(object)
    failure = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, store, identities=None, batch=None, parent=None):
        super().__init__(parent)
        self.store, self.identities, self.batch = store, identities, batch

    def run(self):
        try:
            if external_readers(include_calibre=True):
                raise RuntimeError('Waiting for library access: close Calibre and all readers, then Retry.')
            recovery = self.store.folder / 'metadata-recovery'
            if self.batch is None:
                with_snapshot = Snapshot(Path(self.store.library)).create(self.isInterruptionRequested)
                try:
                    response = run_request(with_snapshot.root, dict(action='bulk_read', books=self.identities), recovery)
                finally: with_snapshot.close()
                self.result.emit(response)
                return
            batch = self.batch
            path = self.store.folder / (batch['id']+'.json')
            self.store.save(batch)
            for index in range(len(batch['items'])):
                item = batch['items'][index]
                if self.isInterruptionRequested(): break
                if item['state'] in FINAL or item['state'] in ('conflict', 'inflight'): continue
                pending = remaining(item)
                if not pending: item['state'] = 'complete'; self.store.save(batch); continue
                from .compatibility import require_compatible
                require_compatible()  # Block before recording a new write intent.
                item['state'] = 'inflight'
                item['attempt_before'] = {f: item['baseline'][f] for f in pending}
                self.store.save(batch)  # No mutation without a durable intent.
                self.progress.emit(f"Verifying book {index+1} of {len(batch['items'])}: {item['title']}")
                try:
                    response = run_request(self.store.library, dict(action='save', book=item['book'], uuid=item['uuid'],
                        library_uuid=batch['library_uuid'], baseline=item['baseline'], changes=pending, bulk_journal=str(path)), recovery)
                    if response.get('conflicts'):
                        item['state'] = 'conflict'; item['current'] = {f:v for f,v in response['current'].items() if f in FIELDS | {'title','uuid'}}; item['conflicts'] = response['conflicts']
                        self.store.save(batch)
                    else:
                        # The writer commits its verified outcome before acknowledging success.
                        batch = json.loads(path.read_text())
                except Exception as exc:
                    # May have committed. Keep the journal's in-flight/verified state intact.
                    batch = json.loads(path.read_text())
                    entry = next(i for i in batch['items'] if i['uuid'] == item['uuid'])
                    entry['errors'] = {'operation': str(exc)}
                    self.store.save(batch)
                # Continue with the updated journal objects (never stale loop references).
                if index + 1 < len(batch['items']):
                    self.batch = batch
            self.batch = batch
            self.result.emit(batch)
        except Exception as exc:
            self.failure.emit(str(exc))
