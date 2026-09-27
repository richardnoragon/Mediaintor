# Changelog

Current M5 status: **M5 COMPLETE; M5-G PASSED / CLOSED** following final evidence review and user desktop acceptance. [Gate review](test_data/m5_acceptance/gate_review.md). All M5-01–M5-07 tasks are complete. Earlier dated/stage checkpoints are historical; no release is implied.

## Unreleased — 0.1.0-alpha.1

### M18/M19 review fixes (2026-09-27)

- Collect multiple draft/module close and workspace decisions before changing drafts; Cancel preserves pending work.
- Validate Paper library ownership before recovery and protect active staged copies with a file-operation lock.
- Apply Paper document imports off the GUI thread, with cancellable chunked copying and GUI-thread result updates.
- Replace Qt stand-in assumptions in tests with native button actions and asynchronous waits; add preservation, responsiveness and metadata-precedence regressions.

### M19 Paper-inator Knowledge Foundation (development only)

- Paper-inator becomes an available Hub module with one library per Hub profile (`Paper/profiles/<profile id>/`): Home dashboard (Inbox, Continue reading, Needs review, Recently opened, Active projects, Recent notes), Library, Notes, Projects and Trash; startup view Home/Library/Projects/Restore last view.
- Knowledge Items (11 types) with an item editor (Save/Discard/Close, validation keeping input, revision conflict review); versions of a work with a preferred version; documents and attachments as managed copies or referenced files (explicit choice); locate moved files with a content check; external reader (desktop default or configured command).
- Independent reading progress, library handling and flags for one or many selected items; tags; bulk organize with an explicit scope; collections and optional projects without duplicating items.
- Markdown notes (independent or on an item) stored authoritatively in the library, with formatting commands, stable internal links, a safe preview and Markdown export that never overwrites; typed connections (Supports, Contradicts, Extends, Uses, Derived From, References, Related To) between items, notes and projects.
- Search across metadata, tags, notes and document text (optional Poppler `pdftotext`; FTS5), filters, sorts and saved searches.
- Import of PDFs and folders or by drag-and-drop with a reviewable preview: local metadata proposals with sources (optional `pdfinfo`/`pdftotext`, no network), identical files skipped, possible versions offered but never merged automatically, required file-handling choice, revalidation before writing, originals never modified; *Propose metadata from PDF…* applies checked fields only.
- Recoverable Trash keeping notes, connections, memberships and reading state; restore; permanent deletion only after an exact preview, removing managed copies only and finishing interrupted deletions on the next load.
- Reader, annotation and metadata-provider adapter interfaces defined for M20/M21 (no engine selected, no provider implemented).
- Hub: fourth module in the combined close review and shutdown guard; workspaces accept Paper-inator and its selected item; activity guidance and library-reload retry; `--paper-library` for disposable libraries.
- Documents: technical overview and features updated with the owner decisions (SQLite-authoritative notes, PDF engine chosen in M20, DOI lookup in M21, M19–M22 sequence).
- New tests: `test_paper_core.py` (no Qt, 29) and `test_m19_paperinator.py` (Qt, 20; run on a headless stand-in only). Full-suite KDE run, packaging and owner acceptance pending; M19-G open.

### M18 Music-inator foundation (development only)

- Music-inator becomes an available Hub module: catalog tab with Grid/List, Browse by Albums/Artists/Genres/Years, search across album, artists and track titles, genre/format/favourite-and-rating filters and sorts; album editor with Save/Discard/Cancel and revision conflict review; editions with discs and track lists; physical copies and digital copies (sets of audio files); per-profile rating 1–10 and Favourite.
- Import by file/folder selection or drag-and-drop with a reviewable preview: tags first (optional ffprobe), folder and file names as fallback, disc subfolders joined, FLAC/MP3 rips of one release grouped as copies of one edition, compilations under Various Artists, matching to existing albums and editions. Files are never copied, moved, renamed, retagged or deleted.
- Play album: playlist written to application data and opened in the desktop default or configured player (`{playlist}`, `{files}`, `{file}`); moved folders can be located.
- Hub: third module in the combined close review and shutdown guard; workspaces accept any combination of Book-, Music- and Movie-inator plus the selected album; activity guidance and catalog-reload retry; `--music-catalog` for disposable catalogs.
- New tests: `test_music_core.py` (no Qt, 22) and `test_m18_musicinator.py` (Qt, 15; run on a headless stand-in only). Full-suite KDE run, packaging and owner acceptance pending; scan grouping awaits owner confirmation; M18-G open.

### M17 Movie-inator foundation (development only)

- Movie-inator becomes an available Hub module: catalog tab with Grid/List, search, genre/format/watched filters and sorts; detail editor with Save/Discard/Cancel and revision conflict review; editions and physical/file copies; per-profile watched flag and rating.
- Import by file/folder selection or drag-and-drop with a reviewable preview; same title/year files are grouped into one movie; optional ffprobe technical details. Files are never copied, moved, renamed or deleted.
- External player (desktop default or configured command); missing files offer Locate….
- Hub: generic tab close, combined close review, workspaces with Movie-inator tab and selection, activity guidance, `--movie-catalog` for disposable catalogs.
- New tests: `test_movie_core.py` (no Qt) and `test_m17_movieinator.py` (Qt). Full-suite KDE run, packaging and owner acceptance pending; M17-G open.

### M9 closure

- M9-01–M9-07 COMPLETE; M9-G PASSED / CLOSED after migrated-data verification, isolated snapshot rollback/return and all three owner KDE checks. [Evidence](test_data/m9_promotion/gate_review.md).
- Accepted package unchanged; personal test/validation environment only. No RC1/source modification, live NAS deployment or publication.

### M8 closure

- M8-01–M8-07 COMPLETE; M8-G PASSED / CLOSED after owner acceptance of installed KDE launch/filtering, rename/resume and restart persistence.
- Accepted candidate `0.1.0a1-184039712b870efd`, backed by 185 regression tests, 16 disposable probes and eight installed checks. [Gate review](test_data/m8_usability/gate_review.md).
- Closure documentation only: accepted archive remains unchanged; no RC1 change, active-installation promotion or publication. M7 observation remains independent.

### M8 search/filter integration (development only)

- Added title/author/series search, multi-value tag/format/status filters, persisted criteria/panel state and Clear All without clearing selection.
- Full regression: 185 tests passed, including progress malformed-record and rename-history checks. Final desktop search/filter acceptance remains pending; M8-G open.

### M8 progress integration (development only)

- Added bounded viewer-position reading, UTC timestamp selection, tied-format summaries and Unknown progress/status fallbacks.
- Added independent per-format details and application-owned rename provenance; matching identity and unchanged content can resume through an explicit viewer position without rewriting Calibre records.
- Automated regression and disposable rename tests passed; integrated desktop acceptance remains pending. RC1 and active M8 data unchanged.

### M8 scope approved

- Approved independent resume availability, Unknown percentage/status when unavailable, and a clearly labelled most-recently-read-format card summary with per-format details. Three-format desktop resume/navigation confirmed; UI integration remains pending.

- Approved viewer focus reliability, title/author/series search, AND-across/OR-within filters, persisted criteria and Clear All, and Calibre-based per-format progress/resume. Manual progress/status editing and synchronization are deferred.
- M8-01 scope definition complete; separate setup and capability verification remain pending. RC1 unchanged; M8-G remains open with test-based acceptance. [M8 plan](milestone_08_everyday_usability.md).

### M7 conditional acceptance — 2026-09-22

- Owner confirms all planned tests passed; M7-G conditionally accepted and subsequent work authorized immediately. Seven-day observation remains a non-blocking condition, not a completed result.
- Future gates use test-based acceptance without mandatory elapsed-time requirements. [Decision](test_data/m7_daily_use/conditional_acceptance.md). No candidate change or publication.

### M6 closure — 2026-09-22

- M6-01–M6-07 COMPLETE; M6-G PASSED / CLOSED after review of all eight criteria and personal desktop acceptance. See [M6-G closure review](test_data/m6_07_acceptance/gate_review.md).
- Accepted artifact reproduced exactly; no application change, version bump, working-account installation or publication. Earlier checkpoints retain their historical status.

### Added

- Hub and Book-inator with private-snapshot browsing, grid/list views, title/author search, format buttons and remembered profile/device preferences.
- Single-book metadata editor for title, ordered authors, unordered tags, series/number, basic formatted description and local cover replacement/removal.
- Explicit Save/Discard/Cancel, field-level conflicts and global choices, partial-save reporting and retry, and automatic cover-backup recovery.
- Version-bound Calibre 9.2.1 metadata helper with database locking, UUID verification, validation and field read-back. Explicit saves may trigger Calibre-managed path changes.
- Focus/30-second refresh with draft/access deferral; combined metadata/reader/loading close review.
- 41 automated tests, 16 disposable adapter/fault checks and 17 real hub/editor checks on a 101-book copy.

### Behaviour and recovery

- Preferences save immediately; book metadata remains a draft until explicit Save.
- Discard never rolls back successful partial writes. Retry rereads current values and detects new conflicts.
- Clearing Series hides/ignores its internally retained number without a failure; assigning a new series defaults to 1. Non-negative finite decimals are allowed.
- Commas in tag names are rejected with an explanation; commas and order in author names are preserved.
- Untouched description HTML is preserved exactly. Failed cover recovery retains backup data and reports its location.
- Readers open selected-library files. Owned-reader closure is verified/version-bound; no force-close or adoption of external applications.

### Acceptance and known limits

- M1 and G2 viewer lifecycle complete for Calibre 9.2.1, including user-confirmed EPUB/MOBI/PDF reading and both hub close outcomes.
- M2 implementation and automated verification passed; final desktop sign-off is complete. See [acceptance report](test_data/m2_acceptance/README.md).
- Original-library hashes unchanged during M2 acceptance; all mutations targeted disposable copies.
- Concurrent-writer safety beyond Calibre locking is not claimed. Initial viewer keypress remains deferred. Imports, exports, conversion and direct file-management controls are outside M2.

No release or commit has been created. Development version and schema 1 remain unchanged. The workspace has no Git repository; publication requires release/versioning checks and commit references.

### M3 — Safe Ebook Imports (accepted)

- Copy-only EPUB/MOBI/PDF intake via file selection, recursive folders and drag/drop, with mandatory preview/confirmation, exact-content duplicate protection and explicit no-overwrite attachments.
- Source/library revalidation, staged writes, durable version-1 import journals, tracked partial-record repair and commit-before-ack reconciliation. Stop/Review/Retry/Discard Pending never resume writes automatically or remove completed imports.
- Filename/Unknown fallback warnings, a Needs Metadata Review filter and independent completeness/review states. Only explicit Mark Reviewed clears review status.
- Fixed missing destination identity after repair and ensured similar-title rows require an explicit action.
- M3 and M3-G complete: 50 tests, 23 import/recovery checks, five catalog checks and all three user desktop confirmations. Original-library/fixture hashes unchanged during verification.
- Existing hub settings remain schema 1; import journals are a separate versioned store. No release published. Subsequent M4 work is recorded below.

### M4 — Bulk Metadata Editing (accepted)

- Added temporary multi-selection, all-search-result selection, selected count and sorting.
- Added single-operation bulk tag, series and exact-author updates with ordered sequence numbering and mandatory previews.
- Added per-book conflict review, durable partial-save recovery, pending review/retry/discard and field-scoped batch revert.
- Added library-specific history retained until explicit confirmed deletion. Ordinary selections clear when the module closes.
- Passed 64 unit/UI tests, 25 disposable application checks including 101-book edit/revert, and 8 Calibre fault checks; original-library hashes unchanged. User confirmed all desktop checklist items on 2026-09-21; M4 COMPLETE and M4-G PASSED/CLOSED. No release published.

### M5-03 — Production activity and recovery integration

- Added owner-scoped durable activity/attempt history, operation journal integration and actionable-failure recording without successful preference-save telemetry.
- Added recovery payload storage, revision/identity/integrity checks, alternate-location registration and explicit preservation/review APIs. Automatic emergency preservation and close continuation remain M5-06.
- Migrated book-review provenance/status independently of import journals; history cleanup cannot silently clear review warnings.
- Removed automatic startup import-dialog opening in preparation for the M5-04 summary UI.
- Passed 85 unit/UI tests and 14 real disposable integration checks; original-library hashes unchanged. M5-03 complete, M5-G open; no release published.

### M5-04 — Hub Activity, history and startup summary

- Added default collapsible Activity panel with module/operation groups, distinct attention counts and latest success/actual failure details.
- Added read-only full history, all attempt details, dismissed/unresolved filters and next-step guidance.
- Added one non-modal summary above the tabs, including local-journal discovery with Book-inator closed; no automatic resumption. Summary Dismiss retains all work.
- Passed 93 unit/UI tests using isolated stores; recorded offscreen UI evidence. Shared actions remain M5-05, automatic emergency preservation/close handling M5-06, and M5-G open. No release published.

### M5-05 — Shared recovery actions

- Added selected-operation Review / Retry, durable Dismiss, current-revision Discard Pending and separately confirmed Delete History to Activity details.
- Routed imports/bulk edits through existing review/confirmation workflows; recovered single-book edits require identity/conflict review and explicit Save. Partial recovery keeps only outstanding edits; verified completion resolves the copy.
- Added restart-safe, explicitly retried cleanup with owned-file hashes, generation tracking, deletion markers and preservation of book-review status and separate revert descendants.
- Passed 119 unit/UI tests and 13 real-Calibre checks on a fresh disposable copy; seed unchanged, original library untouched. M5-05 complete; automatic emergency preservation/close handling remains M5-06 and M5-G remains open. No release published.

### M5-06 — Automatic emergency preservation and close handling

- Automatically preserve outstanding valid edits after failed Save and failed explicit Retry, with durable registration, current-revision checks and Preserve Elsewhere on failure.
- Continue an already-requested editor/tab/Hub close after successful preservation; ordinary editing stays open. Cancellation leaves no latent close. Existing task, reader and settings-save safeguards remain enforced.
- Show truthful preservation notices and retain startup recovery; ignore validation errors/cancelled conflicts when counting failed writes. Later successful Save resolves preserved work.
- Handle cooperative Qt desktop shutdown with the existing review, or veto noninteractive shutdown with outstanding work.
- Passed 143 unit/UI tests and 14 real disposable Calibre checks; disposable seed unchanged and original library untouched. M5-06 complete; M5-G remains open for M5-07 application/desktop acceptance. No release published.

### M5-07 — Automated acceptance and native KDE close fix

- Passed 147 unit/UI tests and 21 application/scale checks on a fresh 101-book disposable copy; seed unchanged. Prepared an isolated desktop acceptance fixture.
- Passed real KWin 6.6.6 Wayland Cancel and preservation/close scenarios on a private bus/runtime, without host logout or shutdown.
- Fixed duplicate editor Save prompts when KWin separately closes a Hub whose current editor revision was already protected and approved for closure.
- Desktop acceptance is user-confirmed, including successful close and restart recovery without automatic editor opening or cover application. M5-07 complete; M5-G open as requested. No release published.

- M5-07 desktop testing exposed a snapshot-thread destruction failure on close. Suppress new refreshes during close and join owned background reads before destroying widgets; Cancel permits refreshing again. All 147 regression tests and both isolated KWin scenarios pass. Successful desktop close (exit code 0) and restart recovery are user-confirmed; M5-G stays open.

### M5 — Formal milestone and gate closure

- Completed the final evidence review: all 11 M5-G criteria pass. M5 is COMPLETE and M5-G is PASSED / CLOSED for the agreed scope.
- Recorded user acceptance of desktop recovery and isolated KWin evidence; host logout/poweroff was not performed. No release published.
- Updated planning, scope, technical design and module documents; earlier checkpoint status remains historical. See [gate review](test_data/m5_acceptance/gate_review.md).

### M6 — Approved release-readiness scope

- Recorded personal-use packaging, first-run/help improvements, separate Calibre prerequisite checks and privacy-default diagnostic export with preview.
- Added M6-01–M6-07 tasks and M6-G criteria, including upgrade/uninstall data preservation and installed-package acceptance. Implementation not started; M6-G open. No release published.

- Final M6 decisions confirmed: current-user installation only; missing/incompatible/unverified Calibre blocks protected operations with detected/supported-version guidance and no override; diagnostics always exclude book data, paths, library names, backup locations and recovery contents, including in logs/tracebacks. Sensitive-detail opt-in is deferred. M6-01 technical design is next; no version bump or publication performed.

### M6-01 — Technical design complete

- Selected a per-user versioned installation bundle using the verified system Python/PyQt6 runtime; documented upgrade/uninstall preservation and pending clean-environment qualification.
- Recorded the exact Calibre 9.2.1 baseline, shared operation-boundary compatibility guards, and always-redacted typed diagnostics with safe error templates/stack frames.
- No application code, dependency installation or version changes. M6-02–M6-07 remain pending; M6-G open. See [technical design](technical_design_m6.md).

### M6-02 — Installable package built and verified

- Added deterministic offline per-user bundle construction, runtime checks, a menu entry and launcher, versioned activation, installation locks and program-only uninstall.
- Verified 153 unit/UI tests and seven private-namespace install/Hub-smoke/reinstall/uninstall checks; no working user installation or original library changed. Package version remains 0.1.0a1.
- Fresh-OS dependency closure, interrupted/populated-state upgrades and KDE desktop acceptance remain M6-06/07. Calibre operation guards remain M6-03. M6-G open; no release published.

### M6-03 — Compatibility guards and first-run guidance

- Enforce the verified runtime and Calibre 9.2.1 at library, helper and viewer boundaries; missing/unverified versions block without an override. Tool changes invalidate cached checks.
- Add asynchronous first-run guidance and explicit Recheck, preserving local recovery access and preventing automatic replay. Stop pending import/bulk work before further protected operations when compatibility is lost.
- Passed 162 unit/UI tests and 10 disposable/installed checks. Rebuilt the unpublished 0.1.0a1 personal bundle. M6-04–M6-07 remain pending; M6-G open.

### M6-04 — Help and error guidance

- Added offline Help topics/search, F1 and About/version information; packaged standalone installation, workflow and troubleshooting guides.
- Improved startup/settings/missing-format guidance and installed runtime-import errors; accepted Hub exit closes help too. Existing recovery and compatibility safeguards remain unchanged.
- Passed 166 unit/UI tests and seven installed-help checks. Rebuilt personal preview 0.1.0a1; M6-G open, no publication. Next: M6-05 diagnostics.

### M6-05 — Always-redacted diagnostics

- Added Help → Preview redacted diagnostics with frozen exact JSON preview, explicit local export, atomic owner-only files and safe retry after failure.
- Added strict version/state/feature allowlists and bounded current-session fixed error summaries with sanitized stack symbols. Raw logs, metadata, paths and recovery contents are never attached; no sensitive-detail opt-in or automatic upload.
- Passed 174 unit/UI tests and seven installed diagnostic checks. Rebuilt unpublished personal preview 0.1.0a1; M6-G open. Next: M6-06 installation/upgrade qualification.

### M6-06 — Installation/upgrade and retained-data verification

- Added durable installer transactions, explicit repair, interrupted-action launch blocking and hash-checked cleanup without removing application data.
- Passed 177 tests and 14 checks in a fresh package-derived Ubuntu userspace, including a real prior-build upgrade, installed startup, native Qt dependencies, uninstall/reinstall and retained recovery/history read-back.
- Retained the M6-05 artifact as an upgrade baseline. No schema or preview-version bump; original library and working installation untouched. M6-07 desktop acceptance remains pending; M6-G open, nothing published.

M6-07 installed acceptance checkpoint: [21 application and two isolated KWin checks passed](test_data/m6_07_acceptance/README.md) against the unchanged M6-06 artifact. A real installed launcher with isolated HOME/XDG directories is prepared for personal desktop checks. Personal acceptance passed on 2026-09-22, including restart persistence without automatic recovery/resumption. M6-07 is COMPLETE; M6-G is OPEN pending final evidence review and nothing was published.

## M7 scope approved — 2026-09-22

Personal daily-use validation is the next milestone: normal-account installation/KDE menu, dedicated testing library, one-week validation and fixes/usability corrections only. External testing and publication remain excluded. Backup/restore procedure and trial-clock details await clarification. [M7 plan](milestone_07_daily_use_validation.md). M7-G OPEN; no installation or trial started by this documentation update.

M7 clarification confirmed: manual complete-library/application-data copies and isolated restoration only; seven consecutive logged normal-use days on the final candidate, restarting after code/package/configuration fixes changing that build. Daily-use template prepared; installation and trial remain unstarted.

M7-01 complete: inspected expected host installation/data paths, prepared durable Docker-state/test/backup/restore directories and verified a fresh 101-book copy and accepted package hash. Docker deployment replaces native installation by user instruction. GUI mode, runtime and writable database access require M7-02 qualification. No installation or trial started.

M7 testing separated from development: copied and hash-verified the accepted package and 101-book library into sibling `Mediaintor-M7-Testing`, with independent persistent home, backup/restore, deployment and evidence directories. Original preparation files retained. Docker installation and trial not started.

M7 display choice confirmed: native KDE windows for the Docker-contained Hub and Calibre viewer, with host KDE menu launch. Implementation/qualification remains M7-02; no installation or trial started.

M7-02 in progress: prepared standalone Docker deployment and native KDE/Wayland launcher drafts; host SQLite storage checks pass. Docker remains uninstalled pending local administrator commands. No image/runtime acceptance or seven-day trial claimed.

M7-02 update: built/pinned independent Docker image, installed accepted package, verified exact runtime/native Wayland/SQLite locking/private snapshots and throwaway Calibre writes. Added labelled KDE menu launch; verified isolated mounts. User display/viewer/relaunch acceptance remains pending. Trial not started; M7-G OPEN.

M7-02 COMPLETE following user confirmation of native KDE catalog, EPUB/MOBI/PDF reader operation and menu relaunch retaining List view. M7-03 is next; the seven-day trial has not started and M7-G remains OPEN.

M7-03 COMPLETE: manual copies/isolated restore, recovery review/Save and populated-state upgrade/uninstall/reinstall passed 16 checks. Fixed helper-generated bytecode altering installed release inventories; strict installer checks retained, legacy caches quarantined after hash verification. Corrected M7 candidate installed with all retained data unchanged. 177 existing tests plus new helper regression passed. M7-G OPEN; trial not started; original M6 artifact preserved.

RC1 pre-trial deployment approved and completed: pinned Compose, self-contained local image/application bundle, configuration example and verified non-overwriting backup/restore scripts. Eighteen extracted-bundle checks pass. Frozen checksum record substitutes for unavailable Git tag. KDE shortcut now uses Compose; personal handoff and Day 1 agreement pending. No publication/version bump; seven-day trial not started.

M7-04 STARTED: user confirmed all six RC1 acceptance checks and authorized Day 1 on 2026-09-22. Daily result pending; earliest uninterrupted Day 7 is 2026-09-28. No frozen artifact changed; M7-G OPEN.
