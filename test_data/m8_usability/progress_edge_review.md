# M8 progress edge verification

Result: **14 disposable capability probes passed** against installed Calibre 9.2.1. [Executable probe](verify_progress_edges.py), [results](progress_edge_results.json). These verify upstream behavior and risks, not an implemented production adapter.

The probe copied the preserved manual-backup library into a temporary directory, then performed a real title change through Calibre's metadata API. All mutations were confined to the temporary library/configuration and synthetic annotation fixtures. No RC1 or active M8 data was changed. Temporary libraries were removed normally after each run.

## Timestamp selection

- UTC timestamps select the latest record in the checked Calibre merge path.
- Different timezone offsets expose lexical ordering: 12:00+02:00 sorts above 10:30+00:00 although it is earlier.
- Equivalent instants expressed with different offsets must be treated as a tie.
- An invalid timestamp such as `zzzz` can outrank a valid date in the upstream merge function.

Adapter requirements: parse timezone-aware timestamps, normalize to UTC, reject malformed/missing/timezone-free values for recency comparison. A valid position with an invalid timestamp may still expose resume availability, but cannot establish last-read ordering. For an unresolved tie, expose tied formats without claiming one is uniquely most recent. Do not use filesystem modification time or selection clicks as reading evidence. Test implausible future timestamps before choosing a policy; no arbitrary completion/progress inference.

## Renamed files

A real Calibre title save changed the EPUB path while preserving book UUID and file bytes. A synthetic viewer sidecar keyed by the old absolute path remained under the old key; there was no new-path sidecar. The fixture did not launch the viewer or test fallback from embedded ebook annotations, so it does not establish that every renamed book loses resume.

An attempted last-read save through Calibre's API produced no library last-read annotation. Source inspection explains why: `annot_db_data` provides database identities for bookmarks and highlights only; last-read records are omitted. Do not use library annotation persistence as a assumed resume fallback.

Adapter design direction: retain provenance using library identity, book UUID, format and observed path. Reconcile a rename only after verifying identity and unchanged format content. Never attach a stale position to a different/replaced file by title matching. Viewer-side migration, conflicting old/new records, external renames and ebook-embedded fallbacks require separate disposable end-to-end validation before implementation is accepted. Do not overwrite viewer-owned records blindly.

## Missing and corrupt records

Missing paths are distinct from malformed JSON. Truncated JSON and invalid UTF-8 raise parser errors. Valid JSON with wrong shape or missing position fields parses successfully, so JSON parsing alone is insufficient validation. Read-only parse failure preserves corrupt bytes.

Adapter requirements: bound input size, validate structure/type/position, isolate failure per format, retain raw files untouched, display Unknown where data is unavailable and do not claim resume from an invalid record. A source error must not erase a previously verified record silently; distinguish stale last-known data from currently verified resume availability. Actual CFI validity against the current ebook, permissions, oversize inputs and production error handling remain implementation tests.

## Run history and remaining work

The first probe used the wrong Calibre API argument shape; it was corrected to annotation/timestamp pairs. The second probe exposed the unsupported database last-read assumption, now recorded as a verified limitation rather than a failed rename assertion. Final run: 14 checks passed.

Next: implement and test the validated reader/selection policy in M8 only, then validate safe rename continuity (including embedded fallback), timestamp ties/future values, missing/corrupt/oversize/permission errors and real viewer reopening. M8-05 remains in progress; M8-G remains open. No production application code changed.
