# M13 installed acceptance fixes — gate remains open

Installed build: `0.1.0a1-594c20d70805c834`. Previous build and pre-upgrade data retained in the verified backup recorded in [installation evidence](installed_acceptance_fixes_candidate.json). 480 retained data files unchanged by upgrade. No promotion or publication.

## Changes and causes

- **M13-PICKER-01:** native picker path editing/paste was unavailable in owner testing. Added a visible File or folder path input and Preview path button in the application. Absolute paths, spaces, folder paths, invalid paths and busy guards are covered; existing preview/explicit confirmation still controls all writes. Native picker browsing remains available. Help now describes the actual input.
- **M13-IMPORT-FEEDBACK-01:** action changes previously did not update row warnings, and completed similar-title rows reverted visually to Choose action. Warning text now reflects the selected action while retaining other warnings; completed records display their recorded action. Destination entry is enabled for attachment only. Similar-title imports still require explicit action selection.
- **M13-WORKSPACE-REVISION-01:** restore and Last Session autosaves advance the shared store revision, leaving the open dialog stale. Mutation obtains a current revision only when named snapshots and startup choice still exactly match the reviewed dialog state. Real named/startup changes still require reload; store-level concurrent revision checks remain. Delete confirmation now includes the workspace name.

## Verification

- 54 affected source tests passed: [log](acceptance_fixes_regression.log).
- 235 full source tests passed: [log](acceptance_fixes_full_regression.log).
- 87 installed targeted tests plus package install/reinstall/data-retention checks passed in an isolated temporary environment: [report](acceptance_fixes_package_verification.json).
- [Post-restart saved-data review](post_restart_saved_data_review.json): 104 books, database check OK, recovery tag saved/resolved, Persuasion temporary tag absent, completed linked edit/revert journals, imported EPUB matches retained source, saved reading position and last selection retained, only M11 Everyday named snapshot remains. All 770 M12 baseline entries unchanged.

## Required desktop retest — criteria unchanged

1. Type and paste the existing M13 fixture path in the new application field, including spaces; verify folder entry, invalid-path feedback, keyboard focus and browsing fallback. Preview only is enough to inspect input; do not duplicate the already imported book.
2. In a similar-title preview choose an action and verify warning/destination feedback; verify completed action display using retained import history where available. Do not execute duplicate imports merely to inspect UI.
3. Save a temporary workspace, switch Hub, restore it, then delete it without manual reload. Confirm the named target and cancellation behavior; original snapshot and books must remain. Inspect readable layout and keyboard navigation.
4. Complete any outstanding recovery close-scope/local-discard preservation checks from the original checklist, then normal restart and final evidence review on this build.

Automated results and previous-build evidence do not substitute for the remaining KDE checks. M13-G OPEN; M12 everyday and M11 reference unchanged.

## Workspace KDE retest result

Owner explicitly confirmed successful completion on build `0.1.0a1-594c20d70805c834`: restore, cancel deletion (snapshot retained), then confirm deletion without reloading. Screenshot shows only M11 Everyday remaining, 104 books and saved reading position retained. M13-WORKSPACE-REVISION-01 resolved. This does not close import responsiveness/feedback findings or waive remaining gate criteria.
