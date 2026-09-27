# M13 — Clearer Everyday Workflows

Status: **M13-G CLOSED — accepted 2026-09-24; M13-01–M13-08 complete.** [Final acceptance evidence](test_data/m13_workflows/final_acceptance.md). Acceptance criteria unchanged. Owner-authorized M13 Everyday promotion completed; M12 is stopped and retained as Rollback. [Promotion evidence](test_data/m13_workflows/promotion.md).

## Goal

Reduce uncertainty through specific action labels, visible operation states, clear batch selection and instructions matching the actual UI. Priority order is the order below.

## Approved scope

1. Specific action labels: identify the action and context, for example Open recovery draft, Close history and Close editor. Review recovery/import/bulk/history controls for ambiguous duplicate labels without changing the underlying protection or save semantics.
2. Clear operation states: consistently distinguish Preview, Running, Completed, Failed and Interrupted in relevant titles, dialogs and messages. Do not claim completion before verified results. Preserve accurate partial-result counts and distinguish cancellation before writes from interruption after writes.
3. Safer batch selection: make the selected batch, newly completed batch and proposed revert target explicit. Select the newly completed batch by default; keep preview, per-book review and confirmation before any revert writes. Handle interrupted, failed and no-change outcomes without silently selecting a different target during review.
4. Simpler instructions: describe the actual visible controls and file-picker workflow. Use concise contextual help and instructions that identify the window and action. Validate paste-path and folder-navigation guidance; investigate direct typing before calling it unsupported.

Approved layout: **New Bulk Edit** and **Batch History** tabs, each with a dedicated preview/result area. Completed reverts select their new record; original/revert navigation is bidirectional and read-only. Partial reverts never imply all original changes were undone.

## Boundaries

No new catalog capabilities, book/file deletion, NAS integration, additional modules, broad Hub expansion, publication or external tester program. At M13 approval, M14/M15 were provisional. M14 scope is now approved in its separate milestone; M15 remains provisional.

Keep M12 package, deployment and working data separate from M13. Normal everyday use may change M12 user data; “frozen” means its accepted software/deployment is not modified by M13 development. Create an independent M13 installation from a quiet copied snapshot, including independent library, settings, recovery/history, backups and launcher. Never use shared writable M12 paths for M13 tests. Do not clean up copied records without review/authorization.

## Actionable work plan

| Task | Status | Deliverable |
| --- | --- | --- |
| M13-01 UI inventory and technical design | COMPLETE — [inventory](test_data/m13_workflows/control_inventory.md) and [approved technical design](technical_design_m13.md) | Map current controls to specific labels; define state transitions, selected-batch behavior and screenshot-based acceptance scenarios. |
| M13-02 isolated setup | COMPLETE — [evidence](test_data/m13_workflows/implementation.md) | Quiet backup and independent M13 installation/data/launcher, verified source preservation. |
| M13-03 specific action labels | COMPLETE — automated and owner KDE verification passed | Implement contextual recovery/history/editor/import/bulk labels and help; keep action semantics intact. |
| M13-04 operation-state feedback | COMPLETE — automated and owner KDE verification passed | Accurate titles and messages throughout preview, execution, cancellation, failure and completion. |
| M13-05 batch-selection clarity | COMPLETE — automated and owner KDE verification passed | Correct completed-batch selection and explicit revert target; no automatic writes. |
| M13-06 instructions and regression | COMPLETE — automated and owner KDE verification passed | Match help to actual dialogs; targeted tests plus existing save/recovery/import/revert/workspace regression. |
| M13-07 package and installed verification | COMPLETE — [evidence](test_data/m13_workflows/implementation.md) | Verify an isolated installed candidate, artifact identity and preserved data. |
| M13-08 KDE acceptance and gate review | COMPLETE — [checklist](test_data/m13_workflows/desktop_acceptance.md) | Owner tests actual workflows; reconcile persisted results and limitations before closure. |

## M13-G acceptance

- [x] Action labels make their purpose and affected context clear.
- [x] Titles/messages reflect actual operation state and verified results.
- [x] Selected batch and revert target are explicit; the completed batch is selected appropriately.
- [x] Instructions match the installed UI and file picker.
- [x] Save, recovery, import, bulk/revert, workspace and history protections pass regression.
- [x] Independent installation and copied data preserve accepted M12 and M11.
- [x] Targeted tests, installed-package verification and personal KDE acceptance pass.

No minimum duration. No publication requirement. Acceptance does not automatically replace the everyday installation; any later M13 promotion is a separate decision.
