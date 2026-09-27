# Book-inator Constitution

Current M5 status: **M5 COMPLETE; M5-G PASSED / CLOSED** following final evidence review and user desktop acceptance. [Gate review](../test_data/m5_acceptance/gate_review.md). All M5-01–M5-07 tasks are complete. Earlier dated/stage checkpoints are historical; no release is implied.

Status: Planning baseline. Inherited hub requirements are agreed; module-specific reference features and proposed modelling principles require confirmation. This constitution does not itself authorize implementation; the user has separately authorized M1 and M2 implementation. Initial delivery direction is personal use on Linux, books first, one device, and synchronisation later; M1 is complete and M2 implementation passed automated verification, with final user desktop sign-off complete. Later feature scope remains open. See [First Release Scope](../first_release_scope.md).

## 1. Authority and scope

Book-inator is the specialist book-collection module within Media-inator. Its reference material covers paper books, e-books, audiobooks, authors, editions, physical locations, and reading devices.

The [hub constitution](../mediaintor%20hub/constitution_hub.md) governs common behaviour. Explicit user decisions take precedence. “Must” below describes inherited requirements; “candidate,” “proposed,” and “open” do not mean approved features. Resolve conflicts through the recorded decisions and update affected documents together.

The module's existing overview, features, and configuration files are captured third-party reference material, not specifications already approved for Media-inator. Their product versions, supported formats, provider integrations, operating systems, shortcuts, and settings defaults must not be copied as commitments.

## 2. Required integration with the hub

### Confirmed initial book scope

The first workflow covers **e-books only**, with paper books and audiobooks deferred. Initial formats are **EPUB, MOBI, and PDF**, using approximately **100 books from an existing Calibre collection** for testing. This test size is not a capacity limit. The confirmed test library is `/home/sproket01/Calibre Library`, now containing 101 records: the original Quick Start Guide plus 100 imported test titles. See the [test collection](../test_data/free_ebooks_100/README.md).

The confirmed initial environment is **Ubuntu 26.04.1 LTS with KDE**, with **Calibre’s e-book viewer** as the selected reading application. Representative EPUB/MOBI/converted-PDF reading and page navigation have been verified; exact position-restoration integration and concurrent annotation-write reliability remain unverified. See the [capability report](../calibre_capability_validation.md).

Book-inator will manage the **existing Calibre library** and import Calibre titles, authors, tags, covers, and reading information where available. Title, author, tag, and cover edits made in Book-inator must update the existing Calibre library. Changes made in Calibre must refresh automatically in Book-inator. If Calibre changes a field with unsaved Book-inator edits, show the competing values in a comparison dialog and let the user choose which to keep; do not silently overwrite either value. Refresh timing and failed write-back handling remain open. This is same-device Calibre integration, not the multi-device synchronisation deferred until later. Integration must be specified before choosing a mechanism for library updates or file operations.

Users add books manually by drag-and-drop or from a folder, **including subfolders**. Copy, move, and rename capabilities are in scope. Before confirming an import, show destination paths and proposed filenames and let the user choose copy or move. Only **identical file contents** count as duplicates. Skip and report such files already in the library, even if their names or locations differ. Matching titles, authors, or filenames alone does not make different file contents a duplicate. Naming rules, destinations, filename collisions, and interrupted-operation recovery remain open.

Different formats remain **separate files**, but reading progress for the same book is **shared across formats within the owning profile**. This does not share progress between people. Present one book card with separate format buttons; offer both cover-grid and table/list views with a switch, showing title, author, formats, tags, and reading status. When an exact reading position cannot be transferred between formats, share **completion status and percentage** while retaining a **separate last-opened position for each file**. Do not treat an approximate percentage as an exact page/location. Matching files to the same book, exact position mapping, and associating imported Calibre reading information with a profile require further definition. Book identity across formats is distinct from duplicate detection based on identical contents.

### First milestone boundary

[Milestone 01](../milestone_01_browse_and_read.md) covers selecting and remembering one Calibre library, browsing/finding books, and opening a chosen format in the viewer. One personal profile and automatic last-session restoration are sufficient. Metadata editing and file intake follow later. Reading progress need not be tracked or updated in M1; existing reading-status display is distinct from that later integration. M1 displays Unknown when reading status is unavailable and uses title/author text search to find books. Profile switching and five named states are deferred from M1, not removed from the suite.

### Shared requirements

- Launch through the hub, with tabs by default and support for docked or separate module windows. First-use startup and profile switching follow the hub's user/device fallback rules.
- Inherit common font, theme, and language preferences while permitting module overrides. Save settings immediately; remember layout and window geometry by person, module, and device.
- Participate in suite-wide profile switching, restoring the destination profile's selection and layout. Personal activity and ratings remain distinct from shared catalog information.
- Apply the shared owner/editor/viewer model. The scope of owner approval and direct editor changes remains deferred; this module must not invent a different policy.
- Make accessible collection results available to hub search even when the module is closed. Selecting a result opens this module at the selected item. Hub search-history and favourite limits are suite policies, not separate per-module allocations.
- Participate in the hub's five named states and automatic last-session saving. Do not create an independent five-state allowance per module. Named states change on explicit saves; maintenance must not alter last-saved timestamps or replacement order.
- Report task activity by operation/module and person/device, including detailed outcomes, latest success/failure, and a separate interrupted status. Retain completed work and expose unfinished work for Retry / Dismiss; dismissal retains inspectable history.
- Participate in settings transfer and the separate backup scopes for settings, catalogs/artwork/personal activity, and media files, for this module or the suite. Emergency edit copies are not backups of the whole catalog.

The hub retains responsibility for common controls and orchestration. Specialist metadata, collection editing, filters, and approved domain operations belong in module planning; no process boundary or storage implementation is implied.

## 3. Reference-derived candidate capabilities

These are a structured inventory for remaining decisions, not a release checklist. Confirmed initial scope above takes precedence over broader reference candidates.

| Area | Reference-derived candidates | Decision still needed |
| --- | --- | --- |
| Collection coverage | Paper, electronic, and audio books; multiple editions and copies; alternate titles. | EPUB/MOBI/PDF e-books are initial scope; other types later. Edition/file grouping remains open. |
| Adding books | Manual entry, title/barcode lookup, file scanning, and imports from other catalogs. | Recursive drag-and-drop/folder intake and Calibre metadata import are agreed; other entry methods remain open; only identical-content duplicates are skipped and reported. |
| Book and author information | Summaries, covers, genres, language, publication information, author biographies and bibliographies. | Which providers and fields are supported, and how are conflicting matches reviewed? |
| Organisation | Search, sorting, combined filters, custom fields/lists, wanted/unread views, and physical locations. | Which fields apply to a work, edition, owned copy, or personal profile? |
| Loans and reports | Physical-copy loans, loan history, reports, statistics, and exports. | What are the copy-level loan rules and reporting requirements? |
| Reading and listening | External readers/audio players, an optional internal audiobook player, reader-device transfer and conversion. | Which integrations support saved locations; are internal playback, transfer, or conversion in scope? |

## 4. Book-specific planning distinctions

The following are proposed modelling principles derived from the references, pending user confirmation; they are not a database schema:

- Distinguish a book/work, edition or translation, owned copy, and digital file. A paper copy, e-book, and audiobook may relate to the same work without being the same owned item.
- Distinguish author information and bibliographies from books actually owned or wanted. Downloading information alone must not be assumed to establish ownership.
- Keep physical shelf location, digital file location, and reading position conceptually separate. The reference product's automatic loan return on location change has not been adopted.
- Decide whether read status and ratings belong to the work, edition, or copy. Do not assume audiobook listening and reading progress can share one position.

The hub's approved restoration rules apply: reopen books at the saved page/location and audio paused at its saved position when supported; explain unsupported external-reader/player restoration and offer Open normally. Paper-book progress entry, audiobook chapter handling, and conversion between page/location representations remain open.

## 5. Restoration and external application ownership

The module must honour Locate / Retry / Skip for missing content while allowing available content to restore. Use once leaves stored locations unchanged; Update saved location updates every reference in the current profile, including named states.

Exclusion temporarily suppresses restoration across the profile while preserving associations. Excluded from Restoration allows re-enabling surviving associations; deleted, overwritten, or manually removed associations must not be recreated. Permanent removal destroys associations and is distinct from deleting media or catalog entries. Maintenance does not change state save timestamps.

Distinguish hub-launched applications from existing applications the hub attached to. Track originating profile/module ownership of sessions. Attached applications and unrelated content remain open; only hub-opened sessions may close where supported. Keep shared applications open while another module needs them and explain why. Keep open across profile switching retains original profile/progress ownership.

The combined review offers Keep open / Close and respects the hub's owner-count and global Close for all modules rules. Failed closure offers Retry / Leave open and continue / Cancel; avoid force-closing by default. Unsupported position restoration requires an explanation and an offer to Open normally, not a silent fallback.

## 6. Edits, interruptions, and recovery

Closing this module uses one review scoped to its unsaved edits, running tasks, and external sessions. Hub exit/profile switching combine affected modules in the same review. Save / Discard apply to catalog edits; Cancel stops the requested operation before pending actions execute. Show no review when nothing needs attention.

On failed catalog saves during hub exit/profile switching, permit retry and then preserve only unsaved edits in an emergency version if retry fails. Successful emergency saving permits continuation with an accurate banner and later Review and recover edits. If emergency saving fails, stop and offer an alternate location. Recovery conflicts show current/recovered values for user selection.

Emergency storage/retention, applying emergency recovery to individual module closure, and handling partially completed items remain open at suite level. This constitution does not resolve them independently.

## 7. Configuration boundaries

Synopsis length, result pagination, title sorting, hover previews, artwork display, image extraction from e-books, provider/download choices, reader/player associations, custom fields, and backup reminders are candidate settings. EPUB, MOBI, and PDF are the initial formats. Exact defaults, archive handling, and reader-device compatibility remain open.

Approved settings save immediately, unlike the captured reference products' explicit OK-to-save descriptions. Do not silently adopt reference behaviours such as making an item owned on metadata download or marking a loan returned after a location change. Define such choices explicitly if wanted.

Player/reader selection scope, provider credentials, import/export rules, preset precedence, and device-specific options require further planning. Reference password locks do not establish a Media-inator authentication design. No database, framework, schema, sync protocol, plugin runtime, or provider is selected here.

The rough scaffold's manual/automatic ingestion and later-sync goals are planning context. Manual file/folder intake and copy/move/rename are now agreed initial capabilities; operation policies, metadata extraction beyond the agreed Calibre import, and integration/write ownership still need decisions. Automatic watched-folder ingestion has not been selected for the first workflow. The scaffold's technical suggestions are not binding.

## 8. Documentation and change discipline

Module help, user documentation, and relevant release notes must explain inherited immediate settings saving, profile switching, named-state versus last-session behaviour, recovery, exclusions, and external-session ownership. Explain domain-specific restoration limitations accurately and distinguish collection information, owned media, and personal activity. Document shared completion status/percentage versus per-file reading positions, the Calibre edit-conflict comparison, and identical-content-only duplicate skipping.

When a candidate becomes agreed scope, record the decision and update this constitution and the applicable module planning documents without presenting third-party reference prose as original requirements. Preserve the hub's shared rules and explicitly identify any requested amendment. Do not describe planned capabilities as shipped.

## 9. Open module decisions

- How should files be matched to the same book, and how should shared progress update when formats report different percentages? Book-card presentation with separate format buttons is agreed.
- How are failed metadata writes reported/retried, and when does automatic refresh run? Conflicting edits use the agreed comparison dialog.
- What are the naming, destination, filename-collision, and interruption rules for copy/move/rename in the existing Calibre library? Identical file contents are the only duplicate criterion.
- Which reading information is available from the Calibre integration, and how is imported progress associated with the personal profile?
- Should read status and ratings be shared across editions or maintained separately?
- Are reader-device transfer or format conversion wanted? Paper-copy loans and internal audiobook playback belong to later book-type planning.
- Which candidate metadata providers, imports, exports, custom fields, reports, and loan functions are wanted?
- What should scanning/matching do with ambiguous entries, missing metadata, and user-edited values? Only identical-content matches may be reported as skipped duplicates.
- Which defaults and first-release deliverables should be selected after the module scope is agreed?

Suite-level deferred questions remain deferred: owner-approval scope/editor rights and backup category/profile selection. Linux is the initial platform and Book-inator is the first module priority for personal use on one device. Synchronisation comes later; later platforms and LAN/cloud timing remain undecided.

## 10. Sources

| Source | Role |
| --- | --- |
| [Hub constitution](../mediaintor%20hub/constitution_hub.md) | Governing shared commitments |
| [Hub overview](../mediaintor%20hub/mediainator%20hub%20overview.md) | Shared purpose and summary |
| [Hub features](../mediaintor%20hub/mediainator%20hub%20features.md) | Workflows and remaining suite decisions |
| [Hub configuration](../mediaintor%20hub/mediainator%20hub%20config.md) | Settings, defaults, and scope |
| [Module overview](bookinator%20overview.md) | Reference collection types and domain purpose |
| [Module features](bookinator%20features.md) | Candidate specialist capabilities |
| [Module configuration](bookinator%20config.md) | Candidate settings, not adopted defaults |
| [Rough scaffold](../mediainator%20rough%20scaffold.md) | Historical goals and exploratory suggestions |

M1 implementation decision: initially allow one hub-launched reader at a time. The restriction is limited to M1 and does not authorize closing unrelated external readers. Live-library integration and full 101-book application acceptance remain gated on the production read/concurrency decision.

## Accepted M1 access restriction

For the initial Book-inator milestone, browse a temporary private copy of the selected Calibre library and open books from their original locations. Require Calibre and other readers to be closed while the hub refreshes or launches a reader; allow one hub-launched reader at a time. Explain conflicts and let the user close external apps and Retry; do not close or adopt unrelated sessions. Remember the original library location, not the temporary snapshot. This is an M1 delivery restriction, not a removal of later suite capabilities or an optional concurrency setting already implemented.

The external reader may save its normal annotations/settings. Snapshot copying uses temporary disk space and time and is not a backup. The policy is user-approved; integration verification remains open before full 101-book acceptance. Details: [accepted decision](../m1_library_access_decision.md).

## M2 metadata-editing scope

The user selected catalog viewing and one-book-at-a-time metadata editing for M2. Editable fields are title, authors, tags, cover, series, series index and comments/description. Catalog edits use explicit Save/Discard; hub preferences still save immediately. Focus regain and 30-second idle refresh must preserve drafts and defer for unavailable access. Conflicts use per-field choices and keep-all/use-all shortcuts. Partial saves retain successes and report/retry failures. Import/export, add/delete, conversion, move/rename and bulk editing are excluded from M2. See [M2 specification](../milestone_02_metadata_editing.md) for the now-confirmed Calibre-managed file side effects, draft exit and partial-save semantics; do not infer that the earlier release-level goals are removed.

M2 clarification decisions confirmed: metadata Save may perform Calibre-managed title/author path changes, cover writes and database updates, but M2 provides no direct filesystem commands. Dirty book selection, editor/module/app close and explicit Refresh use Save / Discard / Cancel. Automatic focus/idle refresh defers while dirty and updates clean editors. Save continues the requested action only once outstanding edits/results are resolved. Partial successes remain committed; Discard abandons only remaining unsaved changes. Every Save/Retry re-reads Calibre and checks remaining edits against their baseline for new conflicts. The three blocking questions are settled; initial disposable write validation is now complete; next is the guarded editor/write adapter, using the now-confirmed editor and recovery decisions. See [M2 specification](../milestone_02_metadata_editing.md).

M2-01 capability validation completed on a fresh 101-book copy using one multi-format record. Seven-field round trip, path changes, real partial mutation and protocol conflict/retry checks are recorded in the [validation report](../test_data/m2_validation/README.md). Original-library hashes were unchanged. Missing/invalid covers and ignored index changes require prevalidation, cover recovery protection and field read-back. M2 editor implementation, access/race handling and application acceptance remain open.

Confirmed M2 series rule: clearing Series hides its number and removes the series name on Save. Any internally retained Calibre index is ignored and is not a save failure. New series default explicitly to 1 unless edited; no retained index carries over. This supersedes literal stored-index removal. The future keep-number/start-at-1 prompt remains outside M2.

M2 editor/recovery decisions confirmed: actual failed series-name removal follows normal partial-save handling with Retry / Keep Editing / Discard and no rollback of successful writes. Covers support local selection, preview, replacement and complete removal; failed cover writes automatically restore the backed-up original, verify recovery and retain the proposed replacement for retry. Descriptions use basic rich text (paragraphs, bold, italic, bullet and numbered lists), preserving untouched HTML exactly. Series numbers accept non-negative decimals and default to 1 for a new series. Authors use ordered Add/Remove/Reorder entries; tags use unordered Add/Remove entries. Author names preserve commas; comma-containing tag names cannot be saved, with an explanation that Calibre treats commas as separators. These requirements are implemented and accepted; M2-A12–M2-A17 record acceptance in the M2 specification.

## M2 follow-up compatibility checkpoint

Disposable Calibre 9.2.1 API verification passed cover deletion, automatic backup-restoration protocol, ordered author round trips (including commas), exact untouched HTML preservation and numeric validation. UUID and format contents were preserved; original-library hashes were unchanged. These are capability/protocol results, not completed application acceptance.

The user resolved both compatibility blockers: when no series exists, hide and ignore Calibre's internally retained index; it is not a save failure. Assigning a new series explicitly defaults to 1 unless edited. Individual tag names may not contain commas; validation must prevent saving them and explain that Calibre treats commas as separators. Application implementation and acceptance remain open; these decisions do not mark tests complete.

## Current M2 implementation and gate status

M2-02–M2-06 are implemented and automated verification passed: 41 tests, 16 adapter checks and 17 real application checks on disposable 101-book copies. M2-07 is DONE following user desktop sign-off; M2 is COMPLETE for the agreed scope. G2 (M1 viewer lifecycle) is PASSED/CLOSED for Calibre 9.2.1 using recorded user confirmations and passing regressions. Earlier implementation-pending checkpoints are historical. See [M2 acceptance](../test_data/m2_acceptance/README.md) and [M2 technical design](../technical_design_m2.md). No release or schema migration was performed.

## Approved M3–M5 sequence

M3 is [Safe Ebook Imports](../milestone_03_safe_ebook_imports.md), with copy-only intake and mandatory preview/confirmation before every import. Source contents, filenames and locations must be preserved; move, rename and delete-original operations remain deferred. Exact-content duplicates are skipped/reported, and similar-title/missing-metadata/validation issues are surfaced in preview. M3-G is the approved gate and remains open. M4 is Bulk Metadata Editing; M5 is Hub Activity / Recovery. Detailed M4/M5 scope remains open; essential per-import recovery belongs to M3. Automatic import without preview is a future unassigned preference, not M3 behaviour.

M3 import decisions confirmed: users may explicitly attach formats to existing books without automatic overwrite. Missing title/author use filename/Unknown fallbacks, with preview warnings and a persistent Needs metadata review marker. Interruption finishes verifying the current item if possible, preserves completed imports and records unfinished work. Restart offers Review / Retry / Discard Pending with completed/pending counts and no automatic resumption. Retry reconciles uncertain writes and requires the mandatory preview/confirmation; Discard Pending never removes completed imports or source files. See [M3 requirements and gate criteria](../milestone_03_safe_ebook_imports.md). M3-01 planning is done; M3-02 technical validation is next. M3-G remains OPEN / NOT RUN.

M3 capability checkpoint: M3-02 is complete with 13 disposable import/attachment/recovery protocol checks and unchanged original-library hashes. Production input validation must handle Calibre parser fallbacks, and recovery must reconcile metadata-only partial records and committed-but-unacknowledged operations. See [M3-02 results](../test_data/m3_validation/RESULTS.md). M3-G remains open; no production import implementation or UI acceptance is claimed.

Current M3 implementation: safe copy-only imports, mandatory preview, explicit no-overwrite attachments, durable stop/retry/discard recovery and fallback review markers are implemented with passing automated verification. Metadata completeness is calculated independently; Needs Metadata Review persists until explicit Mark Reviewed. M3-G is PASSED/CLOSED: all three desktop confirmation groups are now user-confirmed. See [M3 acceptance](../test_data/m3_acceptance/README.md).

Final M3 acceptance: all seven tasks and eleven M3-G criteria complete with 50 tests, 23 import/recovery checks, five 101-book hub checks and user-confirmed preview/import, review controls and EPUB/MOBI/PDF reading. Earlier open-gate statements are historical. See [acceptance record](../test_data/m3_acceptance/README.md). M4 implementation and acceptance status are recorded below; no release was published.

## Approved M4 boundary

[M4 Bulk Metadata Editing](../milestone_04_bulk_metadata_editing.md) includes tag add/remove, series set/clear, specified-author replacement, selection retained across filtering/sorting/paging, three series-number modes, mandatory per-book preview, isolated conflict review, M3-style pending recovery and batch revert with before/after values and fresh conflicts. Titles/descriptions/covers remain single-book; previously deferred ISBN/file-level editing is not added by this scope. M4 is COMPLETE and M4-G is PASSED/CLOSED following automated verification and user desktop sign-off on 2026-09-21. M5 remains the shared Hub Activity / Recovery milestone.

Confirmed M4 semantics: exact selected-author replacement preserves co-author order and deduplicates the replacement; Keep Existing Numbers uses active visible values or 1, ignoring orphan indices; sequential start is finite and non-negative with a finite positive increment, preserving previewed numbers and gaps. Each batch has one operation. Ordinary library-specific selection clears on module/application close, while pending batches remain recoverable. Library-specific history persists indefinitely until explicit confirmed deletion, warning that deleting the record permanently removes the ability to revert that batch.

Final M4 acceptance: M4-01–M4-07 complete and M4-G PASSED/CLOSED; the user confirmed all desktop checklist items on 2026-09-21. Passed 64 unit/UI tests, 25 application checks including 101-book edit/revert, and 8 injected-failure checks. Original-library hashes were unchanged. [Evidence and confirmed desktop checks](../test_data/m4_acceptance/README.md). Earlier M4 scope-only statements are historical.

## Approved M5 boundary

[M5 Hub Activity & Recovery](../milestone_05_hub_activity_recovery.md) covers a default collapsible Hub activity panel, full persistent history, operation grouping/outcomes, review-based Retry, Dismiss, Discard Pending, confirmed Delete History, a startup recovery summary and emergency preservation of unsaved single-book edits. Scope remains Book-inator, one profile/device. No automatic resumption, backups, synchronization, additional modules or dashboard customization. Emergency copies use Application Data / Recovery / Single Book Edits, with Preserve Elsewhere on failure; tab closure and orderly Hub/application shutdown are included. Scope definition is complete and all three clarification decisions are confirmed. Successful emergency preservation automatically completes an already-requested close with truthful recovery notices; without a close request, the editor remains open. Delete History is unavailable for unresolved recovery until separate Review Recovery and explicit Discard Pending; resolved records may be deleted with confirmation. Successful routine preference saves are excluded from Activity, while actionable settings-save failures are included. M5-01–M5-03 DONE; M5-G OPEN pending the remaining application features and acceptance.

Historical M5-02 technical checkpoint: [design](../technical_design_m5.md) and [31 passing disposable recovery checks](../test_data/m5_validation/README.md) complete. Original-library hashes and ebook contents unchanged. Production Activity/recovery UI, safe book-review-state migration and acceptance remain outstanding. No application code changed.

Current M5-03 checkpoint: production activity/recovery storage, import/save/bulk/revert outcome recording, actionable failure recording and independent book-review-state migration are implemented. [85 unit/UI tests and 14 disposable integration checks](../test_data/m5_03_integration/README.md) passed; original-library hashes unchanged. M5-04–M5-07 and M5-G remain open. Automatic emergency preservation and close continuation are not enabled yet.

Current M5 implementation checkpoint: M5-01–M5-05 are complete. Hub Activity/history/startup summary and shared review/retry, persistent dismissal, guarded discard and coordinated history deletion are implemented. [M5-05 evidence](../test_data/m5_05_actions/README.md): 119 unit/UI tests and 13 real disposable checks passed. Automatic emergency preservation and close handling remain M5-06; final application acceptance remains M5-07. M5-G stays OPEN. Earlier stage checkpoints are historical, not current completion claims.

Current M5-06 checkpoint: automatic preservation after failed Save/Retry and requested-close continuation are implemented. Ordinary editing stays open; preservation/registration failure keeps the draft open and offers an alternate location. Protection is specific to the current draft revision. Cooperative session shutdown reuses review where supported; forced termination is not draft autosave. [143 unit/UI tests and 14 disposable checks](../test_data/m5_06_emergency/README.md) passed. M5-01–M5-06 DONE; M5-07 application/desktop acceptance and M5-G remain OPEN. Earlier checkpoint statements are historical.
