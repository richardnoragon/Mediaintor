# M1 acceptance report

Status: **M1 COMPLETE for the accepted workflow.** G1, automated 101-book checks and final desktop reader/close confirmation passed.

## G1 integration verification

[Machine-readable result](g1_verification.json).

- Real OS process discovery detected a controlled stand-in named `ebook-viewer`; refresh and reader launch were rejected without closing it. This tests the detection/refusal path, not actual simultaneous Calibre writes.
- After that process exited, the real Qt/Calibre snapshot adapter loaded a one-book fixture successfully.
- Calibre queried only the private copy, returned paths were remapped to original files, source hashes were unchanged, and unavailable libraries generated errors.
- The normal entry point now enables the accepted private-snapshot workflow with a remembered library picker. Sample and marked-copy modes remain explicit development options.

G1 is complete for **one hub reader and exclusive refresh/launch**, not for unrestricted concurrent applications. Detection is best-effort; the known initial parallel-viewer annotation contention is not claimed fixed.

## Full-dataset automated results

[Application checks](application_checks.json), [grid screenshot](grid.png), [list screenshot](list.png).

| Criterion | Evidence / result |
| --- | --- |
| M1-A01 | Library picker action saved the selected original library; passed with dialog selection supplied by automation |
| M1-A02 | New hub instance restored library, module, view and selection; passed |
| M1-A03 | Grid/list matched all 101 records and displayed required fields; passed |
| M1-A04 | All 121 format buttons dispatched the matching original path; desktop reader portion user-confirmed |
| M1-A05 | Title search found one Pride and Prejudice; author search found six Austen books; absent query found zero; passed |
| M1-A06 | Installed viewer previously passed three-format component checks; current app-launched desktop reading/navigation user-confirmed |
| M1-A07 | Unknown fallback, missing artwork and missing-format error checks passed without losing catalog |
| M1-A08 | Failed library reload retained 101 previous records with a stale/error message; Retry and library picker available; passed |
| M1-A09 | External process untouched; automated Cancel and Leave-open checks passed. Actual Cancel and owned-reader Close paths user-confirmed |
| M1-A10 | Preferences/module selection survived close/restart; passed |
| M1-A11 | All original-library hashes unchanged through browsing/search checks; no app progress update claimed; passed |
| M1-A12 | This report records the full dataset; all desktop checks are now confirmed; final completion recorded |

There are 101 covers and 121 file paths. All 120 imported file hashes and record titles/format groups matched the dataset manifest. Catalog load was about 0.4 seconds in this local run, not a general performance guarantee. The 23 automated tests also pass. A stale format-button display bug found during screenshot inspection was fixed and the affected checks rerun. Temporary snapshots are explicitly released on module/hub close and library change.

## Completed desktop checks

The normal app is open using isolated acceptance settings under `/tmp/mediainator-m1-desktop` and the original 101-book library. Through the hub, open The Time Machine's EPUB, MOBI and PDF sequentially, confirm readable text and page changes, and close each reader before the next. Then verify Cancel keeps the hub/reader open and Close reader closes both through the owned-process handler. The user has confirmed the three-format reading/navigation checks. The user also confirmed Cancel keeps both open and Close reader closes both.

## Limits retained

- Original-file reading can update Calibre annotations/preferences; the unchanged-source result applies to catalog browsing, not reader use.
- Existing-reader protection is conservative: refuse a new launch and leave unrelated content untouched; no session takeover.
- Converted text PDFs are covered, not scanned-PDF quality or all possible ebooks.
- Reading-status mapping beyond available verified data remains Unknown; progress integration is deferred.
- No synchronized-write guarantee; no automatic force-kill; graceful close is version-gated to the tested Calibre 9.2.1.
- Initial keypress issue remains a deferred usability TODO.

The user confirmed all three formats open and navigate correctly through the hub. See [desktop_confirmation.json](desktop_confirmation.json). The final hub-close confirmation has now passed.

Close-flow follow-up: user reported only the reader closes; initiating control is not yet confirmed. A real-Qt-dialog regression check with simulated asynchronous reader exit passes, and reader-only exit correctly leaves the hub open. Twenty-three automated tests pass; no application fix was made because the discrepancy is not yet reproduced. Desktop M1-A09/A12 remain open pending clarification and verification.

Final clarification: the reported reader-only close was initiated from the reader window, so the hub remaining open was expected. The user subsequently confirmed both hub close-dialog outcomes. See [desktop evidence](desktop_confirmation.json). All M1 criteria are complete; limitations above remain in effect.
