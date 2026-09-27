# M4 — Bulk Metadata Editing

Status: M4 COMPLETE and M4-G PASSED/CLOSED following automated verification and user desktop sign-off on 2026-09-21. Requirements: [M4 specification](milestone_04_bulk_metadata_editing.md).

## Selection and preview

Catalog checkboxes maintain an in-memory set of book UUIDs, separate from the single current book used for reading/editing. Selection survives search, review filtering, grid/list changes and explicit sorting; Select All Search Results covers the complete matching set. The current catalog has no pagination. Missing UUIDs are removed on refresh. Closing the module clears the set; switching libraries creates a separate module instance. No bulk selection is written to hub preferences.

Bulk editing presents exactly one of five operations, an explicitly reorderable book list and a mandatory current/proposed preview. Sequence numbers use decimal arithmetic before conversion to Calibre's numeric representation. Exclusions retain the assigned numbers. Operation settings are disabled once previewed; returning to settings invalidates that preview. The dialog blocks interaction with its parent during review; background catalog refresh is deferred until it closes.

## Adapter and ownership

A worker takes a private library snapshot for multi-record preview/recovery reads. Writes use the existing version-bound Calibre metadata adapter on the selected original library. Each book is checked against both library UUID and book UUID, then revalidated under Calibre's database lock. The existing requirement to close Calibre/readers during access remains in force. Calibre-managed author path changes are permitted; format management is not exposed.

Bulk writes restrict intents to authors, tags, series and series index. Exact author matching uses the stored Calibre string; Calibre may canonicalize author spelling/case at storage time. No fuzzy matching is added. Tags retain their comma validation. A missing series hides and ignores Calibre's retained index.

## Durable execution and recovery

`bulk.py` defines deterministic plans, journals, conflict/reconciliation logic and revert plans. `bulk_worker.py` runs serial per-book requests. `bulk_dialog.py` provides preview, history and explicit recovery controls.

History is stored beneath the hub configuration's `bulk/<library-path-hash>/` folder using a separate schema version 1. Every record includes the library UUID; path matching alone never authorizes writes. Atomic file replacement and file/directory fsync precede mutation. The writer records the actual pre-write values under the lock and writes its verified result to the journal before acknowledging success. No cover image data or unrelated description HTML is stored in bulk history.

Each item stores baseline, desired values, observed before/after changes, per-field errors and pending/complete/conflict/in-flight status. Observed partial field changes retain their earliest before values across retries. Completed fields remain committed; retry revalidates only unfinished or explicitly reapproved changes. An uncertain acknowledgement remains in-flight until a fresh read reconciles it. Matching the intended value verifies the state, not the historical authorship of a concurrent external change.

Stop/close requests finish verification of the current book; no writer is force-killed. Restart exposes pending batches without automatic execution. Review/Retry Pending reads current values and rebuilds the review; Confirm changes is still required. Conflicting books remain queued while unaffected books continue. Discard Pending abandons only unfinished work; uncertain writes must be reviewed first.

## Revert and retention

Revert produces a separate batch referencing the original ID, restoring only observed changed fields. Current values are compared against the original verified post-write values; later changes require review. Series/name coupling is retained. Revert uses the same preview, exclusions, lock, journal, partial-result and interruption mechanisms as forward edits.

History is library-specific and has no expiry. Deleting a terminal record requires the approved warning and confirmation. Pending recovery records must first be reviewed/discarded; history deletion does not alter library metadata. Deleting an original record does not delete a separate revert record.

## Evidence

[Acceptance records](test_data/m4_acceptance/README.md) distinguish passing checks from outstanding checks. No release is published and M1–M3 acceptance is not renamed or reset.
