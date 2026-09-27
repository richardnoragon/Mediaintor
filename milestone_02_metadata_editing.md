# Milestone 02 — Catalog metadata editing

Status: **M2 COMPLETE for the agreed scope.** All seven implementation tasks and 17 acceptance criteria are complete. G2 is PASSED/CLOSED for Calibre 9.2.1. User sign-off: [desktop confirmation](test_data/m2_acceptance/desktop_confirmation.json).

## Goal and boundary

View the existing catalog, select one book, edit its metadata locally, and explicitly save changes to Calibre. Retain the M1 hub, catalog views, search, original-library binding and reader protections.

Included editable fields: **title, authors, tags, cover, series, series index/number, and comments/description**. Publisher, ISBN, language, formats and custom columns are deferred. Preserve unedited fields; reading-progress integration remains later work.

Excluded: adding books, deleting books from disk, imports, exports, library import/export, format conversions, user-initiated moves/renames, bulk file reorganization and direct format-file management. Bulk editing is assigned to M4. M3 is now approved as copy-only Safe Ebook Imports; M5 is Hub Activity / Recovery. See [M3 specification](milestone_03_safe_ebook_imports.md).

An explicit metadata Save may trigger Calibre’s normal internal file operations: title-related folder/file renaming, author-related path reorganization, cover-file updates and metadata database updates. These are permitted side effects of saving through Calibre; M2 exposes no direct file-management commands. Reconcile resulting paths using stable library/book identity rather than treating the old path as identity.

## Editing and saving

- Edit one book at a time in a local draft. Clearly mark a modified record.
- Explicit **Save** attempts all pending metadata changes. **Discard** abandons outstanding local edits and reloads current Calibre values. Any successfully committed fields remain saved, including after partial success.
- Hub preferences still save immediately. Metadata drafts are not preferences and must not be silently auto-saved.
- Retain unsaved values after failures and offer **Retry / Keep Editing / Discard**.
- Partial success is permitted: keep verified successful changes committed, identify saved and failed fields, and offer **Retry Failed Changes**. Do not roll back successes merely because another field failed.
- A failed command does not prove that nothing changed. Read back affected fields before reporting success/failure; distinguish unverified results if read-back fails. Validate the actual command behaviour before choosing a write grouping or retry strategy.
- Series and its index may be coupled by Calibre. Do not promise independent field writes until tested. Do not inadvertently reset unedited metadata by submitting stale whole-record values.

## Leaving a modified book or requesting refresh

Selecting another book, closing the editor/module/application, or explicitly refreshing with unsaved edits presents **Save / Discard / Cancel**:

- **Save:** attempt pending changes, verify their results, then continue the requested action only when no outstanding edits or unresolved save results remain. A partial failure must not silently abandon the remaining draft; keep it available for Retry / Keep Editing / Discard.
- **Discard:** abandon only outstanding local changes, preserve committed writes, and continue the requested action with current Calibre values.
- **Cancel:** keep the current book/draft and abort the requested action. Do not undo successful earlier writes.

Use the hub's combined review when leaving the module/application also involves an active task or reader. Automatic refresh triggers defer quietly while dirty; the explicit user Refresh action asks for the review above. This distinction avoids repeated timer-driven save dialogs.

## Automatic refresh

Triggers are window focus regain and every **30 seconds while idle**. Refresh immediately on those triggers when the editor is clean, even if it is open. Defer catalog replacement while local unsaved edits exist. Preserve the draft and the currently displayed catalog.

When an external change is detected while edits are pending, display: **“Library changed externally. Refresh pending until edits are saved or discarded.”** Do not assert an external change solely because a timer fired. Change detection must not replace the draft or bypass library-access restrictions.

When library access is unavailable/locked, retain the catalog, show **“Waiting for library access...”**, and retry automatically.

M1's private-snapshot browsing and single-reader/exclusive-access rules remain the baseline. Revalidate access rules for metadata writes; do not write to a snapshot and claim that the original library was updated. Do not queue automatic metadata commits merely because access becomes available; user-triggered saves and safe retries must remain distinguishable.

## Conflicts

Compare current Calibre values with the draft's baseline and local modifications. Present per-field **Keep My Value / Use Calibre Value**, plus **Keep All Mine / Use All Calibre Values**. Preserve non-conflicting external changes. Cover comparison must be meaningful rather than presenting opaque paths alone.

Before every Save or Retry, read current Calibre values and compare them with the baseline for the remaining dirty fields and the user’s outstanding edits. Present new conflicts before writing. Update the baseline for successfully verified writes; retries must not resend already successful fields unnecessarily. Revalidation covers changes made by Calibre, other tools, plugins or another application instance without promising simultaneous writer support. Subsequent races and exclusive-access limits must be covered by technical validation, not described as atomic transactions without evidence.

## Confirmed clarifications

All three blocking product questions are resolved: Calibre-managed file side effects are permitted, leaving a dirty book uses Save / Discard / Cancel while a clean editor can refresh, and partial-save successes remain committed with fresh conflict checks before every Save/Retry. Installed-source inspection supports the need to account for path updates; disposable write validation now establishes the behaviours and limitations recorded below.

The following editor and recovery decisions are confirmed. No online-cover lookup or metadata-provider integration is implied.

### Cover editing and recovery

M2 includes selecting a local image, previewing before Save, replacing the existing cover, and removing the cover entirely. Choose Image and Remove Cover modify the draft only; removal must be verified in Calibre, not implemented by substituting a blank image.

Back up the existing cover before attempting a cover write, then validate the result. If the write fails, automatically restore the original cover from backup, verify restoration, report the failure and retain the proposed replacement in memory for Retry. Successfully saved text metadata remains committed. Restoring a damaged failed cover does not roll back successful metadata writes.

After verified restoration, report: “Cover update failed. Original cover was restored successfully. The selected replacement has been retained and can be retried.” If restoration itself fails or cannot be verified, report that actual result rather than claiming recovery; preserve the backup and pending work for recovery. Disposable API verification established cover removal and restoration protocol feasibility; application integration and failure tests passed within the documented acceptance scope.

### Description editor

Provide basic rich-text editing: paragraphs, bold, italic, bullet lists and numbered lists. Tables, embedded images and custom HTML editing controls are excluded from M2. When the description is untouched, preserve its existing HTML exactly as stored; opening or saving other fields must not reserialize it. Existing descriptions may contain links; link-authoring controls were not explicitly selected in these decisions.

### Authors and tags

Authors use separate entries with **Add / Remove / Reorder**, preserving author order in storage, display, change tracking and conflict comparison. Tags use separate entries with **Add / Remove** and are treated as an unordered collection. Commas inside author names are preserved. Individual tag names may not contain commas. Validate before saving and explain: “Tag names cannot contain commas because Calibre treats commas as separators.” Keep the invalid draft available for correction; do not silently split or convert the tag. Validate ordered author and valid-tag round trips.

## Validated write behaviour and remaining design details

Calibre 9.2.1 disposable-copy tests passed the seven-field round trip and verified title/author path changes without changing format contents or record UUID. Missing cover input can be silently ignored; invalid image input can save the title and truncate the previous cover even when the command fails. Validate/stage images and preserve a recoverable existing cover before writes; verify actual results and test failed-cover recovery without rolling back successful fields. Read-back must recognize damaged failed values, not assume failure leaves them unchanged.

Clearing a series leaves its stored index unchanged; an index write without a series can be ignored despite exit 0. The agreed clearing/default rule below now defines the required UI and Calibre storage semantics; the user now accepts any retained index as an implementation detail when no series exists, removing the storage blocker. Three-way conflict and retry detection passed in a protocol harness, preserving unrelated external changes; race-free multi-process writes are not established. See the [evidence and adapter requirements](test_data/m2_validation/README.md). M2 application acceptance is now complete; historical capability evidence is supplemented by the final acceptance report.

## Confirmed series-number behaviour

When the Series field is cleared, the Series Number field is hidden and its value is removed. When a new Series is assigned, the Series Number defaults to **1** until explicitly changed by the user. Never carry a removed number into a newly assigned series.

Series numbers must be finite numeric values greater than or equal to zero, including decimals such as 0, 1 and 2.5. Reject negatives and nonnumeric input; a newly assigned series defaults to 1 until edited.

These changes follow the normal draft contract: clearing Series removes the number from the local draft immediately; explicit Save commits the paired change. Discard restores the current saved values. An unchanged existing series retains its number. For M2, assigning a different series also starts at 1 unless the user explicitly changes the number; the optional retention prompt below is deferred.

**Confirmed M2 implementation requirement (supersedes literal stored-index removal):** When a series is removed, Book-inator hides the series number. Calibre's internally stored value is accepted as an implementation detail and is not considered an error. Any retained index is ignored while no series exists. Verify removal of the series name; do not require a null stored index, queue index cleanup, or report “Series removal incomplete” merely because the index remains.

Only actual failed or unverified intended writes use partial-save handling. When assigning a new series, explicitly save the default number 1 unless the user changes it; never reuse the hidden retained index. Draft comparisons and conflict detection must treat the index as inapplicable when no series exists. No Calibre schema changes or direct database writes are needed for this policy.

Future milestone candidate (unassigned, outside M3 imports): when changing an existing series, offer “Keep existing series number (3) or start at 1?” This prompt is outside M2.

## Implementation passes

| Task | Status | Action | Completion evidence |
| --- | --- | --- | --- |
| M2-01 | DONE | Validate supported field writes on disposable copies against the now-confirmed contract | Decision record and capability matrix including path/cover effects |
| M2-02 | DONE | Extend catalog data and single-book editor with confirmed cover, rich-text, numeric and author/tag controls | Seven fields, ordered authors/unordered tags, preserved untouched HTML and dirty draft; no source mutation while typing |
| M2-03 | DONE | Implement explicit save/read-back, series removal with hidden/ignored index, cover removal/recovery and failed-field retry | Verification of series-name removal and explicit new-series default, cover deletion/restoration, partial and unverified outcomes, lossless author/tag transport |
| M2-04 | DONE | Implement focus/idle refresh with draft and access deferral | No draft loss; truthful change/waiting messages; eventual refresh |
| M2-05 | DONE | Implement per-field/global conflict decisions | Local/external/baseline cases; unedited values preserved |
| M2-06 | DONE | Integrate book-switch/module/hub review and failure recovery | Save/Discard/Cancel and partial-save exit scenarios |
| M2-07 | DONE | Run catalog-scale and focused mutation acceptance, then user desktop review | Evidence for all criteria below; remaining limits documented |

M2-01 is DONE for initial capability validation, with version-specific limitations and required safeguards recorded in the [validation report](test_data/m2_validation/README.md); this is not live-write or application acceptance. M2-02 through M2-06 are DONE for implementation and automated checks. M2-07 is DONE following final user desktop confirmation. Validate writes on disposable data before live use. M1 acceptance is not evidence that metadata writes are safe.

## Acceptance checklist

- [x] M2-A01: Existing catalog browsing/selection remains available; excluded import/export/file-operation controls are absent.
- [x] M2-A02: Seven agreed fields can be edited for one book; typing changes only the draft, with a visible modified indication.
- [x] M2-A03: Explicit Save writes intended changes and verifies results; unedited fields and book/format associations are preserved.
- [x] M2-A04: Book selection, editor/module/app close and explicit Refresh review Save/Discard/Cancel only for dirty edits; Cancel aborts the action and Discard preserves successful writes.
- [x] M2-A05: Focus/30-second idle refresh updates a clean editor, defers quietly while dirty, and resumes after save/discard without losing drafts.
- [x] M2-A06: Access contention retains the catalog and unsaved work, reports waiting and retries safely.
- [x] M2-A07: Genuine external changes trigger per-field comparison; both global shortcuts apply correctly and can be cancelled before writes.
- [x] M2-A08: Failure retains pending edits; partial success is accurately identified and only failed outstanding changes are retried after revalidation.
- [x] M2-A09: Title/author path effects, cover effects, series/index coupling and description preservation match the clarified contract and disposable-test evidence.
- [x] M2-A11: Clearing Series removes the name on Save and hides/ignores its number. Any retained Calibre index is accepted without a save error. Assigning a new series explicitly defaults to 1 unless edited; Discard restores saved draft values.
- [x] M2-A10: Hub preferences still save immediately; metadata and lifecycle changes do not regress the accepted M1 workflow.

- [x] M2-A12: Retained index alone causes no incomplete-removal warning, pending cleanup or Retry request. Actual failed/unverified writes retain normal partial-save handling without rollback of successful writes.
- [x] M2-A13: Local cover selection/preview, replacement and complete removal use draft/Save semantics and verified Calibre results.
- [x] M2-A14: Failed cover writes automatically restore and verify the backup, retain the proposed replacement for Retry and preserve successful text writes; failed restoration is reported truthfully.
- [x] M2-A15: Description supports the five agreed formatting features, excludes advanced editing controls and preserves untouched HTML exactly.
- [x] M2-A16: Series numbers accept zero and positive decimals, reject negative/nonnumeric/nonfinite input, and default to 1 for a new series.
- [x] M2-A17: Authors support Add/Remove/Reorder with order and embedded commas preserved; tags support Add/Remove with order-insensitive comparisons. Comma-containing tag names cannot be saved and receive an explanation that Calibre treats commas as separators; valid tags round-trip unchanged.

Links: [implementation plan](implementation_plan_hub_bookinator.md), [release scope](first_release_scope.md), [M1](milestone_01_browse_and_read.md), [Book-inator constitution](bookinator/bookinator_constituion.md).

## M2 follow-up compatibility checkpoint

Disposable Calibre 9.2.1 API verification passed cover deletion, automatic backup-restoration protocol, ordered author round trips (including commas), exact untouched HTML preservation and numeric validation. UUID and format contents were preserved; original-library hashes were unchanged. These are capability/protocol results, not completed application acceptance.

The user resolved both compatibility blockers: when no series exists, hide and ignore Calibre's internally retained index; it is not a save failure. Assigning a new series explicitly defaults to 1 unless edited. Individual tag names may not contain commas; validation must prevent saving them and explain that Calibre treats commas as separators. Implementation and automated tests are now complete; final user desktop acceptance is complete.

## Implementation checkpoint

M2-02–M2-06 implemented: single-book draft editor, isolated version-bound Calibre helper, verified field saves and partial recovery, automatic refresh deferral, conflicts and combined lifecycle review. Forty-one automated tests, sixteen adapter integration checks and seventeen application checks pass. G2 is closed using recorded M1 user evidence and current regressions. Final M2 user desktop review is accepted; all 17 acceptance criteria are complete for the agreed scope. See [technical design](technical_design_m2.md) and [acceptance report](test_data/m2_acceptance/README.md).
