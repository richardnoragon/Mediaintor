# Media-inator Hub Features

M10 delivery scope: workspace persistence covers existing Hub/Book-inator tabs, active tab, selected book and geometry only. Shared search/filter preferences remain independent; hidden selections are explained with an explicit Clear All option. Critical operations block switching. External readers remain untouched, and docking/floating windows are not introduced. Broader reader restoration and windowing requirements below remain future scope. [Final M10 plan](../milestone_10_workspace_restore.md).

Current M5 status: **M5 COMPLETE; M5-G PASSED / CLOSED** following final evidence review and user desktop acceptance. [Gate review](../test_data/m5_acceptance/gate_review.md). All M5-01–M5-07 tasks are complete. Earlier dated/stage checkpoints are historical; no release is implied.

Status: Planning. Agreed behaviour unless explicitly marked open or deferred. See the [overview](mediainator%20hub%20overview.md) for product scope and [configuration](mediainator%20hub%20config.md) for options and defaults.

## Launching, windows, and startup

- The hub must launch before other modules. Users can launch individual modules or all modules through it.
- Modules support tabbed, docked, and separate window arrangements.
- Startup restores the selected person's last stored module selection and layout for the device. With no saved settings for that person and device, open the hub and all modules in tabbed view.
- Opening or closing a module immediately updates the automatically saved last session. A selected named startup state controls what opens next time without stopping last-session saving. Suite exit preserves the selection from before shutdown rather than recording the shutdown itself as closing every selected module.
- Restore last session is the default startup choice. Users can instead select one of up to five user-named states saved in their profile. A selected state takes precedence over the changing module selection and includes modules, layouts, and collection context, with optional playback/reading restoration. Named states remain unchanged until explicitly updated by the user; last-session saving continues automatically. Saving a sixth state requires the user to choose an existing state to replace, or Cancel without changing any state. If that state was selected for startup, revert the startup choice to Restore last session.
- When restoring, ask: **“Would you like to restore the collections only, or also playback/reading?”** When playback/reading is included, open media paused at the saved position and books at the saved page/location. Do not start playback automatically.
- If a collection or media file is unavailable, restore everything available and list missing items with **Locate / Retry / Skip** actions.
- After locating missing content, offer **Use once** or **Update saved location**. Use once applies to the current session without replacing the stored location; Update saved location persists the new reference for future use. Update every reference to that item in the current profile, including named states. Choosing this action is an explicit update to those references; it does not replace unrelated state contents.
- Skip omits the item for the current session and asks whether to **Keep for future restores** or **Exclude from Restoration**. The latter is the temporary-suppression action previously described as Remove from future restores. Suppress every restoration reference to that item in the current profile, including last session and all named states, while preserving the associations. Other profiles, catalog entries, and media files are unaffected.
- When playback/reading restoration is selected, reopen the configured external player or reader where applicable. Restore paused playback or the saved reading position when supported. If the application cannot restore the saved position, explain the limitation and offer **Open normally** rather than silently falling back. Normal opening follows the external application's behaviour; do not promise paused playback or position restoration when unsupported.
- The hub close button initiates exit for the entire suite. After required review, all modules close and settings are preserved.
- If a saved window position belongs to a disconnected monitor, move the window onto a current display while retaining its original position. Move the window back immediately when the monitor returns.
- The optional minimise-after-launch action applies only to separate module windows. Launching a docked or tabbed module does not minimise the hub.

### State timestamps and restoration exclusions

**Last-saved date** changes only when the user explicitly saves a state or the application automatically saves active state progress. Automatic progress saving applies to the active/last-session state; named snapshots remain unchanged until explicitly saved, apart from agreed metadata maintenance. Profile-wide location updates, path remapping, restore exclusions, and cleanup actions change metadata without changing save timestamps. Replacement of one of the five named states is explicitly user-selected, not driven by maintenance or timestamps.

Provide an **Excluded from Restoration** list for the current profile. Users can inspect excluded items and re-enable them for future restoration. Exclusions apply across restoration references, including named states, without deleting catalog entries or media. Re-enabling automatically restores all previous state associations that still exist. Do not recreate an association if its state has been deleted, overwritten, or manually edited to remove that location. Retain association information while excluded to support this undo behaviour, future features, and migrations.

**Exclude = temporary suppression. Remove permanently = destroy associations.** Permanent removal is a distinct action, not a synonym for exclusion, and concerns restoration associations rather than deleting media or catalog entries. Its controls and confirmation remain to be defined. Excluding or re-enabling items is metadata maintenance and does not update save timestamps.

## Profiles and profile switching

A personal profile represents a person and owns their collections and settings. Preference presets save appearance and layout choices for reuse by different profiles.

Switching profiles changes the active person across the entire suite. Restore the destination person's saved module selection and device-specific layout, opening or closing modules as required by that selection. No module remains assigned to the previous profile. External playback/reading sessions deliberately kept open are distinct from module windows: each remains owned by its original profile, and any tracked progress belongs only to that profile, never to the newly active one. Resolve the current person's unsaved edits and running tasks before completing the switch.

The active profile determines accessible personal/shared collections and personal ratings and status. Switching to a profile without saved settings on the device opens the hub and all modules in tabbed view.

## Combined review when switching or exiting

Use one combined dialog to review unsaved edits, running background tasks, and external playback/reading sessions in applications the hub launched or attached to before confirming an exit or profile switch:

- List modules with unsaved edits and provide Save / Discard choices for each. Save keeps those edits; Discard abandons them.
- List running tasks and explain that proceeding interrupts them.
- List applicable external players/readers with **Keep open / Close** choices per application, identifying whether the hub launched it or attached to an existing application. For attached applications, Close means close only the hub-opened media/session where supported, not the application itself.
- Provide Cancel for the entire exit or switch. Cancelling leaves the current session active and does not apply pending Save / Discard choices, interrupt tasks, or close external applications.
- Apply the selected actions only after the user confirms the combined review.
- If there are no unsaved edits, omit save questions. If there are no running tasks, omit interruption warnings. Omit external-application choices if no applicable applications remain open. If none of these three categories requires attention, proceed without the review dialog.
- Settings and layout changes save immediately and are separate from the catalog edits covered by Save / Discard.

Closing an individual module tab or window uses the same review, limited to that module's edits, tasks, and external players/readers. Cancel stops that module closure.

External-application choices are part of this combined review, not a separate prompt. Their closure is not automatic. If an application cannot close, offer **Retry / Leave open and continue / Cancel**. Avoid force-closing by default.

When another module still uses an external application, keep it open and explicitly explain which module(s) still need it. Only carry out a requested close when no module owners remain, or when the user explicitly chooses **Close for all modules** during global exit. Having no remaining owners permits closing; it does not override a Keep open choice.

Planning note: maintain a reference count or ownership list for external applications so the hub can determine which modules still use them and explain why they remain open. This is a design requirement, not an implementation. Track the originating profile and module for each media/session separately from whether the application was launched or attached to. Profile switching does not transfer ownership of sessions kept open.

For an application that was already running, leave the application itself open and close only the hub-opened media/session where supported. If that session cannot be closed separately, explain the limitation and use the failure choices rather than closing the whole application. **Close for all modules** follows the same boundary: it covers hub-owned sessions and does not authorise closing an attached application or unrelated content.

Keep completed task work when interrupting a task. Report unfinished work for later retry. Handling a partially completed item remains open.

### Failed saves and emergency versions

If saving an edit during exit or profile switching fails, let the user retry. If retry is unsuccessful, create an **emergency version containing only unsaved edits**. When this recovery copy succeeds, continue exit or profile switching automatically and display a banner reporting that emergency saving succeeded. The banner must distinguish preserving edits in a recovery copy from saving them normally to the catalog. During exit, briefly show “Unsaved edits preserved in an emergency copy” before closing, then show a recovery notice on the next launch.

When the affected profile is reopened, offer **Review and recover edits**. If creating the emergency copy also fails, stop the exit/profile switch and let the user choose an alternate save location. If catalog information has changed since the emergency copy was created, show current and recovered values side by side and let the user choose which to keep. Default storage, retention, and application to individual module closure remain open.

## Hub panels and search

Users can add, remove, move, and resize hub panels. Candidate panels already agreed include collection counts, recent items, loan reminders, cross-module search, and activity. The panel catalogue can expand beyond these examples.

Cross-module search includes accessible collections from modules that are not open. Results indicate when their module is closed. Selecting such a result opens the module and navigates to the selected item. Users can filter by module, collection, and owned/wanted/loaned status. Retain the last five searches and allow up to five pinned favourites. Each entry contains both search text and filters and belongs to the profile across devices. This establishes the desired scope without committing cross-device synchronisation to a release. When five favourites are already pinned, ask the user which one to replace before pinning another. Search result presentation remains open.

## Activity panel

- Unfinished tasks appear in a hub activity panel with **Retry** and **Dismiss** actions.
- Dismiss hides an unfinished task from the action list while retaining its details and history.
- Group activity by operation and module, for example Book imports, Music metadata downloads, and Suite backups.
- For each category, show the last successful task and the last failed attempt for that person and device.
- Each successful or failed output provides a link to a detailed description.
- Details show the time, module, operation, affected items, completed/unfinished counts, errors, and suggested next steps as applicable.
- Interrupted tasks have their own status and do not replace the last failed attempt merely because they were interrupted. Failed attempts represent actual errors.
- Retain completed work when a task is interrupted; report the unfinished work for retry.

A **Show dismissed/history** view lets users inspect and retry dismissed tasks. History retention duration and the full category list remain open. Dismissal itself does not delete a task's record.

## Shared collections and roles

Profiles can access personal and shared collections. A family movie library, for example, shares catalog information while each person retains their own ratings and watched status.

- Support owner, editor, and viewer roles.
- The owner manages roles and permission settings.
- Viewers can browse and update personal ratings/status without changing shared catalog details.
- An owner approval workflow allows accepting or rejecting submitted changes, but not modifying submitted content.
- All approval records are logged and visible to everyone with access to the shared collection. Show the submitter, original and proposed values, and the person accepting or rejecting the submission when a decision exists.

**Deferred — ask again later:** Which changes require owner approval, who may submit them, and can editors make any changes directly?

## Backup and settings transfer

Provide settings backup, export, and import. Backup offers separate choices for:

- Settings only.
- Catalogs, artwork, and personal activity.
- Actual media files.

Users can select individual modules or the whole suite.

**Deferred — ask again later:** Can categories be combined, and can users select which profiles and shared collections to include?

Restore behaviour and detailed import/export behaviour remain open.

## Help, user documentation, and release notes

Provide general help and module-specific help through the hub. User documentation, help, and release notes for the relevant features must explicitly explain the following planned behaviour:

> Settings and layout changes are saved immediately for their applicable scope. There is no need to wait until exit to preserve those changes. Save / Discard choices when exiting or switching profiles apply to unsaved catalog edits, not to settings that have already been saved.

> Switching profiles applies to the entire Media-inator suite. The selected person's saved module selection and layout for this device are restored. Modules show that person's settings and accessible collections, including shared collections. Personal ratings and watched status belong to the selected profile.

Also explain:

- One review dialog combines unsaved edits, running-task interruption warnings, and Keep open / Close choices for external players/readers. Save / Discard choices apply per affected module; Cancel stops the whole exit or switch. Individual module closure scopes all three categories to that module. If none requires attention, no review dialog appears.
- Interrupted tasks keep completed work and expose unfinished work through Retry / Dismiss in the activity panel.
- Dismiss hides an unfinished task from the action list while preserving its details/history. Activity is grouped by operation and module for each person/device; latest success and actual failure link to detailed descriptions. Interruption has a separate status.
- The hub close button exits the suite. Minimise-after-launch applies only to separate module windows.
- Startup restores stored user/device settings; without them, the hub and all modules open in tabs.
- Opening or closing modules immediately updates last session; a selected named startup state takes precedence for restoration without being modified. Switching to a profile without saved device settings also opens the hub and all modules as tabs.
- Failed edit saves allow retry and then preserve only unsaved edits in an emergency version. Successful emergency saving permits automatic exit/profile switching with a success banner; the normal catalog save has not succeeded. Show a brief emergency-copy success banner before exit and a recovery notice next launch. Offer Review and recover edits on reopening the affected profile; if emergency saving fails, stop and offer an alternate location.
- Individual module closure uses review limited to that module. Dismissed tasks remain inspectable and retryable through Show dismissed/history.
- Restore last session is the startup default; users can select one of five named states instead. Named states change only on explicit update. Saving a sixth asks the user which state to replace (or Cancel); if it was the startup selection, revert to Restore last session. Ask whether to restore collections only or also playback/reading; media opens paused and books reopen at the saved page/location. Search retains text and filters for five recent searches and five pinned favourites belonging to the profile across devices.
- Missing content does not block restoration of available content; offer Locate / Retry / Skip. Emergency recovery conflicts show current and recovered values side by side for the user to choose. A sixth pinned search requires choosing a favourite to replace.
- Locate offers Use once or Update saved location. Skip applies to the current session and asks whether to keep the item for future restores or exclude it. Exclusion suppresses all restoration references in the current profile, including named states, without deleting associations or content. Re-enabling restores surviving associations, but not those removed through state deletion, replacement, or manual editing. Remove permanently is a separate association-destruction action. Saved-location updates apply to every reference in the current profile, including named states. External players/readers reopen when restoring playback/reading; if position restoration is unsupported, explain the limitation and offer Open normally.
- Last-saved dates change only for explicit state saves or automatic saves of active state progress. Location updates, path remapping, restore exclusions, and cleanup do not alter save timestamps or named-state replacement order. Excluded from Restoration lets users inspect exclusions and re-enable items.
- Distinguish hub-launched applications from existing applications the hub attached to. Attached applications remain open; only hub-opened media/sessions may close where supported. External sessions kept open across a profile switch retain their original profile and progress ownership.
- If an external application cannot close, offer Retry / Leave open and continue / Cancel; avoid force-closing by default. Keep shared applications open while other modules own them and explain why. During global exit, offer explicit Close for all modules.
- Windows from a disconnected monitor move onto a current display and move back to their retained original positions immediately when the monitor returns.

These passages are planned documentation content, not release announcements. Final instructions must reflect resolutions to the remaining open questions.

## Open workflow questions

- Define the full activity category list and history retention.
- Define recovery for partially completed task items.
- Define emergency-version destination, retention, and application to individual module closure.
- Define common controls, the complete panel catalogue, and search result presentation.
- Define controls and confirmation for permanent removal of restoration associations.
- Define treatment of external applications that cannot open paused, and progress reconciliation for sessions left open after the hub exits.
- Define restore and settings import/export behaviour.
- Revisit the two explicitly deferred questions later.

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
