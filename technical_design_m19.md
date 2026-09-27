# M19 technical design — Paper-inator Knowledge Foundation

Status: first implementation candidate; automated real Qt/KDE verification passed; owner desktop acceptance pending. Constraints: Python 3.14, PyQt6 6.10, **no new Python dependencies**. Poppler command-line tools (`pdfinfo`, `pdftotext`) are optional. No network code. Governing documents: [constitution](paperinator/paperinator%20constition.md), [technical overview](paperinator/paperinator%20technical%20overview.md). Structure follows [M17](technical_design_m17.md) and [M18](technical_design_m18.md).

## Modules

| File | Role | Qt? |
| --- | --- | --- |
| `paper_model.py` | Frozen dataclasses `KnowledgeItem`, `Version`, `DocumentFile`, `Note`, `Container`, `Connection`, `SavedSearch`, `TrashBatch`, `Library`; constants (item types, states, flags, relations); `find_items`, `find_notes`, `home_sections`, DOI cleaning, note links, Markdown export; read-only sample library | No |
| `paper_store.py` | Profile library: SQLite schema, validation, revisions, file placement (managed/referenced), document text index, notes, containers, connections, saved searches, trash/restore/purge with operation records, recovery | No |
| `paper_import.py` | Discovery, local inspection (fingerprint, document information, text), proposals with provenance, identical-file and version-candidate matching, revalidation | No |
| `paper_adapters.py` | `PdfReaderAdapter`, `AnnotationAdapter` (M20 contracts), `UnavailableReader`, `TextExtractor`/`InfoExtractor` + Poppler implementations, `MetadataProvider` (M21 contract), `ExternalOpener`, `validate_command` | No |
| `paper_ui.py` | `Paperinator` tab (Home, Library, Notes, Projects, Trash), `ItemEditor`, `NoteEditor`, `VersionsDialog`, `FileChoiceDialog`, `ConnectionDialog`, `ContainerDialog`, `OrganizeDialog`, `MetadataReviewDialog`, `PaperImportDialog`, `ScanWorker` | Yes |

Hub changes: `modules.py` (Paper-inator available + launch), `window.py` (`paper_library` argument, `paper_store`, `open_papers`, `remove_papers`, tab close, `review_close` = Paper-inator → Music-inator → Movie-inator → Book-inator, shutdown guard, focus refresh, shutdown), `settings.py` (`validate_paper_settings`, optional keys), `workspaces.py` (`paperinator` in generated module sets, optional `paper_selection`), `workspace_ui.py` (capture, busy guard), `workspace_restore.py` (open/close, active tab, selection restore, rollback keys, draft review), `activity_panel.py` guidance, `recovery_actions.py` library reload retry, `__main__.py` `--paper-library`.

## Storage

```text
<AppLocalData>/Paper/profiles/<stable profile id>/
    library.sqlite
    files/<2 hex>/<file uuid>-<safe name>.pdf     managed copies
    files/.staging/*.part                          verified-copy staging (own temporary files)
```

`--paper-library ROOT` replaces `<AppLocalData>/Paper`. Non-live Hubs without it use the read-only sample library and create nothing. Profile separation is organizational, not a security boundary (constitution §4).

Schema 1: `meta` (`schema`, `kind='paper'`, `library_uuid`, `profile_id`, `created_at`, `fts`). A foreign, kind-less, damaged, newer or **other-profile** database is refused and left byte-identical.

| Table | Contents |
| --- | --- |
| `items` | type, title, authors JSON, year, venue, abstract, keywords JSON, doi, identifiers JSON, url, tags JSON, reading, handling, needs_review, key_reference, favorite, preferred_version_id, revision, added/modified/opened_at, trash_batch |
| `versions` | item_id → items CASCADE, label, kind, year, doi, venue, notes, position |
| `files` | version_id → versions CASCADE, mode (managed/referenced), path UNIQUE (managed: relative to the library; referenced: canonical absolute), original_path, size, sha256, role (document/attachment), label, trash_batch |
| `doc_text` + `doc_fts` | derived, rebuildable document text (FTS5 when available, otherwise plain scan) |
| `notes` | title, body (Markdown, authoritative), kind, item_id → items SET NULL, revision, created/modified_at, trash_batch |
| `containers` | kind (project/collection), name, description, status, trash_batch |
| `memberships` | (container, object type, object id) primary key — no duplication |
| `connections` | source (type, id), relation, target (type, id), comment; UNIQUE per direction; symmetric relations checked both ways |
| `saved_searches` | name (unique, case-insensitive), criteria JSON |
| `trash_batches` | label, state (`trashed`/`purging`), objects JSON, purge_files JSON — the operation record |

Every write is one `BEGIN IMMEDIATE` transaction (5 s busy timeout), fully rolled back on error. `load()` reads one consistent snapshot inside a read transaction. Item metadata edits and note edits increment their revision; `update_item`/`update_note(id, expected_revision, changed_fields)` raise `ConflictError(current)` on mismatch; editors send only changed fields. Reading/handling/flags, tags, opening time and memberships are not metadata edits and do not change the revision. Validation reports missing information but never invents it; only the title is required; a DOI must be a real DOI form (a doi.org link is normalised).

## Files, versions and imports

`import_document(source, mode, item_fields | item_id, version_id | version_fields, expected=(size, sha256), text)`:

1. Canonical path; the source must exist; its fingerprint must equal the previewed one (`expected`), otherwise *changed since the preview*.
2. Referenced: the row records the path as-is. Managed: copy to `files/.staging/<uuid>.part`, fsync, re-hash; mismatch discards our copy.
3. Duplicate checks: identical content anywhere in the library (active or in Trash) or an already referenced path → refused.
4. One transaction inserts the item (or uses the existing one), the version (new or existing, which must belong to the item), the file row and document text. The verified copy is moved into `files/…` with `os.replace` just before commit; if the transaction fails, our copy is removed. The original is never touched.

A crash between placing a copy and committing leaves an unreferenced file inside `files/`; `orphans()` reports such files and nothing deletes them. `recover()` validates the catalog and profile before filesystem work, takes a non-blocking per-library file-operation lock, and defers while an import holds that lock. It then removes abandoned `.part` staging files and completes interrupted permanent deletions. Copying holds the lock through commit/rollback and checks cancellation between chunks.

The preferred version is the default for opening (its first document) and will be the default for citations; changing it never changes item metadata. The first version added becomes preferred; removing the preferred (empty) version selects another. Versions with files (active or in Trash) cannot be removed. Future highlights/positions are anchored to `(file id, content hash)` so a changed file cannot silently inherit them (M20).

`relocate_file(file_id, path, accept_changed)` applies to referenced files only; a different content hash raises `ChangedFileError` unless accepted, in which case stale document text is dropped.

Import planning (`paper_import.plan`) runs in a `QThread`: discover (explicit files of any type; folders scanned recursively for `.pdf`, no hidden or symlinked folders) → inspect (`fingerprint`, `pdfinfo`, `pdftotext` with timeouts) → `propose` (title from document information unless it looks generated, else file name; authors and keywords from document information; DOI from document information or the first page; **year is never taken from file dates**) → match (identical file, same DOI, same normalised title ≥ 13 characters) → warnings (image-only PDF, missing tools, identical copies in the selection, shared titles within the selection). Confirm applies each checked proposal in its own transaction after `revalidate`; Stop takes effect between documents. One activity record per import (`kind=paper_import`).

## Trash and permanent deletion

Owner-confirmed M19 policy: logical trash is sufficient; normal removal/restoration does not physically move managed files. Permanent deletion remains separate and explicit.

`trash(objects)` → one batch (operation record) and `trash_batch` markers on items, notes, containers or single files. An item takes along its active source notes. Nothing else is marked: memberships and connections stay stored and are hidden while an end is in Trash (`Library.connections_of` requires both ends active; loaded container members exclude trashed objects), so restore needs no reconstruction. Reading state and flags stay on the item row. `trash_preview` reports the objects, retained states, affected connections and memberships, managed copies (count, bytes) and referenced files. `restore(batch)` clears the markers (a project whose name was taken meanwhile gets “(restored)”).

`purge(batch)` — explicit, previewed — deletes the records, connections and memberships involving the purged objects (notes that referenced a purged item become independent through `ON DELETE SET NULL`) and records the managed paths to delete, all in one transaction that also sets the batch to `purging`. The files are then deleted, each only if it resolves inside this library's `files/` folder; referenced paths are never listed. Failures keep the batch in `purging` with the remaining paths; `recover()` retries on the next load. A `purging` batch cannot be restored. No automatic purging exists.

## Search

`find_items(library, criteria, document_hits)`: every normalised search word must appear in the item's metadata, versions, file names, tags or its notes — or the item is in `document_hits` from `search_documents` (FTS5 prefix query over active files of active items; LIKE fallback). Filters: type, reading, handling, tags (OR within), flags (all chosen), project/collection. Sorts: recently added, title, year both ways, first author, recently opened. Saved searches store validated criteria only. Trash is excluded from normal search.

## Notes

Markdown in the database is authoritative. `NoteEditor` offers formatting commands, *Link to item, note or project…* (`[Label](paper:<type>/<uuid>)`), and a `QTextBrowser` preview whose `loadResource` returns nothing (no remote or local fetching) and whose links are handled by the tab (`paper:` navigates; web links open only after confirmation). `export_markdown` writes YAML front matter (title, kind, id, modified, source, source DOI/id) and rewrites internal links to readable text with the stable reference. Export files are created exclusively and never overwrite existing files.

## UI

`Paperinator(state, save, store, activity, opener)`; `store=None` → sample library, all writes disabled. Sections: Home, Library, Notes, Projects, Trash (`QListWidget` navigation + `QStackedWidget`). Library uses a `QTableWidget` with extended row selection; state controls apply to all selected rows and the selection survives the reload. Drafts (`ItemEditor`, `NoteEditor`, shared `DraftEditor`) follow Save / Discard / Close with review on close; the tab tracks all open drafts. `review_close()` = running import, then each draft. `unattended_close_blocked()` = import or any dirty draft. Auto-refresh every 30 s and on window activation when the database signature changes, deferred while a draft is dirty.

## Settings (schema 1, optional keys)

`paperinator_open` bool; `paper_startup` ∈ Home Dashboard/Library/Projects/Restore Last View; `paper_view` ∈ Home/Library/Notes/Projects/Trash; `selected_paper`, `selected_paper_note`, `selected_paper_project`, `paper_saved_search` str|null; `paper_reader` str ≤ 1000; `paper_search` {text, types[], reading[], handling[], flags[], tags[], container|null, sort, expanded}. Research content is never stored in settings.

## Workspaces

`WORKSPACE_MODULES = (bookinator, musicinator, movieinator, paperinator)`; `MODULE_SETS` is generated, so all M17/M18 sets stay valid. Optional `paper_selection {library_uuid, item_id}`, restored only when the library UUID matches. **Compatibility note:** M16–M18 builds reject snapshots that include Paper-inator; keep M19 data isolated from Everyday, as with earlier milestones.

## Activity

Module `paperinator`. Kinds: `paper_library` (load failure, pending; retry = open tab and *Reload library*), `paper_open` (pending), `paper_import` (summary), `paper_save`, `paper_trash`, `paper_purge` (pending when files remain; retry = reload, which runs recovery).

## Adapters

Reader engine selection is deferred to M20 (owner decision). `PdfReaderAdapter` (open/close document, page count, render page, search text, text selection, reading position) and `AnnotationAdapter` (create/load highlights and bookmarks, export annotated copy) are abstract; `UnavailableReader` raises `ReaderUnavailable`. `MetadataProvider.lookup(identifier)` is the M21 contract: explicit request only, identifier only, proposals with provenance. `ExternalOpener` starts the desktop default (`xdg-open`) or a validated command (`{file}` placeholder, otherwise appended) detached; the reader is not tracked or closed and nothing is synchronised.

## Tests

- `tests/test_paper_core.py` (no Qt, 29): DOI cleaning, filters/sorts/home/notes/links/export, connection direction; validation atomicity, conflicts, independent states, bulk tags, versions and preferred version, notes, projects/collections, connections (duplicates, symmetric, self, reverse), saved searches, profile isolation and foreign/newer files; managed copy keeps the original (content and mtime), referenced files, identical-file refusal and cleanup, changed-after-preview, rollback cleanup, versions with attachments, relocation with content check, FTS and non-FTS document search; trash/restore keeps context, purge deletes managed copies only, interrupted purge completed by recovery, single note/project/file trash and name clashes, staging cleanup and orphan reporting; discovery (hidden, symlinked), proposals and provenance, plan duplicates/versions/image-only/missing tools, revalidation; reader contract, Poppler extractors, reader commands, external opener.
- `tests/test_m19_paperinator.py` (Qt, 20): sample read-only mode, empty library/home, add/edit/validation/conflict, multi-select states surviving reload, search/filters/saved searches/document text, notes with links, navigation, export and close review, projects/organize/membership, connections dialog, trash/restore/purge, import preview (required file handling, identical skip, version candidate, managed copies, Needs Review), versions/files/open/locate, metadata review, startup views; Hub launch/focus/close and profile library path, restart and workspace snapshot/restore, Hub close review, sample Hub creates nothing, separate profile libraries, settings validation, library failure activity and retry.

Verification update (2026-09-27): real PyQt6/Wayland and installed tests pass; see [final evidence](test_data/m18_m19_review/completion.md) for exact counts, scope, and remaining owner acceptance. The previous stand-in results are superseded by these runs.

## Known limits

No built-in reader, highlights or positions yet (M20); no citations, provider lookups, backup/restore (M21); no migration or library-wide duplicate review (M22). Title proposals depend on the PDF's document information; without Poppler, titles come from file names. Confirmed document imports run in a background executor, with GUI-thread polling and per-document results. Managed copying checks cancellation between chunks; completed documents remain committed. Import decisions are disabled while applying. One `pdftotext` run per document limits import speed. Document text is capped at 2 MB per file.


## 2026-09-27 preservation fixes

Multi-draft and cross-module exit reviews collect choices before applying them; Cancel leaves all drafts unchanged. Multi-draft workspace switching follows the same rule. Saves are attempted before discards. A post-confirmation save failure stops continuation; already completed saves are retained. Single-editor review remains unchanged. Native Qt regression tests cover cancellation and profile-safe recovery.
