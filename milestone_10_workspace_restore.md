# M10 — Hub Workspace Save and Restore

Status: **M10 COMPLETE; M10-G PASSED / CLOSED.** M10-01–M10-07 complete, including installed KDE owner acceptance and [final evidence review](test_data/m10_workspaces/gate_review.md).

## Objective

Save and restore existing Hub layout and context without adding windowing models, media modules or external-reader restoration. Keep accepted M9 unchanged; use a separate M10 installation, configuration and copied test library. No NAS/live-library access or publication.

## Approved behavior

- Automatically save/restore Last Session; default startup restores Last Session.
- Up to five user-named workspaces, with explicit Save, Restore, Rename, Overwrite and Delete actions.
- Workspace captures open modules, active module/tab, existing supported arrangement, window size/position and selected book if available.
- Optional startup selection of a named workspace. Named snapshots change only through explicit saves; automatic Last Session updates remain separate.
- Search/filter preferences remain shared and continue their existing persistence; workspace operations must not snapshot, reset or overwrite them.
- Restore Hub/modules only. Never launch Calibre Viewer or restore external reading position/application state as a workspace action.
- Before switching/restoring with unsaved edits, offer Save / Discard / Cancel. Continue only after successful save or explicit discard. Cancel leaves the current workspace intact; failed/partial saves must not silently discard remaining edits.
- If saved displays are unavailable, keep windows on an available display, visible and usable, preserving supported layout as closely as possible.
- Preserve module selection from before application shutdown; shutting down must not save a falsely empty Last Session.

## Existing implementation boundary

Current Hub uses a QTabWidget with Hub and Book-inator tabs and saved top-level geometry. No module docking/floating-window model is present in the inspected implementation. M10 persists this existing arrangement; it does not introduce movable docks or separate module windows. Active-tab restoration and named-workspace management are new M10 work. Future modules/windowing remain deferred.

## Final behavior decisions

1. At five named workspaces, creating a sixth presents the existing names and requires the user to select a replacement, with Replace / Cancel. Cancel leaves all workspaces unchanged. This explicitly supersedes automatic oldest-state replacement. Retain the existing startup fallback: replacing a startup-selected state reverts startup to Last Session.
2. If the restored selected book is hidden by shared filters, preserve the selection context and filters, explain why the book is hidden, and offer Clear All Filters or Keep Filters. Clear All is an explicit user action using the existing shared preference behavior. Missing books must not prevent restoring the remaining workspace.
3. Block workspace switching/restoration during critical operations, including imports, metadata/bulk writes, database updates or file operations. Explain the active operation and ask the user to wait; do not interrupt or silently queue a restore. Existing external readers remain untouched: no launch, close, reposition or reading-position restore as an incidental workspace action. Existing module-close protection still applies, and must not be bypassed to force restoration.

## Work plan

| Task | Status | Deliverable |
| --- | --- | --- |
| M10-01 | COMPLETE — technical design recorded | Final behavior approved; define workspace schema, atomic persistence and acceptance fixtures. |
| M10-02 | COMPLETE — verified isolated baseline and startup smoke | Prepare isolated M10 installation/data and verify accepted M9 remains unchanged. |
| M10-03 | COMPLETE — [implementation and 192-test regression](test_data/m10_workspaces/m10_03.md) | Implement validated atomic workspace storage, five-state management and explicit snapshot semantics. |
| M10-04 | COMPLETE — [core integration and tests](test_data/m10_workspaces/m10_04.md) | Implement restore/startup/Last Session with active tab, open modules, geometry and stable selected-book identity. |
| M10-05 | COMPLETE — [failure-path implementation and automated checks](test_data/m10_workspaces/m10_05.md); KDE acceptance completed in M10-07 | Integrate unsaved-edit review, busy-task handling, missing-book and unavailable-screen fallback. |
| M10-06 | COMPLETE — [review, 215 regression tests and isolated package verification](test_data/m10_workspaces/m10_06.md) | Run targeted and M9 regression tests on disposable data; update help and limitations. |
| M10-07 | COMPLETE — [installed KDE acceptance and final review](test_data/m10_workspaces/gate_review.md) | Verify installed KDE behavior and review all M10-G evidence. |

## M10-G acceptance

- [x] Save and restore the supported layout/context accurately.
- [x] Last Session restores on restart without overwriting named snapshots.
- [x] Five named workspaces support rename, explicit overwrite and deletion; approved capacity/startup fallback policy works.
- [x] Named-startup selection works; existing search/filter preferences remain untouched by workspace restoration.
- [x] Save / Discard / Cancel protects unsaved work and handles failures without switching prematurely.
- [x] Unavailable monitors cannot strand windows off screen; remaining geometry is usable.
- [x] Missing/filtered selected books and busy-task/reader scenarios follow approved rules; no external reader auto-launch.
- [x] M9 regression checks pass; corrupt/missing workspace data is handled without destroying valid state.
- [x] Separate M10 installation remains isolated from M9; owner KDE acceptance and final review recorded.

Acceptance depends on test results and owner confirmation, with **no minimum duration**. All criteria are evidenced in the final gate review. No publication is implied.
