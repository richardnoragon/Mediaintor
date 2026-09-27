# M5-02 — Disposable recovery protocol validation

Current disposition: **M5 COMPLETE; M5-G PASSED / CLOSED**. [Final gate review](../m5_acceptance/gate_review.md). The stage status and remaining-work notes below record the state at that earlier verification.

Status: **M5-02 protocol validation PASSED — 31 checks**, with original-library hashes unchanged. See [results](results.json) and [individual checks](checks.json). This is candidate-protocol and Calibre-capability evidence, **not M5 application acceptance**. The Activity UI, application close coordinator and production recovery store are not implemented by this experiment. M5-G remains OPEN / NOT RUN.

## Method

`verify.py` obtains Calibre's real global database lock, checks for running Calibre/readers, creates a fresh coherent snapshot of the existing 101-book library, and copies it to a marked disposable library. All Calibre writes target that disposable copy. The helper's nested lock acquisition is patched only because the outer real lock is already held for the entire experiment; library/book checks and actual Calibre writes/read-back remain real.

Inject failures in Calibre's tag-write method to retain a committed title while both Save and Retry fail for tags. A bounded prototype in `protocol.py` then captures only pending fields plus comparison/identity context, writes and verifies recovery envelopes and discovery registrations, reconstructs reviewed drafts, and enforces separate review/discard/deletion steps. It is not imported by the application.

The experiment checks:

- Fresh 101-book copy; partial save and failed retry; only outstanding fields preserved.
- Durable payload read-back, registration and multiple simultaneously discoverable copies.
- Previously requested close versus ordinary editing and changed draft revisions (protocol decisions, not actual window closure).
- Restart discovery without library writes; external conflicts; choosing current or recovered values; preserving unrelated title/description changes.
- Explicit recovery Save, post-review revalidation and already-committed recovery as a no-op.
- Embedded pending cover bytes independent of the selected image file and exact pending HTML.
- Failed atomic replacement, destination denial, alternate location, failed registration and prevention of false preservation success.
- Damaged/unknown-schema copies retained and rejected; mismatched profile/device/library/book identities rejected.
- Dismiss retains pending work; unresolved deletion blocked; review required before separate discard/delete.
- Import metadata-review state can be preserved independently before deleting the import journal. This exposes a required production migration, not an already-implemented migration.
- Existing bulk unresolved-history guard; ebook content and original-library hash preservation.

## Findings and implementation requirements

1. Existing metadata adapter writes support the proposed recovery flow, including fresh conflict checks on explicit recovered Save.
2. Recovery envelopes must embed pending cover data, retain field baselines, verify read-back and preserve the captured draft revision. A copy of an earlier revision cannot authorize closing newer edits.
3. A file created before registration fails must not be reported as fully registered recovery. Keep editing/closing blocked and explain the partial storage result. Alternate locations need durable discovery; a completely unwritable application data area is still an actionable failure.
4. M3 currently stores Needs Metadata Review/provenance inside deletable import history. M5 must migrate that book state safely before allowing history deletion. The prototype verifies a detached representation, not a crash-safe production migration.
5. Current startup automatically opens import recovery. M5 must replace that behavior with the single summary, and preserve existing import/bulk review and confirmation requirements.
6. Keep the real database/process access guards and current one-profile/device scope. No automatic resume, third-party force-close, library backup or continuous draft autosave is introduced.

## Reproduction

With Calibre/readers closed, from the project root:

```bash
QT_QPA_PLATFORM=offscreen CALIBRE_CONFIG_DIRECTORY=/tmp/mediainator-m5-validation-config calibre-debug -e test_data/m5_validation/verify.py
```

Use an isolated Calibre configuration. Calibre's locking socket requires execution outside a sandbox that prohibits it. The experiment checks original-library hashes after completion and stores its disposable root in the report. It preserves copies and does not delete the original library or user recovery state.

## Still required for M5-G

Implement and test production storage/schema validation, multi-record locking, crash-safe migration and cleanup, activity projection/aggregation, the Hub panel/history/startup summary, exact-operation routing, real close/retry/cancel behavior, corrupt index discovery, alternate-path unavailability and recovery of partial outcomes. Then run M1–M4 regressions and user desktop acceptance. Protocol checks alone do not pass any M5-G application criterion.

[Technical design](../../technical_design_m5.md) · [M5 milestone](../../milestone_05_hub_activity_recovery.md)
