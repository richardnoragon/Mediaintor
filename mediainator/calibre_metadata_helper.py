"""Version-bound Calibre subprocess. JSON request/response files; no direct SQL writes."""
import base64
import json
import sys
# Calibre starts a fresh interpreter; keep the installed release manifest unchanged.
sys.dont_write_bytecode = True
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mediainator.metadata_rules import FIELDS, conflicts, equal, validate


def execute(request):
    from mediainator.compatibility import require_helper_version
    require_helper_version()
    from calibre.constants import __version__
    from calibre.utils.lock import singleinstance
    from calibre.db.legacy import LibraryDatabase
    from qt.core import QImage
    if __version__ != '9.2.1':
        raise ValueError('Metadata adapter validated only for Calibre 9.2.1. Revalidate before upgrading.')
    if not singleinstance('db'):
        raise RuntimeError('Waiting for library access: close Calibre and other library tools, then Retry.')
    root = Path(request['library']).resolve(strict=True)
    if not (root/'metadata.db').is_file() or any(p.is_symlink() for p in root.rglob('*')):
        raise ValueError('A local Calibre library without symlinks is required.')
    db = LibraryDatabase(str(root)); api = db.new_api; book = int(request.get('book', 0))
    def read():
        if not api.has_id(book):
            raise ValueError('Book no longer exists. Discard this draft and refresh.')
        result = {f: api.field_for(f, book) for f in FIELDS if f != 'cover'}
        for f in ('authors', 'tags'):
            result[f] = list(result[f] or [])
        result['comments'] = result['comments'] or ''
        result['series'] = result['series'] or ''
        if not result['series']:
            result['series_index'] = None
        data = api.cover(book)
        result['cover'] = base64.b64encode(data).decode() if data else None
        result['uuid'] = api.field_for('uuid', book)
        return result
    try:
        if request.get('library_uuid') and request['library_uuid'] != api.library_id:
            raise ValueError('Library identity changed. Rebuild the preview.')
        if request['action'] == 'bulk_read':
            records = {}; errors = {}
            for identity in request['books']:
                book = int(identity['book'])
                try:
                    value = read()
                    if value['uuid'] != identity['uuid']:
                        raise ValueError('Book identity changed.')
                    # Bulk history never stores unrelated covers or descriptions.
                    records[value['uuid']] = {f: value[f] for f in ('title', 'authors', 'tags', 'series', 'series_index', 'uuid')}
                except ValueError as exc:
                    errors[identity['uuid']] = str(exc)
            return {'records': records, 'errors': errors, 'library_uuid': api.library_id}
        current = read()
        if current['uuid'] != request['uuid']:
            raise ValueError('Book identity changed. Refresh before editing.')
        if request['action'] == 'read':
            return {'current': current, 'library_uuid': api.library_id}
        pending = request['changes']
        if not set(pending) <= set(FIELDS):
            raise ValueError('Unsupported metadata field.')
        proposed = dict(current, **pending)
        validate(proposed)
        # Reject bad images before *any* intended metadata mutation.
        if pending.get('cover'):
            data = base64.b64decode(pending['cover'], validate=True)
            if QImage.fromData(data).isNull():
                raise ValueError('Selected cover is not a valid image. Choose another image.')
        blocked = conflicts(request['baseline'], current, pending)
        if 'series_index' in pending and current['series'] != request['baseline']['series'] and 'series' not in pending:
            blocked.append('series')
        if request.get('bulk_journal') and {'series', 'series_index'} & set(pending):
            for f in ('series', 'series_index'):
                if not equal(f, current[f], request['baseline'][f]) and not equal(f, current[f], proposed[f]):
                    blocked.append(f)
        if blocked:
            return {'current': current, 'conflicts': sorted(set(blocked))}
        journal = None
        if request.get('bulk_journal'):
            from mediainator.bulk import BulkStore, record_result
            journal_path = Path(request['bulk_journal'])
            journal = json.loads(journal_path.read_text())
            if journal['library'] != str(root) or journal['library_uuid'] != api.library_id:
                raise ValueError('Bulk journal library identity differs.')
            entry = next(i for i in journal['items'] if i['uuid'] == current['uuid'])
            if entry['book'] != book or entry['state'] != 'inflight':
                raise ValueError('Bulk intent is not ready.')
            from mediainator.import_store import atomic_json
            entry['attempt_before'] = {f: current[f] for f in pending}
            atomic_json(journal_path, journal)
        # Treat series/name changes as a coupled conflict boundary for bulk writes.
        errors = {}; saved = []; recovery = None
        for field in FIELDS:
            if field not in pending:
                continue
            value = pending[field]
            if equal(field, current[field], value):
                saved.append(field)
                continue
            backup = None
            try:
                if field == 'cover':
                    original = api.cover(book)
                    recovery_dir = Path(request['recovery_dir'])
                    recovery_dir.mkdir(parents=True, exist_ok=True)
                    import uuid
                    backup = recovery_dir / (str(uuid.uuid4()) + '.json')
                    backup.write_text(json.dumps({'library':str(root),'book':book,'uuid':current['uuid'],'cover':current['cover']}))
                    from calibre.utils.img import save_cover_data_to
                    expected = save_cover_data_to(base64.b64decode(value)) if value else None
                    api.set_cover({book: base64.b64decode(value) if value else None})
                    actual = api.cover(book)
                    if value:
                        if not actual or QImage.fromData(actual).isNull():
                            raise ValueError('Saved cover is invalid.')
                        if actual != expected:
                            raise ValueError('Saved cover differs from the expected Calibre image conversion.')
                    elif actual is not None:
                        raise ValueError('Cover removal could not be verified.')
                elif field == 'series_index' and not proposed['series']:
                    pass  # Calibre retained index is intentionally accepted.
                else:
                    api.set_field(field, {book:value or None if field=='series' else value}, allow_case_change=False)
                now = read()
                if field != 'cover' and not equal(field, now[field], value):
                    raise ValueError('Calibre did not retain the requested value.')
                saved.append(field)
                current = now
            except Exception as exc:
                errors[field] = str(exc)
                if field == 'cover' and backup is not None:
                    try:
                        api.set_cover({book:original})
                        if api.cover(book) != original:
                            raise ValueError('Original cover bytes could not be verified.')
                        recovery = 'Cover update failed. Original cover was restored successfully. The selected replacement has been retained and can be retried.'
                    except Exception as restore_error:
                        recovery = f'Cover recovery failed: {restore_error}. Backup retained at {backup}'
                if field == 'series':
                    errors['series_index'] = 'Save the series successfully before its number.'
                    pending = {k:v for k,v in pending.items() if k!='series_index'}
        result = {'current':read(), 'saved':saved, 'errors':errors, 'recovery':recovery}
        if journal is not None:
            record_result(entry, result)
            atomic_json(journal_path, journal)
        return result
    finally:
        db.close()


if __name__ == '__main__':
    request_path, response_path = map(Path, sys.argv[1:3])
    try:
        response = execute(json.loads(request_path.read_text()))
    except Exception as exc:
        response = {'error':str(exc)}
    response_path.write_text(json.dumps(response))
