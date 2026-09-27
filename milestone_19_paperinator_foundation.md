# M19 — Paper-inator Knowledge Foundation

Review update (2026-09-26): real PyQt6 full suite **381 passed**, M18/M19 native Wayland tests **35 passed**, and installed M18/M19 tests **86 passed** after test-harness corrections. Targeted review also reproduced preservation defects; **acceptance remains OPEN**. See [compliance review and outstanding items](test_data/m18_m19_review/review.md). Earlier stand-in-only status below is historical evidence, not the latest verification result.

Status: **Implemented and automatically verified candidate (2026-09-27); follow-up owner desktop checks passed; M19-G formal closure pending.** See [final implementation and test evidence](test_data/m18_m19_review/completion.md). Isolated acceptance launchers are available; Everyday is unchanged.

## Purpose

Make Paper-inator the fourth working Hub module and prove its knowledge model before the reader and research services arrive. Goal question: **“Can I build and manage a research knowledge base?”**

Paper-inator follows the agreed [overview](paperinator/paperinator%20overview.md), [features](paperinator/paperinator%20features.md), [technical overview](paperinator/paperinator%20technical%20overview.md) and [constitution](paperinator/paperinator%20constition.md). M19 is the first of several milestones delivering the Foundation; it is fully offline.

## Owner decisions (2026-09-26)

| Topic | Decision |
| --- | --- |
| M19 scope | **Knowledge Foundation (library core first).** Hub integration, profile library database, Knowledge Items, version grouping, managed/referenced files, reading/handling states and flags, tags, collections, projects, Markdown notes, typed connections, search, saved searches, trash. External PDF opening only. |
| Roadmap | **M20 Reading & Annotation** (built-in reader, positions, bookmarks, highlights, sticky notes, highlight-to-note links, highlight search). **M21 Research & Preservation** (citations, bibliographies, BibTeX/RIS/CSL JSON, DOI lookup/Crossref, metadata retrieval, backup/restore). **M22 Import & Migration** (existing-library import, duplicate review, metadata merge workflows, watch folders if still wanted). |
| PDF engine | **Decide later.** M19 defines and tests the reader and annotation adapter interfaces without committing to an engine. The engine is selected in M20 after compatibility, licensing, annotation, search and packaging evaluation. QtPdf is the first evaluation candidate; PyMuPDF is not the default. |
| Notes storage | **SQLite is authoritative.** Note content is Markdown stored in the profile library database; users can explicitly export notes as standard `.md` files, which are copies, not authoritative. |
| DOI lookup | **Deferred to M21.** M19 has no network code; metadata comes from manual entry and local PDF metadata/text proposals. Provider adapters exist only as an interface. |
| Process | Full candidate as for M17/M18: decisions, milestone document, technical design, code, Hub integration, tests, help/README/CHANGELOG, document updates; Qt tests run on the owner's KDE machine. |

Implementation choices made by Claude within those decisions (routine, reversible; no constitutional change):

- **Library location.** `AppLocalData/Paper/profiles/<profile id>/` holds `library.sqlite` and `files/` (managed copies). The profile id is the stable Hub identity; a renamed profile keeps its library. The database records its owning profile and refuses to open for another profile. `--paper-library DIR` selects a disposable root for testing; sample/test Hubs without it show a read-only sample library and create nothing.
- **Trash is logical — explicitly confirmed by the owner.** Moving to Trash marks records in one transaction; no file is moved. Managed copies are deleted only by **Delete permanently…**, after a preview, through an operation record that is completed on the next start if interrupted. Referenced files are never deleted.
- **What travels with an item into Trash.** The item's source notes go with it (same Trash entry). Independent notes, other items, projects and their files stay. Connections and project memberships are kept and hidden while an end is in Trash; restore brings them back; permanent deletion removes them.
- **Duplicates and versions at import.** Identical files (SHA-256) are skipped; files already referenced are left out; a file whose DOI or title matches an existing item is offered as **Add as new version of …**, never merged automatically. New items land in the Inbox; items with missing authors/year or a title taken from the file name are flagged *Needs Review*.
- **Local proposals.** Optional Poppler tools (`pdfinfo`, `pdftotext`) supply document information, first-page DOI and searchable text. Without them imports still work with file-name titles and no document-text search. Image-only PDFs are reported as not searchable (no OCR).
- **Internal note links** use standard Markdown links to stable ids: `[Label](paper:item/<uuid>)`, `paper:note/…`, `paper:project/…`. Renaming never breaks them; exports rewrite them as readable text with the stable reference.
- **Search.** Metadata, tags, notes and file names are searched in memory; document text through SQLite FTS5 (plain scan fallback). Every word must match; filters combine AND across groups, OR within a group; flags require every chosen flag.
- **Startup view** is chosen in the tab (*Start with*: Home Dashboard, Library, Projects, Restore Last View); default Home Dashboard.

## Delivered in the first candidate

- Registry: Paper-inator tile Available; repeat launch focuses one tab; tab close leaves the Hub; reopened after restart.
- **Home**: Inbox, Continue reading, Needs review, Recently opened, Active projects, Recent notes.
- **Library**: table of Knowledge Items (11 types), search across metadata, notes and document text, filters (type, reading, handling, flags, tags, project/collection), sorts, remembered criteria, **saved searches** (save, choose, update, remove; criteria not results). Detail pane with versions and files (availability, managed/referenced, searchable), notes, connections (with direction) and projects; links navigate.
- Independent **reading / handling / flags** controls that apply to every selected item, with a mixed-values notice; **Organize selected…** for tags, states, flags and project/collection membership with an explicit scope list.
- **Item editor** with Save / Discard / Close, validation that keeps input, revision conflict review (only changed fields are written).
- **Versions & files**: versions (preprint, accepted manuscript, published, other) with their own year/DOI/venue; preferred version (opening default; metadata unchanged); add documents or attachments as managed copy or referenced file (explicit choice); open, locate moved referenced files (content check; changed files need explicit acceptance), remove files to Trash.
- **Propose metadata from PDF…**: field-by-field review with source; existing values unchecked by default.
- **Notes**: independent or item notes, nine note types, Markdown editor with formatting commands and *Link to item, note or project…*, safe rendered preview (no remote or local resources loaded), conflict review, **Export as Markdown…** (never overwrites).
- **Projects and collections**: optional; projects hold items and notes with status (Active/Paused/Completed); collections hold items; membership never duplicates items; *Show items in Library*.
- **Connections**: Supports, Contradicts, Extends, Uses, Derived From, References, Related To (symmetric); between items, notes and projects; inspect, add, reverse, remove.
- **Import**: files/folders/drag-and-drop → background inspection → reviewable preview (editable title, authors, year, DOI; sources and warnings; create / add as version / skip) → required file-handling choice → Confirm. Revalidation of size and content before each write; per-document transactions; staged, verified managed copies; stop between documents; activity record.
- **Trash**: preview of scope (notes, connections, memberships, managed and referenced files, retained reading state); restore; **Delete permanently…** with exact preview; interrupted deletions finish on reload.
- **Adapters**: `PdfReaderAdapter`, `AnnotationAdapter` (contracts for M20; `UnavailableReader` placeholder), `TextExtractor`/`InfoExtractor` (Poppler implementations), `MetadataProvider` (contract for M21), `ExternalOpener` (desktop default or configured reader, `{file}` placeholder).
- Hub integration: combined close review (Paper-inator first), cooperative shutdown guard, activity guidance and library-reload retry, workspaces (module sets including Paper-inator; active tab; item selection by library UUID), `--paper-library`.
- Help: User guide section “Paper-inator (M19 Development)”.

## Work breakdown

| Item | Deliverable | Status |
| --- | --- | --- |
| M19-01 decisions | Owner decisions above; technical overview and features updated | Done |
| M19-02 technical design | `technical_design_m19.md` | Done |
| M19-03 core | Model, profile library store, import planner, adapters + `tests/test_paper_core.py` | Done; 29 tests pass |
| M19-04 module UI | `paper_ui.py` tab, editors, dialogs, import | Implemented; real Qt/Wayland and installed-package tests pass |
| M19-05 Hub integration | Registry, tabs, close review, settings, workspaces, activity, recovery, CLI | Implemented; real Qt/Wayland and installed-package tests pass |
| M19-06 regression | Full existing suite + M19 tests on the owner's machine | Passed; see final evidence and run scope |
| M19-07 isolated environment and package | Independent M19 Development install/data from the Everyday baseline | Verified frozen candidate; isolated acceptance launcher prepared |
| M19-08 owner acceptance | Desktop checks below; M19-G record | Pending |

## Proposed M19-G acceptance

- Paper-inator launches from the Hub, focuses on repeat, closes without closing the Hub, and reopens after restart; Book-, Music-, Movie-inator and all M16–M18 regressions unchanged.
- A second Hub profile sees an empty, separate library; the first profile's library is refused for it and left unchanged.
- Import a real folder of PDFs as **Referenced files** and another as **Managed copies**: the choice is required; originals are unchanged (content and timestamps); managed copies appear under the profile library; identical files are skipped; a re-downloaded version of an existing paper is offered as a new version and nothing merges by itself; new items are in the Inbox; incomplete ones are flagged Needs Review; nothing is written before Confirm.
- With Poppler installed, a word that occurs only inside a PDF finds the item; an image-only PDF is reported as not searchable.
- Reading, handling and flags change independently (archiving keeps Read), also for several selected items; saved searches reflect later library changes.
- Notes: an independent note and an item note with links to an item and a project; the links navigate; editing elsewhere is detected; export writes readable `.md` files and never overwrites.
- Projects and collections hold items (and notes for projects) without duplicates; removing a member keeps the item.
- Connections of each type can be added, shown from both ends with the right direction, reversed and removed.
- Versions: preferred version changes the opened document but not the item details; a moved referenced file can be located; a different file is refused unless accepted.
- Trash: moving an item takes its notes; independent notes, connections to survivors and project memberships come back on restore; **Delete permanently** removes managed copies only and states that referenced files remain.
- Hub close/tab close review unsaved item and note drafts and running imports; Cancel stops the close. Named workspaces restore the Paper-inator tab and selected item. Appearance settings apply to Paper-inator controls.

## Explicitly deferred

Built-in PDF reader, reading positions, bookmarks, highlights, sticky notes, annotated PDF export (M20); citations, bibliographies, BibTeX/RIS/CSL JSON, DOI/Crossref and other provider lookups, backup and restore, broader knowledge exports (M21); existing-library migration (Zotero, EndNote, Mendeley), library-wide duplicate review and metadata merge, watch folders, changing file ownership mode (M22 / Advanced); Book-inator links and academic chapters linked to books; knowledge graph visualization, custom fields and relationships, AI assistance, word-processor integration, collaboration, synchronization, browser capture (Future). OCR is not planned.
