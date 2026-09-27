# M14 technical design — Library Discovery & Metadata Productivity

M14-01 COMPLETE: design grounded in current source and approved owner behavior. This is a design, not implemented functionality. [Scope and gate](milestone_14_library_discovery_metadata_productivity.md). M14-G OPEN; M13 Everyday protected.

## Existing implementation and integration boundaries

- catalog.py: immutable Book includes UUID, series, tags, formats and reading_status (Unknown by default); find_books currently ANDs categories and ORs category values.
- library.py: Calibre listing through a private snapshot; parse_catalog substitutes Untitled/Unknown author, losing raw emptiness. Extend ingestion to preserve raw completeness and author components while retaining display fallbacks.
- snapshot.py: coherent private full-library copy, SQLite backup, source inventory checks, compatibility guard, cancellation and timeout. Preserve these safety checks. Add stage/count progress and cancellation during inventory traversal; never replace a timeout with silent partial success.
- window.py: eager QListWidget/QTableWidget rebuilds and refresh_progress per book are scale risks. Replace catalog presentation with model-backed views; do not perform file hashing, journal traversal or per-book progress I/O during filtering/painting.
- import_store.py: durable book-review provenance survives import-history deletion. Reviewed flags acknowledge warnings; they cannot become a factual completeness source.
- bulk_dialog.py/editor.py/recovery_actions.py: keep established write adapters, explicit previews/confirmation, conflict rereads, pinned UUID targets, recovery and close handling. M14 does not introduce a Calibre writer.

## Data and identities

Use library identity = canonical library path plus library UUID, scoped to profile/device. Book identity is library identity plus book UUID, not row or mutable title. Missing/duplicate UUIDs are explicit errors for mutable operations; browsing may still show an error row. Copies at different external paths are separate libraries. Independent containers intentionally retain internal paths and profile IDs but have separate storage/mounts.

Build an immutable CatalogGeneration off the GUI thread: generation ID, UUID-to-row map, normalized title/authors/series/tags, stable sort order, formats/paths, explicit status/provenance, cover presence and factual missing flags. Do not infer Unread from absent progress. Current loader provides Unknown for normal records; M14 filters values actually supplied by supported data, without a new reading-status editor or invented values. Fixtures exercise explicit known states as well as Unknown.

Normalize matching text with Unicode NFKC, casefold and collapsed whitespace; retain originals for display. Tags and series conditions use normalized whole-value equality, while browser search uses literal substring matching. No regex or executable query syntax. Detect normalization collisions without changing stored Calibre values. Keep natural display spelling and deterministic title/UUID tie-breaking.

## Filter representation and execution

Query schema: {version:1, text:string, mode:all|any, conditions:[{field,operator,value}], sort:{field,direction}}. Fields: reading_status, missing_metadata, series, tag; initial operators are is/equals for approved condition rows. Missing metadata values: title, author, cover, series. Repeated conditions allowed; no nested groups. Empty condition list matches all in either mode. Existing text query matches title/author/series and ANDs with condition results. Existing format filter remains an outer narrowing constraint in both modes, explicitly labeled; preserve legacy filtering when advanced conditions are unused.

Create inverted UUID sets for discrete facets and missing reasons, and normalized text vectors once per generation. AND intersects; OR unions; text/format narrowing follows. Never build all-pairs structures. Query evaluation and result sorting happen in a worker using the immutable generation; 150 ms text debounce included in measured latency. Each request carries library/generation/query tokens; reject stale results after edits, refresh, library switch or closure. Cancel/coalesce obsolete searches. Keep last results visible with updating indication until a verified replacement is ready.

Use QAbstractTableModel/QAbstractListModel with immutable visible UUID arrays and shared backing records. Paint only viewport rows; load thumbnails lazily with a bounded cache. Do not resize every row/column to full contents on each query. Qt GUI objects remain on the GUI thread; workers return data. Reuse existing explicit bulk UUID selection across filters, reporting hidden selections; preview pins its targets independently of later results. Background refresh must not close a metadata editor whose book is filtered out (retain M13 fix).

## Saved searches and review persistence

New sidecar DiscoveryStore under app config/discovery/<library identity hash>/state.json. Schema 1 contains owner/library identity, revision, saved_searches keyed by UUID (name/query), manual_review keyed by book UUID, acknowledged warning IDs and review_missing_series preference (false by default). Names trimmed, nonempty, unique under casefold; limit input lengths with visible validation. Queries refer to values, never a frozen result set. Missing facet values remain valid definitions returning zero results; do not silently delete them.

Use existing locked/atomic_json mechanisms, fsync and readback; revision check before update/delete to prevent overwriting concurrent changes. Unknown schema, invalid query or corrupt JSON produces a recoverable error and retains the original file; never overwrite it with defaults. No query evaluation via eval. Delete-search confirmation names the definition and states books are unaffected. No automatic library relocation/migration by UUID alone.

Factual reasons are derived from raw empty title/author, supported Unknown author placeholders, absent cover, and optional missing series. Filename title fallback counts only when import provenance identifies it and the current title still matches that recorded fallback; never classify arbitrary filenames by guesswork. Preserve provenance separately from acknowledgment. Correcting a field removes that factual reason at next verified refresh, without clearing unrelated flags.

Queue membership = factual reasons OR manual flag OR unacknowledged reviewable import warnings. Missing-series preference affects automatic queue inclusion; an explicit missing-series filter still works when the preference is off. Show all reasons in a Reasons column. Mark reviewed clears the manual flag and acknowledges the currently observed warning IDs; new warning revisions remain outstanding. Factual reasons remain. UI explains why a reviewed book still qualifies.

Read legacy ImportStore.review_records once per generation, not per row. Preserve legacy state and journals. DiscoveryStore can acknowledge legacy warning IDs formed from source batch/operation/reason; union these acknowledgments with existing reviewed flags. Route editor Mark Reviewed and workbench acknowledgment through one service. Do not rewrite old journals or resurrect warnings after history cleanup. Versioned sidecar is additive and rollback to M13 does not modify M14 files. Store failures report incomplete acknowledgment without claiming success or changing book metadata.

## Review workbench and UI

Discovery panel: text search, Match all/any, editable condition rows, filter summary and result count; searchable Tags/Series browsers add visible conditions. Saved-search selector has explicit Save new / Update selected / Rename / Delete actions. Changing a definition does not automatically overwrite it; show modified state.

Review workbench uses the same catalog generation/query engine, with columns title, author, series, tags, format, reading status and review reasons. Entry modes: current search results or Needs Review queue. Sorting, selection and workbench opening are read-only. Add Needs Review / Mark reviewed actions change only sidecar workflow state, and existing Bulk edit actions use selected UUIDs through the established BulkDialog. No inline metadata writes. Incomplete catalog/provenance failures must show partial/unavailable status, not an empty successful queue.

All new controls have visible keyboard focus, labels and accessible names. Tab/Shift+Tab traversal and ordinary window sizes are explicit owner checks. Close workbench closes that window; active workers cancel safely and late callbacks cannot reopen it. Dirty editor review semantics remain unchanged.

## Duplicate review

Explicit Scan library starts against one generation. Records from intake are excluded. Group by format and byte size before SHA-256 streaming; within-format matching checks different book UUIDs. Stat before/after hashing; a changed/unreadable file produces an error/uncertain row, not a confirmed duplicate. Enforce library path containment and existing symlink/access policy. No live-library modifications. Exact groups show UUIDs, title/authors, format/path and content hash.

Similar category starts with normalized nonempty title AND normalized ordered author components; missing/fallback/Unknown values cannot establish a match. This deliberately conservative rule is labeled clearly; it does not claim fuzzy edition identification. Normalization permits case/spacing/Unicode-equivalent matches, not substring-only title matching. Exact and similar groups have separate evidence; a book may occur in both without implying separate copies. False positives require human interpretation; no merge/delete/attach/revert controls.

Dedicated worker scans with one bounded stream at a time to limit I/O contention with search. Discovery uses the in-memory generation, never waits for scan locks. No cross-run hash cache in the initial implementation, avoiding stale-content claims from unchanged stat metadata. Emit throttled phase/files/bytes progress, check cancellation between chunks, and display Cancelled with partial results labeled incomplete. Do not claim a complete no-duplicate result after cancellation/error. Library switch cancels scan. Catalog refresh marks displayed scan stale and requires explicit rescan; background work never silently refreshes an old claim.

## Responsiveness and lifecycle

Loading/indexing: explicit cancellable stages (inventory, copy, catalog extraction, index/review preparation). Existing compatibility and source-coherence guarantees remain. Stage progress does not fabricate percentages where totals are unknown. Shutdown requests cancellation and waits for owned workers; never terminate unrelated Calibre/readers. A cancelled load retains the previous complete catalog with stale status, and deletes only its own temporary snapshot.

Progress reads/hashes and cover existence checks occur outside query/paint paths, once per refresh generation where needed. Do not change reader resume semantics or trusting file identity simply to improve timing. Duplicate worker scheduling and bounded caches isolate discovery responsiveness. Measure current full-snapshot cost and memory before deciding any further optimization; a metadata-only snapshot redesign is not pre-approved.

## Test design and M14-02 fixture

Create a deterministic approximately 10,000-book disposable catalog with an oracle independent of production filter code. Include repeated tags/series, Unicode/case/whitespace, blank and provenance-based fallback metadata, missing covers, explicit Unknown/Unread fixtures, acknowledged/new warnings, manual flags, multiformat books, exact-content groups, similar-only groups and negative matches. Synthetic query-unit fixtures may represent missing fields that Calibre normalizes; installed tests must also validate actual supported Calibre output. Build real scale-library records through supported Calibre tooling in an independent disposable path; do not construct an undocumented production metadata.db schema. Record seed, distribution, identifiers, file count and disk size. Never mix synthetic books into M13 or the copied M14 baseline library.

Measure cold load/index separately from warm discovery. On the actual acceptance machine record CPU/RAM/OS/Qt/Calibre/build and fixture digest. Fixed cases: Unread AND series AND missing cover; missing author OR title; repeated tags under both modes; text with both modes; saved search apply/update after metadata change; review preference/acknowledgment; sorting and switching views. Measure input to visible painted results including debounce. Use 3 warmups and 20 samples per case, report median/p95/max without deleting outliers. Owner's criterion remains normally approximately one second after loading/indexing; measurements near/beyond this need review, not an invented stricter SLA. Repeat discovery during duplicate scanning. Heavy scans have no one-second completion requirement.

Correctness tests: exact result UUIDs against oracle; stale generation rejection; cancel/switch/close; search CRUD and corrupt/concurrent state; factual versus acknowledgment independence; warning-history deletion; refreshed results after verified save; explicit bulk targets including hidden selections; partial/conflict/recovery paths unchanged. Duplicate tests cover format boundaries, file mutation/read failure, cancellation, title/author false positives and no writes. Installed verification plus owner KDE checks remain required. Existing 240 source tests are a baseline, not a substitute for new meaningful tests.

## Delivery and remaining risks

Implement in charter order: isolation/fixture, discovery, searches, review, duplicates, installed/desktop verification. New modules proposed: discovery.py (pure rules/index/query), discovery_store.py, discovery_model.py, discovery_ui.py, review_service.py, duplicate_scan.py and duplicate_ui.py. Keep interfaces small and cover shared rules before UI integration.

M14-01 deliverable is this design. M14-02 is complete only after isolated setup AND scale fixture/baseline measurements; establishing an environment alone is not completion. No M14 feature code, new dependency or Calibre schema change is introduced by this design. Open engineering risks are measured snapshot cost, thumbnail/progress memory/I/O, raw-metadata provenance and UI integration regression; address with the specified probes. No unresolved owner decision is needed to start those tasks. M13 Everyday stays independently launchable; M12 remains Rollback. Any promotion requires a later explicit decision.


## Implementation decisions after scale measurement (2026-09-24)

The shipped M14 development implementation and evidence are in [the implementation report](test_data/m14_discovery/implementation.md). These decisions refine the proposed design; approved scope and acceptance criteria are unchanged.

- The virtual views removed the dominant full-item construction cost. Warm indexed queries plus table repaint take approximately 3–5 ms at 10,000 books. Query evaluation is consequently synchronous against the current immutable in-memory index; text input has a 150 ms debounce. No asynchronous query results exist to become stale. This intentionally avoids the initially proposed per-query worker/generation machinery. The expensive duplicate/file-copy operations retain separate cancellable workers. Reconsider query workers if supported-size measurements cease to meet responsiveness criteria.
- Query schema 1 uses implicit equality (no redundant operator key), `sort` values title_asc/title_desc/author_asc, `formats`, `review_only`, and a visible `catalog_filters` outer constraint for inherited tag/status narrowing. It retains a single Match all/any switch over the explicit condition rows. Missing optional keys remain backward compatible.
- Normalized title/author matching uses the catalog’s ordered author display string. It is conservative potential-match evidence, not author identity resolution or edition grouping.
- The workbench builds the index on opening/reload; measured creation is under one second. Main review filtering caches the index until loaded-catalog or workflow changes. Cover paths are provided by the coherent catalog; viewport icons use a bounded 128-entry cache invalidated on refresh.
- Legacy import provenance is retained by the existing ImportStore migration, while new acknowledgments and flags use the additive DiscoveryStore. The editor and workbench share ReviewService acknowledgment rules.
- A cancelled duplicate scan discards unverified exact groups and explicitly labels results incomplete. This is stricter than showing potentially unverified partial exact evidence.
