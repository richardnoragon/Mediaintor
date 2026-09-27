"""Read-only Calibre viewer progress and explicit, identity-checked rename handoff.

CFIs are opaque resume tokens, not percentages or reading-status signals.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import re
import os
import stat
from pathlib import Path

MAX_RECORD_BYTES = 1024 * 1024

@dataclass(frozen=True)
class Progress:
    position: str | None = None
    last_read: datetime | None = None
    issue: str = ''
    percentage: float | None = None
    status: str = 'Unknown'


def timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if result.tzinfo is None:
            return None
        result = result.astimezone(timezone.utc)
        return result if result <= datetime.now(timezone.utc) else None
    except (ValueError, OverflowError):
        return None


def valid_position(value):
    # Structural screening only; the viewer resolves the CFI against the ebook.
    return (isinstance(value, str) and len(value) <= 16384
            and bool(re.fullmatch(r'epubcfi\(/[^\r\n\x00-\x1f]+\)', value)))


def read_progress(annotation_dir, ebook):
    path = Path(annotation_dir) / (hashlib.sha256(str(Path(ebook).absolute()).encode()).hexdigest() + '.json')
    try:
        if path.is_symlink():
            return Progress(issue='unsafe-record')
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
        with os.fdopen(fd, 'rb') as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                return Progress(issue='unsafe-record')
            raw = stream.read(MAX_RECORD_BYTES + 1)
        if len(raw) > MAX_RECORD_BYTES:
            return Progress(issue='oversize-record')
        rows = json.loads(raw)
        if not isinstance(rows, list):
            return Progress(issue='invalid-record')
        candidates = [Progress(r['pos'], timestamp(r.get('timestamp')))
                      for r in rows if isinstance(r, dict) and r.get('type') == 'last-read'
                      and r.get('pos_type') == 'epubcfi' and valid_position(r.get('pos'))]
        if not candidates:
            return Progress(issue='no-valid-position')
        dated = [r for r in candidates if r.last_read is not None]
        chosen = [r for r in dated if r.last_read == max(x.last_read for x in dated)] if dated else candidates
        if len({r.position for r in chosen}) != 1:
            return Progress(issue='ambiguous-position')
        return chosen[0]
    except FileNotFoundError:
        return Progress(issue='missing-record')
    except (OSError, ValueError, RecursionError):
        return Progress(issue='unreadable-record')


def latest_formats(progress_by_format):
    dated = {fmt: p.last_read for fmt, p in progress_by_format.items() if p.position and p.last_read}
    if not dated:
        return ()
    newest = max(dated.values())
    return tuple(sorted(fmt for fmt, date in dated.items() if date == newest))


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

@dataclass(frozen=True)
class RenameHandoff:
    library_id: str
    book_uuid: str
    format: str
    content_hash: str
    progress: Progress


def capture_rename(library_id, book_uuid, fmt, ebook, annotation_dir):
    if not library_id or not book_uuid:
        raise ValueError('Stable library and book identities required')
    return RenameHandoff(library_id, book_uuid, fmt.upper(), digest(ebook), read_progress(annotation_dir, ebook))


def renamed_resume_args(handoff, library_id, book_uuid, fmt, ebook, annotation_dir):
    """Never write Calibre sidecars; return an explicit viewer position or refuse.

Caller must hold protected access and use fresh Calibre identity/path readback.
A target-side record takes precedence; corrupt/conflicting records require review.
"""
    if (library_id, book_uuid, fmt.upper()) != (handoff.library_id, handoff.book_uuid, handoff.format):
        raise ValueError('Renamed book identity changed')
    if digest(ebook) != handoff.content_hash:
        raise ValueError('Format contents changed; stale position cannot be transferred')
    current = read_progress(annotation_dir, ebook)
    if current.issue != 'missing-record':
        if current.issue:
            raise ValueError('Target progress needs review')
        return []  # Let the viewer use its current record.
    if handoff.progress.issue or not valid_position(handoff.progress.position):
        raise ValueError('No verified position to preserve')
    return ['--open-at', handoff.progress.position]

class ProgressStore:
    """Application-owned rename provenance; never writes viewer or library data."""
    def __init__(self, path, library_id, annotation_dir):
        self.path, self.library_id, self.annotation_dir = Path(path), library_id, Path(annotation_dir)
        try:
            with self.path.open('rb') as stream:
                raw = stream.read(8 * MAX_RECORD_BYTES + 1)
            if len(raw) > 8 * MAX_RECORD_BYTES:
                raise ValueError('Progress history is too large')
            data = json.loads(raw)
            if data.get('schema') != 1 or not isinstance(data.get('records'), dict):
                raise ValueError('Invalid progress history')
            self.records = data['records']
        except FileNotFoundError:
            self.records = {}

    def key(self, book_uuid, fmt):
        return json.dumps([self.library_id, book_uuid, fmt.upper()])

    def refresh(self, book_uuid, fmt, ebook):
        if not book_uuid:
            return Progress(issue='missing-identity')
        current = read_progress(self.annotation_dir, ebook)
        key = self.key(book_uuid, fmt)
        if current.position and not current.issue:
            row = dict(path=str(ebook), content_hash=digest(ebook), position=current.position,
                       last_read=current.last_read.isoformat() if current.last_read else None)
            if self.records.get(key) != row:
                from .import_store import atomic_json
                updated = dict(self.records); updated[key] = row
                atomic_json(self.path, dict(schema=1, records=updated))
                self.records = updated
            return current
        old = self.records.get(key)
        if current.issue == 'missing-record' and isinstance(old, dict) and old.get('path') != str(ebook):
            if valid_position(old.get('position')) and old.get('content_hash') == digest(ebook):
                return Progress(old['position'], timestamp(old.get('last_read')))
        return current

    def resume_args(self, book_uuid, fmt, ebook):
        current = read_progress(self.annotation_dir, ebook)
        if current.issue != 'missing-record':
            return []
        preserved = self.refresh(book_uuid, fmt, ebook)
        return ['--open-at', preserved.position] if preserved.position else []


def progress_label(value):
    text = 'Saved position available' if value.position else 'Saved position unavailable'
    return text + '\nProgress: Unknown\nStatus: Unknown' + (
        '\nLast read: ' + value.last_read.isoformat() if value.last_read else '')
