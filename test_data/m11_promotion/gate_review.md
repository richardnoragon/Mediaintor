# M11-G final review and closure

**M11 COMPLETE; M11-G PASSED / CLOSED.** All M11-01–M11-07 tasks are complete. Correct-installation owner acceptance is corroborated by stored results. No minimum duration, publication or new feature development is implied.

Everyday launcher: **Media-inator Everyday (M11)**.
Installation: `../Mediaintor-M11-Everyday/`, Compose project `mediainator-m11`.
Accepted unchanged build: `0.1.0a1-a3a4679f39f4c255`.
Archive SHA-256: `edc96793ca09a37db7a15bbd1036db96f2c771cff43b16563796590a8805b1f4`.

| Criterion | Evidence |
| --- | --- |
| Installation and package | Explicit isolated installation, package smoke and inventory validation; final archive/inventory checks passed. No rebuild or application-code changes. |
| KDE launch/restart | Owner repeated checks using the correct M11 launcher after identifying an RC1 window; restart and named-workspace restore confirmed. |
| Preservation and baseline | Verified independent copy of current M10 with 101 books, 121 formats, 101 covers and three resume records. User state byte-identical at promotion; owner explicitly chose this backed-up baseline after source-history discrepancy. |
| Workspace | M11 Everyday saved in workspaces.json and owner confirms restoration after restart. |
| Import/reading/editing | Imported M11 Acceptance is now book 102 with a valid EPUB; original source hash unchanged; owner confirms reading. M11 Verified tag and successful metadata Activity record were verified on The Time Machine, rather than the import fixture. |
| Bulk/revert | Completed two-book Add Tags and linked Revert journals verified; database tags on Persuasion and Peter Pan match the original pre-batch values. |
| Recovery/history | Seeded Quick Start Guide draft was explicitly saved; tag persisted, recovery index is recovered, zero unresolved recovery records remain. Owner confirms restart/history retention. |
| Backup and fallback | Verified source and installed snapshots, isolated restore/fallback data checks and package smoke. This is snapshot fallback with the same accepted build, not an in-place downgrade. Active state and accepted source were not overwritten. |
| Cleanup | Retain-all decision followed. No books, workspaces or history deleted; temporary bulk tag reverted through supported UI. |
| Isolation | Final M10 source-file hashes match the promotion backup. RC1/M9 were not modified by promotion; M10 remains intact. |

Evidence: [promotion/restore results](promotion_results.json), [owner acceptance and intermediate checks](desktop_acceptance.json), [final stored integrity](final_integrity.json), [baseline decision](source_discrepancy.json), [cleanup review](cleanup_review.md), [rollback instructions](rollback_procedure.md).

## Known limitations and retained scope

- Personal everyday use of a copied local test library only. NAS, multi-user support, external testers and publication remain excluded.
- Use the explicitly named M11 launcher. Generic Hub window titles can make RC1 and M11 look similar. Do not infer the active installation from the generic title alone.
- Recovery Review / Retry once reported that current metadata could not be read. Closing the metadata editor, waiting for Library loaded and retrying succeeded without losing the draft. A refresh/editor handoff is a possible cause, not proven. Retain this usability issue for later investigation; no forced workaround or data deletion was used.
- Historical acceptance records were not reconstructed. The owner chose the current backed-up baseline, and fresh M11 checks were verified directly.
- Existing Calibre compatibility, closed-reader requirements and private-copy browsing restrictions remain.
- Backups predate later M11 acceptance edits/imports. Before a future rollback, close applications and create a fresh verified backup of current state. Never overwrite newer state with these older snapshots.
- M7 observation remains independent. The application was left open at the owner's request; closure review was read-only and did not create a live backup.

Next: continue personal use or define M12 separately. Nothing was published, no accepted installation was removed, and no further scope is automatically authorized by gate closure.
