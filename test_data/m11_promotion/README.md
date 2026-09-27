# M11 personal everyday promotion evidence

**M11 COMPLETE; M11-G PASSED / CLOSED.** [Final gate review](gate_review.md). Owner acceptance on the correct installation is corroborated by [persisted results](final_integrity.json). Earlier progress notes below are historical.

- [Milestone plan](../../milestone_11_personal_everyday_promotion.md)
- [Promotion and verification results](promotion_results.json)
- [Source-state discrepancy](source_discrepancy.json)
- [Preservation/cleanup review](cleanup_review.md): retain every item; no deletion authorized or performed.
- [Backup/fallback procedure](rollback_procedure.md)

Separate root: `../Mediaintor-M11-Everyday/`; Compose project `mediainator-m11`.
Dedicated launcher created: **Media-inator Everyday (M11)**. Native KDE owner acceptance has not started.
Exact accepted build: `0.1.0a1-a3a4679f39f4c255`; no application changes or rebuild.

Verified: 101 books, 121 format paths, 101 covers, three resume records, Last Session, no named workspaces, one Activity record and one unresolved recovery. SQLite integrity and available library/book ownership references passed. User files match M10 byte-for-byte. Source/deployment hashes remained unchanged; restore tests did not modify active M11.

The absence of named workspaces/import/bulk history and the unresolved recovery differs from earlier owner-confirmed M10 acceptance. This is not evidence of loss during copying: the same state exists in the source and backup. The owner has now chosen this preserved state explicitly. Repeat acceptance and verify persisted results; do not invent historical records.

RC1/M9/M10 unchanged; nothing published. Next: launch M11 and complete fresh personal KDE acceptance with persisted-result checks, then final review.

Investigation update: [workspace-location audit](workspace_location_audit.json) and [library-location audit](library_location_audit.json) found no alternate accepted state in known locations. The lone import JSON is review state, not a batch. The unresolved recovery matches the deliberately seeded fixture. No copy loss was found. Owner choice pending: adopt the preserved M11 baseline and repeat affected checks, or identify another source.

Baseline decision: owner explicitly chose to keep the current backed-up M11 copy. All records retained; M11-G remains open.

Missing Workspaces menu investigation: screenshot showed older UI; Docker confirmed RC1 running and M11 stopped. The current test was viewing RC1. Open the dedicated M11 launcher and repeat; no conclusion about all historical checks is inferred. RC1 is unchanged.

Correct-installation retest: M11 Everyday was verified in M11 workspaces.json; owner then confirmed KDE restart and restoration of Book-inator/selected book. Workspace/restart acceptance passed. Remaining workflow checks and final persisted-result review are pending.

Final state: 102 books; M11 Everyday workspace saved; original import source preserved; metadata tag verified on The Time Machine; bulk tag reverted on both books; recovery resolved with no unresolved records. Use **Media-inator Everyday (M11)**. No application rebuild/publication; accepted source environments retained.
