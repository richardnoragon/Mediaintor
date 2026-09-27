# M3-02 — Disposable import, attachment and recovery results

Status: **M3-02 capability/protocol validation complete. M3-G remains OPEN.** Calibre 9.2.1; all 13 final checks passed. No application code changed. The validation harness and evidence are under `test_data/m3_validation`.

## Scope and evidence

[Final results](results.json), [individual checks](checks.json), [add-operation events](events.json), [reproducible harness](execute_checks.py). The run root in results contains reopened destination inventories, review-marker data, interruption journal, retry/repair previews and reconciled commit intent. These temporary artifacts remain available for inspection but may disappear on reboot.

Each run creates fresh libraries under the prepared workspace, using the immutable 101-book baseline. A separate empty target tests genuinely new imports. The original library, fixture files and baseline remained unchanged. Existing record identity, displayed metadata, covers and format hashes were preserved in all full-library copies. No command targeted the original database for writes.

The first sandbox attempt could not acquire Calibre's local lock socket; substantive runs were authorized outside the sandbox. The harness holds Calibre's database lock for the session. The controlled crash child accesses only the recovery library while its parent has closed that database and continues to hold the lock; this is not a concurrent-writer experiment.

## Final outcomes

| Cases | Result and practical meaning |
| --- | --- |
| V01 | Parsed valid EPUB/MOBI/PDF and missing-metadata fixtures; structural EPUB validation rejected the invalid input. Unsupported text reported. |
| V02 | New EPUB/MOBI/PDF records imported into an empty target, reopened successfully, and stored format bytes matched input hashes. |
| V03 | Hash-policy harness skipped identical contents already in the library and repeated new contents within a batch. A renamed path did not evade detection. No library mutation during duplicate classification. |
| V04 | Different contents with matching metadata produced a similar-title candidate, not an exact duplicate; an explicitly selected new-record action created a separate record without merging. |
| V05 | Missing title/author/both used filename-stem/Unknown fallbacks. Original missing-field reasons were recorded in a persisted sidecar keyed by book UUID and survived rereading. This is marker-storage protocol evidence, not the finished review-marker UI. |
| V06 | Explicit MOBI/PDF attachments to a new EPUB-only record succeeded with `replace=False`; identity, metadata and all previous format bytes were preserved. |
| V07 | An occupied format and a slot filled after preview were both refused with `False`; no overwrite. False must not be reported as successful attachment. |
| V08 | Harness cancellation sent no write. Changed/deleted scratch inputs invalidated their preview. These are protocol checks, not preview UI acceptance. |
| V09 | A separate process failed to acquire the held Calibre lock. A real missing-file failure left a metadata-only partial record; the prior successful import remained intact. |
| V10 | Stop-after-current-item protocol retained a verified completed item and durably journaled pending/unverified work without starting another item. |
| V11 | A child imported using a pre-journaled operation UUID, closed the DB and exited with code 23 before acknowledging success. After reopening, UUID plus format hash found exactly one committed item; the stale in-flight intent was reconciled without a second import. |
| V12 | Restarted journal produced a reviewable retry plan. An explicitly confirmed repair attached the missing format to the tracked partial record while preserving its ID/UUID and record count. Discard Pending changed work state only, leaving completed imports and database contents intact. |
| V13 | Reopened all targets, checked original-record preservation and verified unchanged original-library, baseline and fixture manifests. |

## Findings the production adapter must address

1. **Calibre metadata parsing can hide invalid input.** The initial V01 failed because the deliberately invalid EPUB logged an error yet returned title `invalid` and author `Unknown`. [Initial failure evidence](initial_parser_failure.json) is retained. Add independent format validation before accepting parser fallbacks. The final harness checks EPUB ZIP structure, mimetype, container/OPF XML and archive CRCs. This is not exhaustive EPUB content validation, nor invalid-PDF/MOBI coverage.
2. **Calibre duplicate heuristics are not the product policy.** Compute content fingerprints across the library and batch independently. Use explicit record association and avoid automerge. In the experiment, `add_books(..., add_duplicates=True)` allowed the already-reviewed distinct-content record; this option alone does not protect against byte-identical duplicates.
3. **Disable format replacement explicitly.** Use `add_format(..., replace=False)` and verify its result plus stored bytes. Revalidate destination identity and occupied formats after preview.
4. **Record partial creations.** A failed `add_books` call can leave a book with no format. Journal stable operation identity before mutation, reconcile even after an exception, and repair the known record rather than create a duplicate. Do not silently delete successful/partial records.
5. **Preserve metadata provenance.** Calibre synthesizes filename/Unknown values. Inspect extraction provenance rather than assuming those populated fields prove complete metadata. The experiment uses EPUB raw OPF fields and a separate JSON marker; metadata provenance for other input variations and the marker clearing workflow remain implementation work.
6. **Make recovery durable and explicit.** Persist intent before mutation and verification afterward, with atomic replacement and fsync. UUID/hash reconciliation prevents commit-before-ack duplication. Retry must still require preview/confirmation; journal discovery never starts writes automatically.
7. **Define the import-hook policy.** These calls use isolated configuration, `run_hooks=False` and `apply_import_tags=False` to test predictable copy behaviour. Do not claim validation of arbitrary third-party import plugins. Existing metadata is preserved on attachment.

## Limits and next step

These are Calibre capability and harness-protocol results. Actual drag/drop, preview/confirmation controls, persistent review-marker presentation, production journal/schema, restart actions, progress/cancellation UI, M1/M2 regressions after implementation and final desktop acceptance remain M3-03–M3-07 work. The controlled exit occurs after a completed commit; arbitrary power loss, disk-full and mid-database-write crashes were not tested. No new viewer navigation claims are made.

M3-02 can close on this documented interface/recovery evidence. All M3-G checkboxes remain open until the production implementation and acceptance establish them. Next: design and implement M3-03 discovery/preview, carrying these safeguards into M3-04–M3-06.
