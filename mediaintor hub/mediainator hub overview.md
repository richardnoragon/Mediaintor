# Media-inator Hub Overview

M10 delivery scope: workspace persistence covers existing Hub/Book-inator tabs, active tab, selected book and geometry only. Shared search/filter preferences remain independent; hidden selections are explained with an explicit Clear All option. Critical operations block switching. External readers remain untouched, and docking/floating windows are not introduced. Broader reader restoration and windowing requirements below remain future scope. [Final M10 plan](../milestone_10_workspace_restore.md).

Status: Planning. These documents record agreed product behaviour and open decisions, not implementation or released functionality. Initial direction: personal use, Linux, Book-inator first, one device, synchronisation later. Detailed feature deliverables remain open; see [First Release Scope](../first_release_scope.md).

## Purpose

Media-inator Hub is the required starting point and shared control centre for the collection-management suite. It provides module launch buttons, common controls, profiles, shared preferences, backup and settings transfer, and general and module-specific help.

## Planned modules

| Collection type | Module name |
| --- | --- |
| Movies | Movie-inator |
| Music | Music-inator |
| Books | Book-inator |
| Games | Game-inator |
| Stamps | Stamp-inator |
| Currency | Currency-inator |

This is the planned suite, not a commitment to first-release module coverage.

## Main behaviour

- The hub starts before other modules and can launch individual modules or all modules. Modules can appear as tabs, docked windows, or separate windows.
- Startup restores the last stored settings and module selection for the selected person and device, unless a predefined startup state has been selected. Opening or closing a module immediately updates last session even when a named startup state is selected; named states change only through explicit updates. Without saved settings, the hub and all modules open in tabbed view.
- Users can configure startup to use the last active profile or show a profile chooser. A profile can hold up to five user-named states covering module selection and layouts; Restore last session is the default, with a saved state selectable instead. Saving a sixth state asks the user which state to replace (or Cancel); if it was selected for startup, revert to Restore last session. Restoration asks whether to include playback/reading, opening media paused and books at the saved page/location. Missing content offers Locate / Retry / Skip while available content is restored.
- State save timestamps change only for explicit saves or automatic saves of active progress; profile-wide maintenance does not alter them or named-state replacement order. An Excluded from Restoration list temporarily suppresses items while preserving associations. Re-enabling restores surviving associations without recreating deleted, overwritten, or manually removed ones. Permanent removal destroys associations and is a separate action.
- Personal profiles own collections and settings. Reusable preference presets hold appearance and layout choices. Modules inherit shared settings and allow overrides.
- Locating missing content offers Use once or Update saved location. Skipping applies to the current session and asks whether to retain the item for future restores. Saved-location changes update every affected reference in the current profile, including named states. Exclusions suppress restoration across the profile without deleting associations, catalog entries, or files. External players/readers reopen when restoring playback/reading; unsupported position restoration is explained with an option to open normally.
- External applications are distinguished as hub-launched or attached. Attached applications remain open; only the hub-opened media/session may close where supported. External sessions kept open across profile switches retain their original profile and progress ownership.
- Switching profiles applies across the suite and restores the destination person's saved module selection and layout for the device. Without saved device settings, that person receives the hub and all modules in tabbed view.
- Settings and layout changes save immediately. Unsaved catalog edits are handled separately through a combined review dialog when switching profiles or exiting; individual module closure uses the same review limited to that module.
- Failed edit saves offer retry, followed by an emergency version containing only unsaved edits if retry fails. Successful emergency saving automatically continues exit/profile switching with a success banner; exit briefly shows the banner before closing, and the next launch reports recovery availability. Reopening the affected profile offers Review and recover edits; failed emergency saving stops the operation and offers an alternate location. Recovery conflicts show current and recovered values for the user to choose.
- Closing the hub exits all modules after any required review. The combined review includes Keep open / Close choices for external players/readers, scoped to the whole suite for exit/profile switching or to one module when it closes. Shared external applications stay open with an explanation while other modules still use them; global exit permits an explicit Close for all modules choice. Failed closure offers Retry / Leave open and continue / Cancel, avoiding force-close by default. Users may separately configure minimising the hub after launching a separate module window.
- Users can personalise the hub with movable, resizable panels, including collection counts, recent items, loan reminders, cross-module search, and task activity.
- Activity is grouped by operation and module for each person/device. Unfinished tasks offer Retry / Dismiss; dismissal retains history accessible through Show dismissed/history for inspection and retry. Latest successful and failed attempts link to details, and interrupted tasks have a separate status.
- Search includes closed modules, identifies them as closed, and opens the relevant module when a result is selected. Filters cover module, collection, and owned/wanted/loaned status, with five recent searches and up to five pinned favourites containing text and filters, belonging to the profile across devices. Pinning a sixth favourite asks which existing one to replace.
- Windows saved on a disconnected monitor move onto a current display, retaining their original positions and moving back immediately when the monitor returns.
- Shared collections support owner, editor, and viewer roles while retaining personal ratings and status. Approval records are visible to everyone with access to the shared collection.
- Backup choices cover settings, catalogs with artwork and personal activity, and actual media files, for individual modules or the whole suite.

## Document guide

- [Hub features](mediainator%20hub%20features.md) defines workflows, collection roles, task activity, backup capabilities, and requirements for user documentation, help, and release notes.
- [Hub configuration](mediainator%20hub%20config.md) defines configurable choices, defaults, settings scope, persistence, and configuration questions.
- This overview defines the product's purpose and boundaries. Detailed behaviour and configuration decisions belong in the linked documents.

The book, music, and movie documents are captured reference material from the inspiring products, not approved Media-inator requirements. The rough scaffold contains earlier planning discussions; its technical suggestions and release sequences are not automatically adopted.

## Planning to-do

- Define detailed Book-inator and hub deliverables for initial personal use on one Linux device.
- Confirm the Linux environment and later platform expansion; synchronisation is deferred, with LAN/cloud details still open.
- Resolve the workflow questions in the features document and settings questions in the configuration document.
- Deferred at the user's request: revisit owner-approval scope and backup category/profile selection later.

## Accepted M1 access restriction

For the initial Book-inator milestone, browse a temporary private copy of the selected Calibre library and open books from their original locations. Require Calibre and other readers to be closed while the hub refreshes or launches a reader; allow one hub-launched reader at a time. Explain conflicts and let the user close external apps and Retry; do not close or adopt unrelated sessions. Remember the original library location, not the temporary snapshot. This is an M1 delivery restriction, not a removal of later suite capabilities or an optional concurrency setting already implemented.

The external reader may save its normal annotations/settings. Snapshot copying uses temporary disk space and time and is not a backup. The policy is user-approved; integration verification remains open before full 101-book acceptance. Details: [accepted decision](../m1_library_access_decision.md).

## M16 delivery decision — tabbed Hub

Owner decision recorded 2026-09-25: M16 uses tabs. Available modules open within the Hub; repeated launch focuses the existing tab. Hub remains the primary window, stays open during module use and is not automatically minimized or closed after launching. Hub close retains suite exit and the existing scoped review/recovery rules. Independent/detached windows and Hub-independent operation remain future scope. Configurable post-launch behavior applies to future separate-window delivery, not M16. Broader windowing requirements above remain product plans, not shipped M16 features. See [M16 proposal](../milestone_16_hub_integration.md).

### M16 planned-module presentation

Owner decision: unimplemented modules use disabled tiles with an identifiable icon, a visible **Planned** badge and the tooltip “This module is planned for a future release and is not yet available.” They do not launch placeholder windows or participate in launch-all/first-run opening of available modules. No delivery date is implied. Experimental/Disabled workflows remain future proposals, not approved M16 features.

### M16 common-settings scope

Owner approved exactly four functioning global presentation controls: Theme, Accent color, Font/UI scaling and Density. Language translation, logging controls, update channels and storage/backup-location controls are outside M16 scope until their workflows are designed and implemented. Expose a setting only when it controls a currently implemented workflow. Existing capabilities remain intact; broader product requirements are deferred, not deleted.

### M16 appearance inheritance boundary

Owner approved: ordinary controls and text in metadata, bulk-edit, history, settings and other application dialogs inherit Theme, Accent color, Font/UI scaling and Density. This includes tables/lists, focus/selection states, application-owned dialog chrome and general spacing. Feature-specific behavior/state, previews, window size/position, columns, sorting, thumbnails and media layouts stay local. EPUB fonts/colors/themes, PDF presentation, audio/video/subtitle preferences and external application appearance are excluded. OS-owned title bars remain under desktop control. Appearance changes must not overwrite those local preferences or pending edits.

### M16 module names — owner clarification

Book-inator is the available M16 integration. Planned modules: Music-inator, Movie-inator, Game-inator, Paper-inator, Document-inator, Stamp-inator, Picture-inator and Currency-inator. “Video-inator” was an owner naming mistake, not another module or a rename: Movie-inator remains. Paper-inator specializes in scientific research papers; Document-inator records/saves other document formats. They remain separate planned modules. The family is extensible; these names do not authorize implementation of the planned modules in M16.

### M16 Hub layout and appearance-save transaction

Owner approved: ecosystem module tiles above the existing collapsible Activity panel, with a dedicated Settings entry. The tool-tile sketch is illustrative; Book-inator tools remain inside Book-inator. Settings changes preview immediately, then persist atomically. Failure restores the last saved appearance and selector values, explains the failure and offers Retry / Close. Retry retries the requested change; Close dismisses the error. Reset confirmation affects only the four appearance controls and uses the same rollback behavior. KDE/system scaling remains the foundation. No layout, workspace, module configuration or tool preferences are reset.
