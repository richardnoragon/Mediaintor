"""Music-inator domain model: Album → Edition → Copy. No Qt, no I/O.

An album is the work (Pink Floyd — The Wall, 1979). An edition is a release of it
(original CD, 2011 Remaster, Deluxe Box, Japanese pressing) with its own disc
structure and track list. A copy is something owned: a physical item on a shelf or
a set of digital audio files. Artists are stored as album fields (primary artist
first, then other album artists, plus additional artists) and can be browsed, but
they are not separate records yet. Personal activity (favourite, rating) belongs to
a profile and is kept separate from shared catalog information.
"""
from dataclasses import dataclass
import re

from .movie_catalog import normalize_title, sort_key

AUDIO_EXTENSIONS = frozenset((
    '.flac', '.mp3', '.m4a', '.aac', '.ogg', '.oga', '.opus', '.wav', '.aif', '.aiff',
    '.ape', '.wv', '.wma', '.alac', '.dsf', '.dff', '.mpc', '.mka',
))
LOSSLESS_CODECS = frozenset(('flac', 'alac', 'ape', 'wavpack', 'wv', 'tta', 'mlp', 'truehd'))


def lossless(codec):
    codec = (codec or '').casefold()
    return codec in LOSSLESS_CODECS or codec.startswith(('pcm_', 'dsd_'))
EDITION_FORMATS = ('CD', 'Vinyl', 'Cassette', 'Digital', 'SACD', 'DVD-Audio', 'Blu-ray Audio', 'Other')
COPY_KINDS = ('digital', 'physical')
VARIOUS_ARTISTS = 'Various Artists'
UNKNOWN_ARTIST = 'Unknown artist'
FAVOURITE, RATED, NOT_RATED = 'Favourite', 'Rated', 'Not rated'
PERSONAL_FILTERS = (FAVOURITE, RATED, NOT_RATED)
BROWSE_MODES = ('Albums', 'Artists', 'Genres', 'Years')
UNKNOWN_YEAR = 'Unknown year'


@dataclass(frozen=True)
class Track:
    title: str
    disc: int = 1
    number: int | None = None
    artist: str = ''              # only when it differs from the album artist
    duration: float | None = None  # seconds

    @property
    def position(self):
        return f'{self.disc}-{self.number:02d}' if self.number else f'{self.disc}-?'


@dataclass(frozen=True)
class AudioFile:
    id: str
    path: str
    size: int | None = None
    disc: int | None = None
    number: int | None = None
    title: str = ''
    duration: float | None = None
    codec: str = ''
    bitrate: int | None = None       # bits per second
    sample_rate: int | None = None   # Hz
    bit_depth: int | None = None
    channels: int | None = None


@dataclass(frozen=True)
class Copy:
    id: str
    kind: str                         # 'digital' or 'physical'
    location: str = ''                # shelf/room for physical copies
    quality: str = ''                 # e.g. 'FLAC 16-bit/44.1 kHz', 'MP3 320 kbps'
    notes: str = ''
    files: tuple[AudioFile, ...] = ()

    @property
    def folder(self):
        """Common folder of the files (display only; files may live anywhere)."""
        if not self.files:
            return ''
        import os.path
        try:
            return os.path.commonpath([f.path for f in self.files]) if len(self.files) > 1 else os.path.dirname(self.files[0].path)
        except ValueError:
            return ''

    def describe(self):
        if self.kind == 'physical':
            return 'Physical copy' + (f' · {self.location}' if self.location else '')
        parts = [p for p in (self.quality, f'{len(self.files)} file(s)') if p]
        return 'Digital files · ' + ' · '.join(parts)


@dataclass(frozen=True)
class Edition:
    id: str
    label: str
    format: str = 'CD'
    release_year: int | None = None
    record_label: str = ''
    catalog_number: str = ''
    disc_count: int = 1
    notes: str = ''
    tracks: tuple[Track, ...] = ()
    copies: tuple[Copy, ...] = ()

    @property
    def discs(self):
        """((disc number, (tracks…)), …) including discs that have no tracks yet."""
        numbers = sorted({t.disc for t in self.tracks} | set(range(1, max(1, self.disc_count) + 1)))
        return tuple((n, tuple(t for t in self.tracks if t.disc == n)) for n in numbers)

    @property
    def duration(self):
        values = [t.duration for t in self.tracks if t.duration]
        return sum(values) if values else None

    def describe(self):
        facts = [self.format]
        if self.release_year:
            facts.append(str(self.release_year))
        if self.record_label:
            facts.append(self.record_label + (f' {self.catalog_number}' if self.catalog_number else ''))
        if self.disc_count > 1:
            facts.append(f'{self.disc_count} discs')
        if self.tracks:
            facts.append(f'{len(self.tracks)} tracks')
        return f'{self.label} [' + ', '.join(facts) + ']'


@dataclass(frozen=True)
class Album:
    id: str
    title: str
    artists: tuple[str, ...] = ()             # album artist(s); the first is the primary artist
    additional_artists: tuple[str, ...] = ()  # featured, guests, orchestra, conductor…
    year: int | None = None
    genres: tuple[str, ...] = ()
    cover: str = ''
    notes: str = ''
    revision: int = 0
    editions: tuple[Edition, ...] = ()
    favourite: bool = False
    rating: int | None = None                 # personal, 1–10

    @property
    def primary_artist(self):
        return self.artists[0] if self.artists else ''

    @property
    def display_artist(self):
        return ' & '.join(self.artists) if self.artists else UNKNOWN_ARTIST

    @property
    def display_title(self):
        return f'{self.display_artist} — {self.title}' + (f' ({self.year})' if self.year else '')

    @property
    def copies(self):
        return tuple(c for e in self.editions for c in e.copies)

    @property
    def digital_copies(self):
        return tuple(c for c in self.copies if c.kind == 'digital')

    @property
    def files(self):
        return tuple(f for c in self.digital_copies for f in c.files)

    @property
    def formats(self):
        return tuple(sorted({e.format for e in self.editions}))

    @property
    def track_count(self):
        return max((len(e.tracks) for e in self.editions), default=0)

    @property
    def track_artists(self):
        return tuple(dict.fromkeys(t.artist for e in self.editions for t in e.tracks if t.artist))

    @property
    def all_artists(self):
        """Every credited name, for search and the Artists browser."""
        return tuple(dict.fromkeys((*self.artists, *self.additional_artists, *self.track_artists)))

    def personal_tags(self):
        tags = [RATED if self.rating is not None else NOT_RATED]
        if self.favourite:
            tags.append(FAVOURITE)
        return tags


def _sample(aid, title, artists, year, genres, editions, favourite=False, rating=None):
    return Album(aid, title, artists, year=year, genres=genres, editions=editions, favourite=favourite, rating=rating)


SAMPLE_ALBUMS = (
    _sample('sample-goldberg', 'Goldberg Variations', ('Glenn Gould',), 1955, ('Classical',),
            (Edition('sample-e1', 'Original LP', 'Vinyl', 1956, 'Columbia Masterworks',
                     tracks=(Track('Aria', 1, 1), Track('Variatio 1', 1, 2)),
                     copies=(Copy('sample-c1', 'physical', location='Record shelf'),)),),
            favourite=True, rating=9),
    _sample('sample-kind-of-blue', 'Kind of Blue', ('Miles Davis',), 1959, ('Jazz',),
            (Edition('sample-e2', 'CD', 'CD', 1997, tracks=(Track('So What', 1, 1), Track('Freddie Freeloader', 1, 2)),
                     copies=(Copy('sample-c2', 'physical', location='CD rack 2'),)),)),
    _sample('sample-rhapsody', 'Rhapsody in Blue', ('George Gershwin',), 1924, ('Classical', 'Jazz'),
            (Edition('sample-e3', 'Digital', 'Digital'),)),
)


def find_albums(albums, query, genres=(), formats=(), personal=(), browse=None):
    """Literal text match on album title, any credited artist, track titles and year;
    AND across filter categories, OR within one — the same rule Book-inator uses.
    `browse` is an optional (mode, value) from the Artists/Genres/Years browser."""
    query = query.strip().casefold()

    def text_match(a):
        if not query:
            return True
        values = (a.title, str(a.year or ''), *a.all_artists, *(t.title for e in a.editions for t in e.tracks))
        return any(query in v.casefold() for v in values)

    def browse_match(a):
        if not browse or not browse[1] or browse[0] == 'Albums':
            return True
        mode, value = browse
        if mode == 'Artists':
            return value.casefold() in {n.casefold() for n in a.all_artists} or (value == UNKNOWN_ARTIST and not a.artists)
        if mode == 'Genres':
            return value in a.genres
        if mode == 'Years':
            return (str(a.year) if a.year else UNKNOWN_YEAR) == value
        return True

    return sorted(
        (a for a in albums
         if text_match(a) and browse_match(a)
         and (not genres or set(genres).intersection(a.genres))
         and (not formats or set(formats).intersection(a.formats))
         and (not personal or set(personal).intersection(a.personal_tags()))),
        key=album_sort_key,
    )


def album_sort_key(album):
    return (sort_key(album.primary_artist or '￿'), album.year or 0, sort_key(album.title), album.id)


def browse_values(albums, mode):
    """[(value, album count)] for the Artists / Genres / Years browser."""
    counts = {}
    for album in albums:
        if mode == 'Artists':
            names = album.all_artists or (UNKNOWN_ARTIST,)
            seen = set()
            for name in names:
                key = name.casefold()
                if key not in seen:
                    seen.add(key)
                    counts[name] = counts.get(name, 0) + 1
        elif mode == 'Genres':
            for genre in album.genres:
                counts[genre] = counts.get(genre, 0) + 1
        elif mode == 'Years':
            value = str(album.year) if album.year else UNKNOWN_YEAR
            counts[value] = counts.get(value, 0) + 1
    if mode == 'Years':
        return sorted(counts.items(), key=lambda kv: (kv[0] == UNKNOWN_YEAR, kv[0]), reverse=False)
    return sorted(counts.items(), key=lambda kv: sort_key(kv[0]))


def album_key(artist, title):
    """Identity for scan grouping: (primary artist, title), accents/case ignored.
    The year is not part of it: a 2011 remaster is another edition of the 1979 album."""
    return (normalize_title(artist or ''), normalize_title(title or ''))


def tracklist_signature(tracks):
    return tuple(sorted((t.get('disc') or 1, t.get('number') or 0, normalize_title(t.get('title') or ''))
                        for t in tracks))


def format_duration(seconds):
    if not seconds:
        return ''
    seconds = int(round(seconds))
    hours, rest = divmod(seconds, 3600)
    return f'{hours}:{rest // 60:02d}:{rest % 60:02d}' if hours else f'{rest // 60}:{rest % 60:02d}'


def parse_duration(text):
    """'3:45', '1:02:03' or '225' → seconds; '' → None; invalid → ValueError."""
    text = (text or '').strip()
    if not text:
        return None
    parts = text.split(':')
    if len(parts) > 3 or not all(p.isdigit() for p in parts):
        raise ValueError(f'Use minutes:seconds for track length, not "{text}".')
    value = 0
    for part in parts:
        value = value * 60 + int(part)
    return float(value)


# ----------------------------------------------------------------------------- name parsing
_DISC_FOLDER = re.compile(r'^(?:cd|disc|disk|disque|scheibe)[ ._-]*([0-9]{1,2})\b.*$', re.IGNORECASE)
_YEAR = re.compile(r'(?<![0-9])(19[0-9]{2}|20[0-9]{2})(?![0-9])')
_BRACKETS = re.compile(r'\s*[(\[{]([^()\[\]{}]*)[)\]}]')
_EDITION_WORDS = re.compile(
    r'\b(remaster(?:ed)?|deluxe|edition|anniversary|expanded|bonus|special|collector\'?s|japan(?:ese)?|mono|stereo|'
    r'reissue|limited|legacy|super|box|live|acoustic|demo|version)\b', re.IGNORECASE)
_TECH_WORDS = re.compile(
    r'\b(flac|mp3|aac|alac|ogg|opus|wav|ape|web|cd(?:rip)?|vinyl(?:rip)?|lp|[0-9]{2,3}\s*kbps|v0|v2|320|256|192|'
    r'[0-9]{2}\s*-?\s*bit|[0-9]{2,3}(?:[.,][0-9])?\s*khz|hi-?res|lossless|24-96|24-48|24-192|16-44)\b', re.IGNORECASE)
GENERIC_FOLDERS = frozenset(('music', 'musik', 'musique', 'audio', 'albums', 'album', 'mp3', 'flac', 'downloads',
                             'download', 'library', 'media', 'collection', 'compilations', 'various', 'various artists'))


def disc_folder(name):
    """'CD2', 'Disc 1', 'disk-3' → disc number, else None."""
    match = _DISC_FOLDER.match(name.strip())
    return int(match.group(1)) if match else None


def split_edition(text):
    """'The Wall (2011 Remaster) [FLAC]' → ('The Wall', '2011 Remaster', None).
    Also returns a year that stands alone in brackets: 'Animals (1977)' → ('Animals', '', 1977)."""
    hint, year = '', None
    remaining = text
    for match in list(_BRACKETS.finditer(text)):
        inner = match.group(1).strip()
        cleaned = ' '.join(_TECH_WORDS.sub(' ', inner).split()).strip(' ,;-')
        if re.fullmatch(r'(19|20)[0-9]{2}', inner):
            year = int(inner)
        elif _EDITION_WORDS.search(inner):
            hint = hint or cleaned or inner
        elif cleaned and not _TECH_WORDS.search(inner):
            continue            # an ordinary bracket that belongs to the title, e.g. 'Songs (For Lovers)'
        remaining = remaining.replace(match.group(0), ' ')
    title = ' '.join(remaining.replace('_', ' ').split()).strip(' -')
    return title or text.strip(), hint, year


def parse_album_folder(name, parent=''):
    """Guess (artist, album, year, edition hint) from an album folder name.

    Understands 'Artist - Album (Year)', 'Artist - Year - Album', 'Year - Album' and
    'Album (Year)'. Without an artist in the name the parent folder is used when it
    is not a generic container such as 'Music' or 'Downloads'."""
    text = ' '.join(name.replace('_', ' ').split())
    artist, year = '', None
    parts = [p.strip() for p in re.split(r'\s+[-–—]\s+', text) if p.strip()]
    if len(parts) >= 3 and _YEAR.fullmatch(parts[1]):
        artist, year, album = parts[0], int(parts[1]), ' - '.join(parts[2:])
    elif len(parts) >= 2 and _YEAR.fullmatch(parts[0]):
        year, album = int(parts[0]), ' - '.join(parts[1:])
    elif len(parts) >= 2:
        artist, album = parts[0], ' - '.join(parts[1:])
    else:
        album = text
    album, hint, bracket_year = split_edition(album)
    year = year or bracket_year
    if not artist and parent and parent.strip().casefold() not in GENERIC_FOLDERS:
        artist = parent.strip()
    return artist, album or name, year, hint


_TRACK = re.compile(r'^\s*(?:([0-9])[-.]([0-9]{1,2})|([0-9]{1,3}))(?:\s*[.)_-]\s*|\s+)(.+)$')


def parse_track_filename(stem):
    """'01 - Title', '1-03 Title', '07. Title', 'Artist - Album - 05 - Title' →
    (disc or None, track number or None, title)."""
    text = stem.replace('_', ' ').strip()
    match = _TRACK.match(text)
    if match:
        if match.group(1):
            return int(match.group(1)), int(match.group(2)), match.group(4).strip(' -')
        return None, int(match.group(3)), match.group(4).strip(' -')
    parts = [p.strip() for p in re.split(r'\s+-\s+', text)]
    for index, part in enumerate(parts[:-1]):
        if part.isdigit() and len(part) <= 3:
            return None, int(part), ' - '.join(parts[index + 1:])
    return None, None, text
