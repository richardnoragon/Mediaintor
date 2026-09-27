# M8 isolated baseline and initial capability investigation

Current status: **M8 COMPLETE; M8-G PASSED / CLOSED.** Owner confirms all three installed KDE checks passed. [Closure review](gate_review.md). Earlier pending/open entries below are historical. RC1 unchanged; M7 observation remains independent; nothing published.

## M8-02 — complete

- Separate installation/data root: `../Mediaintor-M8-Development/`.
- KDE launcher: **Media-inator M8 (Development)**; Compose project `mediainator-m8`.
- Copied installed baseline verified: `0.1.0a1-c08faf149723f3c0`. Uses the existing immutable runtime image; no RC1 rebuild or retag.
- All 101 books copied with application home and import sources. Regular-file hashes matched the quiet source; symlinks preserved during copying.
- Runtime writable binds point exclusively to M8 home/library/import sources. No development checkout or RC1 data mounted. Wayland socket and M8 runtime script are read-only binds.
- Isolated init passed; Hub launched without startup log errors. Personal desktop focus/resume checks pending.
- RC1 active-data and frozen-bundle regular-file inventories matched before copying and after M8 startup. [Setup evidence](setup.json).

This is a separate installed baseline for investigation, not a claim that new M8 application features have been implemented. Later builds must be explicitly installed into M8 only; its baseline runtime verifier will need a matching M8 build identity then. Do not change RC1 to facilitate upgrades.

## Viewer focus investigation — M8-03 in progress

Current application launch uses `ebook-viewer --new-instance`, detached with standard input disabled. Calibre has window activation calls, but source inspection alone does not establish KDE focus behavior or the cause of the initial-keypress report. No synthetic keypress or application patch has been added.

Owner requested checks in the launched M8 Hub: open The Time Machine EPUB, report readability before input and whether the first Right Arrow navigates without an intervening click; advance, close and reopen to check saved position. Await results before diagnosing focus versus rendering or navigation behavior.

## Progress capability investigation — M8-05 in progress

Read-only inspection of copied metadata.db found 101 books and empty `annotations` and `last_read_positions` tables. Table existence alone does not prove desktop viewer percentage integration.

Installed Calibre source inspected (host copies hash-match the container copies; hashes recorded in setup.json):

- `gui2/viewer/ui.py`: `cfi_changed` creates `last-read` annotations containing position, position type and timestamp. `initial_cfi_for_current_book` uses an EPUB CFI when remember-last-read is enabled. This supports a resume mechanism, but is not yet an end-to-end format acceptance result.
- `gui2/viewer/integration.py`: library annotations are loaded and saved by book ID and format, normally for local user `viewer`. This is a candidate per-format position source.
- `gui2/viewer/annotations.py`: annotations are also persisted in viewer configuration; saving to the library and sometimes into ebook files are separate operations.
- `last_read_positions` has user/device/book/format identity and `pos_frac`; no observed records yet establish that this desktop workflow populates it.

Do not manufacture percentages from CFIs or treat absent records as unread. Actual EPUB, MOBI and PDF close/reopen persistence, database side effects and percentage availability remain to be verified after controlled reading. Reading-status mapping and the book-level aggregation rule remain open design decisions; no completion threshold or maximum-progress rule is approved.

M8-G remains open. M7-G remains conditionally accepted; RC1 observation remains independent.

## EPUB desktop confirmation

Owner confirms immediate readability, navigation on the first Right Arrow without an intervening click, and resume at the saved location after close/reopen. [Recorded acceptance](epub_desktop_acceptance.json). The original keypress issue did not reproduce in this scenario; no fix has been implemented and broader focus reliability is not yet established.

Read-only follow-up still found no library last-read annotations or last_read_positions. Two viewer annotation files exist in the isolated configuration; their presence alone does not establish which belongs to this test. Successful resume therefore does not yet verify a database-backed percentage/status source. Next: verify MOBI/PDF resume and per-format independence, then identify the authoritative saved-position source.

## Three-format desktop confirmation

Owner confirmed MOBI/PDF immediate readability and first-arrow navigation, close/reopen resume, and preservation of the prior EPUB position after testing other formats. [Evidence](multiformat_desktop_acceptance.json). These specific focus and per-format resume scenarios pass; this is not M8-G closure.

Read-only follow-up found three viewer annotation files, each mapped to The Time Machine's EPUB, MOBI or PDF using Calibre's SHA-256 path-key rule. The records contain a CFI position and timestamp, but no percentage/status; both library progress tables remain empty. Viewer records are path-keyed, so title/author path changes require consideration. Percentage remains Unknown unless a reliable source is established. Reading-status mapping and book-level aggregation still need product decisions before implementation. RC1 was not accessed or changed by these checks.

## Approved display decisions (supersede earlier open product questions)

Per format: show Saved position available when a valid resume point exists, Progress: Unknown when percentage is unavailable, and Status: Unknown when status is unavailable. Book cards summarize the most recently read format with a clear format label; details retain all independent format positions. Do not infer Currently reading from a position record or combine incompatible positions. These are approved requirements, not implemented UI. Timestamp reliability, relocation and invalid-record handling remain technical verification work. See the [updated M8 acceptance examples](../../milestone_08_everyday_usability.md).

## Timestamp, rename and corrupt-record probes

[Edge verification review](progress_edge_review.md): 14 disposable probes passed. Found offset-sensitive timestamp ordering, path-key changes on real Calibre rename, and omission of last-read records from the library annotation API. Missing/corrupt/schema-invalid fixtures were checked without modifying live reading records. Production adapter and end-to-end rename continuity remain outstanding.

## Progress reader implementation and real rename handoff

Implemented `mediainator/progress.py`: bounded read-only annotation loading, timezone-aware recency, ties, invalid-record reporting and identity/content-checked rename handoff using explicit viewer `--open-at`. Percentage and status remain unknown. This is an adapter API, not yet connected to catalog display or metadata-save orchestration; no installed candidate was upgraded.

Two focused tests plus eight existing workflow tests passed. Updated disposable Calibre probe passed 15 checks, including the production handoff after an actual title/path change. A separate renamed EPUB fixture was launched with the captured real EPUB position and isolated viewer configuration. Desktop location confirmation remains pending in `rename_desktop_pending.json`. This does not yet establish automatic rename continuity through the Hub. RC1 and active M8 reading data were not mutated.

## Integrated progress display and launch flow

The development application now reads progress after catalog loading, displays per-format records in details and the most-recent-format summary in grid/list views, and requests refresh when its reader exits (existing dirty/access guards still apply). Application-owned `reading-progress.json` records library identity, book UUID, format, path, content hash and position. On rename, fresh identity and identical content allow `--open-at` handoff; valid target-side records take precedence. No viewer sidecars are rewritten.

Validation: 180-test regression run passed, followed by one additional persistent-store test (3 progress tests now pass). Disposable Calibre checks now total 16, including persistent-store reconstruction after real title/path change. These establish automated adapter continuity, not yet human acceptance of the integrated editor flow.

A fresh temporary copied library and remapped copies of annotation records were launched as **M8 INTEGRATED PROGRESS — DISPOSABLE LIBRARY**. It uses workspace development code and separate settings/data/configuration. Startup log was empty and its own reading-progress history was created. [Pending desktop fixture](integrated_desktop_pending.json). Await owner confirmation of card/details and editor rename → refresh → EPUB resume/navigation. RC1 and the active M8 installation/data were not upgraded or modified. M8-G remains open.

## Open desktop refresh report

Owner could not continue after saving. [Investigation](refresh_blocker.json) confirms the disposable title save succeeded. A fresh-copy real Calibre save/refresh reproduction completed: 101 books loaded, saved title verified, catalog reloaded, clean editor, Reload enabled and one matching book. The reported desktop blockage is not yet reproduced; exact status message/control state requested. Do not mark integrated desktop acceptance passed. RC1 and active M8 data unchanged by this investigation.


Owner confirmation: “yes every thing performed correctly. hub and reader are now closed, by user”. [Integrated acceptance](integrated_desktop_pending.json), [resolved refresh report](refresh_blocker.json). No further rename repetition is required for this accepted scenario. This documentation update does not modify RC1 or active M8 data.

## Search/filter desktop confirmation

Owner confirms combined search/filter behavior in both views and Clear All with preserved bulk selection passed, then closed Hub and reader. Saved state contains active tags Essays and External edit, empty text and expanded filters. Restart confirmation is pending; do not claim nonempty-text restoration from this particular desktop run. [Record](search_desktop_acceptance.json).

## Acceptance fixture reconciliation

The integrated Hub progress-display and editor rename/resume scenario already passed with explicit owner confirmation; it need not be relabelled pending. The earlier standalone rename fixture is superseded by that integrated result, not retroactively marked independently passed. Both fixtures now state this distinction.

Execution qualification: the integrated test used workspace development code with disposable data and a separate temporary launcher. It did not upgrade the installed M8 package. Do not describe it as installed-package acceptance. Before any installed-candidate acceptance claim, build and install the matching candidate into a further isolated acceptance location, preserving RC1 and active M8 data.

Current pending desktop result: restored Essays/External edit tag filters, expanded filter panel and matching results after reopening. The prior user message is a proposed checklist, not a new PASS confirmation. M8-G remains open. There is no `test_data/m8_daily_use/` tracking directory; this README is the authoritative M8 evidence index.

## Installed candidate verification

Built **0.1.0a1-184039712b870efd**; archive retained in `dist/m8/`, SHA-256 `a649ebab6fe334929cc2e42e15ab998710cf5bdcc776d24242de4bccd3d96b14`. [Installed verification](installed_verification.json), [runner](verify_installed.py), [output](installed_verification.log).

Eight automated checks passed in a separate installed home inside a private namespace with no checkout, RC1 or active M8 mounts. Verified installer, installed launcher smoke, installed-only imports, real copied 101-book catalog parsing with series, restored Essays/External edit filters (2 matching books, expanded panel), nonempty-search/filter restart, persisted Clear All and desktop-entry syntax. The UI checks manually supplied the real parsed catalog to an installed Hub; they do not claim interactive live loading or owner KDE acceptance. Host dependencies were reused. Installation fixture is temporary, not the active M8 environment.

Reopened filters are now confirmed by automated UI evidence; no additional personal confirmation is invented. Installed-package **automated verification** passed; final personal installed-candidate acceptance and M8-G sign-off remain outstanding. RC1 and active M8 files were not written.

## Personal installed KDE acceptance prepared

KDE entry **Media-inator M8 Installed Acceptance** launches candidate `0.1.0a1-184039712b870efd` from a separate durable installed home in `../Mediaintor-M8-Installed-Acceptance/`. Installed manifest hashes and desktop-entry syntax verified. Three copied annotation records were re-keyed only within that acceptance fixture. [Fixture record](installed_desktop_acceptance.json), [gate review](gate_review.md). Owner checks for menu launch, filters, rename/resume and persisted restart requested; no PASS inferred yet. M8-G remains open until those results arrive.
