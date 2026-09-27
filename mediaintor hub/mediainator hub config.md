# Media-inator Hub Configuration

M10 delivery scope: workspace persistence covers existing Hub/Book-inator tabs, active tab, selected book and geometry only. Shared search/filter preferences remain independent; hidden selections are explained with an explicit Clear All option. Critical operations block switching. External readers remain untouched, and docking/floating windows are not introduced. Broader reader restoration and windowing requirements below remain future scope. [Final M10 plan](../milestone_10_workspace_restore.md).

Current M5 status: **M5 COMPLETE; M5-G PASSED / CLOSED** following final evidence review and user desktop acceptance. [Gate review](../test_data/m5_acceptance/gate_review.md). All M5-01–M5-07 tasks are complete. Earlier dated/stage checkpoints are historical; no release is implied.

Status: Planning. This document defines settings and persistence, not implementation. See [features](mediainator%20hub%20features.md) for workflows and [overview](mediainator%20hub%20overview.md) for scope.

## Saving and scope

Settings and layout changes save immediately. Exit also preserves settings; saving does not depend on exiting normally. Save / Discard prompts concern unsaved catalog edits, not already-saved settings.

Each person has their own module selection and layout on each device. Window size and position are remembered separately for each module and device within that person's layout. Docking arrangements and hub panels belong to this saved layout.

Opening or closing a module immediately updates the automatically saved last session, even while a named startup state is selected. Suite exit preserves the selection from before shutdown. Restore last session is the default; a user-selected predefined state takes precedence over subsequent module-selection changes; it includes both modules and layouts. Users can save up to five user-named states in their profile. Users can choose one of these states instead of Restore last session. Named states change only when explicitly updated. Saving a sixth asks the user which state to replace (or Cancel). If the overwritten state was selected for startup, revert to Restore last session. Restoration asks whether to restore collections only or also playback/reading; media opens paused at its saved position and books at their saved page/location. This exception does not disable immediate saving of other settings.

If a saved window position belongs to a disconnected monitor, move the window onto a current display and retain its original position. Move it back immediately when that monitor returns.

Modules inherit shared preferences and may override them. A preference preset saves appearance and layout choices for reuse by different profiles; applying presets and resolving existing overrides remain to be defined.

### Last-saved dates

**Last-saved date** changes only when the user explicitly saves a state or the application automatically saves active state progress. Automatic progress saving applies to the active/last-session state; named snapshots remain unchanged until explicitly saved, apart from agreed metadata maintenance. Profile-wide location updates, path remapping, restore exclusions, and cleanup actions change metadata without changing save timestamps. Replacement of one of the five named states is explicitly user-selected, not driven by maintenance or timestamps.

## Configuration choices

| Setting | Agreed choices or behaviour | Default / scope |
| --- | --- | --- |
| Startup profile selection | Use the last active profile, or show a profile chooser | User-configurable; default and storage scope open |
| Startup restoration | Restore last session by default; optionally select one of five saved states | Per person/device; without settings, open hub and all modules as tabs, including on profile switching |
| Predefined startup states | Five explicitly saved/updated states; sixth requires user-selected replacement or Cancel | If selected state is overwritten, revert to Restore last session; device-specific layout handling open |
| Restoration scope | Ask whether to restore collections only or also playback/reading | Media paused at saved position; books at saved page/location |
| Module arrangement | Tabs, docked windows, or separate windows | Tabbed when no settings exist; per person/device |
| Action after separate-window launch | Keep hub open, or minimise hub to tray | Default open for decision; does not apply to docked/tabbed launches |
| Font size | Shared preference with module overrides | Initial value and device scope open |
| Colour/theme | Light, dark, system, or user-defined | Initial selection and customisation detail open |
| Interface language | Shared preference with module overrides | Supported languages and initial selection open |
| Window size and position | Remember each module's size and position | Per person, module, and device |
| Search history and favourites | Last five search/filter entries and up to five pinned favourites; filter by module, collection, and owned/wanted/loaned status | Both text and filters; profile-wide across devices; ask which favourite to replace at capacity |
| Hub panels | Add/remove, move, resize | Layout per person/device; initial panel selection open |
| Excluded from Restoration | Temporarily suppress restoration; re-enable surviving previous associations automatically | Current profile, including named states; maintenance does not change save timestamps |
| Preference presets | Save and reuse appearance/layout choices across profiles | Contents and application rules open |

Missing collections or media are listed with Locate / Retry / Skip while available content is restored. Locate offers **Use once** for the current session or **Update saved location** for future use. Skip applies to the current session and asks whether to **Keep for future restores** or **Exclude from Restoration**. Exclusion temporarily suppresses restoration without deleting associations, files, or catalog entries. Update saved location changes every reference to the item in the current profile, including named states. Exclusion suppresses every restoration reference in that profile, including last session and named states. Re-enabling restores surviving previous associations automatically; it does not recreate associations from deleted/overwritten states or locations manually removed from a state. **Remove permanently** is a distinct operation that destroys restoration associations. Exclusion and re-enabling do not alter save timestamps. These choices are explicit updates to the affected references; unrelated state contents and other profiles are unaffected.

Playback/reading restoration reopens configured external players/readers where applicable. Restore the saved position and paused playback when supported. If position restoration is unsupported, explain the limitation and offer **Open normally**. When exiting or switching profiles, include Keep open / Close choices for hub-launched or attached external players/readers in the combined review dialog, with Cancel for the whole operation. Individual module closure uses the same choices scoped to that module. If closing fails, offer Retry / Leave open and continue / Cancel, avoiding force-close by default. Keep applications open while another module still owns them and explain why. A requested close is permitted when no module owners remain or when Close for all modules is explicitly chosen during global exit. Distinguish hub-launched applications from attached, already-running applications. For attached applications, Close affects only the hub-opened media/session where supported; leave the application and unrelated content open, including during Close for all modules. If the session cannot close separately, explain the limitation and offer the failure choices. Sessions kept open across profile switches retain their original profile ownership, and tracked progress is never attributed to the newly active profile. These ownership rules are fixed behaviour, not a profile preference. No automatic close preference has been agreed. External application selection and capability-specific options remain to be defined; normal opening cannot guarantee unsupported playback/position behaviour.

The hub close button always initiates suite exit; it is not a configurable minimise action. Immediate settings saving is agreed behaviour, not currently an optional mode.

## Activity and backup controls

The activity panel provides Retry / Dismiss and groups tasks by operation and module for the person and device. It displays the latest success and actual failure with detailed links; interrupted tasks have a separate status. Dismiss hides unfinished work from the action list but retains its details/history. Show dismissed/history allows inspection and retry of dismissed tasks. No history-retention duration or preference has yet been agreed.

An emergency version containing only unsaved edits is required after an unsuccessful edit-save retry. Successful emergency saving automatically continues exit/profile switching with a success banner. Briefly show the success banner before exit and a recovery notice next launch. Offer Review and recover edits when the affected profile reopens. If emergency saving fails, stop exit/switching and offer an alternate location. Recovery conflicts show current and recovered values side by side for user selection. Default destination and retention remain open.

Backup controls select individual modules or the whole suite and offer settings, catalogs/artwork/personal activity, and actual media files. Category combinations and profile/shared-collection selection are deferred questions in the features document. No schedule, destination, or retention defaults have been decided.

## Open configuration questions

- Choose the default startup profile-selection behaviour and where that choice is stored.
- Choose the default action after launching a separate module window.
- Define named-state removal, device-specific layout handling, and the relationship to reusable appearance/layout presets.
- Define controls and confirmation for Remove permanently, separate from temporary restoration exclusions.
- Define how progress is reconciled for external sessions left open after the hub exits.
- Define external player/reader selection settings and their module/device scope.
- Define emergency-version storage and retention, and activity-history retention controls if needed.
- Define which preferences follow a person across devices versus remaining device-specific.
- Define preset contents, module-override precedence when applying presets, and reset-to-default behaviour.
- Define initial panels, supported languages, and appearance defaults.

Immediate saving and suite-wide profile switching must be explained in help, user documentation, and the relevant release notes; required content is recorded in the features document.

## Accepted M1 access restriction

For the initial Book-inator milestone, browse a temporary private copy of the selected Calibre library and open books from their original locations. Require Calibre and other readers to be closed while the hub refreshes or launches a reader; allow one hub-launched reader at a time. Explain conflicts and let the user close external apps and Retry; do not close or adopt unrelated sessions. Remember the original library location, not the temporary snapshot. This is an M1 delivery restriction, not a removal of later suite capabilities or an optional concurrency setting already implemented.

The external reader may save its normal annotations/settings. Snapshot copying uses temporary disk space and time and is not a backup. The policy is user-approved; integration verification remains open before full 101-book acceptance. Details: [accepted decision](../m1_library_access_decision.md).

## M5 delivery decisions

[M5 Hub Activity & Recovery](../milestone_05_hub_activity_recovery.md) delivers the agreed activity/recovery behavior for Book-inator on one profile/device. Activity is visible by default and collapsible, with full history; movable/resizable dashboard regions remain deferred. Activity history has no automatic expiry. Emergency single-book edits use Application Data / Recovery / Single Book Edits and offer Preserve Elsewhere on failure. Protection includes Book-inator tab closure and orderly Hub/application shutdown, and is triggered by failed save/retry rather than exit alone. These decisions settle the previously open default emergency location, tab-close coverage and indefinite history retention for M5. Unresolved copies remain until successful recovery or explicit discard after review; history deletion may remove remaining associated state only after resolution. All M5 scope clarifications are confirmed. Successful emergency preservation automatically completes an already-requested close with truthful recovery notices; without a close request, the editor remains open. Delete History is unavailable for unresolved recovery until separate Review Recovery and explicit Discard Pending; resolved records may be deleted with confirmation. Successful routine preference saves are excluded from Activity, while actionable settings-save failures are included. Earlier broader suite questions remain outside this milestone; no M5 implementation is claimed.

M5 technical checkpoint: [technical design](../technical_design_m5.md) complete; [31 disposable protocol checks](../test_data/m5_validation/README.md) passed without original-library changes. This validates the proposed recovery protocol, not the production Hub Activity UI or close workflow. M5-01/M5-02 DONE; M5-G remains OPEN / NOT RUN pending application implementation and acceptance.

M5-03 implementation checkpoint: production activity/recovery stores, operation outcome hooks and independent book-review migration are implemented and [verified](../test_data/m5_03_integration/README.md) by 85 unit/UI tests and 14 disposable checks. Activity UI/startup summary, shared recovery actions and automatic emergency preservation/close handling remain M5-04–M5-07. M5-G remains OPEN. Earlier no-M5-implementation statements refer to prior planning checkpoints.

Current M5 implementation checkpoint: M5-01–M5-05 are complete. Hub Activity/history/startup summary and shared review/retry, persistent dismissal, guarded discard and coordinated history deletion are implemented. [M5-05 evidence](../test_data/m5_05_actions/README.md): 119 unit/UI tests and 13 real disposable checks passed. Automatic emergency preservation and close handling remain M5-06; final application acceptance remains M5-07. M5-G stays OPEN. Earlier stage checkpoints are historical, not current completion claims.

Current M5-06 checkpoint: automatic preservation after failed Save/Retry and requested-close continuation are implemented. Ordinary editing stays open; preservation/registration failure keeps the draft open and offers an alternate location. Protection is specific to the current draft revision. Cooperative session shutdown reuses review where supported; forced termination is not draft autosave. [143 unit/UI tests and 14 disposable checks](../test_data/m5_06_emergency/README.md) passed. M5-01–M5-06 DONE; M5-07 application/desktop acceptance and M5-G remain OPEN. Earlier checkpoint statements are historical.

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
