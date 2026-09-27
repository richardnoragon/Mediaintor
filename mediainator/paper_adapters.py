"""Replaceable document components for Paper-inator. No Qt.

The rest of Paper-inator talks only to these interfaces, so a concrete PDF engine can
be chosen later without changing the library, search or UI code:

* `PdfReaderAdapter` and `AnnotationAdapter` define the built-in reader contract.
  M19 deliberately ships no implementation: the reader milestone (M20) selects an
  engine after compatibility, licensing, annotation, search and packaging evaluation.
  `UnavailableReader` reports that honestly.
* `TextExtractor` and `InfoExtractor` read local document text and document
  information for search and metadata proposals. M19 provides optional Poppler
  command-line implementations (`pdftotext`, `pdfinfo`); without them imports still
  work, with reduced proposals and no document-text search.
* `MetadataProvider` is the contract for explicitly requested online lookups (DOI,
  Crossref, …). None is implemented in M19; nothing here uses the network.
* `ExternalOpener` opens a document in the desktop default or a configured reader.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
import os
from pathlib import Path
import shlex
import shutil
import subprocess

from .paper_store import PaperStoreError

TEXT_TIMEOUT = 60
INFO_TIMEOUT = 20
TEXT_LIMIT = 2_000_000


class ReaderUnavailable(PaperStoreError):
    """The requested reader capability is not implemented in this build."""


# ----------------------------------------------------------------------------- reader contract (M20)
@dataclass(frozen=True)
class PageLocation:
    """A place in one exact document version: page index plus an optional text/geometry anchor."""
    file_id: str
    page: int
    anchor: str = ''


@dataclass(frozen=True)
class TextSelection:
    location: PageLocation
    text: str
    rectangles: tuple = ()


class PdfReaderAdapter(ABC):
    """Built-in reader engine contract. Documents are opened read-only; originals are never modified."""

    @abstractmethod
    def open_document(self, path, file_id):
        """Open a document; returns an opaque handle."""

    @abstractmethod
    def close_document(self, handle):
        """Release the document."""

    @abstractmethod
    def page_count(self, handle):
        """Number of pages."""

    @abstractmethod
    def render_page(self, handle, page, scale=1.0):
        """Rendered page image (engine-specific image object)."""

    @abstractmethod
    def search_text(self, handle, text):
        """Locations (PageLocation) of matches; empty for image-only pages."""

    @abstractmethod
    def text_selection(self, handle, page, start, end):
        """TextSelection between two points on a page, with stable anchors."""

    @abstractmethod
    def reading_position(self, handle):
        """Current PageLocation, saved per document version."""


class AnnotationAdapter(ABC):
    """Annotation storage contract. Annotations are stored by Paper-inator, separately
    from the original PDF, and are tied to the exact document version."""

    @abstractmethod
    def create_highlight(self, selection, color='', note=''):
        """Store a highlight for a TextSelection; returns its id."""

    @abstractmethod
    def load_highlights(self, file_id):
        """Highlights of one document version."""

    @abstractmethod
    def create_bookmark(self, location, label=''):
        """Store a bookmark at a PageLocation; returns its id."""

    @abstractmethod
    def load_bookmarks(self, file_id):
        """Bookmarks of one document version."""

    @abstractmethod
    def export_annotated_copy(self, file_id, destination):
        """Write a separate annotated copy; the original is never overwritten. Returns a list
        of annotation types that could not be exported."""


class UnavailableReader(PdfReaderAdapter):
    """M19 placeholder: every call explains that the built-in reader is not available yet."""
    MESSAGE = ('The built-in reader arrives in a later milestone. Open the document with the external reader; '
               'reading positions and highlights are not recorded yet.')

    def _unavailable(self, *args, **kwargs):
        raise ReaderUnavailable(self.MESSAGE)

    open_document = close_document = page_count = render_page = _unavailable
    search_text = text_selection = reading_position = _unavailable


# ----------------------------------------------------------------------------- local extraction
class TextExtractor(ABC):
    @abstractmethod
    def available(self):
        """Whether extraction can run on this system."""

    @abstractmethod
    def extract(self, path):
        """Plain text of the document with pages separated by form feeds ('' if none)."""


class InfoExtractor(ABC):
    @abstractmethod
    def available(self):
        """Whether extraction can run on this system."""

    @abstractmethod
    def extract(self, path):
        """Document information as a dict (Title, Author, Subject, Keywords, …)."""


def _run(command, timeout):
    try:
        result = subprocess.run(command, capture_output=True, timeout=timeout, check=False,
                                stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired as exc:
        raise PaperStoreError(f'{Path(command[0]).name} took too long.') from exc
    except OSError as exc:
        raise PaperStoreError(f'{Path(command[0]).name} could not run: {exc}') from exc
    if result.returncode != 0:
        message = result.stderr.decode('utf-8', 'replace').strip().splitlines()
        raise PaperStoreError((message[-1] if message else f'{Path(command[0]).name} failed')[:300])
    return result.stdout


class PdfTextExtractor(TextExtractor):
    """Poppler `pdftotext`, optional. Reads the file; never modifies it."""

    def __init__(self, executable=None):
        self.executable = executable or shutil.which('pdftotext')

    def available(self):
        return bool(self.executable)

    def extract(self, path):
        if not self.available():
            return ''
        raw = _run([self.executable, '-q', '-enc', 'UTF-8', str(path), '-'], TEXT_TIMEOUT)
        return raw.decode('utf-8', 'replace')[:TEXT_LIMIT].replace('\x00', '')


class PdfInfoExtractor(InfoExtractor):
    """Poppler `pdfinfo`, optional."""

    def __init__(self, executable=None):
        self.executable = executable or shutil.which('pdfinfo')

    def available(self):
        return bool(self.executable)

    def extract(self, path):
        if not self.available():
            return {}
        raw = _run([self.executable, '-enc', 'UTF-8', str(path)], INFO_TIMEOUT).decode('utf-8', 'replace')
        info = {}
        for line in raw.splitlines():
            key, sep, value = line.partition(':')
            if sep and key.strip() and key.strip() not in info:
                info[key.strip()] = value.strip()
        return info


# ----------------------------------------------------------------------------- online metadata (M21)
class MetadataProvider(ABC):
    """Explicitly requested online lookup. Implementations must only send the identifier
    the user asked about, never documents or research content, and return proposals
    with provenance for review."""
    name = ''

    @abstractmethod
    def lookup(self, identifier):
        """Proposed metadata (dict of item fields) with a 'source' entry."""


# ----------------------------------------------------------------------------- external reader
def validate_command(text):
    """A reader command line: empty for the desktop default, or an executable plus arguments."""
    if not isinstance(text, str) or len(text) > 1000 or any(ord(c) < 32 for c in text):
        raise PaperStoreError('Reader command contains unsupported characters or is too long.')
    text = text.strip()
    if not text:
        return ''
    try:
        parts = shlex.split(text)
    except ValueError as exc:
        raise PaperStoreError(f'Reader command cannot be read: {exc}') from exc
    if not parts or not shutil.which(parts[0]):
        raise PaperStoreError(f'Reader program not found: {parts[0] if parts else text}')
    return text


class ExternalOpener:
    """Opens a document outside Paper-inator. The reader is not tracked or closed, and
    reading positions or annotations made there are not synchronised."""

    def open(self, command, path):
        if not os.path.isfile(path):
            raise PaperStoreError('The file is not available. Use Locate… if it was moved.')
        if command:
            parts = shlex.split(command)
            program = shutil.which(parts[0])
            if not program:
                raise PaperStoreError(f'Reader program not found: {parts[0]}')
            args = [a.replace('{file}', str(path)) for a in parts[1:]]
            if not any('{file}' in a for a in parts[1:]):
                args.append(str(path))
            command_line = [program] + args
        else:
            opener = shutil.which('xdg-open')
            if not opener:
                raise PaperStoreError('No desktop opener (xdg-open) found. Choose a reader command instead.')
            command_line = [opener, str(path)]
        try:
            subprocess.Popen(command_line, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, start_new_session=True)
        except OSError as exc:
            raise PaperStoreError(f'The reader could not be started: {exc}') from exc
