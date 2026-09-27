"""Paper-inator profile library storage (SQLite + managed files). No Qt.

Each Hub profile owns one library directory:

    <library>/library.sqlite   structured records, Markdown notes, personal research state
    <library>/files/            managed copies of documents and attachments
    <library>/files/.staging/   temporary copies being verified (never user data)

Referenced files stay where they are: nothing here moves, renames, overwrites or
deletes a referenced file, and an original from which a managed copy was made is
never touched. Normal removal is a recoverable trash batch in the database; managed
files are deleted only by an explicit, previewed permanent deletion, coordinated by an
operation record so an interruption can be completed on the next start.

Every database change runs in one IMMEDIATE transaction that rolls back completely on
error. Item metadata and note content carry revisions so edits made elsewhere are
detected before they are overwritten.
"""
from contextlib import closing, contextmanager
import hashlib
import fcntl
import json
import os
from pathlib import Path
import shutil
import sqlite3
from uuid import UUID, uuid4

from .movie_store import now
from .paper_model import (
    CONTAINER_KINDS, FILE_ROLES, FLAG_FIELDS, HANDLING, ITEM_TYPES, NOTE_KINDS, OBJECT_TYPES,
    PROJECT_STATUSES, READING, RELATIONS, SORTS, SYMMETRIC, VERSION_KINDS, Connection, Container, DocumentFile,
    KnowledgeItem, Library, Note, SavedSearch, TrashBatch, Version, clean_doi, default_criteria, safe_filename,
)

SCHEMA = 1
KIND = 'paper'
TEXT_LIMIT = 20000
NOTE_LIMIT = 1_000_000
DOC_TEXT_LIMIT = 2_000_000
LIST_LIMIT = 200
CHUNK = 1024 * 1024


class PaperStoreError(Exception):
    pass


class ConflictError(PaperStoreError):
    """The record changed since the draft was loaded. `current` holds the stored object."""
    def __init__(self, message, current=None):
        super().__init__(message)
        self.current = current


class ChangedFileError(PaperStoreError):
    """A located file differs from the one recorded (content fingerprint mismatch)."""


_DDL = """
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS items(
    id TEXT PRIMARY KEY, type TEXT NOT NULL, title TEXT NOT NULL, authors TEXT NOT NULL DEFAULT '[]', year INTEGER,
    venue TEXT NOT NULL DEFAULT '', abstract TEXT NOT NULL DEFAULT '', keywords TEXT NOT NULL DEFAULT '[]',
    doi TEXT NOT NULL DEFAULT '', identifiers TEXT NOT NULL DEFAULT '[]', url TEXT NOT NULL DEFAULT '',
    tags TEXT NOT NULL DEFAULT '[]', reading TEXT NOT NULL DEFAULT 'Unread', handling TEXT NOT NULL DEFAULT 'Inbox',
    needs_review INTEGER NOT NULL DEFAULT 0, key_reference INTEGER NOT NULL DEFAULT 0, favorite INTEGER NOT NULL DEFAULT 0,
    preferred_version_id TEXT, revision INTEGER NOT NULL DEFAULT 0, added_at TEXT NOT NULL, modified_at TEXT NOT NULL,
    opened_at TEXT NOT NULL DEFAULT '', trash_batch TEXT);
CREATE TABLE IF NOT EXISTS versions(
    id TEXT PRIMARY KEY, item_id TEXT NOT NULL REFERENCES items(id) ON DELETE CASCADE, label TEXT NOT NULL,
    kind TEXT NOT NULL, year INTEGER, doi TEXT NOT NULL DEFAULT '', venue TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '', position INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS files(
    id TEXT PRIMARY KEY, version_id TEXT NOT NULL REFERENCES versions(id) ON DELETE CASCADE, mode TEXT NOT NULL,
    path TEXT NOT NULL UNIQUE, original_path TEXT NOT NULL DEFAULT '', size INTEGER, sha256 TEXT NOT NULL DEFAULT '',
    role TEXT NOT NULL DEFAULT 'document', label TEXT NOT NULL DEFAULT '', added_at TEXT NOT NULL,
    position INTEGER NOT NULL DEFAULT 0, trash_batch TEXT);
CREATE TABLE IF NOT EXISTS doc_text(
    file_id TEXT PRIMARY KEY REFERENCES files(id) ON DELETE CASCADE, text TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS notes(
    id TEXT PRIMARY KEY, title TEXT NOT NULL DEFAULT '', body TEXT NOT NULL DEFAULT '', kind TEXT NOT NULL DEFAULT 'Note',
    item_id TEXT REFERENCES items(id) ON DELETE SET NULL, revision INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL, modified_at TEXT NOT NULL, trash_batch TEXT);
CREATE TABLE IF NOT EXISTS containers(
    id TEXT PRIMARY KEY, kind TEXT NOT NULL, name TEXT NOT NULL, description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'Active', created_at TEXT NOT NULL, modified_at TEXT NOT NULL, trash_batch TEXT);
CREATE TABLE IF NOT EXISTS memberships(
    container_id TEXT NOT NULL REFERENCES containers(id) ON DELETE CASCADE, object_type TEXT NOT NULL,
    object_id TEXT NOT NULL, added_at TEXT NOT NULL, PRIMARY KEY(container_id, object_type, object_id));
CREATE TABLE IF NOT EXISTS connections(
    id TEXT PRIMARY KEY, source_type TEXT NOT NULL, source_id TEXT NOT NULL, relation TEXT NOT NULL,
    target_type TEXT NOT NULL, target_id TEXT NOT NULL, comment TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL,
    UNIQUE(source_type, source_id, relation, target_type, target_id));
CREATE TABLE IF NOT EXISTS saved_searches(
    id TEXT PRIMARY KEY, name TEXT NOT NULL, criteria TEXT NOT NULL, modified_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS trash_batches(
    id TEXT PRIMARY KEY, label TEXT NOT NULL, created_at TEXT NOT NULL, state TEXT NOT NULL,
    objects TEXT NOT NULL DEFAULT '[]', purge_files TEXT NOT NULL DEFAULT '[]');
CREATE INDEX IF NOT EXISTS versions_item ON versions(item_id);
CREATE INDEX IF NOT EXISTS files_version ON files(version_id);
CREATE INDEX IF NOT EXISTS files_sha ON files(sha256);
CREATE INDEX IF NOT EXISTS notes_item ON notes(item_id);
CREATE INDEX IF NOT EXISTS memberships_object ON memberships(object_type, object_id);
CREATE INDEX IF NOT EXISTS connections_source ON connections(source_type, source_id);
CREATE INDEX IF NOT EXISTS connections_target ON connections(target_type, target_id)
"""

ITEM_FIELDS = ('type', 'title', 'authors', 'year', 'venue', 'abstract', 'keywords', 'doi', 'identifiers', 'url', 'tags')
VERSION_FIELDS = ('label', 'kind', 'year', 'doi', 'venue', 'notes')
NOTE_FIELDS = ('title', 'body', 'kind', 'item_id')
CRITERIA_KEYS = set(default_criteria())


# ----------------------------------------------------------------------------- validation
def _text(value, name, required=False, limit=TEXT_LIMIT, multiline=False):
    if value is None:
        value = ''
    if not isinstance(value, str):
        raise PaperStoreError(f'Invalid {name}.')
    value = value.strip('\n ') if multiline else value.strip()
    if required and not value:
        raise PaperStoreError(f'{name[0].upper() + name[1:]} is required.')
    allowed = '\n\t' if multiline else '\t'
    if len(value) > limit or any(ord(c) < 32 and c not in allowed for c in value):
        raise PaperStoreError(f'{name[0].upper() + name[1:]} contains unsupported characters or is too long.')
    return value


def _names(values, name, limit=300):
    if isinstance(values, str) or not isinstance(values, (list, tuple)):
        raise PaperStoreError(f'Invalid {name}.')
    result, seen = [], set()
    for value in values:
        value = _text(value, name, limit=limit)
        if value and value.casefold() not in seen:
            seen.add(value.casefold())
            result.append(value)
    if len(result) > LIST_LIMIT:
        raise PaperStoreError(f'Too many {name}.')
    return result


def _year(value, name='year'):
    if value is None or value == '':
        return None
    if type(value) is not int or not 1000 <= value <= 2200:
        raise PaperStoreError(f'{name[0].upper() + name[1:]} must be a whole number from 1000 to 2200.')
    return value


def _doi(value):
    value = _text(value, 'DOI', limit=300)
    if not value:
        return ''
    cleaned = clean_doi(value)
    if not cleaned:
        raise PaperStoreError('DOI must look like 10.1234/example (a doi.org link is also accepted).')
    return cleaned


def _url(value):
    value = _text(value, 'URL', limit=2000)
    if value and not value.lower().startswith(('http://', 'https://', 'ftp://')):
        raise PaperStoreError('URL must start with http://, https:// or ftp://.')
    return value


def _identifiers(values):
    if isinstance(values, (str, dict)) or not isinstance(values, (list, tuple)):
        raise PaperStoreError('Invalid identifiers.')
    result, seen = [], set()
    for entry in values:
        if not isinstance(entry, (list, tuple)) or len(entry) != 2:
            raise PaperStoreError('Each identifier needs a scheme and a value.')
        scheme = _text(entry[0], 'identifier scheme', required=True, limit=40)
        value = _text(entry[1], 'identifier value', required=True, limit=300)
        if (scheme.casefold(), value.casefold()) not in seen:
            seen.add((scheme.casefold(), value.casefold())); result.append([scheme, value])
    if len(result) > 50:
        raise PaperStoreError('Too many identifiers.')
    return result


def validate_item(fields):
    """Normalise user-entered item fields; raise PaperStoreError on invalid input.
    Only the title is required; missing information is reported, never invented."""
    unknown = set(fields) - set(ITEM_FIELDS)
    if unknown:
        raise PaperStoreError('Unknown item fields: ' + ', '.join(sorted(unknown)))
    out = {}
    for key in ITEM_FIELDS:
        if key not in fields:
            continue
        value = fields[key]
        if key == 'type':
            if value not in ITEM_TYPES:
                raise PaperStoreError('Unsupported item type.')
            out[key] = value
        elif key == 'title':
            out[key] = _text(value, 'title', required=True, limit=1000)
        elif key == 'year':
            out[key] = _year(value)
        elif key == 'venue':
            out[key] = _text(value, 'journal, conference or publisher', limit=500)
        elif key == 'abstract':
            out[key] = _text(value, 'abstract', multiline=True, limit=50000)
        elif key == 'doi':
            out[key] = _doi(value)
        elif key == 'url':
            out[key] = _url(value)
        elif key == 'identifiers':
            out[key] = _identifiers(value)
        elif key == 'authors':
            out[key] = _names(value, 'authors')
        else:
            out[key] = _names(value, key, limit=120)
    return out


def validate_version(fields):
    unknown = set(fields) - set(VERSION_FIELDS)
    if unknown:
        raise PaperStoreError('Unknown version fields: ' + ', '.join(sorted(unknown)))
    kind = fields.get('kind') or 'Other version'
    if kind not in VERSION_KINDS:
        raise PaperStoreError('Unsupported version type.')
    return dict(label=_text(fields.get('label') or kind, 'version label', required=True, limit=200), kind=kind,
                year=_year(fields.get('year')), doi=_doi(fields.get('doi', '')),
                venue=_text(fields.get('venue', ''), 'version venue', limit=500),
                notes=_text(fields.get('notes', ''), 'version notes', multiline=True))


def validate_note(fields):
    unknown = set(fields) - set(NOTE_FIELDS)
    if unknown:
        raise PaperStoreError('Unknown note fields: ' + ', '.join(sorted(unknown)))
    out = {}
    if 'title' in fields:
        out['title'] = _text(fields['title'], 'note title', limit=500)
    if 'body' in fields:
        body = fields['body'] if fields['body'] is not None else ''
        if not isinstance(body, str) or len(body) > NOTE_LIMIT or '\x00' in body:
            raise PaperStoreError('Note text is invalid or too long.')
        out['body'] = body.replace('\r\n', '\n')
    if 'kind' in fields:
        if fields['kind'] not in NOTE_KINDS:
            raise PaperStoreError('Unsupported note type.')
        out['kind'] = fields['kind']
    if 'item_id' in fields:
        out['item_id'] = fields['item_id'] or None
    return out


def validate_criteria(criteria):
    if not isinstance(criteria, dict) or set(criteria) - CRITERIA_KEYS:
        raise PaperStoreError('Invalid search criteria.')
    out = default_criteria()
    out.update(criteria)
    if not isinstance(out['text'], str) or len(out['text']) > 1000:
        raise PaperStoreError('Invalid search text.')
    for key, allowed in (('types', ITEM_TYPES), ('reading', READING), ('handling', HANDLING), ('flags', tuple(FLAG_FIELDS))):
        if not isinstance(out[key], list) or any(v not in allowed for v in out[key]):
            raise PaperStoreError('Invalid search filter.')
    if not isinstance(out['tags'], list) or not all(isinstance(t, str) and len(t) <= 120 for t in out['tags']):
        raise PaperStoreError('Invalid tag filter.')
    if out['container'] is not None and not isinstance(out['container'], str):
        raise PaperStoreError('Invalid project or collection filter.')
    if out['sort'] not in SORTS:
        raise PaperStoreError('Invalid sort order.')
    return out


def canonical(path):
    """Absolute, symlink-resolved path used as a referenced file's identity."""
    return str(Path(os.path.abspath(os.path.expanduser(str(path)))).resolve())


def fingerprint(path, cancelled=None):
    """(size, sha256) of a file's content."""
    digest = hashlib.sha256()
    size = 0
    with open(path, 'rb') as stream:
        while True:
            if cancelled is not None and cancelled():
                raise PaperStoreError('Stopped.')
            block = stream.read(CHUNK)
            if not block:
                break
            size += len(block); digest.update(block)
    return size, digest.hexdigest()


# ----------------------------------------------------------------------------- store
class PaperStore:
    def __init__(self, root, profile_id):
        try:
            UUID(profile_id)
        except (TypeError, ValueError, AttributeError) as exc:
            raise PaperStoreError('Invalid profile identity.') from exc
        self.root = Path(root)
        self.path = self.root / 'library.sqlite'
        self.files_dir = self.root / 'files'
        self.profile_id = profile_id
        self._uuid = None
        self._fts = None

    # -- connection handling -----------------------------------------------------
    def _connect(self):
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            db = sqlite3.connect(str(self.path), timeout=5, isolation_level=None)
        except (OSError, sqlite3.Error) as exc:
            raise PaperStoreError(f'Cannot open the Paper-inator library: {exc}') from exc
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        return db

    @contextmanager
    def _write(self):
        with closing(self._connect()) as db:
            try:
                db.execute('BEGIN IMMEDIATE')
                self._ensure(db)
                yield db
                db.execute('COMMIT')
            except sqlite3.OperationalError as exc:
                self._rollback(db)
                if 'locked' in str(exc) or 'busy' in str(exc):
                    raise PaperStoreError('The library is busy. Wait a moment and retry.') from exc
                raise PaperStoreError(f'Library write failed; nothing was changed: {exc}') from exc
            except sqlite3.Error as exc:
                self._rollback(db)
                raise PaperStoreError(f'Library write failed; nothing was changed: {exc}') from exc
            except BaseException:
                self._rollback(db)
                raise

    @staticmethod
    def _rollback(db):
        try:
            db.execute('ROLLBACK')
        except sqlite3.Error:
            pass

    def _check_meta(self, db):
        row = db.execute("SELECT value FROM meta WHERE key='schema'").fetchone()
        if row is None or not row[0].isdigit():
            raise PaperStoreError('The Paper-inator library is damaged (no schema version). It was not changed.')
        if int(row[0]) != SCHEMA:
            raise PaperStoreError('The Paper-inator library was created by a newer or unsupported version. It was not changed.')
        kind = db.execute("SELECT value FROM meta WHERE key='kind'").fetchone()
        if kind is None or kind[0] != KIND:
            raise PaperStoreError('This file is not a Paper-inator library. It was not changed.')
        owner = db.execute("SELECT value FROM meta WHERE key='profile_id'").fetchone()
        if owner is None or owner[0] != self.profile_id:
            raise PaperStoreError('This Paper-inator library belongs to another profile. It was not opened or changed.')

    def _ensure(self, db):
        existing = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if 'meta' in existing:
            self._check_meta(db)
            return
        if existing:
            raise PaperStoreError('This file is not a Paper-inator library. It was not changed.')
        for statement in _DDL.split(';'):
            if statement.strip():
                db.execute(statement)
        try:
            db.execute("CREATE VIRTUAL TABLE doc_fts USING fts5(text, file_id UNINDEXED, tokenize='unicode61 remove_diacritics 2')")
            fts = '1'
        except sqlite3.OperationalError:
            fts = '0'          # SQLite without FTS5: document text search falls back to a plain scan
        for key, value in (('schema', str(SCHEMA)), ('kind', KIND), ('library_uuid', str(uuid4())),
                           ('profile_id', self.profile_id), ('created_at', now()), ('fts', fts)):
            db.execute('INSERT INTO meta VALUES(?, ?)', (key, value))

    def initialize(self):
        with self._write():
            pass
        self.recover()
        return self.library_uuid()

    def library_uuid(self):
        if self._uuid is None:
            db = self._read()
            if db is None:
                return None
            with closing(db):
                row = db.execute("SELECT value FROM meta WHERE key='library_uuid'").fetchone()
            self._uuid = row[0] if row else None
        return self._uuid

    def _read(self):
        """A validated read connection, or None when the library does not exist yet."""
        if not self.path.exists():
            return None
        db = self._connect()
        try:
            names = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not names:
                db.close()            # a first write that rolled back leaves an empty file
                return None
            if 'meta' not in names:
                raise PaperStoreError('This file is not a Paper-inator library.')
            self._check_meta(db)
        except sqlite3.Error as exc:
            db.close()
            raise PaperStoreError(f'Cannot read the Paper-inator library: {exc}') from exc
        except PaperStoreError:
            db.close()
            raise
        return db

    def _has_fts(self, db):
        if self._fts is None:
            row = db.execute("SELECT value FROM meta WHERE key='fts'").fetchone()
            self._fts = bool(row and row[0] == '1')
        return self._fts

    def signature(self):
        """Cheap change detector for refreshing an open library."""
        try:
            return tuple((p.name, p.stat().st_size, p.stat().st_mtime_ns)
                         for p in (self.path, self.path.with_name(self.path.name + '-wal')) if p.exists())
        except OSError:
            return None

    # -- reading --------------------------------------------------------------------
    def load(self):
        """One consistent snapshot of the whole profile library."""
        try:
            db = self._read()
            if db is None:
                return Library()
            with closing(db):
                db.execute('BEGIN')
                try:
                    return self._load(db)
                finally:
                    db.execute('COMMIT')
        except sqlite3.Error as exc:
            raise PaperStoreError(f'Cannot read the Paper-inator library: {exc}') from exc

    def _abs(self, row):
        return str(self.root / row['path']) if row['mode'] == 'managed' else row['path']

    def _load(self, db):
        text_ids = {r[0] for r in db.execute('SELECT file_id FROM doc_text')}
        files = {}
        for f in db.execute('SELECT * FROM files ORDER BY position, added_at'):
            files.setdefault(f['version_id'], []).append(DocumentFile(
                f['id'], f['version_id'], f['mode'], self._abs(f), f['original_path'], f['size'], f['sha256'], f['role'],
                f['label'], f['id'] in text_ids, f['trash_batch'] is not None))
        versions = {}
        for v in db.execute('SELECT * FROM versions ORDER BY position, label'):
            versions.setdefault(v['item_id'], []).append(Version(
                v['id'], v['item_id'], v['label'], v['kind'], v['year'], v['doi'], v['venue'], v['notes'],
                tuple(files.get(v['id'], ()))))
        items, trashed_items = [], []
        for i in db.execute('SELECT * FROM items'):
            item = KnowledgeItem(
                i['id'], i['type'], i['title'], tuple(json.loads(i['authors'])), i['year'], i['venue'], i['abstract'],
                tuple(json.loads(i['keywords'])), i['doi'], tuple(tuple(x) for x in json.loads(i['identifiers'])), i['url'],
                tuple(json.loads(i['tags'])), i['reading'], i['handling'], bool(i['needs_review']), bool(i['key_reference']),
                bool(i['favorite']), i['preferred_version_id'], tuple(versions.get(i['id'], ())), i['revision'],
                i['added_at'], i['modified_at'], i['opened_at'], i['trash_batch'])
            (trashed_items if item.trash_batch else items).append(item)
        notes, trashed_notes = [], []
        for n in db.execute('SELECT * FROM notes'):
            note = Note(n['id'], n['title'], n['body'], n['kind'], n['item_id'], n['revision'], n['created_at'],
                        n['modified_at'], n['trash_batch'])
            (trashed_notes if note.trash_batch else notes).append(note)
        members = {}
        for m in db.execute('SELECT * FROM memberships ORDER BY added_at'):
            members.setdefault(m['container_id'], []).append((m['object_type'], m['object_id']))
        containers, trashed_containers = [], []
        for c in db.execute('SELECT * FROM containers ORDER BY name COLLATE NOCASE'):
            container = Container(c['id'], c['kind'], c['name'], c['description'], c['status'],
                                  tuple(members.get(c['id'], ())), c['created_at'], c['modified_at'], c['trash_batch'])
            (trashed_containers if container.trash_batch else containers).append(container)
        # Memberships of objects in trash stay stored (restore brings them back) but are hidden.
        active = {('item', i.id) for i in items} | {('note', n.id) for n in notes}
        containers = [Container(c.id, c.kind, c.name, c.description, c.status,
                                tuple(m for m in c.members if m in active), c.created_at, c.modified_at, None)
                      for c in containers]
        connections = tuple(Connection(c['id'], c['source_type'], c['source_id'], c['relation'], c['target_type'],
                                       c['target_id'], c['comment'], c['created_at'])
                            for c in db.execute('SELECT * FROM connections ORDER BY created_at'))
        searches = tuple(SavedSearch(s['id'], s['name'], json.loads(s['criteria']), s['modified_at'])
                         for s in db.execute('SELECT * FROM saved_searches ORDER BY name COLLATE NOCASE'))
        trash = tuple(TrashBatch(t['id'], t['label'], t['created_at'], t['state'],
                                 tuple(tuple(o) for o in json.loads(t['objects'])))
                      for t in db.execute('SELECT * FROM trash_batches ORDER BY created_at DESC'))
        return Library(tuple(items), tuple(notes), tuple(containers), connections, searches, trash,
                       tuple(trashed_items), tuple(trashed_notes), tuple(trashed_containers))

    def get_item(self, item_id):
        item = self.load().item(item_id)
        if item is None:
            raise PaperStoreError('This item is no longer in the library.')
        return item

    def get_note(self, note_id):
        note = self.load().note(note_id)
        if note is None:
            raise PaperStoreError('This note is no longer in the library.')
        return note

    def known_files(self):
        """sha256 → (item id, title, trashed) and canonical referenced path → item id, for duplicate checks."""
        db = self._read()
        if db is None:
            return {}, {}
        with closing(db):
            rows = db.execute('''SELECT f.sha256, f.path, f.mode, f.original_path, f.trash_batch AS ftrash, i.id, i.title,
                                        i.trash_batch AS itrash FROM files f JOIN versions v ON v.id=f.version_id
                                        JOIN items i ON i.id=v.item_id''').fetchall()
        by_hash, by_path = {}, {}
        for r in rows:
            if r['sha256']:
                by_hash.setdefault(r['sha256'], (r['id'], r['title'], bool(r['ftrash'] or r['itrash'])))
            if r['mode'] == 'referenced':
                by_path[r['path']] = r['id']
        return by_hash, by_path

    def search_documents(self, text):
        """Ids of active items whose extracted document text contains every search word."""
        words = [w for w in ''.join(c if c.isalnum() else ' ' for c in (text or '')).split() if w][:12]
        if not words:
            return frozenset()
        db = self._read()
        if db is None:
            return frozenset()
        base = '''SELECT DISTINCT v.item_id FROM files f JOIN versions v ON v.id=f.version_id JOIN items i ON i.id=v.item_id
                  WHERE f.trash_batch IS NULL AND i.trash_batch IS NULL AND f.id IN ({})'''
        with closing(db):
            try:
                if self._has_fts(db):
                    query = ' AND '.join('"' + w.replace('"', '') + '"*' for w in words)
                    ids = base.format('SELECT file_id FROM doc_fts WHERE doc_fts MATCH ?')
                    return frozenset(r[0] for r in db.execute(ids, (query,)))
                where = ' AND '.join('lower(text) LIKE ?' for _ in words)
                ids = base.format(f'SELECT file_id FROM doc_text WHERE {where}')
                return frozenset(r[0] for r in db.execute(ids, tuple(f'%{w.lower()}%' for w in words)))
            except sqlite3.Error:
                return frozenset()

    # -- items ----------------------------------------------------------------------------
    @staticmethod
    def _item_row(fields):
        dump = lambda key: json.dumps(fields.get(key, []), ensure_ascii=False)
        return dict(type=fields.get('type', 'Research paper'), title=fields['title'], authors=dump('authors'),
                    year=fields.get('year'), venue=fields.get('venue', ''), abstract=fields.get('abstract', ''),
                    keywords=dump('keywords'), doi=fields.get('doi', ''), identifiers=dump('identifiers'),
                    url=fields.get('url', ''), tags=dump('tags'))

    def _insert_item(self, db, fields, states=None):
        states = states or {}
        item_id = str(uuid4())
        stamp = now()
        reading = states.get('reading', 'Unread'); handling = states.get('handling', 'Inbox')
        if reading not in READING or handling not in HANDLING:
            raise PaperStoreError('Invalid reading or handling state.')
        db.execute('''INSERT INTO items(id,type,title,authors,year,venue,abstract,keywords,doi,identifiers,url,tags,reading,
            handling,needs_review,key_reference,favorite,revision,added_at,modified_at)
            VALUES(:id,:type,:title,:authors,:year,:venue,:abstract,:keywords,:doi,:identifiers,:url,:tags,:reading,:handling,
            :needs_review,:key_reference,:favorite,0,:at,:at)''',
                   dict(self._item_row(fields), id=item_id, at=stamp, reading=reading, handling=handling,
                        needs_review=int(bool(states.get('needs_review'))), key_reference=int(bool(states.get('key_reference'))),
                        favorite=int(bool(states.get('favorite')))))
        return item_id

    def add_item(self, fields, versions=(), states=None):
        """Create a Knowledge Item, optionally with versions (dicts of version fields, no files)."""
        fields = validate_item(dict(fields))
        if 'title' not in fields:
            raise PaperStoreError('Title is required.')
        with self._write() as db:
            item_id = self._insert_item(db, fields, states)
            for position, version in enumerate(versions):
                self._insert_version(db, item_id, version, position)
        return item_id

    def _active_item(self, db, item_id):
        row = db.execute('SELECT * FROM items WHERE id=?', (item_id,)).fetchone()
        if row is None or row['trash_batch'] is not None:
            raise PaperStoreError('This item is no longer in the library (it may be in Trash).')
        return row

    def _item_object(self, db, item_id):
        return self._load(db).item(item_id)

    def update_item(self, item_id, expected_revision, fields):
        """Save changed metadata fields. Raises ConflictError if the item changed meanwhile."""
        fields = validate_item(dict(fields))
        if not fields:
            return
        with self._write() as db:
            row = self._active_item(db, item_id)
            if expected_revision is not None and row['revision'] != expected_revision:
                raise ConflictError('This item was changed elsewhere since you opened it.', self._item_object(db, item_id))
            current = dict(type=row['type'], title=row['title'], authors=json.loads(row['authors']), year=row['year'],
                           venue=row['venue'], abstract=row['abstract'], keywords=json.loads(row['keywords']),
                           doi=row['doi'], identifiers=json.loads(row['identifiers']), url=row['url'], tags=json.loads(row['tags']))
            merged = dict(current, **fields)
            db.execute('''UPDATE items SET type=:type, title=:title, authors=:authors, year=:year, venue=:venue,
                abstract=:abstract, keywords=:keywords, doi=:doi, identifiers=:identifiers, url=:url, tags=:tags,
                revision=revision+1, modified_at=:at WHERE id=:id''', dict(self._item_row(merged), id=item_id, at=now()))

    def set_states(self, item_ids, reading=None, handling=None, flags=None):
        """Change reading progress, handling state and/or flags of the given items. The
        dimensions are independent: nothing here changes a dimension that was not given."""
        item_ids = list(dict.fromkeys(item_ids))
        if not item_ids:
            raise PaperStoreError('No items selected.')
        if reading is not None and reading not in READING:
            raise PaperStoreError('Invalid reading progress.')
        if handling is not None and handling not in HANDLING:
            raise PaperStoreError('Invalid library handling state.')
        flags = dict(flags or {})
        if set(flags) - set(FLAG_FIELDS) or any(type(v) is not bool for v in flags.values()):
            raise PaperStoreError('Invalid flags.')
        with self._write() as db:
            stamp = now()
            for item_id in item_ids:
                self._active_item(db, item_id)
                if reading is not None:
                    db.execute('UPDATE items SET reading=?, modified_at=? WHERE id=?', (reading, stamp, item_id))
                if handling is not None:
                    db.execute('UPDATE items SET handling=?, modified_at=? WHERE id=?', (handling, stamp, item_id))
                for name, value in flags.items():
                    db.execute(f'UPDATE items SET {FLAG_FIELDS[name]}=?, modified_at=? WHERE id=?', (int(value), stamp, item_id))

    def change_tags(self, item_ids, add=(), remove=()):
        add = _names(list(add), 'tags', limit=120)
        remove = {t.casefold() for t in _names(list(remove), 'tags', limit=120)}
        if not add and not remove:
            raise PaperStoreError('No tag changes given.')
        with self._write() as db:
            for item_id in dict.fromkeys(item_ids):
                row = self._active_item(db, item_id)
                tags = [t for t in json.loads(row['tags']) if t.casefold() not in remove]
                have = {t.casefold() for t in tags}
                tags += [t for t in add if t.casefold() not in have]
                if len(tags) > LIST_LIMIT:
                    raise PaperStoreError('Too many tags.')
                db.execute('UPDATE items SET tags=?, modified_at=? WHERE id=?', (json.dumps(tags, ensure_ascii=False), now(), item_id))

    def mark_opened(self, item_id):
        with self._write() as db:
            self._active_item(db, item_id)
            db.execute('UPDATE items SET opened_at=? WHERE id=?', (now(), item_id))

    # -- versions ------------------------------------------------------------------------
    def _insert_version(self, db, item_id, fields, position=None):
        fields = validate_version(dict(fields))
        if position is None:
            position = db.execute('SELECT COALESCE(MAX(position)+1,0) FROM versions WHERE item_id=?', (item_id,)).fetchone()[0]
        version_id = str(uuid4())
        db.execute('INSERT INTO versions VALUES(:id,:item,:label,:kind,:year,:doi,:venue,:notes,:position)',
                   dict(fields, id=version_id, item=item_id, position=position))
        if db.execute('SELECT preferred_version_id FROM items WHERE id=?', (item_id,)).fetchone()[0] is None:
            db.execute('UPDATE items SET preferred_version_id=? WHERE id=?', (version_id, item_id))
        return version_id

    def add_version(self, item_id, fields):
        with self._write() as db:
            self._active_item(db, item_id)
            return self._insert_version(db, item_id, fields)

    def _version_item(self, db, version_id):
        row = db.execute('SELECT item_id FROM versions WHERE id=?', (version_id,)).fetchone()
        if row is None:
            raise PaperStoreError('This version is no longer in the library.')
        self._active_item(db, row[0])
        return row[0]

    def update_version(self, version_id, fields):
        fields = validate_version(dict(fields))
        with self._write() as db:
            self._version_item(db, version_id)
            db.execute('UPDATE versions SET label=:label, kind=:kind, year=:year, doi=:doi, venue=:venue, notes=:notes WHERE id=:id',
                       dict(fields, id=version_id))

    def remove_version(self, version_id):
        """Remove an empty version record. Versions with files keep their files and
        research context; remove (trash) the files first."""
        with self._write() as db:
            item_id = self._version_item(db, version_id)
            if db.execute('SELECT 1 FROM files WHERE version_id=?', (version_id,)).fetchone():
                raise PaperStoreError('This version still has files (active or in Trash). Remove them and empty them '
                                      'from Trash first; nothing was changed.')
            db.execute('DELETE FROM versions WHERE id=?', (version_id,))
            row = db.execute('SELECT preferred_version_id FROM items WHERE id=?', (item_id,)).fetchone()
            if row[0] == version_id:
                other = db.execute('SELECT id FROM versions WHERE item_id=? ORDER BY position LIMIT 1', (item_id,)).fetchone()
                db.execute('UPDATE items SET preferred_version_id=? WHERE id=?', (other[0] if other else None, item_id))

    def set_preferred_version(self, item_id, version_id):
        """Choose the default version for opening and citations. Metadata is not changed."""
        with self._write() as db:
            self._active_item(db, item_id)
            if db.execute('SELECT 1 FROM versions WHERE id=? AND item_id=?', (version_id, item_id)).fetchone() is None:
                raise PaperStoreError('This version does not belong to the item.')
            db.execute('UPDATE items SET preferred_version_id=? WHERE id=?', (version_id, item_id))

    # -- files ----------------------------------------------------------------------------
    def _staging(self):
        folder = self.files_dir / '.staging'
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def _stage_copy(self, source, expected_sha, cancelled=None):
        """Copy a source into staging and verify its content. Returns the staging path."""
        staged = self._staging() / f'{uuid4()}.part'
        try:
            with open(source, 'rb') as reader, open(staged, 'wb') as writer:
                while True:
                    if cancelled and cancelled():
                        raise PaperStoreError('Copy cancelled; nothing was imported.')
                    block = reader.read(CHUNK)
                    if not block:
                        break
                    writer.write(block)
                writer.flush(); os.fsync(writer.fileno())
            size, sha = fingerprint(staged, cancelled)
        except BaseException:
            staged.unlink(missing_ok=True)       # our own temporary copy, never the original
            raise
        if expected_sha and sha != expected_sha:
            staged.unlink(missing_ok=True)
            raise PaperStoreError('The copied file did not match the original; nothing was imported. Try again.')
        return staged, size, sha

    def _managed_target(self, file_id, source_name):
        suffix = Path(source_name).suffix.lower()[:10]
        stem = safe_filename(Path(source_name).stem, 60)
        return Path('files') / file_id[:2] / f'{file_id}-{stem}{suffix}'

    @contextmanager
    def _file_operation(self, blocking=True):
        # Validate before creating a lock or touching any managed content.
        db = self._read()
        if db is not None:
            db.close()
        self.root.mkdir(parents=True, exist_ok=True)
        with (self.root / '.file-operation.lock').open('a') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
            except BlockingIOError:
                yield False
                return
            try:
                yield True
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    @contextmanager
    def _placed_file(self, source, mode, expected=None, cancelled=None):
        with self._file_operation():
            with self._placed_file_locked(source, mode, expected, cancelled) as row:
                yield row

    @contextmanager
    def _placed_file_locked(self, source, mode, expected=None, cancelled=None):
        """Prepare a file for insertion; yields a dict for the files row. For managed
        copies the verified copy is moved into place just before commit and removed
        again (it is our own copy) if the transaction fails."""
        source = canonical(source)
        if not os.path.isfile(source):
            raise PaperStoreError(f'The file is no longer available: {source}')
        size, sha = fingerprint(source, cancelled)
        if expected is not None and (size, sha) != tuple(expected):
            raise PaperStoreError(f'The file changed since the preview: {source}. Build the preview again.')
        file_id = str(uuid4())
        if mode == 'referenced':
            yield dict(id=file_id, mode=mode, path=source, original_path=source, size=size, sha256=sha)
            return
        if mode != 'managed':
            raise PaperStoreError('Choose Managed copy or Referenced file.')
        staged, size, sha = self._stage_copy(source, sha, cancelled)
        relative = self._managed_target(file_id, source)
        final = self.root / relative
        moved = False
        try:
            row = dict(id=file_id, mode=mode, path=str(relative), original_path=source, size=size, sha256=sha)
            final.parent.mkdir(parents=True, exist_ok=True)
            os.replace(staged, final)
            moved = True
            yield row
        except BaseException:
            # The transaction did not commit: remove our copy (never the original).
            if moved:
                final.unlink(missing_ok=True)
            staged.unlink(missing_ok=True)
            raise

    def _insert_file(self, db, version_id, row, role='document', label='', text=''):
        if role not in FILE_ROLES:
            raise PaperStoreError('Unsupported file role.')
        if row['mode'] == 'referenced' and db.execute('SELECT 1 FROM files WHERE path=?', (row['path'],)).fetchone():
            raise PaperStoreError(f'This file is already in the library: {row["path"]}')
        position = db.execute('SELECT COALESCE(MAX(position)+1,0) FROM files WHERE version_id=?', (version_id,)).fetchone()[0]
        db.execute('INSERT INTO files VALUES(?,?,?,?,?,?,?,?,?,?,?,NULL)', (
            row['id'], version_id, row['mode'], row['path'], row['original_path'], row['size'], row['sha256'], role,
            _text(label, 'file label', limit=300), now(), position))
        self._store_text(db, row['id'], text)
        return row['id']

    def _store_text(self, db, file_id, text):
        if not text or not isinstance(text, str):
            return
        text = text[:DOC_TEXT_LIMIT].replace('\x00', '')
        db.execute('INSERT OR REPLACE INTO doc_text VALUES(?,?)', (file_id, text))
        if self._has_fts(db):
            db.execute('DELETE FROM doc_fts WHERE file_id=?', (file_id,))
            db.execute('INSERT INTO doc_fts(text, file_id) VALUES(?,?)', (text, file_id))

    def import_document(self, source, mode, *, item_fields=None, states=None, item_id=None, version_id=None,
                        version_fields=None, expected=None, text='', role='document', allow_duplicate=False,
                        cancelled=None):
        """Add one confirmed document in one transaction and return (item id, version id, file id).

        Create a new item from `item_fields`, or add to `item_id` — either into an existing
        `version_id` or as a new version from `version_fields`. `expected` is the (size, sha256)
        seen in the preview; a changed or already catalogued file is refused.
        """
        if item_id is None:
            item_fields = validate_item(dict(item_fields or {}))
            if 'title' not in item_fields:
                raise PaperStoreError('Title is required.')
        by_hash, by_path = self.known_files()
        with self._placed_file(source, mode, expected, cancelled) as row:
            if row['sha256'] in by_hash and not allow_duplicate:
                other = by_hash[row['sha256']]
                raise PaperStoreError(f'An identical file is already in the library ("{other[1]}"'
                                      + (', in Trash' if other[2] else '') + '). Nothing was imported.')
            if row['original_path'] in by_path:
                raise PaperStoreError(f'This file is already referenced by the library: {row["original_path"]}')
            with self._write() as db:
                if item_id is None:
                    item_id = self._insert_item(db, item_fields, states)
                else:
                    self._active_item(db, item_id)
                if version_id is None:
                    version_id = self._insert_version(db, item_id, version_fields or dict(label='Document', kind='Other version'))
                elif db.execute('SELECT 1 FROM versions WHERE id=? AND item_id=?', (version_id, item_id)).fetchone() is None:
                    raise PaperStoreError('The chosen version does not belong to the item.')
                self._insert_file(db, version_id, row, role, text=text)
                db.execute('UPDATE items SET modified_at=? WHERE id=?', (now(), item_id))
            return item_id, version_id, row['id']

    def add_file(self, version_id, source, mode, role='attachment', label='', text=''):
        """Attach a document or supplementary file to an existing version."""
        with self._placed_file(source, mode) as row:
            with self._write() as db:
                self._version_item(db, version_id)
                clash = db.execute('SELECT 1 FROM files WHERE sha256=? AND version_id=? AND trash_batch IS NULL',
                                   (row['sha256'], version_id)).fetchone()
                if clash:
                    raise PaperStoreError('An identical file is already attached to this version.')
                return self._insert_file(db, version_id, row, role, label, text)

    def store_text(self, file_id, text):
        with self._write() as db:
            if db.execute('SELECT 1 FROM files WHERE id=?', (file_id,)).fetchone() is None:
                raise PaperStoreError('This file is no longer in the library.')
            self._store_text(db, file_id, text)

    def relocate_file(self, file_id, new_path, accept_changed=False):
        """Point a referenced file at the location the user chose after it was moved.
        A file with different content is refused unless the user explicitly accepts it."""
        new_path = canonical(new_path)
        if not os.path.isfile(new_path):
            raise PaperStoreError('The chosen file does not exist.')
        size, sha = fingerprint(new_path)
        with self._write() as db:
            row = db.execute('SELECT * FROM files WHERE id=?', (file_id,)).fetchone()
            if row is None:
                raise PaperStoreError('This file is no longer in the library.')
            if row['mode'] != 'referenced':
                raise PaperStoreError('Managed copies live inside the library and cannot be relocated.')
            if row['sha256'] and sha != row['sha256'] and not accept_changed:
                raise ChangedFileError('The chosen file differs from the recorded one (different content). Existing '
                                       'annotations and search text may not match it.')
            clash = db.execute('SELECT 1 FROM files WHERE path=? AND id<>?', (new_path, file_id)).fetchone()
            if clash:
                raise PaperStoreError('This file is already in the library.')
            db.execute('UPDATE files SET path=?, size=?, sha256=? WHERE id=?', (new_path, size, sha, file_id))
            if sha != row['sha256']:
                db.execute('DELETE FROM doc_text WHERE file_id=?', (file_id,))
                if self._has_fts(db):
                    db.execute('DELETE FROM doc_fts WHERE file_id=?', (file_id,))

    def update_file(self, file_id, label=None, role=None):
        with self._write() as db:
            if db.execute('SELECT 1 FROM files WHERE id=?', (file_id,)).fetchone() is None:
                raise PaperStoreError('This file is no longer in the library.')
            if label is not None:
                db.execute('UPDATE files SET label=? WHERE id=?', (_text(label, 'file label', limit=300), file_id))
            if role is not None:
                if role not in FILE_ROLES:
                    raise PaperStoreError('Unsupported file role.')
                db.execute('UPDATE files SET role=? WHERE id=?', (role, file_id))

    # -- notes -------------------------------------------------------------------------------
    def add_note(self, fields):
        fields = validate_note(dict(fields))
        note_id = str(uuid4())
        with self._write() as db:
            if fields.get('item_id'):
                self._active_item(db, fields['item_id'])
            stamp = now()
            db.execute('INSERT INTO notes VALUES(?,?,?,?,?,0,?,?,NULL)', (
                note_id, fields.get('title', ''), fields.get('body', ''), fields.get('kind', 'Note'), fields.get('item_id'),
                stamp, stamp))
        return note_id

    def update_note(self, note_id, expected_revision, fields):
        fields = validate_note(dict(fields))
        if not fields:
            return
        with self._write() as db:
            row = db.execute('SELECT * FROM notes WHERE id=?', (note_id,)).fetchone()
            if row is None or row['trash_batch'] is not None:
                raise PaperStoreError('This note is no longer in the library (it may be in Trash).')
            if expected_revision is not None and row['revision'] != expected_revision:
                raise ConflictError('This note was changed elsewhere since you opened it.', self._load(db).note(note_id))
            if fields.get('item_id'):
                self._active_item(db, fields['item_id'])
            merged = dict(title=row['title'], body=row['body'], kind=row['kind'], item_id=row['item_id'], **{})
            merged.update(fields)
            db.execute('UPDATE notes SET title=?, body=?, kind=?, item_id=?, revision=revision+1, modified_at=? WHERE id=?',
                       (merged['title'], merged['body'], merged['kind'], merged['item_id'], now(), note_id))

    # -- projects and collections -----------------------------------------------------------
    def add_container(self, kind, name, description='', status='Active'):
        if kind not in CONTAINER_KINDS:
            raise PaperStoreError('Unsupported grouping.')
        name = _text(name, 'name', required=True, limit=200)
        description = _text(description, 'description', multiline=True)
        if status not in PROJECT_STATUSES:
            raise PaperStoreError('Unsupported project status.')
        container_id = str(uuid4())
        with self._write() as db:
            self._unique_name(db, kind, name)
            stamp = now()
            db.execute('INSERT INTO containers VALUES(?,?,?,?,?,?,?,NULL)', (container_id, kind, name, description, status,
                                                                              stamp, stamp))
        return container_id

    @staticmethod
    def _unique_name(db, kind, name, exclude=None):
        clash = db.execute('SELECT id FROM containers WHERE kind=? AND name=? COLLATE NOCASE AND trash_batch IS NULL AND id IS NOT ?',
                           (kind, name, exclude)).fetchone()
        if clash:
            raise PaperStoreError(f'A {kind} with this name already exists.')

    def _active_container(self, db, container_id):
        row = db.execute('SELECT * FROM containers WHERE id=?', (container_id,)).fetchone()
        if row is None or row['trash_batch'] is not None:
            raise PaperStoreError('This project or collection is no longer in the library.')
        return row

    def update_container(self, container_id, name=None, description=None, status=None):
        with self._write() as db:
            row = self._active_container(db, container_id)
            name = row['name'] if name is None else _text(name, 'name', required=True, limit=200)
            description = row['description'] if description is None else _text(description, 'description', multiline=True)
            status = row['status'] if status is None else status
            if status not in PROJECT_STATUSES:
                raise PaperStoreError('Unsupported project status.')
            self._unique_name(db, row['kind'], name, container_id)
            db.execute('UPDATE containers SET name=?, description=?, status=?, modified_at=? WHERE id=?',
                       (name, description, status, now(), container_id))

    def add_members(self, container_id, members):
        """Add items and notes to a project or collection without duplicating them."""
        with self._write() as db:
            row = self._active_container(db, container_id)
            added = 0
            for kind, object_id in members:
                if kind not in ('item', 'note') or (row['kind'] == 'collection' and kind != 'item'):
                    raise PaperStoreError('Collections hold items; projects hold items and notes.')
                self._active_object(db, kind, object_id)
                added += db.execute('INSERT OR IGNORE INTO memberships VALUES(?,?,?,?)',
                                    (container_id, kind, object_id, now())).rowcount
            db.execute('UPDATE containers SET modified_at=? WHERE id=?', (now(), container_id))
            return added

    def remove_members(self, container_id, members):
        """Take items or notes out of a project or collection. The items stay in the library."""
        with self._write() as db:
            self._active_container(db, container_id)
            for kind, object_id in members:
                db.execute('DELETE FROM memberships WHERE container_id=? AND object_type=? AND object_id=?',
                           (container_id, kind, object_id))
            db.execute('UPDATE containers SET modified_at=? WHERE id=?', (now(), container_id))

    # -- connections ---------------------------------------------------------------------------
    def _active_object(self, db, kind, object_id):
        table = {'item': 'items', 'note': 'notes', 'project': 'containers'}.get(kind)
        if table is None:
            raise PaperStoreError('Unsupported connection end.')
        row = db.execute(f'SELECT trash_batch FROM {table} WHERE id=?', (object_id,)).fetchone()
        if row is None or row[0] is not None:
            raise PaperStoreError(f'This {"project or collection" if kind == "project" else kind} is no longer in the library.')

    def add_connection(self, source, relation, target, comment=''):
        """Connect two objects: source (type, id) —relation→ target (type, id)."""
        (source_type, source_id), (target_type, target_id) = source, target
        if relation not in RELATIONS:
            raise PaperStoreError('Unsupported relationship type.')
        if source_type not in OBJECT_TYPES or target_type not in OBJECT_TYPES:
            raise PaperStoreError('Unsupported connection end.')
        if (source_type, source_id) == (target_type, target_id):
            raise PaperStoreError('An object cannot be connected to itself.')
        comment = _text(comment, 'comment', multiline=True, limit=2000)
        connection_id = str(uuid4())
        with self._write() as db:
            self._active_object(db, source_type, source_id)
            self._active_object(db, target_type, target_id)
            self._no_duplicate(db, source, relation, target)
            db.execute('INSERT INTO connections VALUES(?,?,?,?,?,?,?,?)', (
                connection_id, source_type, source_id, relation, target_type, target_id, comment, now()))
        return connection_id

    @staticmethod
    def _no_duplicate(db, source, relation, target, exclude=None):
        pairs = [(source, target)] + ([(target, source)] if relation in SYMMETRIC else [])
        for (st, si), (tt, ti) in pairs:
            if db.execute('''SELECT 1 FROM connections WHERE source_type=? AND source_id=? AND relation=? AND target_type=?
                             AND target_id=? AND id IS NOT ?''', (st, si, relation, tt, ti, exclude)).fetchone():
                raise PaperStoreError('This connection already exists.')

    def update_connection(self, connection_id, relation=None, comment=None, reverse=False):
        with self._write() as db:
            row = db.execute('SELECT * FROM connections WHERE id=?', (connection_id,)).fetchone()
            if row is None:
                raise PaperStoreError('This connection no longer exists.')
            relation = row['relation'] if relation is None else relation
            if relation not in RELATIONS:
                raise PaperStoreError('Unsupported relationship type.')
            comment = row['comment'] if comment is None else _text(comment, 'comment', multiline=True, limit=2000)
            source, target = (row['source_type'], row['source_id']), (row['target_type'], row['target_id'])
            if reverse:
                source, target = target, source
            self._no_duplicate(db, source, relation, target, connection_id)
            db.execute('''UPDATE connections SET source_type=?, source_id=?, relation=?, target_type=?, target_id=?, comment=?
                          WHERE id=?''', (*source, relation, *target, comment, connection_id))

    def remove_connection(self, connection_id):
        """Remove one connection (an explicit edit). The connected objects are unchanged."""
        with self._write() as db:
            if db.execute('DELETE FROM connections WHERE id=?', (connection_id,)).rowcount != 1:
                raise PaperStoreError('This connection no longer exists.')

    # -- saved searches --------------------------------------------------------------------------
    def save_search(self, name, criteria, search_id=None):
        name = _text(name, 'search name', required=True, limit=120)
        criteria = validate_criteria(dict(criteria))
        with self._write() as db:
            clash = db.execute('SELECT id FROM saved_searches WHERE name=? COLLATE NOCASE AND id IS NOT ?',
                               (name, search_id)).fetchone()
            if clash:
                raise PaperStoreError('A saved search with this name already exists.')
            payload = json.dumps(criteria, ensure_ascii=False)
            if search_id is None:
                search_id = str(uuid4())
                db.execute('INSERT INTO saved_searches VALUES(?,?,?,?)', (search_id, name, payload, now()))
            elif db.execute('UPDATE saved_searches SET name=?, criteria=?, modified_at=? WHERE id=?',
                            (name, payload, now(), search_id)).rowcount != 1:
                raise PaperStoreError('This saved search no longer exists.')
        return search_id

    def delete_search(self, search_id):
        with self._write() as db:
            if db.execute('DELETE FROM saved_searches WHERE id=?', (search_id,)).rowcount != 1:
                raise PaperStoreError('This saved search no longer exists.')

    # -- trash, restore and permanent deletion ---------------------------------------------------
    _TABLES = {'item': 'items', 'note': 'notes', 'project': 'containers', 'file': 'files'}

    def _expand(self, db, objects):
        """The objects a removal affects: items take their source notes along."""
        result = []
        for kind, object_id in objects:
            table = self._TABLES.get(kind)
            if table is None:
                raise PaperStoreError('This kind of object cannot be moved to Trash.')
            row = db.execute(f'SELECT trash_batch FROM {table} WHERE id=?', (object_id,)).fetchone()
            if row is None or row[0] is not None:
                raise PaperStoreError('Something selected is no longer in the library (it may already be in Trash).')
            if (kind, object_id) not in result:
                result.append((kind, object_id))
            if kind == 'item':
                for note in db.execute('SELECT id FROM notes WHERE item_id=? AND trash_batch IS NULL', (object_id,)):
                    if ('note', note[0]) not in result:
                        result.append(('note', note[0]))
        return result

    def _files_of(self, db, objects, include_trashed=False):
        """File rows belonging to the objects (items → all versions; files themselves)."""
        rows = []
        extra = '' if include_trashed else ' AND f.trash_batch IS NULL'
        for kind, object_id in objects:
            if kind == 'item':
                rows += db.execute('SELECT f.* FROM files f JOIN versions v ON v.id=f.version_id WHERE v.item_id=?' + extra,
                                   (object_id,)).fetchall()
            elif kind == 'file':
                rows += db.execute('SELECT * FROM files WHERE id=?', (object_id,)).fetchall()
        return rows

    def _describe(self, db, objects, files):
        keys = set(objects)
        labels = []
        for kind, object_id in objects:
            if kind == 'item':
                row = db.execute('SELECT title FROM items WHERE id=?', (object_id,)).fetchone()
            elif kind == 'note':
                row = db.execute("SELECT CASE WHEN title<>'' THEN title ELSE substr(body,1,60) END FROM notes WHERE id=?",
                                 (object_id,)).fetchone()
            elif kind == 'project':
                row = db.execute("SELECT kind || ': ' || name FROM containers WHERE id=?", (object_id,)).fetchone()
            else:
                row = db.execute("SELECT CASE WHEN label<>'' THEN label ELSE path END FROM files WHERE id=?", (object_id,)).fetchone()
            labels.append((kind, object_id, (row[0] if row else '') or 'Untitled'))
        connections = [c for c in db.execute('SELECT * FROM connections')
                       if (c['source_type'], c['source_id']) in keys or (c['target_type'], c['target_id']) in keys]
        memberships = [m for m in db.execute('SELECT * FROM memberships') if (m['object_type'], m['object_id']) in keys
                       or ('project', m['container_id']) in keys]
        managed = [f for f in files if f['mode'] == 'managed']
        referenced = [f for f in files if f['mode'] == 'referenced']
        states = [dict(title=r['title'], reading=r['reading'], handling=r['handling'])
                  for kind, object_id in objects if kind == 'item'
                  for r in db.execute('SELECT title, reading, handling FROM items WHERE id=?', (object_id,))]
        return dict(objects=labels, connections=len(connections), memberships=len(memberships),
                    managed_files=[self._abs(f) for f in managed], managed_bytes=sum(f['size'] or 0 for f in managed),
                    referenced_files=[f['path'] for f in referenced], states=states)

    def trash_preview(self, objects):
        """What a normal removal would put in Trash. Nothing is changed."""
        db = self._read()
        if db is None:
            raise PaperStoreError('The library does not exist yet.')
        with closing(db):
            expanded = self._expand(db, objects)
            return self._describe(db, expanded, self._files_of(db, expanded))

    def trash(self, objects, label=''):
        """Move objects to recoverable Trash as one batch. Connections, memberships, reading
        state and notes are kept and come back on restore. No file is moved or deleted."""
        with self._write() as db:
            expanded = self._expand(db, objects)
            if not expanded:
                raise PaperStoreError('Nothing selected.')
            batch = str(uuid4())
            for kind, object_id in expanded:
                db.execute(f'UPDATE {self._TABLES[kind]} SET trash_batch=? WHERE id=?', (batch, object_id))
            first = self._describe(db, expanded[:1], [])['objects'][0][2]
            label = _text(label, 'label', limit=300) or (first + (f' and {len(expanded) - 1} more' if len(expanded) > 1 else ''))
            db.execute('INSERT INTO trash_batches VALUES(?,?,?,?,?,?)',
                       (batch, label, now(), 'trashed', json.dumps(expanded), '[]'))
        return batch

    def restore(self, batch_id):
        """Bring a Trash batch back with all its associations."""
        with self._write() as db:
            row = db.execute('SELECT * FROM trash_batches WHERE id=?', (batch_id,)).fetchone()
            if row is None:
                raise PaperStoreError('This Trash entry no longer exists.')
            if row['state'] != 'trashed':
                raise PaperStoreError('Permanent deletion of this entry has started and cannot be undone.')
            for kind, object_id in json.loads(row['objects']):
                table = self._TABLES[kind]
                db.execute(f'UPDATE {table} SET trash_batch=NULL WHERE id=? AND trash_batch=?', (object_id, batch_id))
                if kind == 'project':
                    container = db.execute('SELECT kind, name FROM containers WHERE id=?', (object_id,)).fetchone()
                    clash = db.execute('''SELECT 1 FROM containers WHERE kind=? AND name=? COLLATE NOCASE
                                          AND trash_batch IS NULL AND id<>?''', (container[0], container[1], object_id)).fetchone()
                    if clash:
                        db.execute('UPDATE containers SET name=? WHERE id=?', (container[1] + ' (restored)', object_id))
            db.execute('DELETE FROM trash_batches WHERE id=?', (batch_id,))

    def purge_preview(self, batch_id):
        """Exactly what permanent deletion of a Trash batch removes. Nothing is changed."""
        db = self._read()
        if db is None:
            raise PaperStoreError('The library does not exist yet.')
        with closing(db):
            row = db.execute('SELECT * FROM trash_batches WHERE id=?', (batch_id,)).fetchone()
            if row is None:
                raise PaperStoreError('This Trash entry no longer exists.')
            objects = [tuple(o) for o in json.loads(row['objects'])]
            return self._describe(db, objects, self._files_of(db, objects, include_trashed=True))

    def _contained(self, relative):
        """Absolute path of a managed file, only if it lies inside this library's files folder."""
        target = (self.root / relative).resolve()
        files = self.files_dir.resolve()
        if files not in target.parents:
            return None
        return target

    def purge(self, batch_id):
        """Permanently delete a Trash batch. Database records go first in one transaction
        together with an operation record listing the managed files; the files are then
        deleted. Referenced files are never deleted. Returns a list of problems (empty
        when everything was removed); remaining files are retried by recover()."""
        with self._write() as db:
            row = db.execute('SELECT * FROM trash_batches WHERE id=?', (batch_id,)).fetchone()
            if row is None:
                raise PaperStoreError('This Trash entry no longer exists.')
            if row['state'] != 'trashed':
                raise PaperStoreError('Permanent deletion of this entry is already in progress.')
            objects = [tuple(o) for o in json.loads(row['objects'])]
            files = self._files_of(db, objects, include_trashed=True)
            doomed = []
            for f in files:
                if f['mode'] != 'managed':
                    continue
                # A managed path is unique to its row; re-check before listing it for deletion.
                if db.execute('SELECT COUNT(*) FROM files WHERE path=?', (f['path'],)).fetchone()[0] == 1:
                    doomed.append(f['path'])
            keys = set(objects)
            for kind, object_id in objects:
                if kind == 'item':
                    db.execute('DELETE FROM items WHERE id=?', (object_id,))
                elif kind == 'note':
                    db.execute('DELETE FROM notes WHERE id=?', (object_id,))
                elif kind == 'project':
                    db.execute('DELETE FROM containers WHERE id=?', (object_id,))
                else:
                    db.execute('DELETE FROM files WHERE id=?', (object_id,))
            for kind, object_id in keys:
                if kind in ('item', 'note', 'project'):
                    db.execute('DELETE FROM connections WHERE (source_type=? AND source_id=?) OR (target_type=? AND target_id=?)',
                               (kind, object_id, kind, object_id))
                if kind in ('item', 'note'):
                    db.execute('DELETE FROM memberships WHERE object_type=? AND object_id=?', (kind, object_id))
            if self._has_fts(db):
                db.execute('DELETE FROM doc_fts WHERE file_id NOT IN (SELECT id FROM files)')
            db.execute('UPDATE items SET preferred_version_id=NULL WHERE preferred_version_id IS NOT NULL AND '
                       'preferred_version_id NOT IN (SELECT id FROM versions)')
            db.execute("UPDATE trash_batches SET state='purging', purge_files=? WHERE id=?", (json.dumps(doomed), batch_id))
        return self._finish_purge(batch_id)

    def _finish_purge(self, batch_id):
        problems = []
        db = self._read()
        if db is None:
            return problems
        with closing(db):
            row = db.execute('SELECT purge_files FROM trash_batches WHERE id=?', (batch_id,)).fetchone()
        if row is None:
            return problems
        remaining = []
        for relative in json.loads(row[0]):
            target = self._contained(relative)
            if target is None:
                problems.append(f'Skipped a path outside the library files folder: {relative}')
                continue
            try:
                target.unlink(missing_ok=True)
            except OSError as exc:
                remaining.append(relative); problems.append(f'{target}: {exc}')
        with self._write() as db:
            if remaining:
                db.execute('UPDATE trash_batches SET purge_files=? WHERE id=?', (json.dumps(remaining), batch_id))
            else:
                db.execute('DELETE FROM trash_batches WHERE id=?', (batch_id,))
        return problems

    def recover(self):
        # Never clean another profile, unsupported catalog, or a live import.
        db = self._read()
        if db is None:
            return []
        db.close()
        with self._file_operation(blocking=False) as acquired:
            if not acquired:
                return ['File operation active; recovery deferred.']
            return self._recover_locked()

    def _recover_locked(self):
        """Complete interrupted work after a crash: finish permanent deletions that were
        confirmed and committed, and remove leftover staging copies (our own temporary
        files). Returns a list of messages."""
        messages = []
        staging = self.files_dir / '.staging'
        if staging.is_dir():
            for part in staging.glob('*.part'):
                try:
                    part.unlink()
                except OSError as exc:
                    messages.append(f'Could not remove a temporary copy {part}: {exc}')
        db = self._read()
        if db is None:
            return messages
        with closing(db):
            pending = [r[0] for r in db.execute("SELECT id FROM trash_batches WHERE state='purging'")]
        for batch_id in pending:
            messages += self._finish_purge(batch_id)
        return messages

    def orphans(self):
        """Managed-looking files inside files/ that no record refers to (e.g. after a crash
        between placing a copy and committing). Reported only; never deleted."""
        db = self._read()
        if db is None or not self.files_dir.is_dir():
            if db is not None:
                db.close()
            return []
        with closing(db):
            known = {r[0] for r in db.execute("SELECT path FROM files WHERE mode='managed'")}
        found = []
        for path in self.files_dir.rglob('*'):
            if path.is_file() and '.staging' not in path.parts:
                relative = str(path.relative_to(self.root))
                if relative not in known:
                    found.append(str(path))
        return found
