# First Release Scope

**M14 — Library Discovery & Metadata Productivity: scope APPROVED; M14-01 design complete; isolated development environment verified; M14-G OPEN.** [Approved scope and tasks](milestone_14_library_discovery_metadata_productivity.md). Discovery first, metadata review second; approximately 10,000-book acceptance target. M13-G is CLOSED and **Media-inator Everyday (M13)** is promoted; M12 is retained as Rollback. [M13 acceptance](test_data/m13_workflows/final_acceptance.md) and [promotion](test_data/m13_workflows/promotion.md). M15 remains provisional. No publication.

**M12 — Everyday Usability and Reliability COMPLETE; M12-G PASSED / CLOSED.** Accepted installed build `0.1.0a1-f59e8af9b043f304`: 223 source tests, 64 installed targeted tests, personal KDE acceptance and final saved-data verification passed. [Final gate review and known usability follow-ups](test_data/m12_usability/gate_review.md). M11 unchanged; no publication. Owner-authorized [everyday promotion is complete](test_data/m12_usability/promotion.md); accepted package and current data retained.

**M11 — Promote M10 for Personal Everyday Use COMPLETE; M11-G PASSED / CLOSED.** Use **Media-inator Everyday (M11)**. Exact accepted M10 build installed separately; backup/restore, owner KDE checks and persisted workspace/import/edit/bulk-revert/recovery results verified. [Final gate review](test_data/m11_promotion/gate_review.md). RC1/M9/M10 retained; no publication. Next: personal use or define M12.

**M10 — Hub Workspace Save and Restore COMPLETE; M10-G PASSED / CLOSED.** Accepted build `0.1.0a1-a3a4679f39f4c255`: 215 regression tests, isolated package verification, installed KDE workspace/monitor acceptance and final import/bulk/recovery checks passed. [Final gate review](test_data/m10_workspaces/gate_review.md). RC1 and M9 remain unchanged; nothing published. M11 promotion scope is now approved.

**M9 — Everyday Installation and Safe Upgrade COMPLETE; M9-G PASSED / CLOSED.** Accepted M8 package installed and validated in the separate Docker/KDE test environment, with verified data preservation, snapshot rollback/return and owner desktop acceptance. [Final review](test_data/m9_promotion/gate_review.md). RC1 and the M8 source remain unchanged; M7 observation remains independent. No NAS/live-library deployment or publication.

**M8 — Book-inator Everyday Usability COMPLETE; M8-G PASSED / CLOSED.** Owner confirms all three installed KDE checks passed for candidate `0.1.0a1-184039712b870efd`. Search/filter persistence, progress display and rename/resume are accepted, backed by 185 regression tests, 16 disposable probes and eight installed checks. [Final gate review](test_data/m8_usability/gate_review.md). RC1 and M7 observation remain unchanged; nothing published.

**M7 planned testing COMPLETE; M7-G CONDITIONALLY ACCEPTED.** The owner confirms all planned tests passed and authorizes subsequent work to proceed immediately for business reasons. The seven-day normal-use observation remains an outstanding, non-blocking condition; it has not been completed or waived. RC1 remains frozen. Future milestone gates use explicit tests and pass/fail criteria, with no mandatory elapsed-time requirement. Nothing was published. [Acceptance decision](test_data/m7_daily_use/conditional_acceptance.md).

Current status: **M6 COMPLETE; M6-G PASSED / CLOSED (2026-09-22).** All M6-01–M6-07 tasks are complete. [M6-G closure review](test_data/m6_07_acceptance/gate_review.md). Version remains 0.1.0a1; nothing published. Earlier checkpoint notes are historical.

Completed milestone: **M6 — First Release Readiness**, approved for personal use on Ubuntu 26.04.1 with KDE: per-user installation only, protected operations blocked for unverified Calibre versions without an override, and always-redacted diagnostics with no sensitive-detail opt-in. [Scope, tasks and M6-G](milestone_06_release_readiness.md). M6-01 [technical design](technical_design_m6.md) is complete; M6-02 [package build and isolated-user verification](test_data/m6_package/README.md) is complete; M6-03 [compatibility guards and first-run guidance](test_data/m6_03_compatibility/README.md) is complete; M6-04 [help, instructions and error polish](test_data/m6_04_help/README.md) is complete; M6-05 [always-redacted diagnostic export](test_data/m6_05_diagnostics/README.md) is complete; M6-06 [installation, upgrade and retention verification](test_data/m6_06_installation/README.md) is complete; M6-07 is COMPLETE: [installed application/KWin checks and personal desktop acceptance passed](test_data/m6_07_acceptance/README.md). M6-G is PASSED / CLOSED following final evidence review. No release published; publishing requires separate instruction.

Current M5 status: **M5 COMPLETE; M5-G PASSED / CLOSED** following final evidence review and user desktop acceptance. [Gate review](test_data/m5_acceptance/gate_review.md). All M5-01–M5-07 tasks are complete. Earlier dated/stage checkpoints are historical; no release is implied.

Status: M1/G2 complete for the agreed scope. M2 implementation and automated checks passed; final user desktop sign-off is complete. The user has authorized this implementation work. Broader first-release deliverables are not all committed.

## Confirmed direction

| Decision | Agreed scope |
| --- | --- |
| Initial audience | The project owner, for personal use |
| Initial operating system | Ubuntu 26.04.1 LTS with KDE (confirmed by user) |
| First complete module workflow | E-books through Book-inator and the required hub; paper books and audiobooks later |
| Initial file formats | EPUB, MOBI, PDF |
| Existing collection and test scale | Confirmed library: `/home/sproket01/Calibre Library`; 101 records after importing 100 free test titles alongside the original Quick Start Guide; 100 EPUB, 10 MOBI, and 10 converted PDF files in the new collection. Approximately 100 books is a test scale, not a product capacity limit |
| Library management | Manage the existing Calibre library; write Book-inator title/author/tag/cover changes back to Calibre and automatically refresh Calibre-side changes |
| Metadata import | Calibre titles, authors, tags, covers, and reading information where available |
| Format handling | Separate EPUB/MOBI/PDF files; shared reading progress for the same book within the owning profile; one book card with separate format buttons |
| Duplicates | Only identical file contents count as duplicates; skip and report them, regardless of filename or location |
| Reading-progress fallback | Share completion status/percentage across formats within the profile; retain each file’s own last-opened position when exact mapping is unavailable |
| Conflicting metadata edits | Compare Calibre changes and unsaved Book-inator changes; let the user choose which value to keep |
| Reading application | Calibre’s e-book viewer |
| Initial intake | User-triggered drag-and-drop and adding from a folder, including subfolders |
| File management | Copy, move, and rename; preview destination paths and proposed filenames, choose copy or move, then confirm |
| Initial device scope | One device |
| Synchronisation | Add later; not required for the first release |

The hub remains the entry point. Book-inator is the first module priority; movie, music, game, stamp, and currency remain in the planned suite without first-release commitments.

These choices narrow delivery, not the long-term product principles. Personal use does not by itself decide how many profiles are needed or approve deferring all shared-collection features. Milestone one is now defined in [Milestone 01 — Browse and Open E-books](milestone_01_browse_and_read.md): one personal profile, one remembered Calibre library, grid/list switching, title/author/formats/tags/reading-status display, viewer launch, and automatic last-session restoration. M1 uses title/author text search and displays Unknown when reading status is unavailable. Reading-progress updates, editing, and intake follow later; the remaining first-release hub subset still needs selection.

Future synchronisation remains a planning requirement. Distinguish profile-owned information from device-specific settings and locations when specifying the data model. No sync topology, server, database, or implementation is selected here, and no zero-rewrite guarantee is made. Cross-device behaviour in the constitutions describes future scope where it requires synchronisation.

## Decisions needed for the first complete book workflow

- Calibre integration: automatic refresh timing, failed write-back, and consistency of file operations with the existing library. Metadata write-back and automatic refresh are agreed; the integration mechanism is not yet selected or verified. This same-device integration is distinct from deferred multi-device synchronisation.
- Intake details: unsupported files found in selected folders. Identified duplicates are skipped and reported. Automatic watched-folder ingestion is not part of the selected initial intake; later scope remains open.
- File operations: destination selection, naming rules, collisions, meaning of move for external sources versus existing library items, and recovery after interruption. Preview/confirmation is agreed.
- Initial metadata: fields extracted from files, manual editing, and whether online lookup is deferred. File intake is agreed; metadata-only manual record creation has not been specified.
- Core information: work/edition/file relationships and ratings. Reading progress is shared across formats for the same book within a profile; book matching and exact position mapping remain open. When exact mapping is unavailable, share completion status/percentage and keep a separate last-opened position for each file. Matching a book across formats is distinct from identifying an identical-content duplicate.
- Calibre viewer compatibility: Representative EPUB/MOBI/converted-PDF reading and page navigation passed. Access to reading information, exact saved-position restoration, and concurrent-write handling still require integration work. “Where available” does not promise every field or format is supported.
- First-release hub subset: profiles, shared collections, panels, saved states, and recovery/backup requirements.
- M1 workflow and acceptance criteria are recorded in its milestone document; technical validation and M2 detailed acceptance criteria remain to be completed.

## Planning sources

- [Hub constitution](mediaintor%20hub/constitution_hub.md).
- [Book-inator constitution](bookinator/bookinator_constituion.md).
- [Hub overview](mediaintor%20hub/mediainator%20hub%20overview.md).

Foundation coding is authorized. No release or delivery date is committed; the source preview uses development version 0.1.0-alpha.1.

M1 implementation constraints: one hub-launched reader at a time initially; resolve G1 live-library access/concurrency before enabling live access or running the full 101-book application acceptance. Sample-data foundation development and checks may proceed now.

## Accepted M1 library-access workflow

Browse a temporary private copy of the remembered Calibre library; open selected formats from their original locations. Require Calibre and other readers to be closed while refreshing or launching, with one hub-launched reader at a time. External readers remain externally owned and untouched. Temporary copying costs time and disk space; it is not a backup. Policy is accepted; G1 integration validation still precedes full 101-book acceptance. See [decision record](m1_library_access_decision.md).

Current milestone status: **M1 complete for the accepted scope.** G1 passed before the full 101-book application run; automated checks and final user-confirmed reader/navigation/close outcomes passed. Twenty-three automated tests pass. Known limitations and later release work remain documented in the [acceptance report](test_data/m1_acceptance/README.md). This supersedes historical pending-acceptance notes above.

## M2 delivery boundary

[M2](milestone_02_metadata_editing.md) is catalog viewing and single-book metadata editing: title, authors, tags, cover, series, series index and comments/description. Explicit Save/Discard; automatic focus/30-second idle refresh without overwriting drafts; per-field conflicts and partial-save recovery. Imports, exports, add/delete books, conversions and filesystem-management operations are excluded from M2. Earlier release-level intake/file-management goals remain later work. Calibre-managed title/author path changes, cover-file writes and database updates are permitted as metadata-save side effects; direct file-management commands remain excluded. Bulk editing is assigned to M4; M3 is Safe Ebook Imports.

M2 clarification decisions confirmed: metadata Save may perform Calibre-managed title/author path changes, cover writes and database updates, but M2 provides no direct filesystem commands. Dirty book selection, editor/module/app close and explicit Refresh use Save / Discard / Cancel. Automatic focus/idle refresh defers while dirty and updates clean editors. Save continues the requested action only once outstanding edits/results are resolved. Partial successes remain committed; Discard abandons only remaining unsaved changes. Every Save/Retry re-reads Calibre and checks remaining edits against their baseline for new conflicts. The three blocking questions are settled; initial disposable write validation is now complete; next is the guarded editor/write adapter, using the now-confirmed editor and recovery decisions. See [M2 specification](milestone_02_metadata_editing.md).

M2-01 capability validation completed on a fresh 101-book copy using one multi-format record. Seven-field round trip, path changes, real partial mutation and protocol conflict/retry checks are recorded in the [validation report](test_data/m2_validation/README.md). Original-library hashes were unchanged. Missing/invalid covers and ignored index changes require prevalidation, cover recovery protection and field read-back. M2 editor implementation, access/race handling and application acceptance remain open.

Confirmed M2 series rule: clearing Series hides its number and removes the series name on Save. Any internally retained Calibre index is ignored and is not a save failure. New series default explicitly to 1 unless edited; no retained index carries over. This supersedes literal stored-index removal. The future keep-number/start-at-1 prompt remains outside M2.

M2 editor/recovery decisions confirmed: actual failed series-name removal follows normal partial-save handling with Retry / Keep Editing / Discard and no rollback of successful writes. Covers support local selection, preview, replacement and complete removal; failed cover writes automatically restore the backed-up original, verify recovery and retain the proposed replacement for retry. Descriptions use basic rich text (paragraphs, bold, italic, bullet and numbered lists), preserving untouched HTML exactly. Series numbers accept non-negative decimals and default to 1 for a new series. Authors use ordered Add/Remove/Reorder entries; tags use unordered Add/Remove entries. Author names preserve commas; comma-containing tag names cannot be saved, with an explanation that Calibre treats commas as separators. These requirements are implemented and accepted; M2-A12–M2-A17 record acceptance in the M2 specification.

## M2 follow-up compatibility checkpoint

Disposable Calibre 9.2.1 API verification passed cover deletion, automatic backup-restoration protocol, ordered author round trips (including commas), exact untouched HTML preservation and numeric validation. UUID and format contents were preserved; original-library hashes were unchanged. These are capability/protocol results, not completed application acceptance.

The user resolved both compatibility blockers: when no series exists, hide and ignore Calibre's internally retained index; it is not a save failure. Assigning a new series explicitly defaults to 1 unless edited. Individual tag names may not contain commas; validation must prevent saving them and explain that Calibre treats commas as separators. Application implementation and acceptance remain open; these decisions do not mark tests complete.

## Current M2 implementation and gate status

M2-02–M2-06 are implemented and automated verification passed: 41 tests, 16 adapter checks and 17 real application checks on disposable 101-book copies. M2-07 is DONE following user desktop sign-off; M2 is COMPLETE for the agreed scope. G2 (M1 viewer lifecycle) is PASSED/CLOSED for Calibre 9.2.1 using recorded user confirmations and passing regressions. Earlier implementation-pending checkpoints are historical. See [M2 acceptance](test_data/m2_acceptance/README.md) and [M2 technical design](technical_design_m2.md). No release or schema migration was performed.

## Approved M3–M5 sequence

M3 is [Safe Ebook Imports](milestone_03_safe_ebook_imports.md), with copy-only intake and mandatory preview/confirmation before every import. Source contents, filenames and locations must be preserved; move, rename and delete-original operations remain deferred. Exact-content duplicates are skipped/reported, and similar-title/missing-metadata/validation issues are surfaced in preview. M3-G is the approved gate and remains open. M4 is Bulk Metadata Editing; M5 is Hub Activity / Recovery. Detailed M4/M5 scope remains open; essential per-import recovery belongs to M3. Automatic import without preview is a future unassigned preference, not M3 behaviour.

M3 import decisions confirmed: users may explicitly attach formats to existing books without automatic overwrite. Missing title/author use filename/Unknown fallbacks, with preview warnings and a persistent Needs metadata review marker. Interruption finishes verifying the current item if possible, preserves completed imports and records unfinished work. Restart offers Review / Retry / Discard Pending with completed/pending counts and no automatic resumption. Retry reconciles uncertain writes and requires the mandatory preview/confirmation; Discard Pending never removes completed imports or source files. See [M3 requirements and gate criteria](milestone_03_safe_ebook_imports.md). M3-01 planning is done; M3-02 technical validation is next. M3-G remains OPEN / NOT RUN.

M3 capability checkpoint: M3-02 is complete with 13 disposable import/attachment/recovery protocol checks and unchanged original-library hashes. Production input validation must handle Calibre parser fallbacks, and recovery must reconcile metadata-only partial records and committed-but-unacknowledged operations. See [M3-02 results](test_data/m3_validation/RESULTS.md). M3-G remains open; no production import implementation or UI acceptance is claimed.

Current M3 implementation: safe copy-only imports, mandatory preview, explicit no-overwrite attachments, durable stop/retry/discard recovery and fallback review markers are implemented with passing automated verification. Metadata completeness is calculated independently; Needs Metadata Review persists until explicit Mark Reviewed. M3-G is PASSED/CLOSED: all three desktop confirmation groups are now user-confirmed. See [M3 acceptance](test_data/m3_acceptance/README.md).

Final M3 acceptance: all seven tasks and eleven M3-G criteria complete with 50 tests, 23 import/recovery checks, five 101-book hub checks and user-confirmed preview/import, review controls and EPUB/MOBI/PDF reading. Earlier open-gate statements are historical. See [acceptance record](test_data/m3_acceptance/README.md). M4 implementation and acceptance status are recorded below; no release was published.

## Approved M4 boundary

[M4 Bulk Metadata Editing](milestone_04_bulk_metadata_editing.md) includes tag add/remove, series set/clear, specified-author replacement, selection retained across filtering/sorting/paging, three series-number modes, mandatory per-book preview, isolated conflict review, M3-style pending recovery and batch revert with before/after values and fresh conflicts. Titles/descriptions/covers remain single-book; previously deferred ISBN/file-level editing is not added by this scope. M4 is COMPLETE and M4-G is PASSED/CLOSED following automated verification and user desktop sign-off on 2026-09-21. M5 remains the shared Hub Activity / Recovery milestone.

Confirmed M4 semantics: exact selected-author replacement preserves co-author order and deduplicates the replacement; Keep Existing Numbers uses active visible values or 1, ignoring orphan indices; sequential start is finite and non-negative with a finite positive increment, preserving previewed numbers and gaps. Each batch has one operation. Ordinary library-specific selection clears on module/application close, while pending batches remain recoverable. Library-specific history persists indefinitely until explicit confirmed deletion, warning that deleting the record permanently removes the ability to revert that batch.

Final M4 acceptance: M4-01–M4-07 complete and M4-G PASSED/CLOSED; the user confirmed all desktop checklist items on 2026-09-21. Passed 64 unit/UI tests, 25 application checks including 101-book edit/revert, and 8 injected-failure checks. Original-library hashes were unchanged. [Evidence and confirmed desktop checks](test_data/m4_acceptance/README.md). Earlier M4 scope-only statements are historical.

## Approved M5 boundary

[M5 Hub Activity & Recovery](milestone_05_hub_activity_recovery.md) covers a default collapsible Hub activity panel, full persistent history, operation grouping/outcomes, review-based Retry, Dismiss, Discard Pending, confirmed Delete History, a startup recovery summary and emergency preservation of unsaved single-book edits. Scope remains Book-inator, one profile/device. No automatic resumption, backups, synchronization, additional modules or dashboard customization. Emergency copies use Application Data / Recovery / Single Book Edits, with Preserve Elsewhere on failure; tab closure and orderly Hub/application shutdown are included. Scope definition is complete and all three clarification decisions are confirmed. Successful emergency preservation automatically completes an already-requested close with truthful recovery notices; without a close request, the editor remains open. Delete History is unavailable for unresolved recovery until separate Review Recovery and explicit Discard Pending; resolved records may be deleted with confirmation. Successful routine preference saves are excluded from Activity, while actionable settings-save failures are included. M5-01–M5-07 DONE; M5-G PASSED / CLOSED after final evidence review.

Historical M5-02 technical checkpoint: [design](technical_design_m5.md) and [31 passing disposable recovery checks](test_data/m5_validation/README.md) complete. Original-library hashes and ebook contents unchanged. Production Activity/recovery UI, safe book-review-state migration and acceptance remain outstanding. No application code changed.

Current M5-03 checkpoint: production activity/recovery storage, import/save/bulk/revert outcome recording, actionable failure recording and independent book-review-state migration are implemented. [85 unit/UI tests and 14 disposable integration checks](test_data/m5_03_integration/README.md) passed; original-library hashes unchanged. M5-04–M5-07 and M5-G remain open. Automatic emergency preservation and close continuation are not enabled yet.

Current M5-04 checkpoint: Hub Activity panel, full history/details and one startup recovery summary are implemented and verified by [93 unit/UI tests](test_data/m5_04_activity/README.md). Summary dismissal retains pending work; Review Recovery currently opens unresolved history. Shared action routing is M5-05; automatic emergency preservation/close handling is M5-06. M5-G remains OPEN for remaining implementation and application acceptance.

Current M5-05 checkpoint: shared recovery actions are implemented and [verified](test_data/m5_05_actions/README.md) by 119 unit/UI tests and 13 real disposable checks. Review reconstructs drafts/previews, with separate Save/confirmation before catalog writes. Dismiss preserves work; Discard Pending requires current-revision review; Delete History remains separate and guarded, with explicit retry after interrupted cleanup. Recovered partial saves retain only unfinished edits, and verified completion resolves the copy. M5-05 DONE/CLOSED; M5-06 automatic emergency preservation/close handling and M5-07 acceptance remain open. M5-G remains OPEN.

Current M5-06 checkpoint: automatic emergency preservation and close handling are implemented and [verified](test_data/m5_06_emergency/README.md) by 143 unit/UI tests and 14 real disposable checks. Failed Save then failed explicit Retry protects only outstanding valid edits; already-requested closure continues only after verified registration of the current revision and existing reader/task checks. Ordinary editing stays open; failed preservation offers Preserve Elsewhere and retains the draft. M5-06 DONE; M5-07 final application/desktop acceptance remains open. M5-G remains OPEN.

Current M5-07 checkpoint: automated acceptance passed (147 unit/UI tests, 21 fresh-copy application checks, 1,000-operation history coverage and two isolated native KWin Wayland close scenarios). [Desktop acceptance](test_data/m5_acceptance/README.md) is user-confirmed, including successful close and restart recovery without automatic editor opening or cover application. KDE testing fixed a duplicate editor close prompt; real host logout/poweroff was not performed. M5-07 is COMPLETE and M5-G is PASSED / CLOSED.
