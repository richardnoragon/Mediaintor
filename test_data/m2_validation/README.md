# M2 disposable metadata-write validation

Completed 2026-09-20 using installed Calibre 9.2.1. This is capability/protocol evidence for M2-01, not acceptance of an implemented metadata editor. All commands targeted a fresh complete copy of the 101-book library, with isolated Calibre configuration. Mutations used The Time Machine (ID 32), which has EPUB, MOBI and PDF. SHA-256 comparison of every original-library file before/after the completed run found no changes. No application source was changed.

## Results

| Experiment | Observed result |
| --- | --- |
| Title and two authors | Saved; Calibre renamed directories and all three format paths. Book UUID remained stable and format contents were unchanged. Previous paths no longer existed. |
| Tags, cover, series, index and description | Saved and read back. Index 2.5 supported. HTML description preserved exactly. PNG cover re-encoded to JPEG. Unedited identifiers/language/publisher and format hashes preserved in this round trip. Missing optional JSON keys must be handled. |
| Sequential partial save | Title/tags committed; subsequent invalid series number failed with exit 1. Successful values remained, index unchanged. |
| Combined invalid number | Invalid series number rejected before the accompanying title was saved. This one validation failure does not establish general transaction atomicity. |
| Missing cover plus title | Exit 0, no stderr; title saved but cover silently unchanged. Exit status alone cannot establish success. |
| Invalid image plus title | Exit 1; title nevertheless saved, existing cover truncated to **zero bytes**. Real within-command partial mutation, including damage to the failed field. |
| Cover recovery | A subsequent save with the valid replacement succeeded; resulting cover decoded successfully. This tests replacement retry, not an implemented automatic backup-restoration feature. |
| Clear series | Empty series cleared its name, but index stayed 2.5 despite submitting 1. |
| Index without series | Setting 3.5 returned success but index stayed 2.5. Series and index require coupled semantics. |
| External changes before Save | Three-way comparison detected conflicting tags. Choosing external tags and saving local description preserved an unrelated external publisher change. |
| External changes before Retry | A new description change was detected as a conflict; no retry write was sent. |
| Discard remaining draft | Clearing the harness's local draft left committed title/tags intact. No write or rollback was issued. |

## Required write-adapter safeguards

1. Resolve records by library identity, book ID and UUID; reload all paths after verified writes. Never reuse a stale path following title/author updates.
2. Validate requested values before mutation. Decode and stage cover input, reject missing/invalid images, and preserve a recoverable copy of the existing cover before calling Calibre. Verify saved cover content/decodability, allowing legitimate image re-encoding. Recovering a damaged failed cover must not roll back successfully saved text fields. Exercise this recovery in adapter tests before live use.
3. Treat writes as potentially partial. Read back affected values after both successful and failed commands; distinguish verified success, remaining failure and unknown outcome. Keep outstanding drafts. A failed field may itself have changed or become damaged.
4. Send only outstanding intended fields, freshly revalidate baseline/current/draft before every Save/Retry, and preserve unrelated external edits. Compare covers by content, not path alone. CLI read-then-write is not atomic across processes; retain exclusive-access restrictions and test races/contention in the adapter.
5. Group series/index deliberately. Current policy accepts a retained Calibre index when no series exists: hide and ignore it, without a save error. Explicitly default a newly assigned series to 1 unless edited. See [M2 specification](../../milestone_02_metadata_editing.md). Preserve existing description markup unless intentionally edited.

## Evidence and limits

- [Report](report.json), [checks](checks.json), [exact CLI arguments, exit codes and output](commands.json), [baseline](baseline.json).
- [Reproduction script](validate_disposable.py): run from the repository root with Python/Pillow and Calibre installed. It creates its own temporary library; it deliberately tests corrupt cover input only in that copy. It overwrites these evidence JSON files and leaves the temporary copy for inspection. Calibre needs its normal local lock socket; sandbox execution can fail. Do not redirect its writes at a real library.
- An initial run stopped because the harness indexed an absent optional publisher key; corrected to allow missing keys. The final complete run includes all scenarios and source-integrity comparison.
- Full 101-book copy used; mutations target one representative multi-format book. This is not 101-book mutation acceptance.
- Conflict and Discard checks exercise a protocol harness, not application UI or simultaneous writers. No disk-full, permissions, process-crash, lock-contention or automatic cover-backup recovery injected here. Cover removal and automatic backup restoration are now confirmed M2 requirements, but are not established by these tests. Those application failure/recovery checks remain part of M2-03/M2-05/M2-07.
- Installed local sources inspected: `calibre/db/cli/cmd_set_metadata.py`, `calibre/db/cache.py`, and `calibre/db/backend.py` under `/usr/lib/calibre`. Results are version-specific.

## Follow-up verification required by confirmed editor decisions

Verify series-name removal, hidden/ignored retained index and explicit new-series default; cover removal; automatic cover-backup restoration (including failed recovery); ordered author round trips with embedded commas, unordered valid-tag round trips and comma rejection for tags; numeric validation; and exact preservation of untouched description HTML. Basic rich-text editing is now selected. The existing successful valid-cover retry is not evidence of automatic backup restoration. Product decisions are settled; these adapter/application checks remain open under M2-02/M2-03/M2-07.

Follow-up API experiments are now recorded in the [follow-up report](../m2_followup/README.md). They establish cover deletion/recovery feasibility and identify series-index nullability and tag comma normalization blockers; they do not replace the historical CLI results above.

Current compatibility decisions: The user resolved both compatibility blockers: when no series exists, hide and ignore Calibre's internally retained index; it is not a save failure. Assigning a new series explicitly defaults to 1 unless edited. Individual tag names may not contain commas; validation must prevent saving them and explain that Calibre treats commas as separators. Application implementation and acceptance remain open; these decisions do not mark tests complete. Historical CLI/API findings are preserved as evidence of Calibre behaviour.
