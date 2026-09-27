"""Movie-inator domain model: Movie → Edition → Copy. No Qt, no I/O.

A movie is the work. An edition is a release or version of it (Blu-ray Director's
Cut, 4K UHD, MKV rip). A copy is something owned: a physical item on a shelf or a
digital file on disk. Personal activity (watched, rating) belongs to a profile and
is kept separate from shared catalog information.
"""
from dataclasses import dataclass, field
import re
import unicodedata

VIDEO_EXTENSIONS = frozenset((
    '.mkv', '.mp4', '.m4v', '.avi', '.mov', '.wmv', '.mpg', '.mpeg', '.m2ts', '.ts',
    '.webm', '.ogv', '.flv', '.vob', '.iso', '.divx', '.3gp',
))
EDITION_FORMATS = ('Digital', 'DVD', 'Blu-ray', '4K UHD', 'VHS', 'Other')
COPY_KINDS = ('file', 'physical')
WATCHED = 'Watched'
NOT_WATCHED = 'Not watched'
STATUSES = (NOT_WATCHED, WATCHED)


@dataclass(frozen=True)
class Copy:
    id: str
    kind: str                     # 'file' or 'physical'
    path: str = ''                # absolute path for files
    location: str = ''            # shelf/room for physical copies
    size: int | None = None
    container: str = ''
    duration: float | None = None
    width: int | None = None
    height: int | None = None
    video_codec: str = ''
    audio: tuple[str, ...] = ()
    subtitles: tuple[str, ...] = ()

    @property
    def resolution(self):
        return f'{self.width}×{self.height}' if self.width and self.height else ''

    def describe(self):
        if self.kind == 'physical':
            return 'Physical copy' + (f' · {self.location}' if self.location else '')
        parts = [p for p in (self.container.upper(), self.resolution, self.video_codec) if p]
        return 'File' + (' · ' + ' · '.join(parts) if parts else '')


@dataclass(frozen=True)
class Edition:
    id: str
    label: str
    format: str = 'Digital'
    notes: str = ''
    copies: tuple[Copy, ...] = ()


@dataclass(frozen=True)
class Movie:
    id: str
    title: str
    year: int | None = None
    original_title: str = ''
    directors: tuple[str, ...] = ()
    cast: tuple[str, ...] = ()
    genres: tuple[str, ...] = ()
    runtime: int | None = None    # minutes
    synopsis: str = ''
    cover: str = ''
    notes: str = ''
    revision: int = 0
    editions: tuple[Edition, ...] = ()
    watched: bool = False
    rating: int | None = None     # personal, 1–10

    @property
    def display_title(self):
        return f'{self.title} ({self.year})' if self.year else self.title

    @property
    def status(self):
        return WATCHED if self.watched else NOT_WATCHED

    @property
    def copies(self):
        return tuple(c for e in self.editions for c in e.copies)

    @property
    def files(self):
        return tuple(c for c in self.copies if c.kind == 'file')

    @property
    def formats(self):
        return tuple(sorted({e.format for e in self.editions}))


def _sample(mid, title, year, directors, genres, editions, watched=False):
    return Movie(mid, title, year, directors=directors, genres=genres, editions=editions, watched=watched)


SAMPLE_MOVIES = (
    _sample('sample-metropolis', 'Metropolis', 1927, ('Fritz Lang',), ('Science fiction', 'Drama'),
            (Edition('sample-e1', 'Restored Blu-ray', 'Blu-ray', copies=(Copy('sample-c1', 'physical', location='Living room shelf'),)),)),
    _sample('sample-nosferatu', 'Nosferatu', 1922, ('F. W. Murnau',), ('Horror',),
            (Edition('sample-e2', 'DVD', 'DVD', copies=(Copy('sample-c2', 'physical', location='Box 3'),)),), watched=True),
    _sample('sample-general', 'The General', 1926, ('Buster Keaton', 'Clyde Bruckman'), ('Comedy', 'Action'),
            (Edition('sample-e3', 'Digital', 'Digital'),)),
)


def find_movies(movies, query, genres=(), formats=(), statuses=()):
    """Literal text match on title/original title/director/cast/year; AND across
    categories, OR within one — the same rule Book-inator uses."""
    query = query.strip().casefold()

    def text_match(m):
        if not query:
            return True
        values = (m.title, m.original_title, str(m.year or ''), *m.directors, *m.cast)
        return any(query in v.casefold() for v in values)
    return sorted(
        (m for m in movies
         if text_match(m)
         and (not genres or set(genres).intersection(m.genres))
         and (not formats or set(formats).intersection(m.formats))
         and (not statuses or m.status in statuses)),
        key=lambda m: (sort_key(m.title), m.year or 0, m.id),
    )


_ARTICLES = ('the ', 'a ', 'an ', 'der ', 'die ', 'das ', 'le ', 'la ', 'les ', 'el ')


def sort_key(title):
    value = title.strip().casefold()
    for article in _ARTICLES:
        if value.startswith(article) and len(value) > len(article):
            return value[len(article):]
    return value


def normalize_title(title):
    """Identity key for grouping: accents, punctuation and case are ignored."""
    value = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode().casefold()
    value = value.replace('&', ' and ')
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', value).split())


# Release tags that end the title part of a scene-style filename.
_TAGS = re.compile(r'''\b(
    2160p|1080p|1080i|720p|576p|480p|4k|uhd|hdr10?|dv|
    bluray|blu-ray|bdrip|brrip|bdremux|remux|web-?dl|webrip|web|hdtv|dvdrip|dvd|dvdscr|hdrip|
    x264|x265|h\.?264|h\.?265|hevc|avc|xvid|divx|av1|
    aac|ac3|dts|dts-hd|truehd|atmos|flac|ddp?5\.1|5\.1|7\.1|
    extended|unrated|directors\.?cut|theatrical|remastered|proper|repack|limited|internal|
    multi|dual|subbed|german|english|french
)\b''', re.IGNORECASE | re.VERBOSE)
_FOLDER = re.compile(r'^(.+?)\s*[(\[](19[0-9]{2}|20[0-9]{2})[)\]]$')
_YEAR = re.compile(r'(?<![0-9])(19[0-9]{2}|20[0-9]{2})(?![0-9])')
_EDITION_HINTS = (
    (re.compile(r"director'?s[ ._-]?cut", re.I), "Director's Cut"),
    (re.compile(r'\bextended\b', re.I), 'Extended'),
    (re.compile(r'\bunrated\b', re.I), 'Unrated'),
    (re.compile(r'\btheatrical\b', re.I), 'Theatrical'),
    (re.compile(r'\bremastered\b', re.I), 'Remastered'),
)


def parse_filename(stem, parent=''):
    """Guess (title, year, edition hint) from 'Alien (1979)', 'Alien.1979.1080p.BluRay'
    or a generic file name inside a 'Title (Year)' folder."""
    def guess(text):
        raw = text.replace('_', ' ')
        year = None
        cut = len(raw)
        # A year counts only after some title text: '1917 (2019)' → title 1917, year 2019.
        for match in _YEAR.finditer(raw):
            if match.start() > 0 and raw[:match.start()].strip(' .-([{'):
                year = int(match.group(1))
                cut = match.start()
        tag = _TAGS.search(raw)
        if tag and tag.start() > 0 and tag.start() < cut:
            cut = tag.start()
        title = raw[:cut]
        if '.' in title and ' ' not in title.strip('. '):
            title = title.replace('.', ' ')
        title = re.sub(r'[\[\](){}]', ' ', title)
        title = ' '.join(title.replace(' - ', ' ').split()).strip(' -.')
        return title, year
    title, year = guess(stem)
    hint = next((label for rx, label in _EDITION_HINTS if rx.search(stem)), '')
    folder = _FOLDER.match(parent.strip()) if parent else None
    if folder and not year:
        # Only the conventional 'Title (Year)' folder layout is trusted.
        ptitle, pyear = ' '.join(folder.group(1).split()), int(folder.group(2))
        if not title or normalize_title(title) != normalize_title(ptitle):
            title = ptitle
        year = pyear
    if not title:
        title = stem.strip() or 'Untitled'
    return title, year, hint


def movie_key(title, year):
    return (normalize_title(title), year)
