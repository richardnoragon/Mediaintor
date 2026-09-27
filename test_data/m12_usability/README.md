# M12 usability/reliability evidence

**M12 COMPLETE; M12-G PASSED / CLOSED (2026-09-23).** Accepted build `0.1.0a1-f59e8af9b043f304`. [Final review](gate_review.md), [saved-data verification](final_saved_data.json). M11 unchanged; no promotion/publication.

The entries below are chronological history; earlier pending/open statuses are superseded by the final review.

**Final scope approved; M12-G OPEN.** [Milestone plan](../../milestone_12_everyday_usability_reliability.md).

M12-01 complete: [technical design](../../technical_design_m12.md), [reproduction results](recovery_reproduction.json), [script](reproduce_recovery_handoff.py), [log](recovery_reproduction.log). Removal scope approved: test existing tag, cover, workspace and eligible-history actions; book/file deletion, library item destruction and recycle-bin workflows are excluded. Actual revert outcome counts are approved; no-change cancellation wording is permitted only when no writes occurred. M12-G acceptance and working-installation promotion are separate decisions. No scope questions remain. Controlled reproduction passed using real UI control flow with simulated loader/metadata I/O. No production fix or real-library acceptance claimed.

Next: M12-02 isolated setup, then M12-03 recovery implementation. M11 remains unchanged as the stable reference.

**M12-02 complete; M12-03–M12-06 source implementation and 220-test regression complete.** [Implementation/evidence](implementation.md), [setup](setup.json). M12 still has the copied stable package; new source is not installed. Next: M12-07 package verification, then M12-08 KDE acceptance. M12-G remains open; M11 unchanged.

**M12-07 complete:** [package review](package_review.md), nine isolation checks including 61 installed test executions; candidate `0.1.0a1-16e57f586750466b` installed in M12 only. M12-08 owner KDE acceptance is next. Earlier not-installed statements are historical. M11 unchanged; promotion remains separate.

M12-08 acceptance issue: owner reports preserved draft only appears on second Review / Retry attempt in M12. First-click acceptance failed despite isolated tests. Awaiting exact first-attempt behavior/message; M12-G remains open, no promotion.

Current candidate supersedes the initial package: [KDE focus fix](focus_fix.md), build `0.1.0a1-254fe2288bf7b39a`. Installed checks passed; first-click recovery visibility must be retested on KDE. M12-G remains open.

## Workspace feedback correction

See [verification and next steps](workspace_feedback_fix.md). Replacement build `0.1.0a1-f59e8af9b043f304` is verified but not installed. M12-G remains open; M11 unchanged.

## Replacement installation completed

Owner confirmed normal shutdown. Build `0.1.0a1-f59e8af9b043f304` installed; backup verified, 459 retained files unchanged, runtime inventory and package smoke passed. M12 launched for KDE workspace feedback retest. See `installed_workspace_candidate.json`. M12-G open; M11 unchanged.

Personal KDE retest passed: owner confirmed and screenshot shows “Workspace restored.” after restoring the copied M11 Everyday workspace on build `0.1.0a1-f59e8af9b043f304`. Misleading workspace feedback issue resolved. Remaining M12 acceptance and final gate review stay open; M11 unchanged.

## Current acceptance review

Bulk preview/cancellation and actual tag-add/revert passed on KDE and are corroborated by persisted journals. Recovery index is recovered. See [remaining checks](remaining_acceptance.md). M12-G stays open.

## Everyday promotion

Owner-authorized promotion complete. Use **Media-inator Everyday (M12)**; [promotion evidence](promotion.md). Current data retained; accepted package unchanged; M11 unchanged. M13 scope approved separately.
