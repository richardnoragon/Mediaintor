# Media-inator Hub Constitution

M10 delivery scope: workspace persistence covers existing Hub/Book-inator tabs, active tab, selected book and geometry only. Shared search/filter preferences remain independent; hidden selections are explained with an explicit Clear All option. Critical operations block switching. External readers remain untouched, and docking/floating windows are not introduced. Broader reader restoration and windowing requirements below remain future scope. [Final M10 plan](../milestone_10_workspace_restore.md).

Current M5 status: **M5 COMPLETE; M5-G PASSED / CLOSED** following final evidence review and user desktop acceptance. [Gate review](../test_data/m5_acceptance/gate_review.md). All M5-01–M5-07 tasks are complete. Earlier dated/stage checkpoints are historical; no release is implied.

Status: Planning baseline derived from recorded user decisions. Initial delivery direction is recorded in [First Release Scope](../first_release_scope.md); detailed feature scope remains open. No implementation is authorised by this document.

## 1. Purpose and authority

The hub is the required entry point and shared control centre for Media-inator. This constitution defines the principles and behavioural commitments that hub planning must preserve.

“Must” describes an agreed requirement. “Open” and “deferred” describe unresolved decisions, not permission to invent defaults. The constitution does not claim that planned features have shipped.

Explicit user decisions take precedence. This constitution consolidates them; the hub overview describes purpose, the features document specifies workflows, and the configuration document records options, scope, and defaults. If these documents disagree, reconcile them against the recorded decisions rather than silently selecting a convenient interpretation.

Reference-product descriptions and suggestions in the rough scaffold are evidence and inspiration, not automatically approved requirements. Changes to agreed behaviour must be identified explicitly and reflected consistently in the affected planning documents. Implementation remains outside the current planning phase.

## 2. Hub responsibility and module boundaries

The planned module family is Movie-inator, Music-inator, Book-inator, Game-inator, Stamp-inator, and Currency-inator. The hub must coordinate launching, windows, profiles, common settings, restoration, search, activity, backup controls, and help.

Specialist collection operations belong in their module specifications. The book, music, and movie references describe physical and digital collections, editions, people, metadata retrieval, loans, reports, custom fields, imports, and playback. These inform module planning without turning every such function into a hub feature or requiring identical behaviour for all six collection types.

Initial delivery targets the project owner's personal use on Linux, with Book-inator as the first complete module workflow on one device. Synchronisation is deferred until later. Detailed hub/book feature deliverables, Linux distribution support, other module availability, and later platform/sync timing remain open. The all-modules startup rule does not itself promise that all six modules ship together. See [First Release Scope](../first_release_scope.md).

## 3. Profiles, shared collections, and ownership

- A personal profile owns a person's collections and settings. A reusable preference preset holds appearance/layout choices; it is not a person or collection owner.
- Modules inherit shared preferences and permit their own overrides. Common preferences include font size, light/dark/system/user-defined themes, and language.
- Module selection, docking, panels, window size, and window position are saved for each person and device, with window geometry tracked per module.
- Switching profiles changes all hub module windows to the destination profile and restores that person's module selection and device layout. No module window remains assigned to the previous person.
- External sessions deliberately kept open are an exception to module-window switching: they retain their original profile ownership. Any tracked reading or playback progress must never be attributed to the newly active profile.
- Shared collections separate common catalog information from personal ratings and watched/read status. They support owner, editor, and viewer roles. Owners manage role/permission settings; viewers may browse and update personal ratings/status without editing shared catalog details.
- The owner approval workflow permits accepting or rejecting submitted content, not modifying the submission. All approval records are visible to everyone with access to the shared collection and identify submitters, original/proposed values, and decision makers where a decision exists.

Which submissions require approval and which changes editors may make directly are explicitly deferred.

## 4. Predictable startup and saved states

The hub must launch before modules. Users can launch individual modules or all modules, using tabs, docked windows, or separate windows.

Restore last session is the default restoration mode. Users can instead select a saved named state. Choosing the last active profile or a profile chooser is configurable; the default for that separate choice remains open.

Without settings for the selected person and device, open the hub and all modules in tabbed view. This fallback also applies when switching to a profile without saved device settings.

The profile may contain up to five user-named states covering module selection, layouts, and collection context, with playback/reading context available for restoration. Named states change through explicit saves, apart from the metadata-maintenance rules below. Active last-session progress continues saving automatically even when a named state is selected for startup.

Saving a sixth named state requires the user to select which existing state to replace, with Replace / Cancel. Cancel preserves every state; there is no automatic oldest-state replacement. If that state was the startup selection, revert to Restore last session. Suite shutdown must preserve the selection from before shutdown rather than recording every module as intentionally closed.

Restoration asks: **“Would you like to restore the collections only, or also playback/reading?”** When included, media opens paused at its saved position and books reopen at their saved page/location. Reopen configured external applications where applicable. If position restoration is unsupported, explain the limitation and offer Open normally; do not silently claim to have restored a position.

Move windows from unavailable monitors onto a current display, retain their original positions, and move them back immediately when the monitor returns.

## 5. Settings persistence and meaningful timestamps

Settings and layout changes must save immediately. Unsaved catalog edits are a separate category governed by review and recovery. Discarding catalog edits does not undo settings already saved.

**Last-saved date changes only for an explicit state save or an automatic save of active state progress.** Automatic progress saving does not overwrite named snapshots.

Profile-wide location updates, path remapping, restoration exclusions, re-enabling exclusions, and cleanup modify metadata without changing save timestamps. Replacement is chosen explicitly by the user, not determined by timestamps. User-authorised maintenance may affect references inside named states without replacing the rest of their saved contents.

## 6. Missing content, exclusion, and permanent removal

Unavailable content must not block restoration of available content. Offer Locate / Retry / Skip for missing collections or media.

Locate offers:

- **Use once:** use the location for this session without replacing the saved reference.
- **Update saved location:** update every reference to the item in the current profile, including named states, without modifying other profiles.

Skip applies to the current session and asks whether to keep the item for future restores or exclude it. Exclusion applies across the current profile's restoration references, including last session and named states.

**Exclude means temporary suppression. Remove permanently means destroying restoration associations.** Neither action is a synonym for deleting a catalog entry or media file.

The Excluded from Restoration list must preserve associations and allow re-enabling. Re-enabling automatically restores all surviving previous associations. It must not recreate associations whose state was deleted, overwritten, or manually edited to remove the location. Exclusion information must remain usable for this undo behaviour, future features, and migrations.

Permanent-removal controls and confirmation remain open. Earlier wording “Remove from future restores” refers to temporary exclusion, not permanent destruction.

## 7. One review for consequential session changes

Hub exit and profile switching must use a combined review covering only categories needing attention:

| Category | User control |
| --- | --- |
| Unsaved catalog edits | Save / Discard per affected module |
| Running tasks | Explain interruption and request confirmation to proceed |
| External applications/sessions | Keep open / Close, subject to ownership and capabilities |
| Entire operation | Cancel the exit or profile switch |

Closing an individual module uses the same review scoped to that module's edits, tasks, and external sessions. If no category needs attention, proceed without a review prompt.

Before confirmation, Cancel must leave pending save/discard choices unapplied, tasks uninterrupted, and external applications unclosed. Actions begin only after confirmation. Preserve completed task work and report unfinished work for retry. Recovery of a partially completed item remains open.

The hub close button exits the suite after review. Minimise-after-launch is a different configurable action and applies only to launching a separate module window, never a tabbed/docked module.

## 8. Conservative external-application control

Distinguish applications the hub launched from existing applications it merely attached to. Track ownership of each media/session by originating profile and module separately from application launch ownership. A reference count or ownership list is the recorded design approach; no code or integration mechanism is prescribed here.

- Attached applications stay open. Close only the hub-opened media/session where supported, leaving unrelated content untouched.
- When another module still uses an application, keep it open and explain which modules need it.
- Carry out a requested application close only when module owner count is zero, or the user explicitly chooses Close for all modules during global exit. Zero owners permits closing; it does not override Keep open.
- Close for all modules respects attached-application boundaries and does not authorise closing unrelated content.
- If closing is unsupported or fails, offer Retry / Leave open and continue / Cancel. Avoid force-closing by default.
- Keeping an external session open across a profile switch never transfers its ownership or progress to the new profile.

Behaviour for integrations unable to open paused and progress reconciliation after the hub itself exits remain open. Requirements must not promise capabilities an external application cannot provide.

## 9. Failed-save recovery must be explicit

If a catalog edit cannot save during exit or profile switching, allow retry. If retry fails, create an emergency version containing only unsaved edits, not a full catalog backup.

Successful emergency saving allows the requested exit/switch to continue automatically, with a success banner clearly identifying the emergency copy. On exit, briefly show the banner before closing and show a recovery notice on next launch. When the affected profile reopens, offer Review and recover edits.

If emergency saving also fails, stop the exit/switch and offer an alternate save location. An emergency copy must not be represented as a successful normal catalog save. Where catalog values changed in the meantime, display current and recovered values side by side and let the user choose.

Default storage, retention, and applying this emergency workflow to individual module closure remain open.

## 10. Optional panels, search, and accountable activity

The default hub provides launch buttons and common controls. Users can add, remove, move, and resize panels, including collection counts, recent items, loan reminders, cross-module search, and activity. The complete panel catalogue and initial panel selection remain open.

Search must include accessible collections in closed modules, identify those modules as closed, and open the relevant module/item on selection. Filters include module, collection, and owned/wanted/loaned status.

Keep five recent searches and up to five pinned favourites, each containing text and filters. These belong to the profile across devices; this scope does not commit synchronisation to a first release. Pinning a sixth favourite asks which one to replace, consistent with the user-selected named-state replacement rule.

Activity must be grouped by operation and module for each person/device. Show the latest successful task and latest failed attempt per category, with detailed links containing time, module, operation, affected items, completed/unfinished counts, errors, and suggested next steps as applicable.

Unfinished tasks offer Retry / Dismiss. Dismiss hides the action without deleting details/history; Show dismissed/history permits inspection and retry. Interrupted is a separate status and must not replace the latest actual failure merely because work was interrupted. History retention remains open.

## 11. Backup and data boundaries

Provide settings backup, export, and import. Offer separate backup choices for settings only; catalogs with artwork and personal activity; and actual media files. Users can select individual modules or the whole suite.

Keep settings transfer, catalog backup, emergency edit recovery, and media-file backup distinct in planning and user explanations. No one operation may be described as preserving data outside its defined scope.

Category combinations and profile/shared-collection selection are explicitly deferred. Backup destinations, schedules, retention, restoration, and detailed import/export behaviour remain open.

## 12. Reference-informed evolution without premature technology decisions

The rough scaffold records the user's interest in manual and automatic ingestion, copying/renaming, metadata extraction, thumbnail generation, external launching, cross-platform use, and adding synchronisation later. LAN-first followed by possible cloud expansion was explored. These are planning context; hub responsibilities and delivery scope must be specified before adopting particular solutions.

No database engine, UI framework, schema, server topology, storage provider, sync algorithm, authentication scheme, plugin system, or first-release roadmap is selected by this constitution. Technical assertions and migration promises in the conversation scaffold are not adopted as validated requirements.

Reference-product features such as barcode scanning, internal players, device conversion, provider scripts, reports, passwords, and custom fields remain candidates unless separately agreed. Reference settings such as automatically marking loans returned when a location changes are not inherited by Media-inator.

## 13. Documentation and change discipline

Provide general and module-specific help. Help, user documentation, and relevant release notes must explain immediate settings saving, suite-wide profile switching, external-session ownership, combined review, emergency recovery, restoration choices, exclusions, timestamp rules, activity outcomes, and the differing state/favourite replacement policies.

Keep planned documentation separate from claims of released functionality. A change to an agreed rule must update the constitution and affected overview/features/configuration passages together. Preserve explicit unresolved/deferred status; do not use a reference product or technical convenience to decide an open user-facing behaviour silently.

## 14. Outstanding decisions

The constitution does not resolve these remaining items:

- Detailed first-release hub/book deliverables and Linux environments; later platforms and LAN/cloud scope/timing. Personal use, Linux, books first, and one-device initial operation are decided.
- Defaults for profile selection and post-launch hub behaviour; initial panels, languages, and appearance.
- Named-state device handling, preset contents/precedence, reset and removal controls, and remaining preference scopes.
- Emergency-copy storage/retention and use on individual module closure; partially completed task recovery; activity retention.
- External player/reader configuration scope, unsupported paused opening, and progress reconciliation after hub exit.
- Permanent association-removal controls; search presentation; detailed common controls.
- Backup restoration and settings import/export behaviour.

Explicitly deferred at the user's request: owner-approval scope/editor submission rights, and backup category combinations/profile/shared-collection selection. Revisit these separately; their omission is intentional.

## 15. Source register

All thirteen Markdown documents present before this constitution were considered. Links point to workspace sources; captured product pages are treated as reference snapshots, not claims about current third-party products.

| Source | Contribution and authority |
| --- | --- |
| [Hub overview](mediainator%20hub%20overview.md) | Agreed hub purpose and behavioural summary |
| [Hub features](mediainator%20hub%20features.md) | Agreed workflows, ownership, recovery, documentation obligations, and open decisions |
| [Hub configuration](mediainator%20hub%20config.md) | Agreed options, persistence, defaults, scopes, and configuration questions |
| [Book overview](../bookinator/bookinator%20overview.md) | Reference: physical/electronic/audio books, locations, authors, reader transfer |
| [Book features](../bookinator/bookinator%20features.md) | Reference: editions, loans, search, metadata, reports, imports, custom fields |
| [Book configuration](../bookinator/bookinator%20config.md) | Reference: appearance, providers, players, backup prompts, scanning options |
| [Music overview](../musicinator/musicintor%20overview.md) | Reference: albums, artists, physical/digital collections, playback |
| [Music features](../musicinator/musicinator%20features.md) | Reference: scans, metadata, loans, search, reports, backups, custom fields |
| [Music configuration](../musicinator/musicinator%20config.md) | Reference: shared preference themes and music-specific provider/player settings |
| [Movie overview](../movieinator/movieinator%20overview.md) | Reference: physical/digital movies, people, technical metadata, ratings |
| [Movie features](../movieinator/movieinator%20features.md) | Reference: TV series, editions, multiple catalogs, snapshots, loans, search, imports |
| [Movie configuration](../movieinator/movieinator%20config.md) | Reference: appearance, metadata downloads, players, backup prompts, file-reading options |
| [Rough scaffold](../mediainator%20rough%20scaffold.md) | Historical user goals and exploratory assistant suggestions; not an approved technical specification |

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
