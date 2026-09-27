# Media-inator

**M19 — Paper-inator Knowledge Foundation: first implementation candidate in source; M19-G OPEN.** Paper-inator is now an available Hub module for research knowledge (Knowledge Items with reviewed versions, managed copies or referenced files, independent reading/handling/flags, tags, collections and optional projects, Markdown notes stored in the profile library, typed connections, search including document text, saved searches, recoverable Trash with previewed permanent deletion; Home dashboard; one library per Hub profile). Fully offline: documents open in an external reader; the built-in reader (M20) and citations, DOI lookup and backup (M21) follow. Qt/KDE regression and owner acceptance pending; nothing packaged or promoted. [Scope and decisions](milestone_19_paperinator_foundation.md), [technical design](technical_design_m19.md), [Paper-inator documents](paperinator/).

**M18 — Music-inator Foundation: first implementation candidate in source; M18-G OPEN.** Music-inator is now an available Hub module (Album → Edition → Copy with discs and track lists; artists as album fields; browse by Albums/Artists/Genres/Years; per-profile rating and favourite; external player via playlist; manual entry, folder scan with tags first and folder fallback, drag-and-drop; no online metadata). Scan grouping awaits owner confirmation. Qt/KDE regression and owner acceptance pending; nothing packaged or promoted. [Scope and decisions](milestone_18_musicinator_foundation.md), [technical design](technical_design_m18.md).

**M17 — Movie-inator Foundation: first implementation candidate in source; M17-G OPEN.** Movie-inator is now an available Hub module (movies only; Movie → Edition → Copy; manual watched/rating; external player; manual entry, folder scan and drag-and-drop; no online metadata). Qt/KDE regression and owner acceptance pending; nothing packaged or promoted. [Scope and decisions](milestone_17_movieinator_foundation.md), [technical design](technical_design_m17.md).

**M14 — Library Discovery & Metadata Productivity: M14-01–M14-07 complete; development build installed with 255 source and 107 installed tests passing; M14-08 owner KDE acceptance pending; M14-G OPEN.** [Approved scope and tasks](milestone_14_library_discovery_metadata_productivity.md). Discovery first, metadata review second; approximately 10,000-book acceptance target. M13-G is CLOSED and **Media-inator Everyday (M13)** is promoted; M12 is retained as Rollback. [M13 acceptance](test_data/m13_workflows/final_acceptance.md) and [promotion](test_data/m13_workflows/promotion.md). M15 remains provisional. No publication.

**M12 — Everyday Usability and Reliability COMPLETE; M12-G PASSED / CLOSED.** Accepted installed build `0.1.0a1-f59e8af9b043f304`: 223 source tests, 64 installed targeted tests, personal KDE acceptance and final saved-data verification passed. [Final gate review and known usability follow-ups](test_data/m12_usability/gate_review.md). M11 unchanged; no publication. Owner-authorized [everyday promotion is complete](test_data/m12_usability/promotion.md); accepted package and current data retained.

**M11 — Promote M10 for Personal Everyday Use COMPLETE; M11-G PASSED / CLOSED.** Use **Media-inator Everyday (M11)**. Exact accepted M10 build installed separately; backup/restore, owner KDE checks and persisted workspace/import/edit/bulk-revert/recovery results verified. [Final gate review](test_data/m11_promotion/gate_review.md). RC1/M9/M10 retained; no publication. Next: personal use or define M12.

**M10 — Hub Workspace Save and Restore COMPLETE; M10-G PASSED / CLOSED.** Accepted build `0.1.0a1-a3a4679f39f4c255`: 215 regression tests, isolated package verification, installed KDE workspace/monitor acceptance and final import/bulk/recovery checks passed. [Final gate review](test_data/m10_workspaces/gate_review.md). RC1 and M9 remain unchanged; nothing published. M11 promotion scope is now approved.

**M9 — Everyday Installation and Safe Upgrade COMPLETE; M9-G PASSED / CLOSED.** Accepted M8 package installed and validated in the separate Docker/KDE test environment, with verified data preservation, snapshot rollback/return and owner desktop acceptance. [Final review](test_data/m9_promotion/gate_review.md). RC1 and the M8 source remain unchanged; M7 observation remains independent. No NAS/live-library deployment or publication.

**M8 — Book-inator Everyday Usability COMPLETE; M8-G PASSED / CLOSED.** Owner confirms all three installed KDE checks passed for candidate `0.1.0a1-184039712b870efd`. Search/filter persistence, progress display and rename/resume are accepted, backed by 185 regression tests, 16 disposable probes and eight installed checks. [Final gate review](test_data/m8_usability/gate_review.md). RC1 and M7 observation remain unchanged; nothing published.

**M7 planned testing COMPLETE; M7-G CONDITIONALLY ACCEPTED.** The owner confirms all planned tests passed and authorizes subsequent work to proceed immediately for business reasons. The seven-day normal-use observation remains an outstanding, non-blocking condition; it has not been completed or waived. RC1 remains frozen. Future milestone gates use explicit tests and pass/fail criteria, with no mandatory elapsed-time requirement. Nothing was published. [Acceptance decision](test_data/m7_daily_use/conditional_acceptance.md).

Current status: **M6 COMPLETE; M6-G PASSED / CLOSED (2026-09-22).** All M6-01–M6-07 tasks are complete. [M6-G closure review](test_data/m6_07_acceptance/gate_review.md). Version remains 0.1.0a1; nothing published. Earlier checkpoint notes are historical.

Completed milestone: **M6 — First Release Readiness**, approved for personal use on Ubuntu 26.04.1 with KDE: per-user installation only, protected operations blocked for unverified Calibre versions without an override, and always-redacted diagnostics with no sensitive-detail opt-in. [Scope, tasks and M6-G](milestone_06_release_readiness.md). M6-01 [technical design](technical_design_m6.md) is complete; M6-02 [package build and isolated-user verification](test_data/m6_package/README.md) is complete; M6-03 [compatibility guards and first-run guidance](test_data/m6_03_compatibility/README.md) is complete; M6-04 [help, instructions and error polish](test_data/m6_04_help/README.md) is complete; M6-05 [always-redacted diagnostic export](test_data/m6_05_diagnostics/README.md) is complete; M6-06 [installation, upgrade and retention verification](test_data/m6_06_installation/README.md) is complete; M6-07 is COMPLETE: [installed application/KWin checks and personal desktop acceptance passed](test_data/m6_07_acceptance/README.md). M6-G is PASSED / CLOSED following final evidence review. No release published; publishing requires separate instruction.

Current M5 status: **M5 COMPLETE; M5-G PASSED / CLOSED** following final evidence review and user desktop acceptance. [Gate review](test_data/m5_acceptance/gate_review.md). All M5-01–M5-07 tasks are complete. Earlier dated/stage checkpoints are historical; no release is implied.

Desktop hub and Book-inator for Ubuntu/KDE, Python and PyQt6. Development version **0.1.0-alpha.1** (`0.1.0a1`); no release published. M1 and G2 are complete for the agreed Calibre 9.2.1 workflow. M2, M3 and M4 are complete, including M3-G, M4-G and final user desktop acceptance.

## Run and browse

```sh
python3 -m mediainator
```

Choose your Calibre library folder with **Choose library…**. Browse Grid/List, search title/author text, select a book and use its format buttons. Library location, view, selection, module state and geometry are remembered. Preferences save immediately.

Browsing and editor reads query private temporary copies. Readers open files in the selected library. Close Calibre and other readers before refreshing, reading metadata or saving. Only one hub-launched reader is allowed. External applications are not adopted or closed.

## Edit metadata

Select a book, then **Edit metadata…**. M2 edits one book at a time: title, authors, tags, cover, series, series number and description. Draft changes show “Modified” and do not write to Calibre until **Save**. Successful writes are read back; title/author changes may make Calibre rename its folders and files. Catalog paths refresh afterwards. A renamed book can disappear from a search for its old title; clear or update the search to find it.

- Authors: Add/Remove/Up/Down preserve order. Commas in author names are allowed.
- Tags: Add/Remove; order does not matter. Commas are rejected because Calibre treats them as separators.
- Series: clearing hides the number. Any internally retained Calibre index is ignored, not a save error. A new series starts at 1 unless you edit it; zero and positive decimals are allowed.
- Description: paragraphs, bold, italic, bullet and numbered lists. Untouched HTML stays exactly as stored. No tables, images or HTML-source editor controls.
- Cover: choose a local image and preview it, or Remove cover. Save commits the change. Failed cover writes automatically attempt restoration from backup while retaining the proposed replacement for retry.

**Save / Discard / Cancel** review appears before leaving a modified record or requesting an explicit refresh. Cancel stops that action. Discard abandons only unsaved work; successful partial writes remain committed. If access is unavailable, fresh values reload when access returns. **Retry Failed Changes** rechecks current Calibre values for conflicts; **Keep Editing** leaves the draft available.

Conflicts show your value and Calibre's value per field, with Keep My Value / Use Calibre Value and global shortcuts. Cancel returns to the draft without writing. Failures distinguish saved fields, failed fields and unverified results. Cover recovery failures report the retained backup path.

Focus regain and a 30-second timer refresh a clean catalog/editor. Dirty edits defer refresh; detected external changes produce a pending-refresh message. Access contention keeps the catalog visible and retries refresh automatically. Metadata is never automatically committed by a timer.

## Import ebooks

Choose **Import ebooks…**, select files/a recursive folder, or drop local EPUB/MOBI/PDF files onto the import window. Every batch requires a preview and **Confirm and import copies**. Originals are never moved, renamed or deleted. Invalid/unsupported files and exact-content duplicates are reported; similar titles require an explicit action.

Choose **Create new book**, **Attach to existing book** or **Skip**. Attachments require an explicit destination and never overwrite an occupied format. If input files or relevant library state change after preview, use Retry to review the updated plan before confirming again.

Missing title/author use filename/Unknown fallbacks with warnings. **Show Needs Metadata Review only** finds imported books needing attention. The editor shows system-calculated **Metadata Completeness** separately from **Review Status**. Saving corrections does not clear review status; use **Mark Reviewed** explicitly after saving/discarding any draft.

**Stop after current item** verifies the active item before pausing. On restart, unfinished work is presented without automatic resumption. **Review / Retry / Discard Pending** preserve completed imports and all source files. Retry reconciles uncertain/partial imports, builds a fresh preview and still requires confirmation. Import journals and review markers persist under `imports` beside hub settings; corrupt/unsupported records are preserved and reported.

M3-G passed 50 tests, 23 real import/recovery checks, five hub/catalog checks and all user desktop confirmations. See [M3 acceptance](test_data/m3_acceptance/README.md) and [technical design](technical_design_m3.md).

## Closing and recovery

Hub/module close reviews owned readers: **Close reader / Leave reader open / Cancel**. When unsaved metadata or a catalog refresh also needs review, one combined dialog includes those choices. Saving requires the reader to close first. Cancel stops the close. Metadata writes are not forcibly interrupted; wait for verification and retry closing.

Handled viewer close is limited to verified Calibre 9.2.1 process identity; no force-kill. Reader ownership persists across restarts. Catalog loading can be interrupted with confirmation. A reader's own close button closes only that reader.

Cover recovery JSON files are retained in `metadata-recovery` beside hub settings. They identify the library/book and hold original image bytes. Do not delete them while recovering a reported failure. A recovery error does not mean successful text changes were rolled back.

## Development and verification

```sh
python3 -m mediainator --sample
python3 -m mediainator --test-library /path/to/registered/disposable/library
QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s tests -v
```

Test libraries require `.mediainator-disposable.json` with their canonical `root` and purpose `mediainator-disposable-test`. Never mark a live library as disposable. Sample mode has no metadata writes. Dependencies are in `pyproject.toml`.

**41 tests pass**, including M1 regressions. M2 also passed 16 adapter/fault checks and 17 real Qt/application checks on fresh 101-book copies. Both runs confirmed unchanged original-library hashes. See [M2 acceptance](test_data/m2_acceptance/README.md), [technical design](technical_design_m2.md), [M1 evidence](test_data/m1_acceptance/README.md) and [living plan](implementation_plan_hub_bookinator.md).

## Limits

Metadata writes are version-bound to Calibre 9.2.1 and use Calibre's lock. Revalidate after upgrading Calibre. This does not guarantee safety with arbitrary tools that bypass that lock or concurrent reader writes. Private snapshots require disk space and reject symlinks/detected source changes. Unknown reading status remains the default where no verified mapping exists.

Settings remain schema 1, normally `~/.config/Media-inator/Media-inator/settings.json`, with atomic writes and a settings-instance lock. Corrupt/newer settings stop startup without overwrite. Failed preference saves block hub exit. No schema migration or release publication occurred.

Exports, direct move/rename/delete-original operations, conversion, shared progress, multiple profiles, named states, docking and other modules remain later work. The accepted initial viewer-keypress issue remains deferred. PDF evidence covers converted text PDFs, not every scanned document.

## Bulk metadata editing (M4 development)

Use the checkboxes beside books, **Select all search results**, or **Clear selection**. The count includes selected books hidden by filtering. Selection survives sorting and view changes but clears when Book-inator closes. Open **Bulk edit / history…** to choose one operation: add/remove tags, set/clear series, or replace an exact author while preserving co-authors.

Set Series supports existing numbers (default 1 when absent), one fixed number, or a sequence with a non-negative start and positive increment. Drag or move books into order before **Build preview**. Uncheck books to exclude them; their numbers are not reassigned to other books. Review current/proposed values, then **Confirm changes**. Changing operation settings requires a fresh preview.

Conflicts are listed separately; unaffected books continue. Select a conflicting row and **Resolve selected conflict**, review the resulting preview and confirm. Close Calibre and readers before accessing the library. **Stop after current book** retains completed results and pending work. After restart, open history and choose **Review / Retry Pending** or **Discard Pending**; no batch resumes automatically.

Choose a history record and **Revert Batch** for a new preview restoring only its changed fields. Later edits trigger conflict review. History survives restart indefinitely until you delete it with confirmation; deletion removes the ability to revert that record. Review/discard pending work before deleting its recovery history.

M4 and M4-G are complete following 64 unit/UI tests, 25 application checks, 8 fault checks and user desktop sign-off: [specification](milestone_04_bulk_metadata_editing.md), [technical design](technical_design_m4.md), [test evidence](test_data/m4_acceptance/README.md).

## M5 implementation progress

M5-03 adds persistent activity/recovery backend storage and records imports, metadata saves/review, bulk edits/reverts and actionable settings/refresh/reader-launch failures. Successful routine preference saves are excluded. Book metadata-review status now survives import-history deletion. Startup no longer automatically opens the import recovery dialog; open Import ebooks or Bulk edit / history manually for existing pending work.

M5-04 adds a default collapsible Activity panel on the Hub and View Full History, including all recorded attempts, dismissed entries and an unresolved-work filter. Select a result and choose View selected details (or double-click/press Enter) to inspect counts, affected items, errors and next steps. The summary above the module tabs offers Open Activity, Review Recovery and Dismiss. Review Recovery currently opens unresolved history; Dismiss hides only the banner for this session, without discarding pending work. Local journals are discovered even when Book-inator is closed. Nothing resumes automatically. M5-05 shared recovery controls and M5-06 automatic emergency preservation/close handling are implemented. Failed saves retain edits; a failed explicit Retry preserves them as described below. [M5-03 verification](test_data/m5_03_integration/README.md): 85 unit/UI tests and 14 disposable checks passed; original-library hashes unchanged. M5-G is PASSED / CLOSED.

[M5-04 verification](test_data/m5_04_activity/README.md): 93 unit/UI tests passed. M5-G remains open pending remaining features and application acceptance.

### Shared recovery actions (M5-05)

Open **Hub → Activity → View selected details** (also available through Full History):

- **Review / Retry** opens the selected import/bulk review, or a preserved single-book draft with conflict review. Confirm the refreshed preview or choose Save to commit changes. Nothing resumes automatically. Refresh/reader/settings retries ask for explicit confirmation.
- **Dismiss** hides an operation from the action list without deleting its history or recovery data. Find it through Full History with Show dismissed.
- **Discard Pending** requires review of the current recovery revision, then a separate warning that pending work cannot be resumed. Committed results remain saved. Close a recovered editor before discarding its preserved copy; discarding local editor changes alone retains that copy.
- **Delete History** is unavailable until pending work is resolved or separately discarded. Confirmation warns that details/revert capability will be lost. Interrupted cleanup remains visible; choose Delete History again to explicitly retry it. Changed/corrupt files are retained for investigation. Metadata-review flags and separate revert batches are preserved.

[Verification](test_data/m5_05_actions/README.md): 119 unit/UI tests and 13 real disposable checks passed. M5-05 is complete. Automatic emergency preservation and close continuation are implemented in M5-06; M5-G is PASSED / CLOSED following full application acceptance.

### Emergency preservation and closing (M5-06)

After a failed **Save**, use **Retry**. If that save also fails, Book-inator preserves the remaining edits in Application Data / Recovery / Single Book Edits. Fields already saved remain committed. The message explicitly distinguishes an emergency copy from a successful library save.

- During ordinary editing, the editor stays open.
- If you already requested an editor/tab/Hub close and chose Save, successful preservation completes that request after the other close safeguards pass.
- If preservation fails, the editor stays open and offers **Preserve Elsewhere…**. The alternate copy must also be registered successfully. Cancel or Keep Editing abandons the close request.
- New edits invalidate protection of the older revision. Invalid input and cancelled conflict review do not trigger emergency preservation.
- At next startup, use Activity → Review Recovery to inspect the preserved draft. Nothing is applied automatically.

Cooperative desktop shutdown uses the same review when the desktop permits interaction; it is cancelled for outstanding work when interaction is unavailable. Forced termination and power loss before preservation are not protected by draft autosave.

[M5-06 verification](test_data/m5_06_emergency/README.md): 143 unit/UI tests and 14 real disposable checks passed. M5-06 is complete; M5-07 full application/desktop acceptance is next. **M5-G is PASSED / CLOSED.**

### M5 acceptance status

M5-07 automated checks pass: 147 unit/UI tests, 21 disposable application checks and two isolated real KWin Wayland shutdown-path scenarios. A duplicate editor Save prompt during KDE window closure was fixed. [Desktop acceptance](test_data/m5_acceptance/README.md) is user-confirmed, including successful close and recovery discovery after restart without automatic writes. **M5-07 is complete; M5-G is PASSED / CLOSED**.

On native KDE Wayland, shutdown uses window-close requests as well as any available session-management support. Cancel keeps the application and draft open; if KDE presents its own logout notification, choose **Cancel Logout** to stop logout. **Log Out Anyway** can override cooperative protection. The isolated tests did not log out or power off the user's desktop.


## M18/M19 verification follow-up (2026-09-27)

The Music/Paper candidate has passed real Qt/Wayland and isolated installed-package verification, including preservation fixes. See [implementation and test evidence](test_data/m18_m19_review/completion.md). Separate M18/M19 acceptance launchers are available. Gates remain open for owner desktop acceptance; no Everyday promotion has occurred.

## M19 daily-use Docker release

The M19 foundation candidate has passed the final 388-test source suite and 93
installed-module tests in its native Wayland Docker image. See
[release evidence](test_data/m19_daily_release/README.md) and
[Docker installation](packaging/docker/README.md). M16 remains a separate fallback;
M18/M19 acceptance data is not part of the daily profile.
