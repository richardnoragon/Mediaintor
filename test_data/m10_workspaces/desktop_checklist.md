# M10-07 guided desktop checks

Candidate: `0.1.0a1-a3a4679f39f4c255`, **Media-inator M10 Development** only.
Catalog/reader, Last Session restart and named startup have owner confirmation. The checks below remain pending; these are not reported defects. M10-G stays open.

Close Calibre and ebook readers before metadata saves. Use only the copied M10 library. Wait for catalog loading to finish.

## 1. Named workspace management

1. Choose Workspaces → Manage named workspaces….
2. Use Save new with distinct names (for example Test A through Test E) until the list has five entries total. Existing entries count toward five; do not delete a workspace you want to keep.
3. Choose Save new, enter Test Sixth, then Cancel at the replacement-selection dialog. Confirm all five previous entries remain unchanged.
4. Repeat and deliberately select an expendable test workspace to replace. Confirm there are still five entries and only the chosen entry was replaced.
5. Select Test Sixth and Rename it to Test Renamed. Confirm only the name changes.
6. Close management, change the active tab, reopen management, select Test Renamed and choose Overwrite. Confirm the overwrite, change tabs again, and Restore Test Renamed. Confirm the newly saved active tab returns.
7. Delete an expendable test workspace and confirm only that workspace disappears; books remain available.

Record pass/fail for Cancel, replacement, rename, overwrite/restore and delete. Report any message verbatim. If a revision conflict asks you to Reload, note it rather than assuming the preceding save succeeded.

## 2. Selection and shared filters

1. In Book-inator, Clear All search/filters and select a book. Note its title.
2. Save a workspace named Selection Test (replace only an expendable test entry if at capacity).
3. Close management and enter text that does not match the selected book, such as `M10-no-matching-title-12345`.
4. Reopen management, select Selection Test and Restore.
5. Confirm the search remains unchanged and the catalog explains that the selected book is hidden by active filters.
6. Close management and click Clear All in Book-inator. Confirm the book is visible and selected.

A hidden book is expected until Clear All is explicitly chosen. Missing selection or silently cleared search is a failure to report.

## 3. Unsaved-edit review

Preparation: save a workspace with the Hub tab active, named Hub Test. Return to Book-inator, select a test book and open its metadata editor. Record its original title.

- Cancel: append ` M10 draft test` to the title without saving. Leave the editor open, return to the Hub window and restore Hub Test through Workspaces. Choose Cancel in Unsaved metadata. The current tab and unsaved draft must remain unchanged.
- Discard: attempt Restore again and choose Discard. The original stored title must remain and the target Hub tab should become active.
- Save: return to Book-inator, edit the same test title again and attempt Restore. Choose Save. The title must be saved and verified before the Hub Test workspace is restored. Reopen the record to check the stored title.
- Cleanup: explicitly restore the original title and Save in the metadata editor.

If the editor prevents access to Workspaces, a loading/busy message prevents continuation, the draft disappears, or Save/Discard does not complete the requested restoration, record the exact behavior. Do not count that path as passed merely because the metadata saved.

## Still separate

Busy-operation protection, reader independence, native KDE monitor recovery and installed workflow regressions remain separate evidence items. These checks alone do not close M10-G.
