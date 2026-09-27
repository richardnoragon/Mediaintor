"""Durable import intents and recovery state, separate from Calibre metadata."""
import hashlib
import json
import os
from pathlib import Path
import uuid

FINAL = {'complete', 'duplicate', 'discarded'}


def fingerprint(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def atomic_json(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.' + str(uuid.uuid4()) + '.tmp')
    try:
        with tmp.open('x') as stream:
            json.dump(value, stream, indent=2); stream.flush(); os.fsync(stream.fileno())
        os.replace(tmp, path)
        fd = os.open(path.parent, os.O_RDONLY)
        try: os.fsync(fd)
        finally: os.close(fd)
    finally:
        tmp.unlink(missing_ok=True)


def discover(paths):
    found = []
    seen = set()
    for value in paths:
        path = Path(value).absolute()
        candidates = sorted(path.rglob('*')) if path.is_dir() and not path.is_symlink() else [path]
        for entry in candidates:
            if entry.is_dir(): continue
            key = str(entry)
            if key not in seen:
                seen.add(key); found.append(key)
    return found


class ImportStore:
    def __init__(self, folder, library):
        self.library = str(Path(library).resolve())
        self.folder = Path(folder) / hashlib.sha256(self.library.encode()).hexdigest()[:20]
        self.folder.mkdir(parents=True, exist_ok=True)

    def batches(self):
        result=[]
        for path in sorted(self.folder.glob('*.json')):
            data=json.loads(path.read_text())
            if data.get('schema') != 1 or data.get('library') != self.library:
                raise ValueError('Import recovery record has an unsupported schema or library identity.')
            if not isinstance(data.get('items'),list) or any(not isinstance(i,dict) or not {'source','state','operation_uuid'}<=set(i) for i in data['items']):
                raise ValueError('Import recovery record is incomplete. Existing file was preserved.')
            result.append((path,data))
        return result

    def create(self, plan):
        batch=dict(schema=1,library=self.library,library_uuid=plan['library_uuid'],catalog_token=plan.get('catalog_token'),id=str(uuid.uuid4()),items=plan['items'])
        path=self.folder/(batch['id']+'.json');atomic_json(path,batch)
        return path,batch

    def pending(self):
        return [(p,b) for p,b in self.batches() if any(i['state'] not in FINAL for i in b['items'])]

    def review_records(self):
        """Migrate book review state before any history cleanup; idempotent and atomic."""
        from .activity import locked
        folder = self.folder / 'book-review'
        path = folder / 'state.json'
        with locked(folder):
            try:
                data = json.loads(path.read_text())
            except FileNotFoundError:
                data = dict(schema=1, library=self.library, entries={})
            if (not isinstance(data, dict) or data.get('schema') != 1 or data.get('library') != self.library
                    or not isinstance(data.get('entries'), dict)):
                raise ValueError('Book review state is damaged or unsupported. History was preserved.')
            for entry in data['entries'].values():
                if not isinstance(entry, dict) or not {'destination_uuid','missing','reviewed'} <= entry.keys():
                    raise ValueError('Book review state is incomplete. History was preserved.')
            changed = False
            for _, batch in self.batches():
                for index, item in enumerate(batch['items']):
                    if item['state'] != 'complete' or not item.get('missing') or not item.get('destination_uuid'): continue
                    key = batch['id'] + ':' + item['operation_uuid']
                    if key not in data['entries']:
                        data['entries'][key] = dict(destination_uuid=item['destination_uuid'], library_uuid=batch.get('library_uuid'),
                            missing=item['missing'], title=item.get('title'), reviewed=bool(item.get('reviewed')),
                            source_batch=batch['id'], operation_uuid=item['operation_uuid'])
                        changed = True
            if changed or not path.exists():
                atomic_json(path, data)
                if json.loads(path.read_text()) != data:
                    raise ValueError('Book review migration could not be verified. History was preserved.')
            return list(data['entries'].values())

    def review_needed(self):
        return {i['destination_uuid'] for i in self.review_records() if not i['reviewed']}

    def mark_reviewed(self, book_uuid):
        self.review_records()
        from .activity import locked
        folder=self.folder/'book-review';path=folder/'state.json'
        with locked(folder):
            data=json.loads(path.read_text())
            for item in data['entries'].values():
                if item['destination_uuid']==book_uuid:item['reviewed']=True
            atomic_json(path,data)

    def delete_history(self, path):
        """Storage guard for future confirmed UI deletion; never delete pending work."""
        path=Path(path)
        if path.parent.resolve()!=self.folder.resolve() or path.is_symlink():
            raise ValueError('History path is not owned by this library.')
        batch=next((b for p,b in self.batches() if p.resolve()==path.resolve()),None)
        if batch is None:raise ValueError('Import history record is unavailable.')
        if any(i['state'] not in FINAL for i in batch['items']):
            raise ValueError('Review and discard pending imports before deleting history.')
        self.review_records()  # A failed migration blocks destructive cleanup.
        path.unlink()
