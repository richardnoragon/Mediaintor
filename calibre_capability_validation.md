# Calibre Capability Validation — M1 and M2

Status: M1 is complete for its agreed access policy and user-confirmed acceptance. M2 initial disposable metadata-write capability validation is complete; M2 application implementation/acceptance remain open. Historical pass notes below retain their original scope.

## Earlier M1 component-validation checkpoint

- 101 library records, 101 valid cover files, 121 format paths, imported metadata/hashes, CLI title/author/no-result searches, and 15 multi-format groups checked successfully on a fresh copy.
- Representative EPUB/MOBI/converted-PDF readability and page navigation confirmed by the user. Detached launch and version-specific handled close passed.
- Sequential bookmarks persisted locally and in the copied library before/after close for all three formats with no errors. Later staggered bookmarks with three viewers open also passed; initial parallel-launch EPUB/PDF lock errors remain unresolved. All test viewers are closed.
- G1 policy is accepted: private snapshot for listing, original files for reading, and exclusive refresh/launch. Integration verification remains open. G2 component feasibility passed; actual hub lifecycle acceptance awaits implementation. G3 foundation checks passed (19 automated tests and one-book adapter smoke checks); full application acceptance remains separate. G4 sample/CLI checks passed; full application format/scale acceptance remains pending.
- The initial-keypress issue is deferred and non-blocking (TODO-VIEWER-01). Application foundation coding is now authorized and has started; the earlier test-data/validation scripts remain separate evidence. Full 101-book application acceptance must wait for G1 completion.

This checkpoint and the pass notes below are historical. See the final M1 sign-off and M2 results for subsequent progress.

## Environment and scope

- Installed tools: `/usr/bin/calibre`, `/usr/bin/calibredb`, `/usr/bin/ebook-viewer`.
- Installed CLI and viewer version: **Calibre 9.2.1**, confirmed by version output.
- Actual `/etc/os-release`: **Ubuntu 26.04.1 LTS**. The user confirmed **KDE** as the desktop environment and this machine as the intended environment, correcting the earlier Kubuntu 24.04 assumption. Follow-up local inspection confirmed XDG_CURRENT_DESKTOP=KDE, XDG_SESSION_TYPE=wayland, and KDE_SESSION_VERSION=6. The exact Plasma package version has not been checked.
- Configured library: `/home/sproket01/Calibre Library`.
- The user confirmed this is the correct test-library path. At the initial validation it contained **one Quick Start Guide record**. It now contains 101 records following the separately authorized test-data import documented below.
- Temporary copy used for library commands: `/tmp/mediainator-calibre-validation-j4r21p1q/library`.
- CLI configuration and viewer configuration were isolated under the same temporary root. All book-opening and library-query experiments targeted that copy, not the original library.

Temporary paths are validation artifacts, not application defaults or permanent test fixtures.

## Pass 1 results (historical)

| Capability | Evidence | Result / limitation |
| --- | --- | --- |
| Library listing | `calibredb list --with-library <copy> --for-machine --fields title,authors,tags,formats,cover,uuid` | Passed: valid JSON with one record |
| Record identity | Returned `id` and `uuid` | Both present; stability across future edits/migrations not tested |
| Display metadata | Returned title, authors, tags | Title and author present; tags an empty list. Authors returned as a string in this installed version |
| Cover access | Returned cover path exists | Passed for the guide's cover; missing-cover cases not yet tested |
| Format-file access | Returned `formats` array with an existing EPUB path | Passed for EPUB; no MOBI/PDF sample available |
| Title search | `--search 'title:"Quick Start"'` | Passed: returned the expected record |
| Author search | `--search 'authors:"Schember"'` | Passed: returned the expected record |
| Reading status | Installed list help has no built-in reading-status field; `custom_columns --details` returned none | No mapped status available in this sample. M1 must display Unknown; this does not imply all libraries lack reading information |
| Viewer CLI | `ebook-viewer --version` and `--help` succeeded outside sandbox | File argument, `--new-instance`, `--open-at`, and `--continue` supported by installed help |
| EPUB viewer launch | Launched guide copy with `--new-instance` and temporary viewer configuration | Passed: process started without captured errors, temporary viewer artifacts appeared, and the user confirmed the guide was readable |
| Position restoration | Installed help documents `--open-at` | Interface documented, not behaviour-tested; not required for M1 |
| MOBI and PDF rendering | No samples in configured library | Not tested; do not mark these formats validated |
| Multi-format grouping / 100-book browsing | Only one single-format record available | Not tested |
| Attached viewer control / graceful session close | Launch used a separate instance | Not tested; CLI help alone does not establish a session-close API |
| Automatic refresh / write-back / copy-move-rename | Outside this M1 read/launch pass | Not tested |

## Important observations

The sandbox blocked Calibre's local lock socket and Qt desktop access. The same CLI/help and viewer commands ran after execution outside the sandbox was approved. These failures are execution-environment restrictions, not evidence of a broken Calibre installation. Do not infer a need to reinstall Qt from the sandbox's initial display-plugin error.

The copied `metadata.db` no longer matched the source byte-for-byte after validation, while the EPUB and cover still matched at the comparison point. This pass did not isolate which operation changed the copy. A command being logically a listing does not establish that opening a library is physically free of database writes. Preserve the temporary-copy approach until database-opening behaviour has been investigated. No Calibre library command targeted the source database.

Viewer settings and annotation artifacts were created under temporary viewer configuration. The viewer is not guaranteed to be a side-effect-free reader. Its precise persistence and isolation behaviours need further testing before managing live personal reading sessions.

## M1 conclusion

The installed CLI provides a workable candidate for JSON metadata listing, format-path lookup, and title/author search. One book card per existing Calibre record with format buttons is consistent with the returned record structure, but multi-format data still needs testing.

Opening the selected guide EPUB passed both the process-start check and user-confirmed readable rendering. M1-01 is **ACTIVE**, not DONE. This pass does not select the final integration architecture or validate all required formats, viewer lifecycle controls, or the full test collection. CLI/EPUB checks ran on the now-confirmed target OS; KDE-specific UI behaviour remains untested.

## Original next-pass plan (historical; completed items superseded below)

1. Environment and library-path clarification is complete. Continue with available data; repeat format/scale checks after the user adds suitable samples. Missing MOBI/PDF/multi-format samples block those checks, not unrelated design work.
2. EPUB visual confirmation is complete. The test viewer may be closed manually; do not force-close unrelated applications.
3. Prepare a temporary copy of representative EPUB/MOBI/PDF and multi-format records, then repeat metadata/path/search checks and viewer opening for each format.
4. Record missing-cover/status, missing-file, and unavailable-library outcomes, plus timings and counts on approximately 100 books.
5. Investigate library-open side effects, concurrent Calibre use, and attached-versus-launched viewer/session controls before choosing the production integration method.

## Official sources

The retrieved online manual identifies itself as Calibre **9.15.0**, newer than the installed **9.2.1**. Local command output is the evidence for installed options; online documentation is supporting reference, not proof that a feature was tested locally.

- [calibredb documentation](https://manual.calibre-ebook.com/generated/en/calibredb.html): JSON listing, selectable fields, library paths, search, and custom columns.
- [ebook-viewer command documentation](https://manual.calibre-ebook.com/generated/en/ebook-viewer.html): file launch, instance and position options.
- [Viewer manual](https://manual.calibre-ebook.com/viewer.html): reading-position behaviour and viewer use; not all of these capabilities were exercised here.

Planning links: [M1 specification](milestone_01_browse_and_read.md), [implementation plan](implementation_plan_hub_bookinator.md).

## Technical-design follow-up observations

- Python 3.14.4 and PyQt6/Qt 6.10.2 are locally available; a QtCore import succeeded. No application GUI smoke test was performed.
- Installed `calibre/db/cli/main.py` opens local `LibraryDatabase` and uses a single-instance lock; its error path rejects another database-owning Calibre program. Concurrent live access is not yet validated.
- Installed `calibre/db/backend.py` defaults to non-read-only opening and contains schema/trigger maintenance. This supports the possibility of library-open writes without isolating the exact prior change.
- Installed list code resolves format/cover paths against files; a metadata-only snapshot cannot be assumed to preserve full format output.
- See [technical design](technical_design_m1.md) for read-strategy and viewer-lifetime gates. These inspections do not complete M1-01.

## Pass 2 — Isolated read side effects and viewer lifetime (2026-09-20)

Temporary evidence directory: `/tmp/mediainator-gates-1bsw3bd3`. Disposable diagnostic scripts were used outside the project; no application code was written. The first sandbox attempt could not bind Calibre's lock socket; the approved outside-sandbox run below is the substantive result.

### Library reading

A full private library copy was prepared, with `metadata.db` captured using SQLite backup from a read-only source connection. Before and after each command, every copied file's SHA-256 was compared, alongside the database SQL dump, schema version, and integrity check.

| Operation | Result | Persistent changes |
| --- | --- | --- |
| JSON listing | Passed; one record | None |
| Repeated JSON listing | Passed; one record | None |
| Title search | Passed; one record | None |
| Author search | Passed; one record | None |
| Occupied Calibre database lock | Expected rejection with a clear busy message | Database unchanged |

All successful read checks retained schema version 116 and database integrity `ok`. Source-library file hashes remained unchanged across the four read tests. The lock test temporarily held the same Linux abstract socket used by the installed Calibre lock implementation; it did **not** exercise actual simultaneous GUI editing or a Content server. Its scope is per user, so using a private snapshot does not bypass this lock.

These results establish absence of persistent file changes for this library/version/sample, not absence of transient writes or a guarantee for older/different schemas. Installed backend maintenance remains a reason to validate new versions and representative libraries.

After the viewer opened the copied EPUB, a fresh SQL comparison found an added row in `annotations_dirtied`. The earlier pass's copy contains the same additional row. This isolates a viewer-associated database change in the new pass and provides an explanation consistent with the earlier observation. Temporary viewer configuration does **not** isolate a book from its containing Calibre library database. M1 may defer reading-progress integration while the external reader independently maintains Calibre reading data.

Evidence: `report.json`, command stdout/stderr and SQL diffs, `lock-report.json`, `viewer-open.sql.diff`, and `previous-pass-vs-source.sql.diff` in the temporary directory. Temporary artifacts may disappear; this document retains the findings.

### Viewer lifecycle

A temporary PyQt6 QCoreApplication launched the copied guide with `QProcess.startDetached`, `ebook-viewer --new-instance`, and isolated viewer configuration, then exited immediately. Launch succeeded; PID 48350 remained running afterwards with a different parent. This validates detached process survival, not a finished hub's close dialog or settings handling. The user confirmed that the guide became readable after a keypress. Record the keypress requirement as a startup/focus/rendering observation whose cause remains undiagnosed; do not claim unattended readiness.

Installed Calibre 9.2.1 source routes SIGTERM/SIGINT through the Qt event loop to the viewer's normal `request_close`/`closeEvent` path, including state and annotation saving. This is version-specific source evidence, not a general external-application close API. The targeted close check passed: the process command, copied book path, and temporary configuration were verified, and a Linux pidfd was used to avoid signalling a reused PID. SIGTERM led to observed exit in 0.277 seconds, updated viewer-webengine.json, gui.json, and a valid annotation JSON file, with empty captured stderr. The copied database integrity check returned `ok`; source-library file hashes were unchanged across the close test. No unrelated or attached viewer was closed. Evidence: `viewer-close-report.json`. Since this was a detached process, no child exit code was collected. Exact position restoration and all annotation contents were not verified by file updates alone.

G1 remains PARTIAL: read side effects and lock rejection are characterized; the production read strategy and real concurrency remain open. G2 component feasibility PASSED for Calibre 9.2.1 on this machine: detached survival, user-confirmed readability after a keypress, and the targeted handled-close path. Full hub lifecycle acceptance remains unimplemented. The user accepted the keypress/startup observation as a deferred, non-blocking usability issue (TODO-VIEWER-01 in the implementation plan); reproduce it in a later pass. Verify exact position restoration later and revalidate close handling after Calibre upgrades. M1 acceptance and G3/G4 are not completed by these checks.

## Test dataset preparation — 2026-09-20

At the user's request, downloaded and imported 100 distinct free titles from Project Gutenberg's documented rsync mirror. New collection: 100 EPUB files, 10 downloaded MOBIs, and 10 PDFs converted locally by Calibre from EPUB. There are 15 multi-format records, including five with all three formats, across 26 broad genre/category labels. Source metadata, download provenance, hashes, and Calibre record IDs are recorded in the [collection manifest](test_data/free_ebooks_100/README.md).

A pre-import library backup was saved under `test_data/free_ebooks_100/library_before_import/`. Supported `calibredb add` and `add_format --dont-replace` commands were used on the live library with user authorization. No direct database edits or title-based automatic merging were used. Batch tag: `mediainator-test-100`.

Verification passed: 100 new records, 101 total including the preserved guide, all 120 imported format hashes matching staging, original ebook files unchanged, and SQLite integrity `ok`. All staged files had unique hashes; EPUB archives and MOBI/PDF signatures were checked. These checks do not establish visual rendering or page fidelity. The PDFs are converted text editions, not scanned-PDF fixtures.

MOBI/PDF and multi-format samples are now available. Repeat read/search/reader checks on a fresh disposable copy before marking broader capability acceptance complete. This authorized import does not resolve the production application's G1 strategy/concurrency boundary.

## Expanded-library validation — 2026-09-20

Fresh disposable copy: `/tmp/mediainator-expanded-n2b0gj31/library`, with the database captured through SQLite backup from a read-only source connection. The original library was only copied/read. Persistent evidence is in [expanded validation results](test_data/free_ebooks_100/expanded_validation/report.json).

- All 101 records loaded in 0.298 seconds in this single local CLI run (not an application performance benchmark).
- All titles, authors, UUIDs and tag-list structures were present; the 100 imported titles/authors, genre tags, Gutenberg identifiers, exact format sets, and 120 file hashes matched the import manifest.
- All 101 cover paths resolved and their image files passed Pillow verification. This checks file decodability, not visual correspondence to each title.
- All 121 format paths resolved inside the copy: 101 EPUB, 10 MOBI, and 10 PDF. Fifteen records have multiple formats; five have all three. No title-based regrouping was performed.
- Title query for Pride and Prejudice returned one expected record; author query for Austen returned the six expected records; an absent-title query returned zero. Each query took approximately 0.29 seconds. These are Calibre CLI search checks, not tests of the planned application's local substring filter.
- Neither source nor copy file hashes changed during catalog/search checks; copied database integrity was `ok`.

Viewer samples were launched as separate detached instances with temporary per-format configuration: Alice's Adventures in Wonderland (EPUB), The Time Machine (MOBI), and The Raven (converted PDF). All three process launches succeeded. **The user confirmed all three windows are open, readable, and support page changes. Representative EPUB, MOBI, and converted-PDF visual/navigation checks PASSED.** See [launch records](test_data/free_ebooks_100/expanded_validation/viewer_launches.json).

Launching the three viewers together exposed annotation-write contention: EPUB and PDF stderr reported `apsw.BusyError: database is locked`; MOBI stderr was empty at inspection. The copied database still passed integrity checking, and source-library file hashes remained unchanged after launch. This is a real concurrency finding; process launch alone must not be reported as successful progress persistence. Error details are retained in [viewer observations](test_data/free_ebooks_100/expanded_validation/viewer_observations.json).

Remaining work: a defined contention/failure policy and any further synchronized-write checks; missing-file/cover and unavailable-library fixtures; actual application search, rendering, restart and lifecycle acceptance. Converted text PDFs do not cover scanned PDFs. The previously deferred initial-keypress issue remains non-blocking. No application code was written, no M1 acceptance checkbox is completed by these component checks, and G1 production concurrency is still open.

Annotation follow-up: TEST-SIMULTANEOUS bookmarks persisted locally and in the copied library for all three formats, before and after verified handled closes, with no new lock errors. User actions were staggered while three viewers were open; this does not establish simultaneous-write safety or automatic retry. The fresh-copy sequential control subsequently completed for all three formats; see the final comparison. See [annotation investigation](test_data/free_ebooks_100/annotation_validation/README.md).

Sequential annotation control: EPUB bookmark persistence passed in local storage and the copied library before/after handled close, with no logged lock errors. The user reused the TEST-SIMULTANEOUS label in the new isolated session; this is recorded in the evidence. MOBI and PDF subsequently passed; all test viewers are now closed. See the annotation investigation.

Sequential MOBI control: PASSED after the user completed bookmark creation. The bookmark matched local storage and the copied library before and after handled close, with no logged lock errors and unchanged source-library hashes. The earlier check found only a last-read position because bookmark creation had not yet been completed; it is not evidence of a save failure. Evidence: `test_data/free_ebooks_100/annotation_validation/sequential-mobi.json`. The final PDF check subsequently passed; all test viewers are now closed.

Annotation comparison completed: sequential EPUB, MOBI, and PDF bookmarks matched local and copied-library storage before and after handled closure, with empty stderr for each. All test viewers closed and source-library hashes remained unchanged. With three viewers open, later staggered bookmarks also persisted without additional errors, but initial concurrent-launch BusyErrors (EPUB/PDF) remain unresolved. This supports sequential sample feasibility, not simultaneous-write safety or automatic recovery. See the [final comparison](test_data/free_ebooks_100/annotation_validation/README.md#final-comparison). G1 concurrency/failure handling and application acceptance remain open; no application code was written.

Policy follow-up: the user accepted the [M1 access workflow](m1_library_access_decision.md). This changes the selected mitigation, not the recorded test outcomes: simultaneous-write errors remain unresolved, and policy approval does not complete G1 integration verification or full acceptance.

Latest application verification: G1 passed for the accepted snapshot/exclusive-access workflow. Twenty-one automated tests and the subsequent full 101-book application catalog/UI run passed. Final app-launched reader/close desktop confirmation remains pending. Source browsing hashes were unchanged. See [acceptance report](test_data/m1_acceptance/README.md); this supersedes historical G1-pending statements.

Current milestone status: **M1 complete for the accepted scope.** G1 passed before the full 101-book application run; automated checks and final user-confirmed reader/navigation/close outcomes passed. Twenty-three automated tests pass. Known limitations and later release work remain documented in the [acceptance report](test_data/m1_acceptance/README.md). This supersedes historical pending-acceptance notes above.

## M2 metadata-write capability validation

Initial M2-01 validation is complete: seven fields, Calibre-managed path changes, partial saves, pre-save/retry conflict protocol, and source-integrity comparison. Invalid cover input can truncate an existing cover after a title has committed; exit status alone is insufficient. Series-index writes without a series can be ignored. See the [full capability matrix, evidence and required safeguards](test_data/m2_validation/README.md). These are disposable CLI/protocol results, not M2 application acceptance or concurrent-write certification.

M2 follow-up: [Calibre API capability checks](test_data/m2_followup/README.md) passed cover removal/recovery protocol, ordered authors, untouched HTML and numeric validation. Literal null series index and comma-preserving tags are blocked by observed Calibre storage/normalization rules. Product compatibility decisions remain pending; no application acceptance is implied.

Current M2 compatibility decisions supersede the blockers above: The user resolved both compatibility blockers: when no series exists, hide and ignore Calibre's internally retained index; it is not a save failure. Assigning a new series explicitly defaults to 1 unless edited. Individual tag names may not contain commas; validation must prevent saving them and explain that Calibre treats commas as separators. Application implementation and acceptance remain open; these decisions do not mark tests complete.

Current implementation checkpoint: M2 metadata adapter and editor pass 41 tests plus 16 adapter and 17 real-application checks on disposable copies. Final M2 desktop sign-off is complete. G2 is closed for Calibre 9.2.1 based on final M1 user evidence and passing lifecycle regressions. See [M2 acceptance](test_data/m2_acceptance/README.md); earlier implementation-pending notes are historical.

M3 capability checkpoint: M3-02 is complete with 13 disposable import/attachment/recovery protocol checks and unchanged original-library hashes. Production input validation must handle Calibre parser fallbacks, and recovery must reconcile metadata-only partial records and committed-but-unacknowledged operations. See [M3-02 results](test_data/m3_validation/RESULTS.md). M3-G remains open; no production import implementation or UI acceptance is claimed.

Current M3 implementation: safe copy-only imports, mandatory preview, explicit no-overwrite attachments, durable stop/retry/discard recovery and fallback review markers are implemented with passing automated verification. Metadata completeness is calculated independently; Needs Metadata Review persists until explicit Mark Reviewed. M3-G is PASSED/CLOSED: all three desktop confirmation groups are now user-confirmed. See [M3 acceptance](test_data/m3_acceptance/README.md).

Final M3 acceptance: all seven tasks and eleven M3-G criteria complete with 50 tests, 23 import/recovery checks, five 101-book hub checks and user-confirmed preview/import, review controls and EPUB/MOBI/PDF reading. Earlier open-gate statements are historical. See [acceptance record](test_data/m3_acceptance/README.md). M4 bulk-editing scope is next; no release was published.
