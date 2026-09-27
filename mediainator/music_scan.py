"""Folder scan / file import planning for Music-inator. No Qt.

Scanning only reads: it never moves, renames, retags or deletes files. Tags come
first (read with ffprobe when installed); folder and file names fill the gaps:
'Artist - Album (Year)/01 - Title.flac', 'Artist/Album (Year)/…', and disc
subfolders such as 'CD1' / 'Disc 2' join the album above them.

The files of one album folder form one *copy*. Copies of the same album (same
artist and title) form one *group*. Within a group, copies with the same edition
hint and the same track list are the same *edition* (for example a FLAC rip and an
MP3 rip of the 2011 Remaster); different track lists become separate editions.
Nothing is written until the user confirms the plan.
"""
from collections import Counter
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

from .music_catalog import (AUDIO_EXTENSIONS, UNKNOWN_ARTIST, VARIOUS_ARTISTS, album_key, disc_folder, lossless,
                            normalize_title, parse_album_folder, parse_track_filename, split_edition, tracklist_signature)
from .music_store import canonical

PROBE_TIMEOUT = 20


@dataclass
class ScanFile:
    path: str
    size: int | None = None
    container: str = ''
    duration: float | None = None
    codec: str = ''
    bitrate: int | None = None
    sample_rate: int | None = None
    bit_depth: int | None = None
    channels: int | None = None
    tags: dict = field(default_factory=dict)   # lower-case keys: album, album_artist, artist, title, track, disc, date, genre, compilation
    probe_error: str = ''
    # filled in by planning
    disc: int | None = None
    number: int | None = None
    title: str = ''
    artist: str = ''

    def file(self):
        return dict(path=self.path, size=self.size, disc=self.disc, number=self.number, title=self.title,
                    duration=self.duration, codec=self.codec or self.container, bitrate=self.bitrate,
                    sample_rate=self.sample_rate, bit_depth=self.bit_depth, channels=self.channels)


@dataclass
class CopyUnit:
    """The audio files of one album found in one folder (disc subfolders included)."""
    folder: str
    files: list = field(default_factory=list)
    title: str = ''
    artist: str = ''
    year: int | None = None
    genres: list = field(default_factory=list)
    hint: str = ''
    from_tags: bool = True

    def tracks(self, album_artist=''):
        return [dict(title=f.title or Path(f.path).stem, disc=f.disc or 1, number=f.number,
                     artist=f.artist if f.artist and f.artist.casefold() != (album_artist or '').casefold() else '',
                     duration=f.duration) for f in self.files]

    def copy(self):
        return dict(kind='digital', quality=quality(self.files), files=[f.file() for f in self.files])

    @property
    def disc_count(self):
        return max((f.disc or 1 for f in self.files), default=1)


@dataclass
class ScanGroup:
    title: str
    artist: str
    year: int | None = None
    genres: list = field(default_factory=list)
    units: list = field(default_factory=list)
    action: str = 'create'            # create | attach | skip
    album_id: str | None = None       # attach target
    match_title: str = ''             # display name of the attach target
    warnings: list = field(default_factory=list)
    existing: tuple = ()              # the attach target's editions, for copy matching

    @property
    def key(self):
        return album_key(self.artist, self.title)

    @property
    def files(self):
        return [f for u in self.units for f in u.files]

    @property
    def display_title(self):
        return f'{self.artist or UNKNOWN_ARTIST} — {self.title}' + (f' ({self.year})' if self.year else '')

    def editions(self, existing=None):
        """One edition per distinct (edition hint, track list); several copies of the
        same release share it. When attaching, a copy whose track list matches an
        existing edition is added to that edition instead (`edition_id`)."""
        existing = self.existing if existing is None else existing
        clusters = {}
        for unit in sorted(self.units, key=lambda u: u.folder):
            tracks = unit.tracks(self.artist)
            key = (unit.hint.casefold(), tracklist_signature(tracks))
            cluster = clusters.setdefault(key, dict(unit=unit, tracks=tracks, copies=[]))
            cluster['copies'].append(unit.copy())
        result, labels = [], Counter()
        for (hint, signature), cluster in clusters.items():
            unit = cluster['unit']
            label = unit.hint or 'Standard'
            labels[label.casefold()] += 1
            edition = dict(label=label, format='Digital', release_year=unit.year, disc_count=unit.disc_count,
                           tracks=cluster['tracks'], copies=cluster['copies'])
            match = next((e for e in existing if e.tracks and tracklist_signature(
                [dict(disc=t.disc, number=t.number, title=t.title) for t in e.tracks]) == signature
                and (not hint or hint == e.label.casefold())), None)
            if match is not None:
                edition['edition_id'] = match.id
                edition['label'] = match.label
            result.append(edition)
        for edition in result:
            if labels[edition['label'].casefold()] > 1 and 'edition_id' not in edition:
                edition['label'] = f"{edition['label']} ({len(edition['tracks'])} tracks)"
        return result


@dataclass
class ScanResult:
    groups: list
    known: list          # paths already in the catalog
    skipped: list        # (path, reason)


def quality(files):
    """'FLAC 16-bit/44.1 kHz', 'MP3 320 kbps', 'MP3 ~245 kbps', 'FLAC (mixed)'."""
    if not files:
        return ''
    codecs = Counter((f.codec or f.container or '').casefold() for f in files)
    codec, _ = codecs.most_common(1)[0]
    name = {'mp3': 'MP3', 'flac': 'FLAC', 'aac': 'AAC', 'alac': 'ALAC', 'vorbis': 'Ogg Vorbis', 'opus': 'Opus',
            'wmav2': 'WMA', 'ape': 'APE', 'wavpack': 'WavPack'}.get(codec, 'WAV' if codec.startswith('pcm_') else codec.upper())
    same = [f for f in files if (f.codec or f.container or '').casefold() == codec]
    if lossless(codec):
        depths = {f.bit_depth for f in same if f.bit_depth}
        rates = {f.sample_rate for f in same if f.sample_rate}
        detail = ''
        if len(depths) == 1 and len(rates) == 1:
            detail = f' {depths.pop()}-bit/{rates.pop() / 1000:g} kHz'
        elif len(rates) == 1:
            detail = f' {rates.pop() / 1000:g} kHz'
    else:
        rates = [f.bitrate for f in same if f.bitrate]
        detail = ''
        if rates:
            average = sum(rates) / len(rates) / 1000
            detail = f' {round(average)} kbps' if max(rates) - min(rates) < 2000 else f' ~{round(average)} kbps'
    return name + detail + (' (mixed)' if len(codecs) > 1 else '')


def discover(paths, cancelled=lambda: False):
    """Audio files from files and (recursively) folders. Symlinked folders, hidden
    folders and non-audio files are ignored. Returns (files, skipped)."""
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
    if path.suffix.lower() not in AUDIO_EXTENSIONS:
        if not quiet:
            skipped.append((str(path), 'Not a supported audio file type.'))
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


_TAG_NAMES = {
    'album': 'album', 'album_artist': 'album_artist', 'albumartist': 'album_artist', 'album artist': 'album_artist',
    'artist': 'artist', 'title': 'title', 'track': 'track', 'tracknumber': 'track', 'disc': 'disc',
    'discnumber': 'disc', 'date': 'date', 'year': 'date', 'originaldate': 'originaldate', 'genre': 'genre',
    'compilation': 'compilation', 'tcmp': 'compilation', 'tpe2': 'album_artist',
}


def _positive(value):
    """'3', '3/12', '03 of 12' → 3; anything else → None."""
    match = re.match(r'\s*([0-9]{1,3})', str(value or ''))
    number = int(match.group(1)) if match else 0
    return number or None


def _year(value):
    match = re.search(r'(1[0-9]{3}|20[0-9]{2})', str(value or ''))
    return int(match.group(1)) if match else None


def probe(path, runner=subprocess.run):
    """Tags and technical details via ffprobe when installed. Never raises."""
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
    fmt = data.get('format') if isinstance(data.get('format'), dict) else {}
    try:
        duration = float(fmt.get('duration') or 0)
        info.duration = duration if duration > 0 else None
    except (TypeError, ValueError):
        pass
    tags = {}
    sources = [fmt.get('tags')] + [s.get('tags') for s in data.get('streams', []) if isinstance(s, dict)]
    for source in sources:     # container tags first; Ogg/Opus keep them on the stream
        if isinstance(source, dict):
            for key, value in source.items():
                name = _TAG_NAMES.get(str(key).casefold())
                if name and name not in tags and str(value).strip():
                    tags[name] = str(value).strip()[:500]
    info.tags = tags
    for stream in data.get('streams', []):
        if isinstance(stream, dict) and stream.get('codec_type') == 'audio':
            info.codec = str(stream.get('codec_name') or '')[:40]
            for attr, key in (('sample_rate', 'sample_rate'), ('channels', 'channels'),
                              ('bit_depth', 'bits_per_raw_sample'), ('bitrate', 'bit_rate')):
                try:
                    value = int(stream.get(key) or 0)
                except (TypeError, ValueError):
                    value = 0
                setattr(info, attr, value if value > 0 else None)
            if not info.bit_depth:
                try:
                    value = int(stream.get('bits_per_sample') or 0)
                except (TypeError, ValueError):
                    value = 0
                info.bit_depth = value if value > 0 and lossless(info.codec) else None
            break
    if not info.bitrate:
        try:
            value = int(fmt.get('bit_rate') or 0)
            info.bitrate = value if value > 0 else None
        except (TypeError, ValueError):
            pass
    return info


def album_folder(path, roots=()):
    """(album folder, disc number from a disc subfolder or None)."""
    parent = Path(path).parent
    disc = disc_folder(parent.name)
    if disc and parent.parent != parent and str(parent) not in roots:
        return parent.parent, disc
    return parent, None


def _most_common(values):
    values = [v for v in values if v]
    return Counter(values).most_common(1)[0][0] if values else None


def build_unit(folder, files, disc_hint, roots=()):
    """Decide title/artist/year/genres/hint for the files of one album folder."""
    folder = Path(folder)
    parent = folder.parent.name if str(folder.parent) not in roots and folder.parent != folder else ''
    if str(folder) in roots and not any(f.tags.get('album') for f in files):
        parent = ''
    f_artist, f_album, f_year, f_hint = parse_album_folder(folder.name, parent)
    tag_album = _most_common(f.tags.get('album') for f in files)
    unit = CopyUnit(str(folder), files, from_tags=bool(tag_album))
    if tag_album:
        unit.title, unit.hint, bracket_year = split_edition(tag_album)
        unit.hint = unit.hint or f_hint
    else:
        unit.title, unit.hint, bracket_year = f_album, f_hint, None
    track_artists = {f.tags.get('artist', '').casefold() for f in files if f.tags.get('artist')}
    compilation = any(str(f.tags.get('compilation', '')).strip() in ('1', 'true', 'True', 'yes') for f in files)
    unit.artist = (_most_common(f.tags.get('album_artist') for f in files)
                   or (VARIOUS_ARTISTS if compilation or len(track_artists) > 1 else None)
                   or _most_common(f.tags.get('artist') for f in files)
                   or f_artist or '')
    unit.year = (_most_common(_year(f.tags.get('date')) for f in files)
                 or _most_common(_year(f.tags.get('originaldate')) for f in files) or bracket_year or f_year)
    genres = []
    for f in files:
        for genre in re.split(r'\s*[;/]\s*', f.tags.get('genre', '')):
            if genre and genre.casefold() not in {g.casefold() for g in genres}:
                genres.append(genre)
    unit.genres = genres[:10]
    for f in files:
        name_disc, name_number, name_title = parse_track_filename(Path(f.path).stem)
        f.disc = _positive(f.tags.get('disc')) or disc_hint.get(f.path) or name_disc or 1
        f.number = _positive(f.tags.get('track')) or name_number
        f.title = f.tags.get('title') or name_title
        f.artist = f.tags.get('artist', '')
    unit.files = sorted(files, key=lambda f: (f.disc or 1, f.number or 0, Path(f.path).name.casefold()))
    return unit


def plan(paths, catalog_albums, known_paths, *, probe_file=probe, cancelled=lambda: False, progress=lambda text: None):
    """Build a reviewable plan. `known_paths` maps canonical file path → album id."""
    roots = {canonical(p) for p in paths if Path(p).is_dir()}
    files, skipped = discover(paths, cancelled)
    known = [p for p in files if p in known_paths]
    folders = {}
    disc_hint = {}
    for index, path in enumerate(p for p in files if p not in known_paths):
        if cancelled():
            break
        progress(f'Reading {index + 1}: {Path(path).name}')
        info = probe_file(path)
        folder, disc = album_folder(path, roots)
        if disc:
            disc_hint[path] = disc
        # One folder may hold several albums (a flat download folder): split by album tag.
        tag = normalize_title(info.tags.get('album', ''))
        folders.setdefault((str(folder), tag), []).append(info)
    existing = {}
    for album in catalog_albums:
        existing.setdefault(album_key(album.primary_artist, album.title), album)
    groups = {}
    known_folders = {str(album_folder(p, roots)[0]) for p in known}
    for (folder, _), items in sorted(folders.items()):
        unit = build_unit(folder, items, disc_hint, roots)
        key = album_key(unit.artist, unit.title)
        group = groups.get(key)
        if group is None:
            group = groups[key] = ScanGroup(unit.title, unit.artist, unit.year, list(unit.genres))
            match = existing.get(key)
            if match is not None:
                group.action, group.album_id, group.match_title = 'attach', match.id, match.display_title
                group.existing = match.editions
        else:
            group.year = min(y for y in (group.year, unit.year) if y) if (group.year or unit.year) else None
            group.genres += [g for g in unit.genres if g.casefold() not in {x.casefold() for x in group.genres}]
        group.units.append(unit)
        name = Path(folder).name
        for f in items:
            if f.probe_error:
                group.warnings.append(f'{Path(f.path).name}: tags and technical details unavailable ({f.probe_error})')
        if not unit.from_tags:
            group.warnings.append(f'{name}: no album tags; title and artist were taken from folder and file names.')
        if not unit.artist:
            group.warnings.append(f'{name}: no artist found; enter one before importing.')
        numbers = [(f.disc, f.number) for f in unit.files if f.number]
        if len(numbers) != len(set(numbers)):
            group.warnings.append(f'{name}: duplicate track numbers — check for duplicate or mixed files.')
        if len(numbers) < len(unit.files):
            group.warnings.append(f'{name}: some files have no track number; check the track order.')
        if folder in known_folders:
            group.warnings.append(f'{name}: other files of this folder are already in the catalog; '
                                  'these files would be added as a separate copy.')
    result = sorted(groups.values(), key=lambda g: (normalize_title(g.artist), normalize_title(g.title)))
    for g in result:
        g.warnings = list(dict.fromkeys(g.warnings))
    return ScanResult(result, known, skipped)


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


def files_for(paths, probe_file=probe):
    """Probe explicitly chosen files/folders for one manual digital copy (editor and
    Editions dialog). Returns (copy dict or None, tracks, unit, skipped)."""
    found, skipped = discover(paths)
    if not found:
        return None, [], None, skipped
    infos = [probe_file(p) for p in found]
    folder = Path(os.path.commonpath([str(Path(p).parent) for p in found]))
    disc_hint = {}
    for info in infos:
        parent = Path(info.path).parent
        if parent != folder and disc_folder(parent.name):
            disc_hint[info.path] = disc_folder(parent.name)
    unit = build_unit(folder, infos, disc_hint, roots={str(folder)} if len(paths) == 1 and Path(paths[0]).is_dir() else ())
    return unit.copy(), unit.tracks(unit.artist), unit, skipped
