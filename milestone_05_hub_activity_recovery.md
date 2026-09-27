# Milestone 05 — Hub Activity & Recovery

Status: Scope definition COMPLETE and APPROVED; all three behavioral clarifications are confirmed. M5-01 technical design and M5-02 disposable protocol validation are DONE. All 31 protocol/capability checks passed; original-library hashes unchanged. M5-03 production activity/recovery storage and operation integration are DONE (85 unit/UI tests and 14 disposable integration checks passed). M5-04 Activity panel/history/startup summary is DONE (93 unit/UI tests passed). M5-05 shared recovery actions are DONE (119 unit/UI tests and 13 disposable integration checks passed). M5-06 automatic emergency preservation/close handling is DONE (143 unit/UI tests and 14 real disposable checks passed). M5-07 is DONE: 147 unit/UI tests, 21 application checks and two isolated KWin scenarios passed; desktop acceptance is user-confirmed, including successful close and restart recovery without automatic writes. **M5 COMPLETE; M5-G PASSED / CLOSED.** M1–M4 remain complete.

## Boundary and tracked operations

Provide persistent activity history, interruption awareness, manual retry and emergency preservation of unsaved single-book edits for Book-inator, one profile and one device.

Include ebook imports, single-book metadata saves, bulk edits, batch reverts and supported operations that write, modify, restore or discard user data. This is activity coverage for existing/in-scope operations, not authorization to add new file-management or backup features.

Exclude successful automatic catalog refreshes, successful background maintenance and successful reader launches by default. Record catalog-refresh failure/interruption. Record reader-launch failure/interruption only for Book-inator-owned launch attempts where useful recovery guidance exists. Track recoverable, user-impacting work rather than general telemetry. Exclude successful routine settings saves, including position, size, theme, layout and other preference updates. Include only settings-save failures requiring user awareness or action. Activity records operational work and actionable failures, not successful housekeeping.

Defer multi-profile support, multi-device synchronization, cloud recovery, scheduled backups, cross-device activity sharing, additional modules, automatic job resumption, external-reader ownership beyond Book-inator's direct involvement, movable/resizable widgets and custom dashboard layouts. These are exclusions, consistent with the user's final milestone definition, not M5-G deliverables.

## Hub presentation and history

Provide an Activity panel on the Hub, visible by default, with expand/collapse and **View Full History**. Group by module and operation, scoped to the owning profile/device and library where applicable. Preserve the previously agreed latest success and latest actual failure per category, with detailed links. Interrupted work is distinct from failure and must not replace the last actual failure.

Details include time, operation, affected items, completed/unfinished counts, errors, recovery availability and suggested next steps as applicable. Show pending, failed and recovery-required counts. Overall activity count must count distinct operations rather than counting the same task repeatedly because it has several indicators.

At startup show one recovery summary with **Open Activity / Review Recovery / Dismiss**. Do not automatically open multiple dialogs, start retry flows, launch readers or resume jobs. Use non-blocking notices for failures/interruption.

## Explicit recovery actions

| Action | Required behavior |
| --- | --- |
| Retry | Reconstruct the original operation and open its normal review/editor/preview. Retain all validation and confirmation. Require another explicit action before a write; previous confirmations are invalid. |
| Dismiss | Hide unfinished work from the active list; retain history, recovery state and retry availability through history. |
| Discard Pending | Abandon unfinished work and remove its retry option; preserve committed results and audit/history. Confirm: “Pending work cannot be resumed after discard.” |
| Delete History | Delete the activity record and associated stored state after confirmation; explain loss of review/recovery/revert capability. Unavailable while recovery state is unresolved. Require Review Recovery, then a separate explicit Discard Pending before deletion; successfully recovered/resolved records may be deleted normally. No combined Discard and Delete action. |

Retain history indefinitely until explicit deletion. Preserve M3/M4 verified partial results and reconcile uncertain writes before retry; no blind replay, rollback of successful fields or automatic resumption. M4 revert lineage and original/revert records must remain understandable through the shared history. Activity should reference existing operation journals rather than present duplicate independently executable tasks.

History-deletion warning: “Deleting this history entry may permanently remove the ability to review or revert this operation.” Discard confirmation must explain loss of any preserved unsaved edits; history deletion is enabled only after unresolved recovery state is cleared.

## Emergency single-book-edit preservation

Include emergency preservation after a normal save fails and the user's retry also fails. Preserve only outstanding unsaved edits, with identity and comparison information needed for safe recovery; successful fields remain committed. Pending cover bytes must be preserved if necessary to recover an unsaved replacement. This is not a library export or full backup.

Store managed recovery copies under **Application Data / Recovery / Single Book Edits**, outside the Calibre library and normal exports. Retain unresolved copies until successfully recovered or explicitly discarded after review. Confirmed history deletion may remove remaining associated stored state only once recovery is resolved. If creation fails, offer **Preserve Elsewhere…** and keep Book-inator open with a prominent explanation of unpreserved edits. Never claim a catalog save succeeded merely because an emergency copy succeeded.

The trigger is unrecoverable unsaved edits, not exit alone. Cover normal failed-save/retry flows, Book-inator tab closure, Hub exit and orderly application shutdown. A requested close may proceed only after verified preservation or explicit discard; no forced termination is introduced. Unexpected process death before preservation cannot be described as protected by this workflow; continuous draft autosave is not agreed.

Offer Review and recover edits for the owning profile/library. Compare recovered values with current Calibre values; require user conflict choices and explicit Save. Recovering edits and viewing a recovery copy must not automatically write to Calibre. After verified emergency preservation, automatically complete an already-requested tab close, Hub exit or orderly shutdown. Record a truthful recovery-success banner in Activity; briefly show the preservation notice before exit and retain a recovery notice for next launch. If no close was requested, keep the editor open so the user can inspect, edit or retry. Preservation satisfies protection of the captured unsaved edits, not a normal catalog save or protection of subsequent edits.

## Implementation passes

| ID | Status | Deliverable |
| --- | --- | --- |
| M5-01 | DONE — technical design | Product decisions and existing journal/editor integration contracts mapped in the technical design |
| M5-02 | DONE — 31 protocol checks passed | Verify durable recovery payloads, partial saves, conflict recovery, failure/alternate-location paths and history deletion on disposable data |
| M5-03 | DONE — production integration verified | Shared activity model, stable ownership/identity and import/save/bulk/revert integrations |
| M5-04 | DONE — 93 unit/UI tests passed | Default Hub panel, grouping, counts, details, full history and startup summary |
| M5-05 | DONE — production actions and safeguards verified | Review-based Retry, Dismiss, Discard Pending and confirmed Delete History |
| M5-06 | DONE — preservation and close coordination verified | Emergency unsaved-edit preservation and reviewed recovery, including tab/Hub close handling |
| M5-07 | DONE — automated checks passed; desktop acceptance user-confirmed | Restart/fault/scale checks, M1–M4 regressions, help/release notes and desktop acceptance |

## M5-G acceptance gate

All criteria passed: [final evidence review](test_data/m5_acceptance/gate_review.md). Earlier implementation checkpoints below describe historical stages.

- [x] M5-G01: Scope/clarifications agreed; tracked operations and exclusions verified, including actionable settings-save failures and exclusion of successful routine preference saves.
- [x] M5-G02: Default collapsible Hub Activity panel and full history show module/operation grouping and detailed outcomes.
- [x] M5-G03: Latest success/failure and pending/failed/recovery counts are accurate; interruptions remain distinct.
- [x] M5-G04: Retry restores normal review and requires fresh validation/confirmation before any write.
- [x] M5-G05: Dismiss preserves recovery/history/retry; Discard Pending confirms loss of resumption and retains committed results/history.
- [x] M5-G06: History persists across restart without expiry; Delete History is unavailable for unresolved recovery until separate review/discard; resolved records require deletion confirmation and preserve the agreed revert-lineage rules.
- [x] M5-G07: Startup provides one recovery summary; no automatic jobs, readers or cascades of dialogs.
- [x] M5-G08: Failed Save then failed Retry preserves only unsaved single-book edits durably, including pending cover changes where needed.
- [x] M5-G09: Successful preservation automatically completes an already-requested tab/Hub/orderly close, but leaves ordinary editing open; preservation failure keeps the app open and offers an alternate location.
- [x] M5-G10: Recovery respects book/library/profile identity, detects current-value conflicts, and requires explicit review/save; completed fields remain committed.
- [x] M5-G11: Disposable fault/restart/partial-result and M1–M4 regression checks pass; user confirms desktop workflows and docs/help/release notes are current.

## Confirmed scope closure

All three recommendations are user-approved:

1. Verified emergency preservation automatically completes an already-requested close, with truthful Activity/exit/startup notices; otherwise the editor remains open.
2. Unresolved recovery must be reviewed and explicitly discarded before Delete History becomes available. Resolved records may be deleted after normal confirmation. No combined discard-and-delete shortcut.
3. Routine successful preference/configuration writes are excluded from Activity; actionable settings-save failures are included.

No product-scope clarification remains. M5-01 and M5-02 are complete. M5-03 production integration and book-review-state migration are complete. M5-04 Hub Activity panel, full history and startup summary are complete. M5-05 shared recovery actions are complete. M5-06 automatic emergency preservation and close handling are complete. M5-07 automated application/KWin checks and user desktop acceptance are complete; the final evidence review passes all 11 criteria. M5 is COMPLETE and M5-G is PASSED / CLOSED.

Links: [implementation plan](implementation_plan_hub_bookinator.md), [release scope](first_release_scope.md), [hub constitution](mediaintor%20hub/constitution_hub.md), [completed M4](milestone_04_bulk_metadata_editing.md).

## Technical design and disposable validation checkpoint

[Technical design](technical_design_m5.md) maps current journals, editor drafts, startup routing, settings failures, durable emergency copies, close intent, and guarded deletion. [M5-02 validation](test_data/m5_validation/README.md) passed 31 checks on a fresh 101-book disposable copy, including real partial saves/conflicts and a candidate storage/recovery protocol. Original-library hashes and ebook contents were preserved. The prototype lives only in `test_data/m5_validation/`; no application code changed.

M5-03 removed automatic startup import-dialog opening and separated book-review status from import history. M5-04 now provides the Activity UI and single startup summary. M5-05 now supplies shared recovery/cleanup controls. M5-06 now implements emergency close coordination. Final application acceptance remains M5-07 work. All M5-G criteria remain unchecked until application evidence exists.

## M5-03 production integration checkpoint

[85 unit/UI tests and 14 disposable production checks](test_data/m5_03_integration/README.md) passed, with original-library hashes unchanged. Activity storage, operation/attempt recording, recovery payload/registration/discovery, explicit editor-preservation and conflict-review APIs, and independent book-review migration are implemented. Successful preference saves remain unlogged. No automatic emergency preservation or close continuation is enabled yet; those remain M5-06. M5-G remains OPEN pending the remaining application features and acceptance.

## M5-04 presentation checkpoint

The default collapsible Hub Activity panel, module/operation grouping, distinct attention counts, latest success/actual failure details, full attempt history and one non-modal recovery summary are implemented. The summary stays visible above module tabs; local journals are discovered even with Book-inator closed. Summary Dismiss hides only this session’s banner, retaining all pending work. Review Recovery opens unresolved history for inspection; shared retry/discard/delete routing remains M5-05. [Verification](test_data/m5_04_activity/README.md): 93 unit/UI tests passed, with isolated temporary stores and offscreen rendering. M5-G remains OPEN; no final desktop acceptance is claimed.

## M5-05 completion checkpoint

M5-05 is DONE/CLOSED for its agreed implementation scope. Activity details expose Review / Retry, Dismiss, guarded Discard Pending and separately confirmed Delete History. Review opens the selected import/bulk journal or reconstructs a single-book draft with identity/conflict checks. No catalog writes occur until a new explicit confirmation/Save. Discard requires review of the current record revision; uncertain writes must first be reconciled. Deletion is disabled for unresolved recovery and uses durable cleanup intents, verified owned-file deletion and retained deletion markers. Interrupted cleanup stays visible and can be explicitly retried after restart. Book-review flags and separate revert descendants survive history cleanup.

[Verification](test_data/m5_05_actions/README.md): 119 unit/UI tests and 13 real-Calibre checks on a fresh disposable copy passed. No original library was used; the disposable seed was unchanged. Automatic emergency preservation/close continuation remain M5-06; final application acceptance remains M5-07. **M5-G remains OPEN.**

## M5-06 completion checkpoint

M5-06 is DONE for its implementation scope. A failed Save followed by a failed explicit Retry automatically preserves the remaining valid draft. Successful fields stay committed. Ordinary editing remains open with a truthful preservation notice; an already-requested editor/tab/Hub close continues after durable registration and current-revision verification. Failure keeps the draft open and offers Preserve Elsewhere; cancelling or keeping editing leaves no latent close request. Invalid input and cancelled conflict review are not counted as failed writes. Existing task/reader and settings-save safeguards still apply.

[Evidence](test_data/m5_06_emergency/README.md): 143 unit/UI tests and 14 real-Calibre checks on a fresh disposable copy passed. The valid-image/blocked-backup test verified actual partial-save failure, preservation of only the failed cover, automatic requested close, and restart discovery without replay. Cooperative desktop shutdown is wired to Qt session management and unit-tested; actual KDE/session behavior and complete desktop acceptance remain M5-07. **M5-G remains OPEN.**

## M5-07 acceptance checkpoint

[Acceptance evidence and desktop checklist](test_data/m5_acceptance/README.md): 147 unit/UI tests and 21 checks on a fresh 101-book disposable copy passed; a 1,000-operation/4,000-attempt history rendered successfully. Two isolated real KWin 6.6.6 Wayland scenarios passed (Cancel retains work; Save/Retry/preservation closes without duplicate prompts). The duplicate editor-close prompt found during KDE testing is fixed and regression-tested. Human Activity/history, recovery Save and discard/delete checks are confirmed. The user accepts isolated KWin evidence as sufficient; successful close and restart recovery without automatic editor opening or cover application are user-confirmed. A host logout/poweroff was not performed. **M5 is COMPLETE and M5-G is PASSED / CLOSED**, following the requested final evidence review.
