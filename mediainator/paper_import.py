"""Paper-inator import planning: discovery, local inspection and reviewable proposals. No Qt.

Import follows discovery → local inspection → proposal → preview → confirmation →
application → outcome. Nothing here writes to the library or touches the chosen files;
no network request is made. Metadata found in the PDF (document information and the
text of the first page) is only a proposal with its source recorded; the user reviews
it in the preview. Identical files (same content fingerprint) and possible versions of
an existing item (same DOI or title) are shown for a decision, never merged silently.
"""
from dataclasses import dataclass, field
import os
from pathlib import Path
import re

from .paper_adapters import PdfInfoExtractor, PdfTextExtractor
from .paper_model import DOI_PATTERN, clean_doi, normalize
from .paper_store import PaperStoreError, canonical, fingerprint

SCAN_EXTENSIONS = frozenset(('.pdf',))       # folder scans; explicitly chosen files may be any type
SOURCE_METADATA = 'PDF document information'
SOURCE_TEXT = 'Document text, first page'
SOURCE_FILENAME = 'File name'
_JUNK_TITLES = re.compile(r'^(untitled|microsoft word|document\d*|slide \d+|title|paper|article|draft|pdf)\b|\.(docx?|tex|dvi|pdf)$',
                          re.IGNORECASE)


@dataclass
class Proposal:
    path: str
    size: int
    sha256: str
    fields: dict
    sources: dict                       # field → where the proposed value came from
    text: str = ''
    warnings: list = field(default_factory=list)
    duplicate: tuple | None = None      # (item id, title, in trash) of an identical file
    candidates: list = field(default_factory=list)   # [(item id, title, reason)] possible versions of existing items
    also: list = field(default_factory=list)        # identical copies found in the same selection

    @property
    def name(self):
        return Path(self.path).name

    def incomplete(self):
        missing = [f for f in ('authors', 'year') if not self.fields.get(f)]
        if self.sources.get('title') == SOURCE_FILENAME:
            missing.append('title (from file name)')
        return missing


@dataclass
class ImportPlan:
    proposals: list
    skipped: list                      # (path, reason)
    tools: dict                        # tool name → available


def discover(paths, cancelled=lambda: False):
    """Explicit files plus supported documents found recursively in chosen folders.
    Hidden and symlinked folders are not entered. Returns (files, skipped)."""
    found, skipped, seen = [], [], set()
    for raw in paths:
        if cancelled():
            break
        path = Path(raw).expanduser()
        if path.is_file():
            key = canonical(path)
            if key not in seen:
                seen.add(key); found.append(key)
        elif path.is_dir():
            for folder, dirs, files in os.walk(path, followlinks=False):
                if cancelled():
                    break
                dirs[:] = sorted(d for d in dirs if not d.startswith('.') and not os.path.islink(os.path.join(folder, d)))
                for name in sorted(files):
                    if name.startswith('.') or Path(name).suffix.lower() not in SCAN_EXTENSIONS:
                        continue
                    key = canonical(os.path.join(folder, name))
                    if key not in seen:
                        seen.add(key); found.append(key)
        else:
            skipped.append((str(path), 'not found'))
    return found, skipped


def title_from_filename(name):
    stem = Path(name).stem
    stem = re.sub(r'[_]+', ' ', stem)
    stem = re.sub(r'(?<=[a-z])-(?=[a-z])', ' ', stem)
    return ' '.join(stem.split()) or name


def plausible_title(value):
    value = ' '.join((value or '').split())
    return value if 4 <= len(value) <= 400 and not _JUNK_TITLES.search(value) else ''


def split_authors(value):
    value = ' '.join((value or '').split())
    if not value or len(value) > 1000 or _JUNK_TITLES.search(value):
        return []
    parts = re.split(r'\s*(?:;|\band\b|&|,(?=\s*[A-Z][^,]*\s+[A-Z]))\s*', value)
    return [p.strip(' ,') for p in parts if 2 <= len(p.strip(' ,')) <= 120][:50]


def first_page(text):
    return (text or '').split('\f', 1)[0][:6000]


def propose(path, info, text):
    """Proposed metadata for one document with provenance; nothing is invented."""
    fields, sources = dict(type='Research paper'), {}
    title = plausible_title(info.get('Title'))
    if title:
        fields['title'], sources['title'] = title, SOURCE_METADATA
    else:
        fields['title'], sources['title'] = title_from_filename(Path(path).name), SOURCE_FILENAME
    authors = split_authors(info.get('Author'))
    if authors:
        fields['authors'], sources['authors'] = authors, SOURCE_METADATA
    keywords = [k.strip() for k in re.split(r'[;,]', info.get('Keywords') or '') if 1 < len(k.strip()) <= 120][:30]
    if keywords:
        fields['keywords'], sources['keywords'] = keywords, SOURCE_METADATA
    doi = ''
    for value, source in ((info.get('doi', ''), SOURCE_METADATA), (info.get('Subject', ''), SOURCE_METADATA),
                          (first_page(text), SOURCE_TEXT)):
        match = DOI_PATTERN.search(value or '')
        if match:
            doi = clean_doi(match.group(1))
            if doi:
                fields['doi'], sources['doi'] = doi, source
                break
    return fields, sources


def inspect(path, cancelled=lambda: False, info_tool=None, text_tool=None):
    """Local inspection of one file: fingerprint, document information, text."""
    info_tool = info_tool or PdfInfoExtractor()
    text_tool = text_tool or PdfTextExtractor()
    size, sha = fingerprint(path, cancelled)
    warnings = []
    info, text = {}, ''
    if Path(path).suffix.lower() == '.pdf':
        try:
            info = info_tool.extract(path)
        except PaperStoreError as exc:
            warnings.append(f'Document information unavailable: {exc}')
        try:
            text = text_tool.extract(path)
        except PaperStoreError as exc:
            warnings.append(f'Text extraction failed: {exc}')
        if text_tool.available() and not text.strip():
            warnings.append('No searchable text found (image-only PDF?). Document text search will not find it; '
                            'OCR is not part of Paper-inator.')
    fields, sources = propose(path, info, text)
    proposal = Proposal(path, size, sha, fields, sources, text, warnings)
    if not text_tool.available() and Path(path).suffix.lower() == '.pdf':
        proposal.warnings.append('pdftotext is not installed: document text is not searchable and no DOI can be read '
                                 'from the first page.')
    return proposal


def match(proposal, library, by_hash):
    """Identical files and possible versions of existing items. Reported, never applied."""
    proposal.duplicate = by_hash.get(proposal.sha256)
    doi = proposal.fields.get('doi')
    title = normalize(proposal.fields.get('title', ''))
    for item in library.items:
        dois = {item.doi} | {v.doi for v in item.versions}
        if doi and doi in dois:
            proposal.candidates.append((item.id, item.display_title, 'same DOI'))
        elif title and len(title) > 12 and normalize(item.title) == title:
            proposal.candidates.append((item.id, item.display_title, 'same title'))


def plan(paths, library, by_hash, by_path, cancelled=lambda: False, progress=lambda message: None,
         info_tool=None, text_tool=None):
    """Build a reviewable import plan. Nothing is written."""
    info_tool = info_tool or PdfInfoExtractor()
    text_tool = text_tool or PdfTextExtractor()
    files, skipped = discover(paths, cancelled)
    proposals, by_sha = [], {}
    for index, path in enumerate(files, 1):
        if cancelled():
            break
        progress(f'Inspecting {index} of {len(files)}: {Path(path).name}')
        if path in by_path:
            skipped.append((path, 'already referenced by the library')); continue
        try:
            proposal = inspect(path, cancelled, info_tool, text_tool)
        except (OSError, PaperStoreError) as exc:
            skipped.append((path, str(exc))); continue
        if proposal.sha256 in by_sha:
            by_sha[proposal.sha256].also.append(path)
            continue
        by_sha[proposal.sha256] = proposal
        match(proposal, library, by_hash)
        proposals.append(proposal)
    titles = {}
    for proposal in proposals:
        key = normalize(proposal.fields.get('title', ''))
        if key and len(key) > 12:
            titles.setdefault(key, []).append(proposal)
    for group in titles.values():
        if len(group) > 1:
            for proposal in group:
                proposal.warnings.append(f'{len(group)} files in this selection share this title: possibly versions of one '
                                         'work. Import one, then add the others as versions of it.')
    for proposal in proposals:
        if proposal.also:
            proposal.warnings.append(f'{len(proposal.also)} identical cop{"y" if len(proposal.also) == 1 else "ies"} in this '
                                     'selection will not be imported separately: ' + ', '.join(Path(p).name for p in proposal.also[:3]))
    return ImportPlan(proposals, skipped, dict(pdfinfo=info_tool.available(), pdftotext=text_tool.available()))


def revalidate(proposal):
    """Problems that make a previewed proposal unsafe to apply now."""
    try:
        if not os.path.isfile(proposal.path):
            return ['The file is no longer available.']
        if os.path.getsize(proposal.path) != proposal.size:
            return ['The file changed since the preview.']
    except OSError as exc:
        return [str(exc)]
    return []
