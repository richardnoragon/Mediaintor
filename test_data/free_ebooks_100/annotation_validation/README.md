# Viewer annotation-saving investigation

Status: Bounded manual comparison COMPLETE; initial concurrent-launch lock errors remain unresolved. No application code written. Existing disposable test library: `/tmp/mediainator-expanded-n2b0gj31/library`; the live library is not a write target.

## Baseline

All three sample viewers were previously confirmed readable with working page navigation. EPUB and PDF logged one `apsw.BusyError` each during the simultaneous launch; MOBI logged none. All three local viewer annotation files contain a `last-read` location. The copied library annotation table is empty; source-library hashes are unchanged.

Installed Calibre 9.2.1 source explains why last-read data alone is not a database-save test: `calibre/db/annotations.py:annot_db_data` provides database identifiers for bookmarks and highlights only. `calibre/gui2/viewer/annotations.py:save_annotations` writes the local annotation JSON before attempting library persistence, and its worker logs exceptions. Therefore local persistence and library persistence must be evaluated separately.

## Comparison procedure

1. With the three existing sample viewers open together, add a bookmark named `TEST-SIMULTANEOUS` to each. Confirm the bookmark appears in each viewer.
2. Snapshot local annotation files and the copied library rows. Capture errors before and after; distinguish old errors from new ones. This tests multiple open viewers, not precisely synchronized writes.
3. Close only the verified test sessions through their handled close path; inspect whether close saves repair any earlier missing library annotations.
4. Use a fresh isolated library copy and fresh viewer settings for a sequential control: one sample viewer at a time, add `TEST-SEQUENTIAL`, inspect local/library persistence, close it, then open the next format.
5. Compare all three formats, retaining exact evidence and recording whether any contention was reproduced. A successful rerun does not establish that concurrent saving is always safe. Manual bookmark checks require user interaction; do not mark them complete before confirmation and evidence.

Remaining limits: highlights, precisely synchronized writes, same-book competing edits, recovery across crashes, and viewer-restored bookmark visibility are not established by the baseline. This investigation does not authorize changing Calibre's database schema, journal mode, or installed source.

Baseline evidence: [simultaneous_before_bookmarks.json](simultaneous_before_bookmarks.json).

## Multiple-open-viewer bookmark result

User created TEST-SIMULTANEOUS in all three viewers. Exact named bookmarks were found in each local annotation file and in the corresponding EPUB/MOBI/PDF library rows, both before and after handled sequential closure of these three verified test sessions. No additional BusyError was logged: counts remained EPUB 1, MOBI 0, PDF 1. Database integrity passed and the source library remained unchanged. The initial errors are still unexplained; the later successful saves do not establish automatic retry or conflict-free simultaneous writes. The bookmark timestamps show staggered user actions, not synchronized writes.

Evidence: `simultaneous_after_bookmarks.json`, `simultaneous_after_close.json`, `simultaneous_close.json`.

Sequential control started on a fresh copy at `/tmp/mediainator-sequential-o5kim_6g/library`, with fresh viewer settings. This control subsequently completed for EPUB, MOBI, and PDF; all viewers are closed. See `sequential_session.json`.

Sequential EPUB result: PASSED. User confirmed readable display, page change, and bookmark creation. Actual bookmark label was TEST-SIMULTANEOUS (reused rather than requested TEST-SEQUENTIAL); its new timestamp and fresh isolated session distinguish it from the previous trial. Local and library bookmark contents matched before and after handled closure, with zero BusyError messages and unchanged source-library hashes. Evidence: `sequential-epub.json`. MOBI and PDF subsequently passed; see the final comparison.

Sequential MOBI control: PASSED after the user completed bookmark creation. The bookmark matched local storage and the copied library before and after handled close, with no logged lock errors and unchanged source-library hashes. The earlier check found only a last-read position because bookmark creation had not yet been completed; it is not evidence of a save failure. Evidence: `sequential-mobi.json`. The PDF check subsequently passed; all test viewers are closed.

## Final comparison

| Check | EPUB | MOBI | PDF |
| --- | --- | --- | --- |
| Sequential bookmark matches local/library storage before close | Pass | Pass | Pass |
| Sequential bookmark persists after handled close | Pass | Pass | Pass |
| Sequential stderr | Empty | Empty | Empty |
| Bookmark with three viewers open, before/after close | Pass | Pass | Pass |
| Initial parallel-launch BusyError count | 1 | 0 | 1 |

All sequential test viewers exited through their handled close path. Database integrity passed and the original library hashes remained unchanged. Evidence: `sequential-epub.json`, `sequential-mobi.json`, `sequential-pdf.json`, and [comparison.json](comparison.json).

The observed sequential workflow passed for these three samples. Multiple open viewers also saved the later, staggered bookmarks successfully without additional errors. This does not prove that simultaneous writes are reliable, that startup serialization alone fixes contention, or that Calibre automatically retries failed saves. The initial parallel-launch lock errors remain a production integration concern. No force-close was used, no Calibre settings/schema/source were modified to work around locking, and no application code was written. Further synchronized-write or failure-recovery testing requires a separate bounded pass; full M1 acceptance remains open.
