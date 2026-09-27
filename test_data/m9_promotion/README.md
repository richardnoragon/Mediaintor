# M9 test-environment promotion

Current status: **M9 COMPLETE; M9-G PASSED / CLOSED.** All three personal desktop checks confirmed. [Final evidence review](gate_review.md). Earlier pending checkpoints below are historical.

Status: **M9-G OPEN.** Owner revised the library choice: use a suitable existing testing library, creating a new one only if necessary. Calibre use is restricted to test scenarios against the test/validation library in the testing environment. No NAS library is requested for this milestone.

Selected source: `../Mediaintor-M8-Development/active/library`. Read-only checks found a healthy SQLite database, 101 books and all 121 format paths present. No new empty library is needed. [Inventory](source_inventory.json).

M8 Development remains the authoritative source of settings/positions/history. Use a fresh separate M9 copy; do not repurpose or modify the active source. Exclude Installed Acceptance data. Preserve matched records and report unmatched ones. Before backup/copy, establish that source writers are closed; this inventory alone does not establish snapshot consistency.

Next: prepare version-specific backups and a separate M9 validation copy, then install the accepted M8 package using the approved Docker/native KDE workflow. RC1 and prior environments remain unchanged. NAS access, live-library deployment and publication are outside the revised scope.

## Backup, copy and installation completed

- Verified no running Docker containers, Calibre or ebook viewers; remaining Python processes were unrelated desktop/editor tools.
- Created verified pre-upgrade backup at `../Mediaintor-M9-Validation/backups/pre-upgrade-c08faf149723f3c0/` and restored it to separate `active/` using the previously verified backup/restore utility.
- Installed exact accepted M8 build `0.1.0a1-184039712b870efd`; archive SHA-256 `a649ebab6fe334929cc2e42e15ab998710cf5bdcc776d24242de4bccd3d96b14`. Pinned existing Docker runtime image; no RC1 rebuild or retag.
- Installed inventory and packaged offscreen startup passed. Library quick_check OK: 101 books, 121 formats, UUID unchanged.
- Post-install comparison: source matches backup, M9 library/import sources unchanged, all home changes confined to installer/program/launcher-owned paths. User configuration, viewer positions and history bytes retained. Internal library/home paths remain unchanged; no acceptance-test records imported.
- Added dedicated **Media-inator M9 Validation** KDE entry; syntax validated. No interactive M9 Hub launched by this step.

[Machine-readable evidence](preparation.json). Data byte retention is not final functional recovery acceptance. Remaining: identity/provenance review, personal desktop workflows, rollback into a separate snapshot and final M9-G review. M9-G remains open. RC1 and M8 source installations remain unchanged.

## Functional migration and isolated rollback results

[Results](migration_rollback_results.json): accepted installed build read valid settings, matching library UUID, 101 books and 121 existing format paths, plus three valid viewer resume records. Source import/bulk/Activity/recovery counts are all zero, explicitly recorded rather than claiming nonexistent history migrated. Synthetic recovery preservation, restart discovery and draft review passed on `functional-check`; database bytes did not change and no pending work auto-applied.

A post-upgrade snapshot was created. Separate `rollback-check` restored the old snapshot, passed old-build startup, then passed upgrade and startup back to the accepted M8 build. M9 active state, the M8 source and rollback-library bytes were unchanged by these tests. [Rollback procedure](rollback_procedure.md). No RC1 mutation.

Personal KDE checks requested: menu launch/three-format reading; metadata edit and previewed import; restart preserving results/history without auto-resume. A new original EPUB fixture was intentionally added only to M9 import-sources after automated comparisons. [Pending desktop record](desktop_acceptance.json). M9-G remains open until those checks and final review pass.
