# M13 technical design — Clearer Everyday Workflows

M13-01 COMPLETE. Source inventory and technical design finalized with both owner decisions confirmed on 2026-09-23. No application code, package or working data changed. M13-G OPEN.

## Inputs and preservation rules

[Approved charter](milestone_13_clearer_everyday_workflows.md), [control inventory](test_data/m13_workflows/control_inventory.md), and [M12 evidence](test_data/m12_usability/gate_review.md). M12 Everyday remains the accepted software baseline; its current user data is not a development fixture. M13-02 creates independent copied data before implementation or desktop tests.

No journal schema migration, new writer, retry policy or automatic write is needed. Keep stable batch/recovery IDs, library/profile ownership checks, Calibre guards, conflict review, per-book exclusion, explicit confirmation, partial-result accounting, emergency preservation and history-deletion safeguards. UI labels must not be used as command identifiers.

## Confirmed owner decisions

1. Separate **New Bulk Edit** and **Batch History** tabs, each with its own dedicated preview/result area. New Bulk Edit shows selected books, edit configuration, validation, before/after preview and execution status. Batch History shows existing batch records, statuses, results/errors, review/retry and revert actions.
2. After a successful revert, automatically select the new revert record and show **Revert of: [original ID]**, with **View original batch**. The original shows linked revert records and **View revert** navigation.

Owner examples of new selection criteria/filters, history search/filtering and export tools are future layout possibilities, not added M13 capabilities. Existing catalog selection and existing journal/error details are reused. No export feature or new filtering engine is introduced.

## Labels and navigation

Use the inventory as the implementation mapping. Centralize action-label lookup by source kind for Activity; labels and guidance derive from the same mapping. Preserve internal review/dismiss/discard/delete action keys and controller dispatch. Only offer actions supported by the existing record state; for resolved recovery show details rather than claiming a draft remains available.

Startup summary dismissal, activity dismissal, local draft discard, durable recovery discard and history deletion must have distinct visible descriptions. A local editor Discard cannot be described as deleting the preserved recovery. Disabled history deletion explains that unresolved work must first be reviewed and discarded.

Keep the accepted focus handoff: hide matching history/details only once the recovered editor is ready; failed reads retain the record and show the reason. Do not add another window or automatic editor Save. Group headers cannot trigger record actions. Explicit Close history/Close details controls are added to the corresponding windows.

Book editor shows the book title plus state. Title truncation is visual only, with full title accessible in content. Labels use visible field context (authors/tags/covers) and preserve author ordering and tag validation.

## Operation-state model

Define a small presentation state independent of journal item state. Derive display through one update path per dialog; do not infer state by parsing status text, button captions or translated labels.

| UI phase | Title suffix / behavior | Confirmation |
| --- | --- | --- |
| Choosing settings/files | Ready | Disabled |
| Reading current metadata/building preview | Preparing preview | Disabled; no writes |
| Preview built | Preview — confirmation required | Enabled only for validated actionable items |
| Writing/verification | Running | Disabled; prevent conflicting commands |
| Stop requested | Stopping after current book/file | Disabled; do not report Interrupted before worker returns |
| All attempted work verified, no remaining errors/work | Completed | Disabled; show verified counts, including unchanged/excluded/discarded |
| No actionable changes in a fresh preview | No changes to apply | Disabled; do not claim a new execution completed |
| Worker returned with failures or pending/conflicts | Failed / Incomplete — review required | Disabled until renewed review and confirmation |
| Stop returned with unfinished work | Interrupted | Disabled; explicit review required |
| Outcome uncertain or journal unreadable | Verification required | Disabled; retain recovery and show reason |
| Preview cancelled before any execution | Preview cancelled — no operation started | Disabled |

If Stop arrives after all work actually completed, show Completed, not Interrupted. If some writes occurred, cancellation/close messages retain actual completed/failed/pending counts; never say no books changed. Successful housekeeping must not erase a meaningful failure. Last Session background busy deferral remains quiet.

Metadata-specific states: Loading, Ready, Unsaved changes, Saving, Saved, Save incomplete, Verification required and Preserved for recovery. Saving and preservation are distinct: emergency preservation is not a successful Calibre save. Keep result book/field feedback from M12.

Imports display original-source preservation and pending/failed distinctions. A missing title still uses filename and review status; a successful import does not silently mark metadata reviewed. Recovery history may record successful preservation while recovery is still pending: display this as “Draft preserved; review pending”, not as contradictory undifferentiated success.

## Batch identity and selection

Track history-selected ID separately from preview target ID and execution ID. Bind callbacks and preview confirmation to stable IDs plus library identity; list ordering and visible row index never determine the target.

- Opening a new bulk edit uses the current explicit catalog selection; display selected count including books hidden by filters. Opening history alone requires no selected books.
- Ordinary history refresh retains its selected ID. If the record disappeared, clear selection and explain why; do not silently substitute row zero for a destructive action.
- After local execution finishes, refresh with the executed batch ID preferred, including failed/interrupted results with a journal. If no journal can be verified, show verification required and do not pretend an older row is the result.
- During preview/running, target identity remains pinned. Disable history switches and target-changing actions or require explicit preview cancellation before a switch. New history arriving in the background never retargets Confirm.
- Selecting history is read-only. Review reconciles current metadata and builds a preview; it never executes pending writes.
- Revert header: “Revert preview for [operation] — [short ID]”, with books and proposed fields. Current Calibre values remain visible alongside proposed values.
- New revert journal retains its existing original ID relationship. Derive reverse links by scanning existing journals in the same library; do not add a schema migration or rewrite the original batch outcome. Multiple revert attempts remain individually visible. Failed/interrupted attempts must be labeled accurately.
- The original retains its historical execution result. Display a separate “Revert completed”, “Revert incomplete” or “Revert requires verification” annotation with linked record/counts. Do not claim all original changes were undone when exclusions, conflicts, partial writes or unverified outcomes remain. This describes a historical revert outcome, not a guarantee that later book metadata is unchanged.
- If a linked record was deleted, explain its absence and disable navigation; never recreate deleted history. Navigation is read-only and never runs a revert.
- New revert journal retains its existing original ID relationship. Show “Reverts batch [ID]” and “View original batch” when available; if original history was deleted, explain that rather than reconstructing it.
- Preserve existing ability/policy for reverting a revert; do not introduce a new prohibition or automatic redo. The preview must identify the selected operation and actual proposed changes clearly.
- Batch history deletion and discard confirmations name the selected batch, counts and consequences. Completed writes remain committed. No automatic cleanup.

## Layout and help

Approved two-tab design: New bulk edit groups operation settings, selected-book ordering and preview; Batch history groups record selection, explicit selected summary and read-only results/review controls. Each tab has its own presentation area, but each operation has one authoritative preview/execution state. New Bulk Edit can retain its finished result while Batch History selects that same new record. Creating a revert uses the Batch History preview/result area. Never duplicate mutable batch state across views. After a normal edit completes, select its history record without forcibly switching away from its visible result; after revert completion, stay in Batch History on the new revert record. Tab changes during active writes are blocked or read-only and cannot change the execution target.

Show only operation-relevant input groups (tags, author replacement or series); irrelevant disabled fields need not consume most of the window. Preserve typed settings when switching operations within the dialog unless explicitly reset. Do not alter batch persistence.

Use plain verbs, singular/plural agreement and consistent capitalization. Desktop instructions identify the window and action, then wait for the result. File-picker help: choose files through folders or paste the full path into the supported field. Do not claim typing is impossible until tested; do not replace the native picker in M13 without evidence of a defect. Container paths are shown only where choosing a file requires them.

## Implementation boundaries

Primary files: activity_panel.py (labels/navigation), recovery_actions.py (existing dispatch/focus only if needed), editor.py (contextual controls/titles), bulk_dialog.py (phase/identity/layout), import_dialog.py (phase/labels), workspace_ui.py (labels), feedback.py (shared result presentation), packaged help/troubleshooting. Keep backend operations and data formats unchanged.

Avoid separate ad hoc title updates in every callback. Explicit phase transitions enter preparing/running before worker event loops and set final states only after readback. Verify Qt queued signals and close/cancel paths do not reset completed state to preview via render().

## Verification and M13-01 completion

Inventory and design must be traceable to actual source. Both layout/selection choices are resolved; no tests are required for these documentation-only changes. Implementation requires meaningful behavioral tests, not merely matching every label string.

Acceptance scenarios:
1. User can navigate summary → history → details → preserved draft with one intended click each; no hidden editor and no Save until explicitly chosen.
2. Local discard, hide-from-action-list and durable discard remain distinct; unresolved history cannot be deleted directly.
3. Bulk edit preview, confirmed execution and result have correct titles and counts; latest executed batch is the displayed result.
4. Revert preview identifies original target and fields; cancellation writes nothing; actual completion selects the new revert record and shows verified counts.
5. Background refresh/new journals, missing selection, partial saves, conflicts, stop, read failures and late callbacks never target a different batch or claim false success.
6. Imports show preparing/preview/running/result accurately, retain source files and require review before retry.
7. Author/tag/cover/workspace/history actions remain correctly scoped; search-filter hidden bulk selections are explained rather than silently altered.
8. KDE keyboard/focus, long labels, small-window layout and actual file-picker instructions are checked on installed M13.
9. Current package, copied data and M12/M11 isolation verified; final promotion remains separate.
