# Milestone 01 — Browse and Open E-books

Status: **COMPLETE for the agreed M1 scope.** All twelve acceptance criteria passed. This is a development milestone, not the complete first release.

## Goal

Launch Media-inator Hub, browse one existing Calibre library, find a book, and open a selected format in Calibre's e-book viewer on Ubuntu 26.04.1 LTS with KDE.

## Agreed scope

- One personal profile and one device; no profile switching in this milestone.
- Choose one Calibre library folder on first use and remember it. Browse its temporary private snapshot; launch selected files from their original locations.
- Require Calibre and other readers to be closed while refreshing or launching; allow one hub-launched reader at a time for M1.
- Launch Book-inator through the hub, using the default tabbed view.
- Read the existing library and display its available metadata and covers.
- One book card with separate format buttons; EPUB, MOBI, and PDF remain separate files.
- Both cover-grid and table/list views, with a switch between them.
- Display title, author, available formats, tags, and reading status without requiring a separate detail screen.
- Find a book and open the selected format in Calibre's e-book viewer.
- Save settings immediately and restore the last session automatically.
- Reading-progress tracking and updates are deferred. Reading-status display does not imply progress integration is complete.

## First-party workflow

1. Start the hub using the personal profile.
2. If no library is remembered, select the existing Calibre library folder.
3. Load the library and show Book-inator in a hub tab.
4. Browse a cover grid or switch to a list showing the same books and metadata.
5. Find a book, select its EPUB, MOBI, or PDF button, and open that file in the external viewer.
6. Close and reopen the hub; recover the remembered library, view preference, and last open module selection.

Catalog access in M1 is read-only: Book-inator does not edit metadata, import new files, or copy/move/rename library files. The external viewer may have its own persistence behaviour; this must be observed during capability validation rather than described as a guarantee that the viewer writes nothing.

## Confirmed search and status defaults

- Use title/author text search for the initial find-book workflow. Richer filters and saved searches remain later work.
- Display existing reading status when available; otherwise show **Unknown**. Do not infer Unread from missing data or write status back.

## Remaining implementation-planning proposals

These have been adopted as working M1 design choices in the technical design; they are not claims of additional user confirmation:

- Use existing Calibre book-record associations to group format buttons. Do not automatically merge distinct Calibre records based only on matching titles/authors.
- Restore catalog/UI context in M1, without reopening previous viewer sessions or restoring reading positions automatically. Explicit format-button selection opens the viewer normally.

Confirm these where needed after the Calibre capability review, without reopening the settled milestone boundary.

## Deferred from M1

| Capability | Later work |
| --- | --- |
| Metadata editing, Calibre write-back, automatic change refresh, conflict comparison | M2 / P5 |
| Drag-and-drop/folder intake, duplicates, copy/move/rename and previews | M2 / P6 |
| Reading-progress capture, shared percentage/status updates, per-file position restoration | P7 later pass |
| Multiple profiles, switching, shared collections and approval workflows | Later hub passes |
| Five named states | P8 |

Full docking, tray actions, optional panels, search favourites, restoration exclusions, emergency catalog-edit recovery, and backup/restore remain tracked in the implementation plan. This document does not remove those requirements or claim that M1 implements the entire hub constitution.

Existing external-application ownership/closure requirements apply as soon as M1 launches a viewer. Use the relevant lifecycle subset; do not wait for P9 to protect an attached application. If opening/closing controls are unsupported, explain the limitation and apply the agreed fallback rather than force-close.

## Implementation slice

| Task | Action | Completion evidence |
| --- | --- | --- |
| M1-01 | Validate library reading, record/format identity, status availability, and viewer launch/control on the installed Calibre version | P1 capability report |
| M1-02 | Select the stack and minimal local profile/settings model | P2 decisions and build instructions |
| M1-03 | Build hub, Book-inator tab, personal profile, remembered library selection, and immediate settings saving | Startup/restart checks |
| M1-04 | Read the library, implement book cards, format buttons, and equivalent grid/list views | Dataset comparison and view checks |
| M1-05 | Implement find-book interaction and selected-format viewer launching with ownership tracking | End-to-end launch evidence per format |
| M1-06 | Implement last-session UI restoration and relevant close/failure handling | Restart and lifecycle checks |
| M1-07 | Run acceptance on approximately 100 test books and document known limitations | M1 acceptance report |

**M1-01 through M1-07 are DONE for the agreed milestone scope.** Evidence: [acceptance report](test_data/m1_acceptance/README.md), automated application checks, G1 verification and user desktop confirmation. Broader P1/P2 and later phases retain their own unfinished tasks; milestone completion does not complete the full release backlog.

## Acceptance checklist

- [x] **M1-A01:** First use allows selecting one library and remembers it for the personal profile/device.
- [x] **M1-A02:** Subsequent launch restores the saved library and Book-inator module selection without repeating setup.
- [x] **M1-A03:** Grid/list switching shows the same books; title, author, formats, tags, and reading status are visible in both presentations.
- [x] **M1-A04:** A book with several formats has separate format controls; selecting one opens that file, not an arbitrary alternative.
- [x] **M1-A05:** Title text and author text each locate matching books in the test collection.
- [x] **M1-A06:** EPUB, MOBI, and PDF launch behaviour is checked against the installed viewer; unsupported behaviour is reported accurately.
- [x] **M1-A07:** Unavailable reading status displays Unknown, not Unread. Missing artwork or an unreadable/missing book does not prevent browsing the remaining library.
- [x] **M1-A08:** An unavailable remembered library produces a clear recovery path; it is not silently replaced with an empty catalog.
- [x] **M1-A09:** A viewer already open outside the hub remains externally owned and untouched; M1 asks the user to close it before refreshing or launching, rather than attaching or claiming ownership. Close choices and failures follow the applicable hub rules.
- [x] **M1-A10:** Changing settings/view preference persists without requiring a catalog save, and shutdown does not erase the pre-exit module selection.
- [x] **M1-A11:** No metadata/file-management mutation is initiated by Book-inator browsing or search. No reading-progress update is claimed.
- [x] **M1-A12:** All checks have results recorded on the approximately 100-book test library; limitations and unimplemented later features are listed.

## Links and progress

Current status: M1 complete; G1 passed under the accepted exclusive-access policy, followed by automated 101-book acceptance and user-confirmed three-format reading/navigation and hub close choices. Earlier entries below are historical.

- [Living implementation plan](implementation_plan_hub_bookinator.md).
- [First-release scope](first_release_scope.md).
- [Book-inator constitution](bookinator/bookinator_constituion.md).
- [Hub constitution](mediaintor%20hub/constitution_hub.md).

Initial entry: recorded the user's six milestone decisions and created acceptance criteria. No coding or capability verification completed. Follow-up: user confirmed Unknown for unavailable reading status and title/author text search. Acceptance checks M1-A05 and M1-A07 reflect those decisions. Next: M1-01 capability validation; no coding or verification completed.

Validation pass 1: installed Calibre 9.2.1 library listing and title/author searches passed on a temporary one-record copy. EPUB viewer launched and the user confirmed readable rendering; representative MOBI/PDF/100-book checks remain pending. No M1 acceptance checkbox is completed by these component checks alone.

Environment/library clarification: the user confirmed Ubuntu 26.04.1 LTS with KDE and `/home/sproket01/Calibre Library` as the correct test library. More books will be added later; format and approximately 100-book acceptance checks remain pending, not waived.

Technical design pass: Python/PyQt6 Widgets, versioned JSON settings, an in-memory catalog, and a Calibre command adapter are the working direction. Library-open side effects and viewer lifecycle remain validation gates. No code written.

Validation pass 2 (2026-09-20): listing/search left copied library files unchanged; opening the viewer added annotation-related database data. Busy-lock rejection and detached viewer survival passed. The user confirmed readability after a keypress; targeted handled close updated saved artifacts and exited without captured errors. G2 component feasibility passed, while actual hub lifecycle and final read strategy remain open. The user accepted deferring the startup keypress observation to TODO-VIEWER-01; it does not block M1 or initial integration; no application acceptance checks marked complete.

Dataset follow-up (2026-09-20): 100 free test titles have now been added alongside the existing guide, with 100 EPUBs, 10 MOBIs, and 10 converted PDFs in the new collection. Import/hash/integrity checks passed; viewer rendering and M1 UI acceptance remain pending. See [test collection](test_data/free_ebooks_100/README.md).

Expanded-library component checks: 101-record catalog, covers, paths, imported hashes, CLI searches and multi-format grouping passed on a fresh copy. The user confirmed all three format samples are open, readable, and allow page changes. Simultaneous viewers produced annotation-lock errors for EPUB/PDF; retain this as an unresolved concurrency limitation. These results do not complete application-level M1 acceptance.

Annotation comparison completed: sequential EPUB, MOBI, and PDF bookmarks matched local and copied-library storage before and after handled closure, with empty stderr for each. All test viewers closed and source-library hashes remained unchanged. With three viewers open, later staggered bookmarks also persisted without additional errors, but initial concurrent-launch BusyErrors (EPUB/PDF) remain unresolved. This supports sequential sample feasibility, not simultaneous-write safety or automatic recovery. See the [final comparison](test_data/free_ebooks_100/annotation_validation/README.md#final-comparison). G1 concurrency/failure handling and application acceptance remain open; no application code was written.

Latest user decisions: coding authorized; M1 permits one hub-launched reader at a time; live-library access remains gated on G1; full 101-book application acceptance must follow G1 completion. The sample-data preview and six automated tests are documented in [README](README.md). M1-02/M1-03 and sample browsing are active; library selection, adapter, actual reader controls and end-to-end acceptance are not complete.

Disposable integration pass: implemented an asynchronous Calibre listing adapter restricted to explicitly registered test copies, cover fallback, retained results on load failure, reload and timeout handling, and real format buttons. Single detached reader ownership (profile/module/PID/start-time) persists across restarts; missing files and second-reader requests are rejected. Reader close uses manual-close/explicit leave-open fallback, not automatic signaling. Twelve automated tests passed and a real one-book-copy Qt/Calibre adapter smoke check passed. Live-library selection, G1 production policy, detailed annotation-error handling and full 101-book application acceptance remain open. This supersedes earlier statements that all adapter/reader code was absent; those described the initial foundation pass.

M1 completion pass in progress: 19 automated tests now pass. Private snapshot creation, remembered-library UI, exclusive-access detection, bounded/cancellable loading and version-gated handled reader-close review have been implemented, with the normal live entry point still disabled pending integration validation. A real one-book snapshot adapter check passed without source changes. The user has approved private-snapshot browsing, original-file reading, and Calibre/other readers being closed during refresh/launch. Policy clarification is complete; integration validation remains. G1 is not yet closed and full 101-book acceptance has not started. See [acceptance preparation](test_data/m1_acceptance/README.md). Earlier test counts and manual-close-only descriptions are historical; M1 is not complete.

Accepted access policy: [private snapshot / original files / exclusive refresh and launch](m1_library_access_decision.md). This resolves the product clarification, not final verification. G1 integration checks precede full 101-book acceptance; no acceptance checkbox is completed by this decision alone.

Current acceptance: G1 passed under the accepted exclusive-access policy, then the full 101-book automated application run passed. Eight criteria are checked with evidence; M1-A04/A06/A09/A12 await final desktop reader/close confirmation. See [acceptance report](test_data/m1_acceptance/README.md). M1 is not yet complete.

Desktop confirmation: the user verified that The Time Machine opens and supports readable text/page navigation in EPUB, MOBI and PDF through the hub. M1-A04 and M1-A06 now pass. Hub-close Cancel/Close reader confirmation remains pending; M1 is not complete. Evidence: [desktop confirmation](test_data/m1_acceptance/desktop_confirmation.json).

Final sign-off: the user confirmed Cancel keeps hub/reader open and Close reader closes both. The earlier report concerned closing the reader itself, which correctly leaves the hub open. M1-A09/A12 pass and M1 is complete. No defect fix was required for that report.
