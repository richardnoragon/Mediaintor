"""Folder scan / file import planning for Movie-inator. No Qt.

Scanning only reads: it never moves, renames or deletes files. A plan groups files
by (normalised title, year), so 'Alien (1979).mkv' and 'Alien (1979).mp4' become one
movie with two editions. Multi-part files (CD1/CD2, Part 1/2) share one edition.
Nothing is written until the user confirms the plan.
"""
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

from .movie_catalog import VIDEO_EXTENSIONS, movie_key, normalize_title, parse_filename
from .movie_store import canonical

PROBE_TIMEOUT = 20
# Only a trailing marker means a multi-part file: 'Movie (1999) CD1', not
# 'Deathly Hallows Part 1 (2010)', which is a title.
_PART = re.compile(r'[ ._-]+[\[(]?(?:cd|part|pt|disc|disk)[ ._-]?([0-9]{1,2})[\])]?$', re.IGNORECASE)
SAMPLE_LIMIT = 200 * 1024 * 1024


@dataclass
class ScanFile:
    path: str
    size: int | None = None
    container: str = ''
    duration: float | None = None
    width: int | None = None
    height: int | None = None
    video_codec: str = ''
    audio: tuple = ()
    subtitles: tuple = ()
    hint: str = ''
    part: int | None = None
    probe_error: str = ''

    def copy(self):
        return dict(kind='file', path=self.path, size=self.size, container=self.container, duration=self.duration,
                    width=self.width, height=self.height, video_codec=self.video_codec,
                    audio=list(self.audio), subtitles=list(self.subtitles))


@dataclass
class ScanGroup:
    title: str
    year: int | None
    files: list = field(default_factory=list)
    action: str = 'create'            # create | attach | skip
    movie_id: str | None = None       # attach target
    match_title: str = ''             # display name of the attach target
    warnings: list = field(default_factory=list)

    @property
    def key(self):
        return movie_key(self.title, self.year)

    def editions(self):
        """One edition per distinct version; parts of one version share an edition."""
        versions = {}
        for f in sorted(self.files, key=lambda f: (f.part or 0, f.path)):
            stem = _PART.sub('', Path(f.path).stem) if f.part else Path(f.path).stem
            versions.setdefault((stem.casefold(), f.container), []).append(f)
        result = []
        for files in versions.values():
            first = files[0]
            result.append(dict(label=edition_label(first), format='Digital', copies=[f.copy() for f in files]))
        return result

    def runtime(self):
        durations = [f.duration for f in self.files if f.duration]
        return max(1, round(max(durations) / 60)) if durations else None


@dataclass
class ScanResult:
    groups: list
    known: list          # paths already in the catalog
    skipped: list        # (path, reason)


# Release source named in the file, e.g. 'Alien.1979.1080p.BluRay.x264'.
_SOURCES = (
    (re.compile(r'\b(?:bd)?remux\b', re.I), 'Remux'),
    (re.compile(r'\b(?:blu-?ray|bdrip|brrip)\b', re.I), 'Blu-ray rip'),
    (re.compile(r'\bweb-?(?:dl|rip)?\b', re.I), 'WEB'),
    (re.compile(r'\bdvd-?rip\b|\bdvd\b', re.I), 'DVD rip'),
    (re.compile(r'\bhdtv\b', re.I), 'TV recording'),
)


def release_source(stem):
    return next((label for rx, label in _SOURCES if rx.search(stem.replace('.', ' ').replace('_', ' '))), '')


def edition_label(f):
    """'Digital (MKV 1080p)', 'Digital (MKV 4K, Blu-ray rip)', "Director's Cut (MKV 1080p)"."""
    height = f.height or 0
    quality = '4K' if height >= 1600 else '1080p' if height >= 900 else '720p' if height >= 650 else 'SD' if height else ''
    base = f.hint or 'Digital'
    detail = ' '.join(p for p in ((f.container or '').upper(), quality) if p)
    source = release_source(_PART.sub('', Path(f.path).stem))
    detail = ', '.join(p for p in (detail, source) if p)
    return f'{base} ({detail})' if detail else base


def discover(paths, cancelled=lambda: False):
    """Video files from files and (recursively) folders. Symlinked folders, hidden
    folders and non-video files are ignored. Returns (files, skipped)."""
    found, skipped, seen = [], [], set()
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            for root, dirs, files in os.walk(path, followlinks=False):
                if cancelled():
                    return found, skipped
                dirs[:] = sorted(d for d in dirs if not d.startswith('.') and not os.path.islink(os.path.join(root, d)))
                for name in sorted(files):
                    _consider(Path(root) / name, found, skipped, seen, quiet=True)
        else:
            _consider(path, found, skipped, seen, quiet=False)
    return found, skipped


def _consider(path, found, skipped, seen, quiet):
    if path.suffix.lower() not in VIDEO_EXTENSIONS:
        if not quiet:
            skipped.append((str(path), 'Not a supported video file type.'))
        return
    if path.name.startswith('.'):
        return
    try:
        if not path.is_file():
            skipped.append((str(path), 'Not a regular file or not readable.'))
            return
        identity = canonical(path)
    except OSError as exc:
        skipped.append((str(path), f'Cannot read: {exc}'))
        return
    if identity not in seen:
        seen.add(identity)
        found.append(identity)


def ffprobe_available():
    return shutil.which('ffprobe') is not None


def probe(path, runner=subprocess.run):
    """Technical details via ffprobe when installed. Never raises; errors are reported."""
    info = ScanFile(path=path)
    try:
        info.size = os.stat(path).st_size
    except OSError as exc:
        info.probe_error = str(exc)
        return info
    info.container = Path(path).suffix.lower().lstrip('.')
    if not ffprobe_available() and runner is subprocess.run:
        return info
    try:
        done = runner(['ffprobe', '-v', 'error', '-print_format', 'json', '-show_format', '-show_streams', '--', path],
                      capture_output=True, timeout=PROBE_TIMEOUT, check=False, text=True)
        if done.returncode != 0:
            info.probe_error = (done.stderr or 'ffprobe could not read this file').strip()[:300]
            return info
        data = json.loads(done.stdout or '{}')
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        info.probe_error = str(exc)[:300]
        return info
    try:
        duration = float(data.get('format', {}).get('duration') or 0)
        info.duration = duration if duration > 0 else None
    except (TypeError, ValueError):
        pass
    audio, subtitles = [], []
    for stream in data.get('streams', []):
        if not isinstance(stream, dict):
            continue
        kind = stream.get('codec_type')
        tags = stream.get('tags') if isinstance(stream.get('tags'), dict) else {}
        language = str(tags.get('language') or '').strip()
        if kind == 'video' and not info.video_codec and not (stream.get('disposition') or {}).get('attached_pic'):
            info.video_codec = str(stream.get('codec_name') or '')[:40]
            w, h = stream.get('width'), stream.get('height')
            info.width = w if type(w) is int and w > 0 else None
            info.height = h if type(h) is int and h > 0 else None
        elif kind == 'audio':
            channels = stream.get('channels')
            label = ' '.join(str(p) for p in (language or 'und', stream.get('codec_name') or '', f'{channels}ch' if channels else '') if p)
            audio.append(label[:80])
        elif kind == 'subtitle':
            subtitles.append((language or 'und')[:40])
    info.audio, info.subtitles = tuple(audio[:50]), tuple(subtitles[:100])
    return info


def plan(paths, catalog_movies, known_paths, *, probe_file=probe, cancelled=lambda: False, progress=lambda text: None):
    """Build a reviewable plan. `known_paths` maps canonical file path → movie id."""
    files, skipped = discover(paths, cancelled)
    known = [p for p in files if p in known_paths]
    by_key = {}
    existing = {}
    for movie in catalog_movies:
        existing.setdefault(movie_key(movie.title, movie.year), movie)
    for index, path in enumerate(p for p in files if p not in known_paths):
        if cancelled():
            break
        progress(f'Reading {index + 1}: {Path(path).name}')
        info = probe_file(path)
        title, year, hint = parse_filename(Path(path).stem, Path(path).parent.name)
        info.hint = hint
        part = _PART.search(Path(path).stem)
        info.part = int(part.group(1)) if part else None
        if info.part:
            title, year, _ = parse_filename(_PART.sub('', Path(path).stem), Path(path).parent.name)
        key = movie_key(title, year)
        group = by_key.get(key)
        if group is None:
            group = by_key[key] = ScanGroup(title, year)
            match = existing.get(key)
            if match is not None:
                group.action, group.movie_id, group.match_title = 'attach', match.id, match.display_title
        group.files.append(info)
        if info.probe_error:
            group.warnings.append(f'{Path(path).name}: technical details unavailable ({info.probe_error})')
        if 'sample' in Path(path).stem.casefold() and (info.size or 0) < SAMPLE_LIMIT:
            group.warnings.append(f'{Path(path).name} looks like a sample clip.')
        if year is None:
            group.warnings.append('No year found in the file name; check the title before importing.')
    groups = sorted(by_key.values(), key=lambda g: (normalize_title(g.title), g.year or 0))
    for g in groups:
        g.warnings = list(dict.fromkeys(g.warnings))
    return ScanResult(groups, known, skipped)


def revalidate(group, known_paths):
    """Files that changed or were catalogued since the preview. Empty list = still valid."""
    problems = []
    for f in group.files:
        try:
            size = os.stat(f.path).st_size
        except OSError:
            problems.append(f'{f.path} is no longer available.')
            continue
        if f.size is not None and size != f.size:
            problems.append(f'{f.path} changed size since the preview.')
        if f.path in known_paths:
            problems.append(f'{f.path} is already in the catalog.')
    return problems
