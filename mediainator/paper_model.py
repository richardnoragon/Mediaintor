"""Paper-inator domain model: Knowledge Items, versions, notes, projects, connections.
No Qt, no I/O.

A Knowledge Item is the primary object (a paper, report, thesis, dataset, standard…).
It can hold several reviewed versions of the same work (preprint, accepted manuscript,
published version); each version has its documents and attachments, which are either
managed copies inside the profile library or referenced files left where they are.
Notes can belong to an item or stand alone. Projects and collections gather items and
notes without duplicating them. Typed connections link items, notes and projects.

Reading progress, library handling and flags are independent dimensions. Everything
in a Paper-inator library belongs to one Hub profile.
"""
from dataclasses import dataclass, field
import re
import unicodedata

ITEM_TYPES = (
    'Research paper', 'Conference paper', 'Proceedings', 'Thesis or dissertation', 'Technical report',
    'White paper', 'Dataset', 'Book chapter', 'Standard or specification', 'Web resource', 'Other',
)
VERSION_KINDS = ('Preprint', 'Accepted manuscript', 'Published version', 'Other version')
READING = ('Unread', 'Reading', 'Read')
HANDLING = ('Inbox', 'Active', 'Archived')
FLAGS = ('Needs Review', 'Key Reference', 'Favorite')
FLAG_FIELDS = {'Needs Review': 'needs_review', 'Key Reference': 'key_reference', 'Favorite': 'favorite'}
NOTE_KINDS = ('Note', 'Summary', 'Finding', 'Methodology', 'Limitation', 'Question', 'Research idea',
              'Meeting notes', 'Experiment result')
RELATIONS = ('Supports', 'Contradicts', 'Extends', 'Uses', 'Derived From', 'References', 'Related To')
SYMMETRIC = frozenset(('Related To',))
# Wording seen from the other end of a directed connection.
INVERSE = {'Supports': 'Supported by', 'Contradicts': 'Contradicted by', 'Extends': 'Extended by',
           'Uses': 'Used by', 'Derived From': 'Source of', 'References': 'Referenced by', 'Related To': 'Related To'}
OBJECT_TYPES = ('item', 'note', 'project')     # connection endpoints in M19 (highlights follow in M20)
CONTAINER_KINDS = ('project', 'collection')
PROJECT_STATUSES = ('Active', 'Paused', 'Completed')
FILE_MODES = ('managed', 'referenced')
FILE_ROLES = ('document', 'attachment')
STARTUP_VIEWS = ('Home Dashboard', 'Library', 'Projects', 'Restore Last View')
VIEWS = ('Home', 'Library', 'Notes', 'Projects', 'Trash')
SORTS = ('Recently added', 'Title A–Z', 'Year (newest first)', 'Year (oldest first)', 'First author A–Z',
         'Recently opened')
DOI_PATTERN = re.compile(r'\b(10\.\d{4,9}/[^\s"<>]+)', re.IGNORECASE)
LINK_PATTERN = re.compile(r'\]\(paper:(item|note|project)/([0-9a-fA-F-]{36})\)')

_ARTICLES = ('the ', 'a ', 'an ')


def normalize(text):
    """Identity key for matching: accents, punctuation and case are ignored."""
    value = unicodedata.normalize('NFKD', text or '').encode('ascii', 'ignore').decode().casefold()
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', value.replace('&', ' and ')).split())


def sort_key(title):
    value = (title or '').strip().casefold()
    for article in _ARTICLES:
        if value.startswith(article) and len(value) > len(article):
            return value[len(article):]
    return value


def clean_doi(value):
    """A DOI in canonical form (lower case, no resolver prefix, no trailing punctuation), or ''."""
    if not value:
        return ''
    value = value.strip()
    value = re.sub(r'^(https?://(dx\.)?doi\.org/|doi:\s*)', '', value, flags=re.IGNORECASE)
    match = DOI_PATTERN.match(value)
    return match.group(1).rstrip('.,;:)]}').lower() if match else ''


@dataclass(frozen=True)
class DocumentFile:
    id: str
    version_id: str
    mode: str                 # 'managed' (copy inside the library) or 'referenced' (left in place)
    path: str                 # absolute path for use (managed paths are resolved by the store)
    original_path: str = ''
    size: int | None = None
    sha256: str = ''
    role: str = 'document'    # 'document' or 'attachment'
    label: str = ''
    has_text: bool = False
    trashed: bool = False

    @property
    def name(self):
        return self.label or self.path.replace('\\', '/').rsplit('/', 1)[-1]


@dataclass(frozen=True)
class Version:
    id: str
    item_id: str
    label: str
    kind: str = 'Other version'
    year: int | None = None
    doi: str = ''
    venue: str = ''
    notes: str = ''
    files: tuple[DocumentFile, ...] = ()

    @property
    def documents(self):
        return tuple(f for f in self.files if f.role == 'document' and not f.trashed)

    @property
    def attachments(self):
        return tuple(f for f in self.files if f.role == 'attachment' and not f.trashed)

    def describe(self):
        parts = [self.label]
        if self.kind and self.kind != self.label:
            parts.append(self.kind)
        if self.year:
            parts.append(str(self.year))
        if self.venue:
            parts.append(self.venue)
        return ' · '.join(parts)


@dataclass(frozen=True)
class KnowledgeItem:
    id: str
    type: str
    title: str
    authors: tuple[str, ...] = ()
    year: int | None = None
    venue: str = ''                 # journal, conference, publisher or site
    abstract: str = ''
    keywords: tuple[str, ...] = ()
    doi: str = ''
    identifiers: tuple[tuple[str, str], ...] = ()   # (scheme, value): arXiv, ISBN, ISSN, PMID, URL…
    url: str = ''
    tags: tuple[str, ...] = ()
    reading: str = 'Unread'
    handling: str = 'Inbox'
    needs_review: bool = False
    key_reference: bool = False
    favorite: bool = False
    preferred_version_id: str | None = None
    versions: tuple[Version, ...] = ()
    revision: int = 0
    added_at: str = ''
    modified_at: str = ''
    opened_at: str = ''
    trash_batch: str | None = None

    @property
    def first_author(self):
        return self.authors[0] if self.authors else ''

    @property
    def display_authors(self):
        if not self.authors:
            return 'Unknown author'
        if len(self.authors) > 3:
            return f'{self.authors[0]} et al.'
        return ', '.join(self.authors)

    @property
    def display_title(self):
        return self.title + (f' ({self.year})' if self.year else '')

    @property
    def flags(self):
        return tuple(name for name, attr in FLAG_FIELDS.items() if getattr(self, attr))

    @property
    def preferred_version(self):
        chosen = next((v for v in self.versions if v.id == self.preferred_version_id), None)
        return chosen or (self.versions[0] if self.versions else None)

    @property
    def files(self):
        return tuple(f for v in self.versions for f in v.files if not f.trashed)

    @property
    def documents(self):
        return tuple(f for v in self.versions for f in v.documents)

    @property
    def default_document(self):
        """The document opened by default: the preferred version's first document."""
        preferred = self.preferred_version
        if preferred is not None and preferred.documents:
            return preferred.documents[0]
        return self.documents[0] if self.documents else None

    def incomplete(self):
        """Missing information worth reviewing. Never invented, only reported."""
        missing = []
        if not self.authors and self.type not in ('Web resource', 'Dataset', 'Standard or specification'):
            missing.append('authors')
        if not self.year and self.type != 'Web resource':
            missing.append('year')
        if self.type in ('Research paper', 'Conference paper') and not self.venue:
            missing.append('journal or conference')
        if self.type == 'Web resource' and not self.url:
            missing.append('URL')
        return missing


@dataclass(frozen=True)
class Note:
    id: str
    title: str
    body: str = ''               # Markdown, the authoritative note content
    kind: str = 'Note'
    item_id: str | None = None   # source association; None for an independent note
    revision: int = 0
    created_at: str = ''
    modified_at: str = ''
    trash_batch: str | None = None

    @property
    def display_title(self):
        return self.title or first_line(self.body) or 'Untitled note'

    def links(self):
        """(type, id) targets of internal links in the body, in order, without duplicates."""
        seen, result = set(), []
        for kind, target in LINK_PATTERN.findall(self.body):
            key = (kind, target.lower())
            if key not in seen:
                seen.add(key); result.append(key)
        return result


@dataclass(frozen=True)
class Container:
    """A project (an investigation with a status) or a collection (a plain grouping)."""
    id: str
    kind: str
    name: str
    description: str = ''
    status: str = 'Active'
    members: tuple[tuple[str, str], ...] = ()     # (object type, id) of items and notes
    created_at: str = ''
    modified_at: str = ''
    trash_batch: str | None = None

    @property
    def item_ids(self):
        return tuple(i for t, i in self.members if t == 'item')

    @property
    def note_ids(self):
        return tuple(i for t, i in self.members if t == 'note')


@dataclass(frozen=True)
class Connection:
    id: str
    source_type: str
    source_id: str
    relation: str
    target_type: str
    target_id: str
    comment: str = ''
    created_at: str = ''

    def seen_from(self, kind, object_id):
        """(label, other type, other id) as seen from one endpoint."""
        if (self.source_type, self.source_id) == (kind, object_id):
            return self.relation, self.target_type, self.target_id
        return INVERSE[self.relation], self.source_type, self.source_id


@dataclass(frozen=True)
class SavedSearch:
    id: str
    name: str
    criteria: dict = field(default_factory=dict, hash=False, compare=False)
    modified_at: str = ''


@dataclass(frozen=True)
class TrashBatch:
    id: str
    label: str
    created_at: str
    state: str                    # 'trashed', 'purging'
    objects: tuple[tuple[str, str], ...] = ()     # (type, id) removed together


@dataclass(frozen=True)
class Library:
    """One consistent snapshot of a profile library."""
    items: tuple[KnowledgeItem, ...] = ()
    notes: tuple[Note, ...] = ()
    containers: tuple[Container, ...] = ()
    connections: tuple[Connection, ...] = ()
    searches: tuple[SavedSearch, ...] = ()
    trash: tuple[TrashBatch, ...] = ()
    trashed_items: tuple[KnowledgeItem, ...] = ()
    trashed_notes: tuple[Note, ...] = ()
    trashed_containers: tuple[Container, ...] = ()

    def item(self, item_id):
        return next((i for i in self.items if i.id == item_id), None)

    def note(self, note_id):
        return next((n for n in self.notes if n.id == note_id), None)

    def container(self, container_id):
        return next((c for c in self.containers if c.id == container_id), None)

    @property
    def projects(self):
        return tuple(c for c in self.containers if c.kind == 'project')

    @property
    def collections(self):
        return tuple(c for c in self.containers if c.kind == 'collection')

    @property
    def tags(self):
        found = {}
        for item in self.items:
            for tag in item.tags:
                found.setdefault(tag.casefold(), tag)
        return sorted(found.values(), key=str.casefold)

    def exists(self, kind, object_id):
        if kind == 'item':
            return self.item(object_id) is not None
        if kind == 'note':
            return self.note(object_id) is not None
        if kind == 'project':
            return self.container(object_id) is not None
        return False

    def label(self, kind, object_id):
        if kind == 'item':
            item = self.item(object_id)
            return item.display_title if item else 'Unavailable item'
        if kind == 'note':
            note = self.note(object_id)
            return note.display_title if note else 'Unavailable note'
        container = self.container(object_id)
        if container is None:
            return 'Unavailable project'
        return ('Project: ' if container.kind == 'project' else 'Collection: ') + container.name

    def connections_of(self, kind, object_id):
        """Connections whose both ends are active (not in trash)."""
        return tuple(c for c in self.connections
                     if (kind, object_id) in ((c.source_type, c.source_id), (c.target_type, c.target_id))
                     and self.exists(c.source_type, c.source_id) and self.exists(c.target_type, c.target_id))

    def notes_of(self, item_id):
        return tuple(n for n in self.notes if n.item_id == item_id)

    def containers_of(self, kind, object_id):
        return tuple(c for c in self.containers if (kind, object_id) in c.members)


def first_line(text):
    for line in (text or '').splitlines():
        line = line.strip().lstrip('#').strip()
        if line:
            return line[:120]
    return ''


def note_excerpt(note, limit=160):
    body = re.sub(r'\(paper:(item|note|project)/[0-9a-fA-F-]{36}\)', '', note.body or '')
    text = ' '.join(re.sub(r'[#*_`>\[\]]', '', body).split())
    return text[:limit] + ('…' if len(text) > limit else '')


def default_criteria():
    return dict(text='', types=[], reading=[], handling=[], flags=[], tags=[], container=None, sort=SORTS[0])


def _terms(text):
    return [t for t in normalize(text).split() if t]


def item_haystack(item, library=None):
    parts = [item.title, *item.authors, item.venue, item.abstract, *item.keywords, item.doi, item.url, *item.tags,
             str(item.year or ''), item.type]
    for version in item.versions:
        parts += [version.label, version.venue, version.doi]
        parts += [f.name for f in version.files if not f.trashed]
    if library is not None:
        for note in library.notes_of(item.id):
            parts += [note.title, note.body]
    return normalize(' '.join(p for p in parts if p))


def find_items(library, criteria=None, document_hits=frozenset()):
    """Items matching the search text and filters.

    Every search word must appear in the item's metadata, its notes, or (for items in
    `document_hits`) its document text. Filters combine AND across groups and OR
    within a group. Flags require every chosen flag.
    """
    criteria = dict(default_criteria(), **(criteria or {}))
    terms = _terms(criteria.get('text', ''))
    types, reading, handling = set(criteria['types']), set(criteria['reading']), set(criteria['handling'])
    flags = list(criteria['flags'])
    tags = {t.casefold() for t in criteria['tags']}
    members = None
    if criteria.get('container'):
        container = library.container(criteria['container'])
        members = set(container.item_ids) if container else set()
    result = []
    for item in library.items:
        if types and item.type not in types:
            continue
        if reading and item.reading not in reading:
            continue
        if handling and item.handling not in handling:
            continue
        if flags and not all(getattr(item, FLAG_FIELDS[f]) for f in flags if f in FLAG_FIELDS):
            continue
        if tags and not tags & {t.casefold() for t in item.tags}:
            continue
        if members is not None and item.id not in members:
            continue
        if terms:
            hay = item_haystack(item, library)
            if not all(t in hay for t in terms) and item.id not in document_hits:
                continue
        result.append(item)
    return sort_items(result, criteria.get('sort'))


def sort_items(items, sort=None):
    items = list(items)
    if sort == 'Title A–Z':
        items.sort(key=lambda i: (sort_key(i.title), i.year or 0))
    elif sort in ('Year (newest first)', 'Year (oldest first)'):
        dated = sorted((i for i in items if i.year), key=lambda i: (i.year, sort_key(i.title)),
                       reverse=sort == 'Year (newest first)')
        items = dated + sorted((i for i in items if not i.year), key=lambda i: sort_key(i.title))
    elif sort == 'First author A–Z':
        items.sort(key=lambda i: (not i.authors, normalize(i.first_author), sort_key(i.title)))
    elif sort == 'Recently opened':
        opened = sorted((i for i in items if i.opened_at), key=lambda i: i.opened_at, reverse=True)
        items = opened + [i for i in items if not i.opened_at]
    else:
        items.sort(key=lambda i: i.added_at, reverse=True)
    return items


def find_notes(library, text='', kinds=()):
    terms = _terms(text)
    kinds = set(kinds)
    result = []
    for note in library.notes:
        if kinds and note.kind not in kinds:
            continue
        if terms:
            source = library.item(note.item_id) if note.item_id else None
            hay = normalize(' '.join((note.title, note.body, note.kind, source.title if source else '')))
            if not all(t in hay for t in terms):
                continue
        result.append(note)
    return sorted(result, key=lambda n: n.modified_at, reverse=True)


def home_sections(library, limit=8):
    """The Home dashboard: what needs attention first."""
    items = library.items
    recent = sorted((i for i in items if i.opened_at), key=lambda i: i.opened_at, reverse=True)
    return dict(
        inbox=sorted((i for i in items if i.handling == 'Inbox'), key=lambda i: i.added_at, reverse=True)[:limit],
        recent=recent[:limit],
        continue_reading=sorted((i for i in items if i.reading == 'Reading'),
                                key=lambda i: i.opened_at or i.modified_at, reverse=True)[:limit],
        review=[i for i in sorted(items, key=lambda i: i.modified_at, reverse=True) if i.needs_review][:limit],
        projects=[p for p in library.projects if p.status == 'Active'][:limit],
        notes=sorted(library.notes, key=lambda n: n.modified_at, reverse=True)[:limit],
    )


def note_link(kind, object_id, label):
    """A Markdown link to a library object that keeps working when titles change."""
    label = (label or kind).replace('[', '(').replace(']', ')')
    return f'[{label}](paper:{kind}/{object_id})'


def export_markdown(note, library):
    """A readable, standalone Markdown file for one note. Internal links become plain
    text with a stable reference, so nothing points into the private library."""
    def replace(match):
        return f'] (→ {library.label(match.group(1), match.group(2))} · paper:{match.group(1)}/{match.group(2)})'
    body = LINK_PATTERN.sub(replace, note.body or '')
    lines = ['---', f'title: {yaml_text(note.display_title)}', f'kind: {note.kind}', f'id: {note.id}',
             f'modified: {note.modified_at}']
    source = library.item(note.item_id) if note.item_id else None
    if source is not None:
        lines.append(f'source: {yaml_text(source.display_title)}')
        if source.doi:
            lines.append(f'source_doi: {source.doi}')
        lines.append(f'source_id: {source.id}')
    lines += ['---', '', body.rstrip(), '']
    return '\n'.join(lines)


def yaml_text(value):
    return '"' + (value or '').replace('\\', '\\\\').replace('"', '\\"') + '"'


def safe_filename(text, limit=80):
    value = re.sub(r'[\\/:*?"<>|\x00-\x1f]+', ' ', text or '').strip().strip('.')
    value = ' '.join(value.split())[:limit].strip()
    return value or 'untitled'


def _sample():
    """Read-only sample library shown when the Hub runs without a profile library."""
    a, b, c = ('00000000-0000-4000-8000-00000000000' + str(n) for n in (1, 2, 3))
    items = (
        KnowledgeItem(a, 'Research paper', 'Attention Is All You Need', ('Ashish Vaswani', 'Noam Shazeer', 'Niki Parmar',
                      'Jakob Uszkoreit'), 2017, 'Advances in Neural Information Processing Systems',
                      keywords=('transformers', 'attention'), doi='10.48550/arxiv.1706.03762', tags=('machine learning',),
                      reading='Read', handling='Active', key_reference=True, added_at='2026-01-03'),
        KnowledgeItem(b, 'Technical report', 'Sample technical report on data sharing', ('A. Researcher',), 2024,
                      'Example Institute', reading='Reading', handling='Inbox', needs_review=True, added_at='2026-02-01',
                      opened_at='2026-02-02'),
        KnowledgeItem(c, 'Dataset', 'Example measurement dataset', (), 2023, url='https://example.org/data',
                      handling='Inbox', added_at='2026-02-05'),
    )
    notes = (Note('00000000-0000-4000-8000-000000000011', 'Why attention works', 'Summary of the key idea.\n\n'
                  + note_link('item', a, 'Attention Is All You Need'), 'Summary', a, modified_at='2026-02-03'),)
    containers = (Container('00000000-0000-4000-8000-000000000021', 'project', 'Literature review', 'Sample project',
                            'Active', (('item', a), ('item', b), ('note', notes[0].id))),)
    connections = (Connection('00000000-0000-4000-8000-000000000031', 'item', b, 'References', 'item', a),)
    return Library(items, notes, containers, connections)


SAMPLE_LIBRARY = _sample()
