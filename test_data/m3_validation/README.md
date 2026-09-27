# M3 disposable validation preparation

Status: **M3-02 capability/protocol validation COMPLETE.** All 13 final checks passed; see [results and limitations](RESULTS.md). M3-G remains OPEN / NOT RUN at application level. No application code changed. The preparation plan below is retained as context.

## Prepared workspace

See [workspace.json](workspace.json) for canonical paths. Current root: `/tmp/mediainator-m3-validation-puabdpci`.

- `baseline/`: coherent private snapshot of all 101 source records. Treat as immutable; never open it with a mutating Calibre command.
- `imports/library`, `attachments/library`, `recovery/library`: independent full copies, each registered with the project's disposable-library marker. All library files matched the baseline after copying, excluding the added marker.
- `fixtures/`: ten input files, including EPUB/MOBI/PDF from The Time Machine, a nested renamed byte-identical EPUB, a different-content EPUB retaining its metadata, missing-title/author/both EPUB variants, unsupported text and a deliberately invalid EPUB.
- [Source manifest](source_manifest.json), [baseline manifest](baseline_manifest.json), [fixture manifest](fixture_manifest.json): sizes and SHA-256 hashes. Source hashes were checked before/after preparation and unchanged.

The XML-edited EPUBs are deliberate test inputs. Their observed Calibre parser behaviour and fallback outcomes are now recorded in RESULTS.md; file creation alone was not counted as validation. Duplicate inputs intentionally already exist in the full library. For genuinely new clean EPUB/MOBI/PDF imports, create a separate empty library through Calibre during execution; do not mistake existing-library duplicates for clean imports.

Temporary storage may disappear after reboot. The project manifests persist, but do not replace a reusable fixture dataset. If paths no longer exist, recreate fresh snapshots/fixtures and update the workspace record before testing. Do not repoint test commands at the original library.

## Execution boundaries

1. Read and verify `workspace.json`, disposable markers and canonical paths. Every mutation target must be inside this temporary workspace, never the original library or immutable baseline. Use separate Calibre configuration per test area and Calibre's database lock; close Calibre/readers before execution.
2. Capture each case's starting record count, IDs/UUIDs, metadata, format paths and hashes. Record expected outcomes **before** executing it. Reset a working copy from the baseline between destructive/failure cases rather than reusing unexplained state.
3. Preview the concrete case plan before mutations. Recheck input hashes and destination formats immediately before execution. Scope approval alone is not a substitute for the application's future mandatory preview.
4. Use Calibre API/CLI operations only. The installed `add_format` command defaults to replacement; use `--dont-replace`, or API `add_format(..., replace=False)`. Verify actual stored bytes, not just exit status. Do not use automerge for explicit attachment tests.
5. Compare source/fixture hashes and existing records after each case, reopen the disposable database, and capture outcomes. Any changed source, overwrite, lost record or unexplained outcome stops the affected validation pass.

Local source inspection: Calibre 9.2.1 `db/cli/cmd_add_format.py` and `db/cache.py` expose replacement-disabled attachment. `add_books` and CLI `add` also have metadata-based duplicate/merge behaviour; neither should be assumed to implement M3's exact-content duplicate policy. Runtime outcomes for these interfaces are now recorded in RESULTS.md.

## Ordered case plan

| ID | Area / setup | Required observation | Status |
| --- | --- | --- | --- |
| V01 | Read baseline/catalog and parse all ten inputs | 101 baseline records; three representative formats; truthful extraction/failure reports for malformed/missing metadata | Executed — see RESULTS.md for scope |
| V02 | Create an empty target through Calibre; plan and copy valid EPUB/MOBI/PDF inputs | Confirmed new records/formats, source bytes unchanged, reopened metadata and valid destination paths | Executed — see RESULTS.md for scope |
| V03 | Full imports copy and nested duplicate input | Exact-content duplicates detected across library and batch; skipped/reported regardless of filename; no new record | Executed — see RESULTS.md for scope |
| V04 | Different-content/same-metadata EPUB | Similar-title warning, not an exact duplicate; no automatic merge; explicit chosen action | Executed — see RESULTS.md for scope |
| V05 | Missing-title/author/both EPUBs into empty target | Filename/Unknown fallbacks and warnings; track missing-field provenance for a persistent review marker | Executed — see RESULTS.md for scope |
| V06 | In attachments copy, create a new EPUB-only record via Calibre; select it explicitly | Add MOBI then PDF with replacement disabled; preserve record UUID, prior metadata and existing formats | Executed — see RESULTS.md for scope |
| V07 | Occupied EPUB slot; repeat with slot filled after preview | Refusal/review instead of overwrite; original format hash unchanged; no misleading success | Executed — see RESULTS.md for scope |
| V08 | Cancel a reviewed batch; stage source changes/disappearance and validation failures | Cancel has no mutation; stale plan cannot execute silently; valid unrelated items retained in preview | Executed — see RESULTS.md for scope |
| V09 | Denied access and injected per-item failure on recovery copy | Completed imports retained; remaining/failed items distinguishable; no automatic write retry | Executed — see RESULTS.md for scope |
| V10 | Stop request during a multi-item batch | Verify current item if possible, stop starting further items, persist completed/pending/unverified outcomes | Executed — see RESULTS.md for scope |
| V11 | Simulate restart after Calibre commit but before success journal update | Reconcile destination identity/hash before retry; do not create a duplicate or blindly claim success | Executed — see RESULTS.md for scope |
| V12 | Review / Retry / Discard Pending from saved recovery state | Counts truthful; Retry builds a revalidated preview requiring confirmation; Discard Pending preserves successes and all sources | Executed — see RESULTS.md for scope |
| V13 | Final inventories and reopen | No source changes, no unintended existing-record changes; all intended destination associations valid | Executed — see RESULTS.md for scope |

## Recovery evidence to design and test

A validation harness should journal a batch ID, library identity/path, operation ID, source path/hash/format, proposed action, selected destination ID/UUID, effective metadata/fallback reasons, and current outcome. Distinguish pending, in-flight/unverified, verified success, skipped, failed and discarded-pending items. Persist before mutation and after verification; reconcile uncertain commits by identity and content, not title alone. This is a proposed technical test contract, not an implemented production journal/schema.

Test a controlled interruption after a verified item and a controlled process exit after commit/before journal acknowledgement. Do not label these simulations as proof of disk-full or arbitrary crash recovery. Keep any recovery evidence alongside the per-case before/after inventories. Do not add hidden Calibre tags/custom columns for review markers without a documented design.

## Evidence and gate limits

For each case retain: exact request/arguments, Calibre version, target path, preview/confirmation, before/after inventories, exit/errors, read-back, expected versus actual outcome and remaining limits. Record failures as failures, not skipped successes. Write a results report only after execution.

Calibre capability tests can establish import/attachment feasibility. Drag/drop UI, preview controls, durable metadata-review flags, restart UI, M1/M2 regressions and desktop acceptance still require M3 implementation. Do not check M3-G criteria solely because this workspace or a protocol harness exists.

V01–V13 are executed; see RESULTS.md. Next is production discovery/preview and recovery implementation. M3-G remains open.
