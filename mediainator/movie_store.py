"""Movie-inator catalog storage (SQLite). No Qt.

The catalog is owned by Media-inator and lives beside other application data, never
inside media folders. Video files are referenced in place: nothing here moves,
renames or deletes a file. Personal activity (watched, rating) is stored per profile.
Every change runs in one IMMEDIATE transaction; a movie's revision number detects
edits made elsewhere since a draft was loaded.
"""
from contextlib import closing, contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
from uuid import UUID, uuid4

from .movie_catalog import COPY_KINDS, EDITION_FORMATS, Copy, Edition, Movie

SCHEMA = 1
TEXT_LIMIT = 20000
LIST_LIMIT = 200


class MovieStoreError(Exception):
    pass


class ConflictError(MovieStoreError):
    """The movie changed since the draft was loaded. `current` holds stored values."""
    def __init__(self, message, current=None):
        super().__init__(message)
        self.current = current


def now():
    return datetime.now(timezone.utc).isoformat()


_DDL = """
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS movies(
    id TEXT PRIMARY KEY, title TEXT NOT NULL, original_title TEXT NOT NULL DEFAULT '',
    year INTEGER, directors TEXT NOT NULL DEFAULT '[]', cast_list TEXT NOT NULL DEFAULT '[]',
    genres TEXT NOT NULL DEFAULT '[]', runtime INTEGER, synopsis TEXT NOT NULL DEFAULT '',
    cover TEXT NOT NULL DEFAULT '', notes TEXT NOT NULL DEFAULT '',
    revision INTEGER NOT NULL DEFAULT 0, added_at TEXT NOT NULL, modified_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS editions(
    id TEXT PRIMARY KEY, movie_id TEXT NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
    label TEXT NOT NULL, format TEXT NOT NULL, notes TEXT NOT NULL DEFAULT '', position INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS copies(
    id TEXT PRIMARY KEY, edition_id TEXT NOT NULL REFERENCES editions(id) ON DELETE CASCADE,
    kind TEXT NOT NULL, path TEXT UNIQUE, location TEXT NOT NULL DEFAULT '', size INTEGER,
    container TEXT NOT NULL DEFAULT '', duration REAL, width INTEGER, height INTEGER,
    video_codec TEXT NOT NULL DEFAULT '', audio TEXT NOT NULL DEFAULT '[]', subtitles TEXT NOT NULL DEFAULT '[]',
    added_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS personal(
    profile_id TEXT NOT NULL, movie_id TEXT NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
    watched INTEGER NOT NULL DEFAULT 0, rating INTEGER, modified_at TEXT NOT NULL,
    PRIMARY KEY(profile_id, movie_id));
CREATE INDEX IF NOT EXISTS editions_movie ON editions(movie_id);
CREATE INDEX IF NOT EXISTS copies_edition ON copies(edition_id);
"""

MOVIE_FIELDS = ('title', 'original_title', 'year', 'directors', 'cast', 'genres', 'runtime', 'synopsis', 'cover', 'notes')


def _text(value, name, required=False, limit=TEXT_LIMIT):
    if not isinstance(value, str):
        raise MovieStoreError(f'Invalid {name}.')
    value = value.strip() if name != 'synopsis' and name != 'notes' else value.strip('\n ')
    if required and not value:
        raise MovieStoreError(f'{name.capitalize()} is required.')
    if len(value) > limit or any(ord(c) < 32 and c not in '\n\t' for c in value):
        raise MovieStoreError(f'{name.capitalize()} contains unsupported characters or is too long.')
    return value


def _names(values, name):
    if isinstance(values, str) or not isinstance(values, (list, tuple)):
        raise MovieStoreError(f'Invalid {name}.')
    result, seen = [], set()
    for value in values:
        value = _text(value, name, limit=300)
        if value and value.casefold() not in seen:
            seen.add(value.casefold())
            result.append(value)
    if len(result) > LIST_LIMIT:
        raise MovieStoreError(f'Too many {name}.')
    return result


def _int(value, name, low, high):
    if value is None or value == '':
        return None
    if type(value) is not int or not low <= value <= high:
        raise MovieStoreError(f'{name.capitalize()} must be a whole number from {low} to {high}.')
    return value


def validate_movie(fields):
    """Normalise user-entered movie fields; raise MovieStoreError on invalid input."""
    unknown = set(fields) - set(MOVIE_FIELDS)
    if unknown:
        raise MovieStoreError('Unknown movie fields: ' + ', '.join(sorted(unknown)))
    out = {}
    for key in MOVIE_FIELDS:
        if key not in fields:
            continue
        value = fields[key]
        if key == 'title':
            out[key] = _text(value, 'title', required=True, limit=500)
        elif key in ('original_title', 'cover'):
            out[key] = _text(value, key.replace('_', ' '), limit=4096)
        elif key in ('synopsis', 'notes'):
            out[key] = _text(value, key)
        elif key == 'year':
            out[key] = _int(value, 'year', 1870, 2200)
        elif key == 'runtime':
            out[key] = _int(value, 'runtime', 1, 3000)
        else:
            out[key] = _names(value, key)
    return out


def validate_edition(label, fmt, notes=''):
    label = _text(label, 'edition label', required=True, limit=300)
    if fmt not in EDITION_FORMATS:
        raise MovieStoreError('Unsupported edition format.')
    return label, fmt, _text(notes, 'notes')


def canonical(path):
    """Absolute, symlink-resolved path used as a file's identity."""
    return str(Path(os.path.abspath(os.path.expanduser(str(path)))).resolve())


class MovieStore:
    def __init__(self, path, profile_id):
        try:
            UUID(profile_id)
        except (TypeError, ValueError, AttributeError) as exc:
            raise MovieStoreError('Invalid profile identity.') from exc
        self.path = Path(path)
        self.profile_id = profile_id
        self._uuid = None

    # -- connection handling ------------------------------------------------
    def _connect(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            db = sqlite3.connect(str(self.path), timeout=5, isolation_level=None)
        except (OSError, sqlite3.Error) as exc:
            raise MovieStoreError(f'Cannot open the movie catalog: {exc}') from exc
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
                    raise MovieStoreError('The movie catalog is busy. Wait a moment and retry.') from exc
                raise MovieStoreError(f'Movie catalog write failed; nothing was changed: {exc}') from exc
            except sqlite3.Error as exc:
                self._rollback(db)
                raise MovieStoreError(f'Movie catalog write failed; nothing was changed: {exc}') from exc
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
                raise MovieStoreError('The movie catalog is damaged (no schema version). It was not changed.')
            if int(row[0]) != SCHEMA:
                raise MovieStoreError('The movie catalog was created by a newer or unsupported version. It was not changed.')
            return
        if existing:
            raise MovieStoreError('This file is not a Movie-inator catalog. It was not changed.')
        for statement in _DDL.split(';'):
            if statement.strip():
                db.execute(statement)
        db.execute("INSERT INTO meta VALUES('schema', ?)", (str(SCHEMA),))
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
            raise MovieStoreError('The movie catalog does not exist yet.')
        db = self._connect()
        try:
            names = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not names:
                # A first write that failed and rolled back leaves an empty file.
                db.close()
                return None
            if 'meta' not in names:
                raise MovieStoreError('This file is not a Movie-inator catalog.')
            row = db.execute("SELECT value FROM meta WHERE key='schema'").fetchone()
            if row is None or row[0] != str(SCHEMA):
                raise MovieStoreError('The movie catalog was created by a newer or unsupported version. It was not changed.')
        except sqlite3.Error as exc:
            db.close()
            raise MovieStoreError(f'Cannot read the movie catalog: {exc}') from exc
        except MovieStoreError:
            db.close()
            raise
        return db

    # -- reading --------------------------------------------------------------
    def load(self):
        """Every movie with editions, copies and this profile's activity."""
        if not self.path.exists():
            return ()
        try:
            db = self._read()
            if db is None:
                return ()
            with closing(db):
                return self._load(db)
        except sqlite3.Error as exc:
            raise MovieStoreError(f'Cannot read the movie catalog: {exc}') from exc

    def _load(self, db, only=None):
        where, args = ('WHERE m.id=?', (only,)) if only else ('', ())
        movies = db.execute(f'''SELECT m.*, p.watched, p.rating FROM movies m
            LEFT JOIN personal p ON p.movie_id=m.id AND p.profile_id=? {where}''', (self.profile_id, *args)).fetchall()
        if not movies:
            return ()
        ids = [m['id'] for m in movies]
        marks = ','.join('?' * len(ids)) if only else None
        editions = db.execute('SELECT * FROM editions' + (f' WHERE movie_id IN ({marks})' if only else '') +
                              ' ORDER BY position, label', ids if only else ()).fetchall()
        copies = db.execute('SELECT c.* FROM copies c' + (' JOIN editions e ON e.id=c.edition_id WHERE e.movie_id=?' if only else '') +
                            ' ORDER BY c.added_at, c.id', (only,) if only else ()).fetchall()
        by_edition = {}
        for c in copies:
            by_edition.setdefault(c['edition_id'], []).append(Copy(
                c['id'], c['kind'], c['path'] or '', c['location'], c['size'], c['container'], c['duration'],
                c['width'], c['height'], c['video_codec'], tuple(json.loads(c['audio'])), tuple(json.loads(c['subtitles']))))
        by_movie = {}
        for e in editions:
            by_movie.setdefault(e['movie_id'], []).append(
                Edition(e['id'], e['label'], e['format'], e['notes'], tuple(by_edition.get(e['id'], ()))))
        return tuple(Movie(
            m['id'], m['title'], m['year'], m['original_title'], tuple(json.loads(m['directors'])),
            tuple(json.loads(m['cast_list'])), tuple(json.loads(m['genres'])), m['runtime'], m['synopsis'],
            m['cover'], m['notes'], m['revision'], tuple(by_movie.get(m['id'], ())),
            bool(m['watched']), m['rating']) for m in movies)

    def get(self, movie_id):
        found = ()
        db = self._read() if self.path.exists() else None
        if db is not None:
            with closing(db):
                found = self._load(db, movie_id)
        if not found:
            raise MovieStoreError('This movie is no longer in the catalog.')
        return found[0]

    def known_paths(self):
        db = self._read() if self.path.exists() else None
        if db is None:
            return {}
        with closing(db):
            return {r['path']: r['movie_id'] for r in db.execute(
                'SELECT c.path, e.movie_id FROM copies c JOIN editions e ON e.id=c.edition_id WHERE c.path IS NOT NULL')}

    def signature(self):
        """Cheap change detector for refreshing an open catalog."""
        try:
            return tuple((p.name, p.stat().st_size, p.stat().st_mtime_ns)
                         for p in (self.path, self.path.with_name(self.path.name + '-wal')) if p.exists())
        except OSError:
            return None

    # -- writing ----------------------------------------------------------------
    @staticmethod
    def _movie_row(fields):
        return dict(title=fields['title'], original_title=fields.get('original_title', ''), year=fields.get('year'),
                    directors=json.dumps(fields.get('directors', []), ensure_ascii=False),
                    cast_list=json.dumps(fields.get('cast', []), ensure_ascii=False),
                    genres=json.dumps(fields.get('genres', []), ensure_ascii=False),
                    runtime=fields.get('runtime'), synopsis=fields.get('synopsis', ''),
                    cover=fields.get('cover', ''), notes=fields.get('notes', ''))

    def add_movie(self, fields, editions=()):
        """Create a movie. `editions` is a list of dict(label, format, notes, copies=[copy dicts])."""
        fields = validate_movie(fields)
        if 'title' not in fields:
            raise MovieStoreError('Title is required.')
        movie_id = str(uuid4())
        with self._write() as db:
            row = self._movie_row(fields)
            stamp = now()
            db.execute('''INSERT INTO movies(id,title,original_title,year,directors,cast_list,genres,runtime,synopsis,cover,notes,revision,added_at,modified_at)
                VALUES(:id,:title,:original_title,:year,:directors,:cast_list,:genres,:runtime,:synopsis,:cover,:notes,0,:at,:at)''',
                       dict(row, id=movie_id, at=stamp))
            for position, edition in enumerate(editions):
                self._insert_edition(db, movie_id, edition, position)
        return movie_id

    def _insert_edition(self, db, movie_id, edition, position=None):
        label, fmt, notes = validate_edition(edition.get('label', ''), edition.get('format', 'Digital'), edition.get('notes', ''))
        if position is None:
            position = db.execute('SELECT COALESCE(MAX(position)+1,0) FROM editions WHERE movie_id=?', (movie_id,)).fetchone()[0]
        edition_id = str(uuid4())
        db.execute('INSERT INTO editions VALUES(?,?,?,?,?,?)', (edition_id, movie_id, label, fmt, notes, position))
        for copy in edition.get('copies', ()):
            self._insert_copy(db, edition_id, copy)
        return edition_id

    def _insert_copy(self, db, edition_id, copy):
        kind = copy.get('kind')
        if kind not in COPY_KINDS:
            raise MovieStoreError('Unsupported copy type.')
        path = None
        if kind == 'file':
            path = canonical(copy.get('path') or '')
            clash = db.execute('SELECT e.movie_id FROM copies c JOIN editions e ON e.id=c.edition_id WHERE c.path=?', (path,)).fetchone()
            if clash:
                raise MovieStoreError(f'This file is already in the catalog: {path}')
        location = _text(copy.get('location', ''), 'location', limit=500)
        audio = _names(list(copy.get('audio', ())), 'audio tracks')
        subtitles = _names(list(copy.get('subtitles', ())), 'subtitles')
        def number(key, kind=int):
            value = copy.get(key)
            return value if isinstance(value, kind) and not isinstance(value, bool) and value >= 0 else None
        copy_id = str(uuid4())
        db.execute('INSERT INTO copies VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (
            copy_id, edition_id, kind, path, location, number('size'), str(copy.get('container', ''))[:40],
            number('duration', (int, float)), number('width'), number('height'), str(copy.get('video_codec', ''))[:40],
            json.dumps(audio, ensure_ascii=False), json.dumps(subtitles, ensure_ascii=False), now()))
        return copy_id

    def _bump(self, db, movie_id, expected=None):
        row = db.execute('SELECT revision FROM movies WHERE id=?', (movie_id,)).fetchone()
        if row is None:
            raise MovieStoreError('This movie is no longer in the catalog.')
        if expected is not None and row[0] != expected:
            raise ConflictError('This movie was changed elsewhere since you opened it.', self._load(db, movie_id)[0])
        db.execute('UPDATE movies SET revision=revision+1, modified_at=? WHERE id=?', (now(), movie_id))

    def update_movie(self, movie_id, expected_revision, fields):
        """Save changed fields. Raises ConflictError if the revision moved on."""
        fields = validate_movie(fields)
        if not fields:
            return
        with self._write() as db:
            self._bump(db, movie_id, expected_revision)
            row = self._movie_row({**self._current_fields(db, movie_id), **fields})
            db.execute('''UPDATE movies SET title=:title, original_title=:original_title, year=:year, directors=:directors,
                cast_list=:cast_list, genres=:genres, runtime=:runtime, synopsis=:synopsis, cover=:cover, notes=:notes WHERE id=:id''',
                       dict(row, id=movie_id))

    def _current_fields(self, db, movie_id):
        movie = self._load(db, movie_id)[0]
        return dict(title=movie.title, original_title=movie.original_title, year=movie.year, directors=list(movie.directors),
                    cast=list(movie.cast), genres=list(movie.genres), runtime=movie.runtime, synopsis=movie.synopsis,
                    cover=movie.cover, notes=movie.notes)

    def remove_movie(self, movie_id):
        """Remove the catalog entry only. Video files are never touched."""
        with self._write() as db:
            if db.execute('DELETE FROM movies WHERE id=?', (movie_id,)).rowcount != 1:
                raise MovieStoreError('This movie is no longer in the catalog.')

    def add_edition(self, movie_id, label, fmt, notes='', copies=()):
        with self._write() as db:
            self._bump(db, movie_id)
            return self._insert_edition(db, movie_id, dict(label=label, format=fmt, notes=notes, copies=copies))

    def update_edition(self, edition_id, label, fmt, notes=''):
        label, fmt, notes = validate_edition(label, fmt, notes)
        with self._write() as db:
            row = db.execute('SELECT movie_id FROM editions WHERE id=?', (edition_id,)).fetchone()
            if row is None:
                raise MovieStoreError('This edition is no longer in the catalog.')
            self._bump(db, row[0])
            db.execute('UPDATE editions SET label=?, format=?, notes=? WHERE id=?', (label, fmt, notes, edition_id))

    def remove_edition(self, edition_id):
        with self._write() as db:
            row = db.execute('SELECT movie_id FROM editions WHERE id=?', (edition_id,)).fetchone()
            if row is None:
                raise MovieStoreError('This edition is no longer in the catalog.')
            self._bump(db, row[0])
            db.execute('DELETE FROM editions WHERE id=?', (edition_id,))

    def add_copy(self, edition_id, copy):
        with self._write() as db:
            row = db.execute('SELECT movie_id FROM editions WHERE id=?', (edition_id,)).fetchone()
            if row is None:
                raise MovieStoreError('This edition is no longer in the catalog.')
            self._bump(db, row[0])
            return self._insert_copy(db, edition_id, copy)

    def update_copy_location(self, copy_id, location):
        location = _text(location, 'location', limit=500)
        with self._write() as db:
            row = db.execute('SELECT e.movie_id FROM copies c JOIN editions e ON e.id=c.edition_id WHERE c.id=?', (copy_id,)).fetchone()
            if row is None:
                raise MovieStoreError('This copy is no longer in the catalog.')
            self._bump(db, row[0])
            db.execute('UPDATE copies SET location=? WHERE id=?', (location, copy_id))

    def relocate_file(self, copy_id, new_path):
        """Point a file copy at its new location (after the user moved it)."""
        path = canonical(new_path)
        with self._write() as db:
            row = db.execute('SELECT e.movie_id FROM copies c JOIN editions e ON e.id=c.edition_id WHERE c.id=? AND c.kind=?', (copy_id, 'file')).fetchone()
            if row is None:
                raise MovieStoreError('This file copy is no longer in the catalog.')
            if db.execute('SELECT 1 FROM copies WHERE path=? AND id<>?', (path, copy_id)).fetchone():
                raise MovieStoreError(f'This file is already in the catalog: {path}')
            self._bump(db, row[0])
            db.execute('UPDATE copies SET path=? WHERE id=?', (path, copy_id))

    def remove_copy(self, copy_id):
        with self._write() as db:
            row = db.execute('SELECT e.movie_id FROM copies c JOIN editions e ON e.id=c.edition_id WHERE c.id=?', (copy_id,)).fetchone()
            if row is None:
                raise MovieStoreError('This copy is no longer in the catalog.')
            self._bump(db, row[0])
            db.execute('DELETE FROM copies WHERE id=?', (copy_id,))

    def set_personal(self, movie_id, watched, rating):
        """This profile's watched flag and rating. Catalog revision is unchanged."""
        if type(watched) is not bool:
            raise MovieStoreError('Invalid watched status.')
        rating = _int(rating, 'rating', 1, 10)
        with self._write() as db:
            if db.execute('SELECT 1 FROM movies WHERE id=?', (movie_id,)).fetchone() is None:
                raise MovieStoreError('This movie is no longer in the catalog.')
            db.execute('''INSERT INTO personal(profile_id,movie_id,watched,rating,modified_at) VALUES(?,?,?,?,?)
                ON CONFLICT(profile_id,movie_id) DO UPDATE SET watched=excluded.watched, rating=excluded.rating,
                modified_at=excluded.modified_at''', (self.profile_id, movie_id, int(watched), rating, now()))

    def apply_group(self, action, editions, *, title=None, year=None, runtime=None, movie_id=None):
        """Apply one confirmed scan/import group in a single transaction.

        editions: [dict(label, format, copies=[copy dicts])]. 'create' makes a new movie;
        'attach' adds the editions to an existing movie. Returns the movie id.
        """
        if action == 'create':
            fields = dict(title=title or '', year=year)
            if runtime:
                fields['runtime'] = runtime
            return self.add_movie(fields, editions)
        if action == 'attach':
            with self._write() as db:
                self._bump(db, movie_id)
                for edition in editions:
                    self._insert_edition(db, movie_id, edition)
            return movie_id
        raise MovieStoreError('Unsupported import action.')
