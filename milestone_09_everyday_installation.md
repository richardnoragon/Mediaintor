# M9 — Everyday Installation and Safe Upgrade

Status: **M9 COMPLETE; M9-G PASSED / CLOSED.** Owner confirms all three desktop checks passed; final evidence reviewed. [Gate closure](test_data/m9_promotion/gate_review.md). Accepted scope is personal test/validation use, not NAS/live-library deployment. No publication.

## Approved outcome

Promote accepted M8 build `0.1.0a1-184039712b870efd` (archive SHA-256 `a649ebab6fe334929cc2e42e15ab998710cf5bdcc776d24242de4bccd3d96b14`) to a separate everyday Docker installation with native KDE windows and a dedicated menu entry. Start against a fresh copy of the selected test/validation library; NAS access and live-library deployment are outside the revised scope. Preserve settings, reading positions, recovery records and history after verifying their library/book identities and provenance.

Keep RC1, the active M8 environment and the previous everyday installation unchanged throughout M9 acceptance. Retain version-specific pre-upgrade snapshots. No new features, public release or external distribution. No minimum acceptance duration. M7's outstanding observation remains independent.

## Migration boundaries and source decisions

Latest owner decision supersedes the NAS-source plan: use a suitable existing test library, creating a new library only if none is suitable/available. Calibre will be used only in test scenarios against the test/validation library in a testing environment. No NAS path is required for this milestone.

Selected library source: `../Mediaintor-M8-Development/active/library`. Read-only suitability checks passed: SQLite quick_check OK, 101 books, all 121 format paths present. [Inventory](test_data/m9_promotion/source_inventory.json). Use a fresh M9 copy of this source; no need to create an empty library. A quiet-source backup and separate restore were verified before installation.

**Authoritative user-state source: M8 Development**, under `../Mediaintor-M8-Development/active/`. Preserve application settings, format-specific reading positions, bookmarks/annotations where available, recovery records and reading history where present, subject to verified mapping into the M9 test-library copy. Exclude M8 Installed Acceptance records entirely, including standalone disposable acceptance fixtures. Keep RC1 and the previous everyday installation available until M9-G acceptance.

Read-only installation metadata identifies the Development environment's current build as `0.1.0a1-c08faf149723f3c0`, not accepted M8 build `0.1.0a1-184039712b870efd`. This is expected from leaving active Development unchanged during acceptance. The user's choice of state source remains authoritative; install the accepted M8 package separately and verify compatibility rather than assuming the source has the newest schema. M8 Development itself began from copied test data, so its label does not prove all library-specific records belong to the selected library. Preserve unmatched records without automatically attaching or replaying them against copied books.

Inventory source installations, versions, UUIDs, paths, settings, progress, recovery/history and storage needs read-only. Shared library UUIDs in cloned test libraries alone do not prove that records should be migrated. Verify origin, book UUIDs, formats, file identity and path mappings; do not merge ambiguous records silently. Keep incompatible/ambiguous records preserved and report them for disposition.

Copy only from a quiet, consistent source after readers and writers close. Snapshot configuration/application data and the entire source library before upgrade. Record checksums and manifest metadata, check adequate free space, and verify restoration in a separate location. Re-map only the new installation's records, including path-keyed Calibre positions and recovery references. No copied pending task may automatically resume or target a source library.

## Work plan

| Task | Status | Deliverable |
| --- | --- | --- |
| M9-01 | COMPLETE | Confirm test-library and settings/history sources; inventory identity, paths, runtime, disk capacity and existing launchers. |
| M9-02 | COMPLETE | Create verified, version-specific backup snapshots and fresh library/app-data copies. Establish separate everyday and rollback validation locations. |
| M9-03 | COMPLETE | Install the exact accepted M8 package in isolated Docker/KDE deployment. Verify package/image identity and mounts; retain existing launchers unchanged. |
| M9-04 | COMPLETE | Migrate chosen settings, format-specific positions and compatible recovery/history with identity and path checks. Preserve unmatched records, with explicit dispositions. |
| M9-05 | COMPLETE | Validate menu launch, restart, reading, metadata editing, imports, bulk/revert regressions and recovery/history on the copied test library. |
| M9-06 | COMPLETE | Test rollback on a separate restored snapshot; document switching installations, retaining newer data and safe return to M8. |
| M9-07 | COMPLETE | Record owner desktop acceptance, reconcile evidence/limitations and close M9-G only when criteria pass. |

## Rollback rule

Rollback is an installation switch to a compatible version-specific data snapshot, not an in-place downgrade of newer data. Retain and label post-upgrade library/application data separately. Never silently overwrite, replay, or discard newer reading, library or recovery records. Test that the old snapshot is usable and newer data remains intact before claiming rollback verified. No backwards schema compatibility is assumed.

## M9-G acceptance

- [x] Exact accepted package installed successfully; runtime and version guards pass.
- [x] Dedicated KDE launcher opens native windows and supports restart.
- [x] Fresh test-library copy and pre-upgrade backups verified; original, RC1 and previous installations unchanged.
- [x] Chosen settings, per-format reading positions, history and recoverable work preserved or explicitly accounted for; identity/path remapping cannot target originals.
- [x] Reading/navigation/resume, editing, importing and regression workflows pass on the copied library.
- [x] Recovery/history review works; pending actions never auto-resume.
- [x] Rollback and return procedure tested with separate snapshots; newer data retained.
- [x] Owner accepts desktop results; no unresolved blocking defect; procedures and limitations current.

Passing tests and agreed acceptance criteria permit progression without a waiting period. M9-G is closed with evidence and owner acceptance recorded. Publication remains outside scope.

Installation checkpoint: [M9 backup/copy/install evidence](test_data/m9_promotion/preparation.json). Source unchanged; user data retained byte-for-byte outside installer-owned paths. Dedicated KDE launcher, functional migration, desktop acceptance and isolated rollback/return are verified; see the final gate review.
