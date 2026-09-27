# M5-03 — Production activity and recovery integration

Current disposition: **M5 COMPLETE; M5-G PASSED / CLOSED**. [Final gate review](../m5_acceptance/gate_review.md). The stage status and remaining-work notes below record the state at that earlier verification.

Status: **M5-03 COMPLETE**. [85 unit/UI tests](unit_tests.txt) and [14 real disposable integration checks](checks.json) passed. The [integration report](report.json) confirms original-library hashes unchanged. This is backend/operation integration evidence; **M5-G remains OPEN** for the remaining M5 application features and acceptance.

## Implemented and verified

- Owner-scoped, schema-versioned Activity storage with atomic replacement, process locking, stable operation keys, attempt identities, interruption recovery, deduplicated journal discovery and latest-success/latest-failure projections. Repeated actionable failures coalesce, while successful settings saves are omitted.
- Import, metadata-save, metadata-review, bulk-edit and batch-revert outcome hooks; actionable settings/refresh/owned-reader-launch failure hooks. Reverts retain original-batch lineage. Startup indexes existing journals without automatically opening the import dialog or executing work.
- Production recovery payload storage with checksums, profile/device/library/book identity checks, draft revisions, multiple generations, embedded cover bytes, exact pending HTML, verified registration and optional alternate destination. Corrupt/default-index recovery discovery preserves files. Activity recording failure is non-recursive and does not discard editor drafts.
- An explicit editor preservation API and recovery-draft reconstruction API; reviewing/reconstructing does not write to Calibre. Real recovered Save uses the existing locked adapter and conflict checks.
- Idempotent migration of metadata-review provenance/status out of import journals. The editor and review filter read the independent book-review store. History deletion is guarded by pending-state checks and verified migration; failures preserve the original journal. Reordering journal items does not duplicate or reset review state.

The real integration run created a fresh 101-book disposable library. It used the actual editor for metadata Save, preserved/reloaded pending tags, introduced a competing Calibre value, reviewed the conflict without writing, then explicitly saved. It exercised the actual bulk edit/revert and import dialogs, and verified a fallback-metadata book retains its review warning after import-journal deletion and can still be marked reviewed.

## Still outside this completed task

- **M5-04:** Hub Activity panel, details/full history UI and the single startup summary. Until then, open existing import/bulk dialogs manually to review pending batches.
- **M5-05:** Shared Retry/Dismiss/Discard/Delete controls, reviewed-revision authorization, coordinated crash-safe multi-file deletion and complete routing to an exact operation.
- **M5-06:** Automatic preservation after failed Save/Retry, alternate-location UI, recovery resolution/cleanup and automatic completion of an already-requested close. The backend API is present, but normal failed saves still keep the editor open; do not claim automatic emergency protection yet.
- **M5-07:** Complete milestone fault/scale/regression checks, help/UI acceptance and user desktop sign-off.

Existing M4 deletion controls remain scoped to their original behavior; this task does not introduce shared-history deletion UI or delete existing user journals. The source library and user settings were not used as write targets during verification.

## Reproduce

```bash
QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s tests
QT_QPA_PLATFORM=offscreen python3 tests/verify_m5_activity.py
```

Run the integration check with Calibre/readers closed. It uses private configuration for Calibre helpers and requires access to Calibre's local lock socket; a restrictive sandbox may require approval. No viewer is launched or force-closed.
