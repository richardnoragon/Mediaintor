# M2 follow-up adapter capability verification

2026-09-20, installed Calibre 9.2.1. Ran the Calibre database API through `calibre-debug` on a fresh complete disposable copy. Used book 32 (EPUB/MOBI/PDF). Original-library file hashes were unchanged. Application code was not changed.

## Results

| Requirement/check | Result |
| --- | --- |
| Remove stored series name and index | **Historical requirement not met (now superseded):** name becomes absent, but `set_field('series_index', {32: None})` stores 1.0. Reopening and a read-only SQL query confirm 1.0. Schema defines `series_index REAL NOT NULL DEFAULT 1.0`. Literal absence is incompatible with this schema; no schema changes or direct SQL writes attempted. |
| New series starts at 1 | Passed when adapter explicitly sets 1. |
| Ordered authors, embedded commas, reorder | Passed using list-valued API calls and reopening. |
| Tags preserve embedded commas | **Historical requirement not met (now superseded):** `Science, Fiction` becomes `Science; Fiction`, even through list-valued API calls. Other tested tags persisted. UI entry separation does not prevent Calibre normalization. |
| Untouched HTML | Exact string survived an unrelated tag save and reopening, including paragraphs, emphasis, lists and a link. Does not test an implemented rich-text editor. |
| Cover removal | Passed: API `set_cover({32: None})` removed the file, cleared cover flag and returned no cover after reopening. |
| Automatic backup restoration protocol | Injected invalid image bytes at the write boundary, causing a real zero-byte cover failure. Harness automatically restored the backed-up original through the API, verified exact bytes and decodability after reopening, retained pending replacement and preserved the successful title write. |
| Restoration failure reporting | Harness simulated an exception at recovery and retained backup/pending data without reporting success. This is not an actual disk-full or permission-failure test. |
| Numeric validation | Protocol accepted 0, 1, 2.5, 4.1, 12, and round-tripped these through Calibre; rejected negatives, malformed input, NaN and infinity before writing. |
| Identity and formats | UUID and hashes of all three format contents unchanged. |

## Consequences

Cover deletion and recovery are feasible through Calibre's database API, beyond the previously tested CLI. A production helper still needs version checks, exclusive-access protections, process isolation, and error/read-back handling. API feasibility does not certify concurrent writers or finish M2 implementation.

The user resolved both compatibility blockers: when no series exists, hide and ignore Calibre's internally retained index; it is not a save failure. Assigning a new series explicitly defaults to 1 unless edited. Individual tag names may not contain commas; validation must prevent saving them and explain that Calibre treats commas as separators. Application implementation and acceptance remain open; these decisions do not mark tests complete. Historical observations and raw test results below remain unchanged; they tested the earlier requirements.

## Evidence and reproduction

[Checks](checks.json), [report](report.json), [script](validate_disposable.py). From repository root run:

```sh
QT_QPA_PLATFORM=offscreen CALIBRE_CONFIG_DIRECTORY=/tmp/mediainator-m2-followup-config calibre-debug -e test_data/m2_followup/validate_disposable.py
```

The script creates its own `/tmp` copy and writes only that library. It overwrites this follow-up evidence and retains the copy for inspection. Original library is read only for copy/hash comparison. Database SQL is read-only inspection of the disposable copy; all metadata mutations use Calibre API calls.

Local source evidence: `/usr/lib/calibre/calibre/db/write.py` (`adapt_series_index` and tag normalization), `db/cache.py` (`set_field`, `set_cover`). Runtime schema read-back is included in the checks. The script's image failure deliberately bypasses input validation to exercise recovery; production must reject invalid input before attempting writes.
