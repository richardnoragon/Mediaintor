"""Music-inator catalog storage (SQLite). No Qt.

The catalog is owned by Media-inator and lives beside other application data, never
inside music folders. Audio files are referenced in place: nothing here moves,
renames, retags or deletes a file. Personal activity (favourite, rating) is stored
per profile. Every change runs in one IMMEDIATE transaction; an album's revision
number detects edits made elsewhere since a draft was loaded.
"""
from contextlib import closing, contextmanager
import json
import os
from pathlib import Path
import sqlite3
from uuid import UUID, uuid4

from .movie_store import now
from .music_catalog import COPY_KINDS, EDITION_FORMATS, Album, AudioFile, Copy, Edition, Track

SCHEMA = 1
TEXT_LIMIT = 20000
LIST_LIMIT = 200
TRACK_LIMIT = 2000
FILE_LIMIT = 5000


class MusicStoreError(Exception):
    pass


class ConflictError(MusicStoreError):
    """The album changed since the draft was loaded. `current` holds stored values."""
    def __init__(self, message, current=None):
        super().__init__(message)
        self.current = current


_DDL = """
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS albums(
    id TEXT PRIMARY KEY, title TEXT NOT NULL, artists TEXT NOT NULL DEFAULT '[]',
    additional_artists TEXT NOT NULL DEFAULT '[]', year INTEGER, genres TEXT NOT NULL DEFAULT '[]',
    cover TEXT NOT NULL DEFAULT '', notes TEXT NOT NULL DEFAULT '',
    revision INTEGER NOT NULL DEFAULT 0, added_at TEXT NOT NULL, modified_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS editions(
    id TEXT PRIMARY KEY, album_id TEXT NOT NULL REFERENCES albums(id) ON DELETE CASCADE,
    label TEXT NOT NULL, format TEXT NOT NULL, release_year INTEGER, record_label TEXT NOT NULL DEFAULT '',
    catalog_number TEXT NOT NULL DEFAULT '', disc_count INTEGER NOT NULL DEFAULT 1,
    notes TEXT NOT NULL DEFAULT '', position INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS tracks(
    id TEXT PRIMARY KEY, edition_id TEXT NOT NULL REFERENCES editions(id) ON DELETE CASCADE,
    disc INTEGER NOT NULL DEFAULT 1, number INTEGER, title TEXT NOT NULL, artist TEXT NOT NULL DEFAULT '',
    duration REAL, position INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS copies(
    id TEXT PRIMARY KEY, edition_id TEXT NOT NULL REFERENCES editions(id) ON DELETE CASCADE,
    kind TEXT NOT NULL, location TEXT NOT NULL DEFAULT '', quality TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '', added_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS files(
    id TEXT PRIMARY KEY, copy_id TEXT NOT NULL REFERENCES copies(id) ON DELETE CASCADE,
    path TEXT NOT NULL UNIQUE, size INTEGER, disc INTEGER, number INTEGER, title TEXT NOT NULL DEFAULT '',
    duration REAL, codec TEXT NOT NULL DEFAULT '', bitrate INTEGER, sample_rate INTEGER, bit_depth INTEGER,
    channels INTEGER, position INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS personal(
    profile_id TEXT NOT NULL, album_id TEXT NOT NULL REFERENCES albums(id) ON DELETE CASCADE,
    favourite INTEGER NOT NULL DEFAULT 0, rating INTEGER, modified_at TEXT NOT NULL,
    PRIMARY KEY(profile_id, album_id));
CREATE INDEX IF NOT EXISTS editions_album ON editions(album_id);
CREATE INDEX IF NOT EXISTS tracks_edition ON tracks(edition_id);
CREATE INDEX IF NOT EXISTS copies_edition ON copies(edition_id);
CREATE INDEX IF NOT EXISTS files_copy ON files(copy_id)
"""

ALBUM_FIELDS = ('title', 'artists', 'additional_artists', 'year', 'genres', 'cover', 'notes')
EDITION_FIELDS = ('label', 'format', 'release_year', 'record_label', 'catalog_number', 'disc_count', 'notes')


def _text(value, name, required=False, limit=TEXT_LIMIT, multiline=False):
    if not isinstance(value, str):
        raise MusicStoreError(f'Invalid {name}.')
    value = value.strip('\n ') if multiline else value.strip()
    if required and not value:
        raise MusicStoreError(f'{name.capitalize()} is required.')
    allowed = '\n\t' if multiline else '\t'
    if len(value) > limit or any(ord(c) < 32 and c not in allowed for c in value):
        raise MusicStoreError(f'{name.capitalize()} contains unsupported characters or is too long.')
    return value


def _names(values, name):
    if isinstance(values, str) or not isinstance(values, (list, tuple)):
        raise MusicStoreError(f'Invalid {name}.')
    result, seen = [], set()
    for value in values:
        value = _text(value, name, limit=300)
        if value and value.casefold() not in seen:
            seen.add(value.casefold())
            result.append(value)
    if len(result) > LIST_LIMIT:
        raise MusicStoreError(f'Too many {name}.')
    return result


def _int(value, name, low, high):
    if value is None or value == '':
        return None
    if type(value) is not int or not low <= value <= high:
        raise MusicStoreError(f'{name.capitalize()} must be a whole number from {low} to {high}.')
    return value


def _number(value, kind=int):
    """Technical values from scans: keep sane non-negative numbers, drop the rest."""
    return value if isinstance(value, kind) and not isinstance(value, bool) and value >= 0 else None


def validate_album(fields):
    """Normalise user-entered album fields; raise MusicStoreError on invalid input."""
    unknown = set(fields) - set(ALBUM_FIELDS)
    if unknown:
        raise MusicStoreError('Unknown album fields: ' + ', '.join(sorted(unknown)))
    out = {}
    for key in ALBUM_FIELDS:
        if key not in fields:
            continue
        value = fields[key]
        if key == 'title':
            out[key] = _text(value, 'title', required=True, limit=500)
        elif key == 'cover':
            out[key] = _text(value, 'cover', limit=4096)
        elif key == 'notes':
            out[key] = _text(value, 'notes', multiline=True)
        elif key == 'year':
            out[key] = _int(value, 'year', 1000, 2200)
        else:
            out[key] = _names(value, key.replace('_', ' '))
    if 'artists' in out and 'additional_artists' in out:
        album = {n.casefold() for n in out['artists']}
        out['additional_artists'] = [n for n in out['additional_artists'] if n.casefold() not in album]
    return out


def validate_edition(fields):
    unknown = set(fields) - set(EDITION_FIELDS)
    if unknown:
        raise MusicStoreError('Unknown edition fields: ' + ', '.join(sorted(unknown)))
    fmt = fields.get('format', 'CD')
    if fmt not in EDITION_FORMATS:
        raise MusicStoreError('Unsupported edition format.')
    disc_count = fields.get('disc_count', 1)
    return dict(
        label=_text(fields.get('label', ''), 'edition label', required=True, limit=300),
        format=fmt,
        release_year=_int(fields.get('release_year'), 'release year', 1000, 2200),
        record_label=_text(fields.get('record_label', ''), 'record label', limit=300),
        catalog_number=_text(fields.get('catalog_number', ''), 'catalog number', limit=100),
        disc_count=_int(disc_count if disc_count not in (None, '') else 1, 'disc count', 1, 99),
        notes=_text(fields.get('notes', ''), 'notes', multiline=True),
    )


def validate_tracks(tracks):
    if isinstance(tracks, (str, dict)) or not isinstance(tracks, (list, tuple)):
        raise MusicStoreError('Invalid track list.')
    if len(tracks) > TRACK_LIMIT:
        raise MusicStoreError('Too many tracks.')
    result = []
    for index, track in enumerate(tracks, 1):
        if not isinstance(track, dict) or set(track) - {'title', 'disc', 'number', 'artist', 'duration'}:
            raise MusicStoreError(f'Invalid track {index}.')
        title = _text(track.get('title', ''), f'title of track {index}', required=True, limit=500)
        disc = _int(1 if track.get('disc') in (None, '') else track.get('disc'), f'disc of track {index}', 1, 99)
        number = _int(track.get('number'), f'number of track {index}', 1, 999)
        duration = track.get('duration')
        if duration is not None and (isinstance(duration, bool) or not isinstance(duration, (int, float))
                                     or not 0 <= duration <= 100000):
            raise MusicStoreError(f'Invalid length for track {index}.')
        result.append(dict(title=title, disc=disc, number=number, artist=_text(track.get('artist', ''), 'track artist', limit=300),
                           duration=float(duration) if duration else None))
    return result


def canonical(path):
    """Absolute, symlink-resolved path used as a file's identity."""
    return str(Path(os.path.abspath(os.path.expanduser(str(path)))).resolve())


class MusicStore:
    def __init__(self, path, profile_id):
        try:
            UUID(profile_id)
        except (TypeError, ValueError, AttributeError) as exc:
            raise MusicStoreError('Invalid profile identity.') from exc
        self.path = Path(path)
        self.profile_id = profile_id
        self._uuid = None

    # -- connection handling ------------------------------------------------
    def _connect(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            db = sqlite3.connect(str(self.path), timeout=5, isolation_level=None)
        except (OSError, sqlite3.Error) as exc:
            raise MusicStoreError(f'Cannot open the music catalog: {exc}') from exc
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
                    raise MusicStoreError('The music catalog is busy. Wait a moment and retry.') from exc
                raise MusicStoreError(f'Music catalog write failed; nothing was changed: {exc}') from exc
            except sqlite3.Error as exc:
                self._rollback(db)
                raise MusicStoreError(f'Music catalog write failed; nothing was changed: {exc}') from exc
            except BaseException:
                self._rollback(db)
                raise

    @staticmethod
    def _rollback(db):
        try:
            db.execute('ROLLBACK')
        except sqlite3.Error:
            pass

    def _ensure(self, db):
        existing = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if 'meta' in existing:
            row = db.execute("SELECT value FROM meta WHERE key='schema'").fetchone()
            if row is None or not row[0].isdigit():
                raise MusicStoreError('The music catalog is damaged (no schema version). It was not changed.')
            if int(row[0]) != SCHEMA:
                raise MusicStoreError('The music catalog was created by a newer or unsupported version. It was not changed.')
            if db.execute("SELECT value FROM meta WHERE key='kind'").fetchone() is None:
                raise MusicStoreError('This file is not a Music-inator catalog. It was not changed.')
            return
        if existing:
            raise MusicStoreError('This file is not a Music-inator catalog. It was not changed.')
        for statement in _DDL.split(';'):
            if statement.strip():
                db.execute(statement)
        db.execute("INSERT INTO meta VALUES('schema', ?)", (str(SCHEMA),))
        db.execute("INSERT INTO meta VALUES('kind', 'music')")
        db.execute("INSERT INTO meta VALUES('catalog_uuid', ?)", (str(uuid4()),))
        db.execute("INSERT INTO meta VALUES('created_at', ?)", (now(),))

    def initialize(self):
        with self._write():
            pass
        return self.catalog_uuid()

    def catalog_uuid(self):
        if self._uuid is None:
            if not self.path.exists():
                return None
            db = self._read()
            if db is None:
                return None
            with closing(db):
                row = db.execute("SELECT value FROM meta WHERE key='catalog_uuid'").fetchone()
            self._uuid = row[0] if row else None
        return self._uuid

    def _read(self):
        if not self.path.exists():
            raise MusicStoreError('The music catalog does not exist yet.')
        db = self._connect()
        try:
            names = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not names:
                # A first write that failed and rolled back leaves an empty file.
                db.close()
                return None
            if 'meta' not in names:
                raise MusicStoreError('This file is not a Music-inator catalog.')
            row = db.execute("SELECT value FROM meta WHERE key='schema'").fetchone()
            if row is None or row[0] != str(SCHEMA):
                raise MusicStoreError('The music catalog was created by a newer or unsupported version. It was not changed.')
            if db.execute("SELECT value FROM meta WHERE key='kind'").fetchone() is None:
                raise MusicStoreError('This file is not a Music-inator catalog.')
        except sqlite3.Error as exc:
            db.close()
            raise MusicStoreError(f'Cannot read the music catalog: {exc}') from exc
        except MusicStoreError:
            db.close()
            raise
        return db

    # -- reading --------------------------------------------------------------
    def load(self):
        """Every album with editions, tracks, copies, files and this profile's activity."""
        if not self.path.exists():
            return ()
        try:
            db = self._read()
            if db is None:
                return ()
            with closing(db):
                return self._load(db)
        except sqlite3.Error as exc:
            raise MusicStoreError(f'Cannot read the music catalog: {exc}') from exc

    def _load(self, db, only=None):
        where, args = ('WHERE a.id=?', (only,)) if only else ('', ())
        albums = db.execute(f'''SELECT a.*, p.favourite, p.rating FROM albums a
            LEFT JOIN personal p ON p.album_id=a.id AND p.profile_id=? {where}''', (self.profile_id, *args)).fetchall()
        if not albums:
            return ()
        scope = ' WHERE e.album_id=?' if only else ''
        params = (only,) if only else ()
        editions = db.execute('SELECT e.* FROM editions e' + scope + ' ORDER BY e.position, e.label', params).fetchall()
        tracks = db.execute('SELECT t.* FROM tracks t JOIN editions e ON e.id=t.edition_id' + scope +
                            ' ORDER BY t.disc, t.position, t.number', params).fetchall()
        copies = db.execute('SELECT c.* FROM copies c JOIN editions e ON e.id=c.edition_id' + scope +
                            ' ORDER BY c.added_at, c.id', params).fetchall()
        files = db.execute('SELECT f.* FROM files f JOIN copies c ON c.id=f.copy_id JOIN editions e ON e.id=c.edition_id' +
                           scope + ' ORDER BY f.disc, f.position, f.number, f.path', params).fetchall()
        by_copy, by_edition_tracks, by_edition_copies, by_album = {}, {}, {}, {}
        for f in files:
            by_copy.setdefault(f['copy_id'], []).append(AudioFile(
                f['id'], f['path'], f['size'], f['disc'], f['number'], f['title'], f['duration'], f['codec'],
                f['bitrate'], f['sample_rate'], f['bit_depth'], f['channels']))
        for t in tracks:
            by_edition_tracks.setdefault(t['edition_id'], []).append(
                Track(t['title'], t['disc'], t['number'], t['artist'], t['duration']))
        for c in copies:
            by_edition_copies.setdefault(c['edition_id'], []).append(
                Copy(c['id'], c['kind'], c['location'], c['quality'], c['notes'], tuple(by_copy.get(c['id'], ()))))
        for e in editions:
            by_album.setdefault(e['album_id'], []).append(Edition(
                e['id'], e['label'], e['format'], e['release_year'], e['record_label'], e['catalog_number'],
                e['disc_count'], e['notes'], tuple(by_edition_tracks.get(e['id'], ())), tuple(by_edition_copies.get(e['id'], ()))))
        return tuple(Album(
            a['id'], a['title'], tuple(json.loads(a['artists'])), tuple(json.loads(a['additional_artists'])), a['year'],
            tuple(json.loads(a['genres'])), a['cover'], a['notes'], a['revision'], tuple(by_album.get(a['id'], ())),
            bool(a['favourite']), a['rating']) for a in albums)

    def get(self, album_id):
        found = ()
        db = self._read() if self.path.exists() else None
        if db is not None:
            with closing(db):
                found = self._load(db, album_id)
        if not found:
            raise MusicStoreError('This album is no longer in the catalog.')
        return found[0]

    def known_paths(self):
        """Canonical audio file path → album id for every catalogued file."""
        db = self._read() if self.path.exists() else None
        if db is None:
            return {}
        with closing(db):
            return {r['path']: r['album_id'] for r in db.execute(
                'SELECT f.path, e.album_id FROM files f JOIN copies c ON c.id=f.copy_id JOIN editions e ON e.id=c.edition_id')}

    def signature(self):
        """Cheap change detector for refreshing an open catalog."""
        try:
            return tuple((p.name, p.stat().st_size, p.stat().st_mtime_ns)
                         for p in (self.path, self.path.with_name(self.path.name + '-wal')) if p.exists())
        except OSError:
            return None

    # -- writing ----------------------------------------------------------------
    @staticmethod
    def _album_row(fields):
        dump = lambda key: json.dumps(fields.get(key, []), ensure_ascii=False)
        return dict(title=fields['title'], artists=dump('artists'), additional_artists=dump('additional_artists'),
                    year=fields.get('year'), genres=dump('genres'), cover=fields.get('cover', ''), notes=fields.get('notes', ''))

    def add_album(self, fields, editions=()):
        """Create an album. `editions` is a list of dict(edition fields…, tracks=[…], copies=[copy dicts])."""
        fields = validate_album(fields)
        if 'title' not in fields:
            raise MusicStoreError('Title is required.')
        album_id = str(uuid4())
        with self._write() as db:
            stamp = now()
            db.execute('''INSERT INTO albums(id,title,artists,additional_artists,year,genres,cover,notes,revision,added_at,modified_at)
                VALUES(:id,:title,:artists,:additional_artists,:year,:genres,:cover,:notes,0,:at,:at)''',
                       dict(self._album_row(fields), id=album_id, at=stamp))
            for position, edition in enumerate(editions):
                self._insert_edition(db, album_id, edition, position)
        return album_id

    @staticmethod
    def _split_edition(edition):
        if not isinstance(edition, dict):
            raise MusicStoreError('Invalid edition.')
        fields = {k: v for k, v in edition.items() if k in EDITION_FIELDS}
        return validate_edition(fields), validate_tracks(edition.get('tracks', ())), list(edition.get('copies', ()))

    def _insert_edition(self, db, album_id, edition, position=None):
        fields, tracks, copies = self._split_edition(edition)
        if position is None:
            position = db.execute('SELECT COALESCE(MAX(position)+1,0) FROM editions WHERE album_id=?', (album_id,)).fetchone()[0]
        fields['disc_count'] = max(fields['disc_count'], max((t['disc'] for t in tracks), default=1))
        edition_id = str(uuid4())
        db.execute('''INSERT INTO editions(id,album_id,label,format,release_year,record_label,catalog_number,disc_count,notes,position)
            VALUES(:id,:album,:label,:format,:release_year,:record_label,:catalog_number,:disc_count,:notes,:position)''',
                   dict(fields, id=edition_id, album=album_id, position=position))
        self._insert_tracks(db, edition_id, tracks)
        for copy in copies:
            self._insert_copy(db, edition_id, copy)
        return edition_id

    @staticmethod
    def _insert_tracks(db, edition_id, tracks):
        for position, track in enumerate(tracks):
            db.execute('INSERT INTO tracks VALUES(?,?,?,?,?,?,?,?)', (
                str(uuid4()), edition_id, track['disc'], track['number'], track['title'], track['artist'],
                track['duration'], position))

    def _insert_copy(self, db, edition_id, copy):
        if not isinstance(copy, dict):
            raise MusicStoreError('Invalid copy.')
        kind = copy.get('kind')
        if kind not in COPY_KINDS:
            raise MusicStoreError('Unsupported copy type.')
        files = list(copy.get('files', ()))
        if kind == 'digital' and not files:
            raise MusicStoreError('A digital copy needs at least one audio file.')
        if kind == 'physical' and files:
            raise MusicStoreError('A physical copy cannot have audio files.')
        if len(files) > FILE_LIMIT:
            raise MusicStoreError('Too many files in one copy.')
        location = _text(copy.get('location', ''), 'location', limit=500)
        quality = _text(copy.get('quality', ''), 'quality', limit=120)
        notes = _text(copy.get('notes', ''), 'notes', multiline=True)
        copy_id = str(uuid4())
        db.execute('INSERT INTO copies VALUES(?,?,?,?,?,?,?)', (copy_id, edition_id, kind, location, quality, notes, now()))
        for position, item in enumerate(files):
            self._insert_file(db, copy_id, item, position)
        return copy_id

    @staticmethod
    def _insert_file(db, copy_id, item, position):
        if not isinstance(item, dict) or not item.get('path'):
            raise MusicStoreError('Invalid audio file.')
        path = canonical(item['path'])
        if db.execute('SELECT 1 FROM files WHERE path=?', (path,)).fetchone():
            raise MusicStoreError(f'This file is already in the catalog: {path}')
        title = item.get('title', '')
        title = title[:500] if isinstance(title, str) else ''
        disc, number = _number(item.get('disc')), _number(item.get('number'))
        db.execute('INSERT INTO files VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (
            str(uuid4()), copy_id, path, _number(item.get('size')), disc if disc and disc <= 99 else None,
            number if number and number <= 999 else None, ''.join(c for c in title if ord(c) >= 32),
            _number(item.get('duration'), (int, float)), str(item.get('codec', ''))[:40], _number(item.get('bitrate')),
            _number(item.get('sample_rate')), _number(item.get('bit_depth')), _number(item.get('channels')), position))

    def _bump(self, db, album_id, expected=None):
        row = db.execute('SELECT revision FROM albums WHERE id=?', (album_id,)).fetchone()
        if row is None:
            raise MusicStoreError('This album is no longer in the catalog.')
        if expected is not None and row[0] != expected:
            raise ConflictError('This album was changed elsewhere since you opened it.', self._load(db, album_id)[0])
        db.execute('UPDATE albums SET revision=revision+1, modified_at=? WHERE id=?', (now(), album_id))

    def _album_of(self, db, table, row_id, what):
        queries = {
            'editions': 'SELECT album_id FROM editions WHERE id=?',
            'copies': 'SELECT e.album_id FROM copies c JOIN editions e ON e.id=c.edition_id WHERE c.id=?',
        }
        row = db.execute(queries[table], (row_id,)).fetchone()
        if row is None:
            raise MusicStoreError(f'This {what} is no longer in the catalog.')
        return row[0]

    def update_album(self, album_id, expected_revision, fields):
        """Save changed fields. Raises ConflictError if the revision moved on."""
        fields = validate_album(fields)
        if not fields:
            return
        with self._write() as db:
            self._bump(db, album_id, expected_revision)
            merged = validate_album({**self._current_fields(db, album_id), **fields})
            db.execute('''UPDATE albums SET title=:title, artists=:artists, additional_artists=:additional_artists,
                year=:year, genres=:genres, cover=:cover, notes=:notes WHERE id=:id''', dict(self._album_row(merged), id=album_id))

    def _current_fields(self, db, album_id):
        album = self._load(db, album_id)[0]
        return dict(title=album.title, artists=list(album.artists), additional_artists=list(album.additional_artists),
                    year=album.year, genres=list(album.genres), cover=album.cover, notes=album.notes)

    def remove_album(self, album_id):
        """Remove the catalog entry only. Audio files are never touched."""
        with self._write() as db:
            if db.execute('DELETE FROM albums WHERE id=?', (album_id,)).rowcount != 1:
                raise MusicStoreError('This album is no longer in the catalog.')

    def add_edition(self, album_id, fields, tracks=(), copies=()):
        with self._write() as db:
            self._bump(db, album_id)
            return self._insert_edition(db, album_id, dict(fields, tracks=list(tracks), copies=list(copies)))

    def update_edition(self, edition_id, fields, tracks=None):
        """Replace edition fields and, when `tracks` is given, the whole track list."""
        fields = validate_edition(fields)
        tracks = validate_tracks(tracks) if tracks is not None else None
        with self._write() as db:
            album_id = self._album_of(db, 'editions', edition_id, 'edition')
            self._bump(db, album_id)
            if tracks is not None:
                db.execute('DELETE FROM tracks WHERE edition_id=?', (edition_id,))
                self._insert_tracks(db, edition_id, tracks)
                top = max((t['disc'] for t in tracks), default=1)
            else:
                top = db.execute('SELECT COALESCE(MAX(disc),1) FROM tracks WHERE edition_id=?', (edition_id,)).fetchone()[0]
            fields['disc_count'] = max(fields['disc_count'], top)
            db.execute('''UPDATE editions SET label=:label, format=:format, release_year=:release_year, record_label=:record_label,
                catalog_number=:catalog_number, disc_count=:disc_count, notes=:notes WHERE id=:id''', dict(fields, id=edition_id))

    def remove_edition(self, edition_id):
        with self._write() as db:
            self._bump(db, self._album_of(db, 'editions', edition_id, 'edition'))
            db.execute('DELETE FROM editions WHERE id=?', (edition_id,))

    def add_copy(self, edition_id, copy):
        with self._write() as db:
            self._bump(db, self._album_of(db, 'editions', edition_id, 'edition'))
            return self._insert_copy(db, edition_id, copy)

    def update_copy(self, copy_id, location, quality, notes=''):
        location = _text(location, 'location', limit=500)
        quality = _text(quality, 'quality', limit=120)
        notes = _text(notes, 'notes', multiline=True)
        with self._write() as db:
            self._bump(db, self._album_of(db, 'copies', copy_id, 'copy'))
            db.execute('UPDATE copies SET location=?, quality=?, notes=? WHERE id=?', (location, quality, notes, copy_id))

    def relocate_files(self, copy_id, moves):
        """Point files of a digital copy at their new locations after the user moved
        them. `moves` maps file id → new path. All or nothing."""
        if not isinstance(moves, dict) or not moves:
            raise MusicStoreError('Nothing to relocate.')
        with self._write() as db:
            album_id = self._album_of(db, 'copies', copy_id, 'copy')
            owned = {r[0] for r in db.execute('SELECT id FROM files WHERE copy_id=?', (copy_id,))}
            targets = {}
            for file_id, new_path in moves.items():
                if file_id not in owned:
                    raise MusicStoreError('This file is no longer part of the copy.')
                path = canonical(new_path)
                if path in targets.values():
                    raise MusicStoreError(f'Two files cannot move to the same location: {path}')
                clash = db.execute('SELECT id FROM files WHERE path=?', (path,)).fetchone()
                if clash and clash[0] not in moves:
                    raise MusicStoreError(f'This file is already in the catalog: {path}')
                targets[file_id] = path
            self._bump(db, album_id)
            # Two-step update so swapping paths never trips the UNIQUE constraint.
            for file_id in targets:
                db.execute('UPDATE files SET path=? WHERE id=?', ('\0moving\0' + file_id, file_id))
            for file_id, path in targets.items():
                db.execute('UPDATE files SET path=? WHERE id=?', (path, file_id))

    def remove_copy(self, copy_id):
        with self._write() as db:
            self._bump(db, self._album_of(db, 'copies', copy_id, 'copy'))
            db.execute('DELETE FROM copies WHERE id=?', (copy_id,))

    def set_personal(self, album_id, favourite, rating):
        """This profile's favourite flag and rating. Catalog revision is unchanged."""
        if type(favourite) is not bool:
            raise MusicStoreError('Invalid favourite value.')
        rating = _int(rating, 'rating', 1, 10)
        with self._write() as db:
            if db.execute('SELECT 1 FROM albums WHERE id=?', (album_id,)).fetchone() is None:
                raise MusicStoreError('This album is no longer in the catalog.')
            db.execute('''INSERT INTO personal(profile_id,album_id,favourite,rating,modified_at) VALUES(?,?,?,?,?)
                ON CONFLICT(profile_id,album_id) DO UPDATE SET favourite=excluded.favourite, rating=excluded.rating,
                modified_at=excluded.modified_at''', (self.profile_id, album_id, int(favourite), rating, now()))

    def apply_group(self, action, editions, *, title=None, artists=(), year=None, genres=(), album_id=None):
        """Apply one confirmed scan/import group in a single transaction.

        editions: [dict(edition fields, tracks, copies, edition_id=optional)]. 'create'
        makes a new album; 'attach' adds to an existing album — an edition dict with an
        `edition_id` of that album only adds its copies (the track list is kept).
        Returns the album id.
        """
        if action == 'create':
            clean = [{k: v for k, v in e.items() if k != 'edition_id'} for e in editions]
            return self.add_album(dict(title=title or '', artists=list(artists), year=year, genres=list(genres)), clean)
        if action == 'attach':
            with self._write() as db:
                self._bump(db, album_id)
                for edition in editions:
                    target = edition.get('edition_id')
                    if target:
                        if self._album_of(db, 'editions', target, 'edition') != album_id:
                            raise MusicStoreError('The chosen edition belongs to another album.')
                        for copy in edition.get('copies', ()):
                            self._insert_copy(db, target, copy)
                    else:
                        self._insert_edition(db, album_id, {k: v for k, v in edition.items() if k != 'edition_id'})
            return album_id
        raise MusicStoreError('Unsupported import action.')
