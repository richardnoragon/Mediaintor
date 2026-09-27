# M1 library access — accepted decision

Status: **User-approved workflow; G1 integration verification passed for this scoped policy. Final M1 desktop acceptance passed.** This records the latest decision and supersedes earlier requests for clarification about the M1 read strategy. G1 evidence is in the [acceptance report](test_data/m1_acceptance/README.md); M1 is complete for its accepted scope.

## Accepted workflow

1. Browse a temporary private copy of the selected Calibre library.
2. Open selected book files from their original library locations, not from the temporary copy.
3. Require Calibre and other readers to be closed while the hub refreshes or launches a reader. Explain a detected conflict and offer Retry after the user closes it; do not terminate external applications.
4. Allow one hub-launched reader at a time in M1, as previously agreed. Keep its originating profile/module ownership when it is deliberately left open.

The selected library remains the authoritative collection. Remember its location for the profile/device. A temporary snapshot is a browsing implementation detail, not another collection, a backup, or a new ownership boundary.

## Technical and user-visible implications

- Run `calibredb list` only against the private snapshot. Obtain a coherent database copy through SQLite backup from a read-only source connection; copy the supporting book/cover files needed for Calibre's path resolution. Do not query the source catalog schema as the production metadata adapter.
- Copying requires temporary storage and time. Show loading, permit cancellation, report failure, and keep the previous successful catalog explicitly marked stale if refresh fails. An unavailable library offers Retry or choosing its location again.
- Detectable source changes while copying invalidate the snapshot. Reject symbolic links in the initial implementation; do not follow them into live data. Clean up temporary snapshots when no longer needed.
- Map selected format paths back to the original library and verify the file exists before launch. The external reader may save annotations/settings normally; catalog browsing being read-only does not imply the viewer writes nothing.
- Reader settings for actual use remain Calibre's normal settings. Isolated test configurations are validation fixtures, not the production preference default.
- Process detection is best-effort. It does not prevent another application from starting after a check, and this decision does not establish simultaneous-write safety. Do not force-close outside applications or claim that the earlier lock errors are fixed.
- The M1 restriction is on refreshing and launching. Do not silently turn it into a permanent suite restriction or a promise that all external processes can be controlled.

## Implementation and verification status

Private snapshot creation, original-path remapping, remembered-library UI, conflict detection, bounded/cancellable loading and reader review are implemented. Twenty-one automated tests pass. G1 verifies source preservation, private-copy querying, original paths, busy refusal/retry and missing-library handling. The normal entry point now enables the accepted workflow.

The full 101-book automated application run occurred after G1 passed and succeeded. The user confirmed app-launched three-format reading/navigation and hub Cancel/Close reader outcomes, completing M1 acceptance. See the [acceptance report](test_data/m1_acceptance/README.md).

The initial-keypress issue remains deferred and non-blocking. Multiple-reader contention, editing, intake and progress synchronisation remain later work; M1 must report limitations accurately.

Links: [implementation plan](implementation_plan_hub_bookinator.md), [technical design](technical_design_m1.md), [milestone](milestone_01_browse_and_read.md), [acceptance preparation](test_data/m1_acceptance/README.md).

Current milestone status: **M1 complete for the accepted scope.** G1 passed before the full 101-book application run; automated checks and final user-confirmed reader/navigation/close outcomes passed. Twenty-three automated tests pass. Known limitations and later release work remain documented in the [acceptance report](test_data/m1_acceptance/README.md). This supersedes historical pending-acceptance notes above.
