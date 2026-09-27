# M10 technical design — workspace storage and restoration

Status: design, implementation, package verification and installed KDE acceptance complete. Scope: [M10](milestone_10_workspace_restore.md). Implementation evidence: [M10-06 review](test_data/m10_workspaces/m10_06.md). M10-G PASSED / CLOSED.

## Storage and ownership

Add an application-owned `workspaces.json` beside settings.json. Keep current settings schema and search/filter persistence separate. Workspace file schema version 1 contains profile_id, device_id, monotonically increasing revision, last_session, startup (`last_session` or named ID), and up to five named entries keyed by generated UUID. Each entry contains name (named only), explicit saved_at UTC, and snapshot. Single profile/device only; no synchronization.

Snapshot fields: ordered module IDs (Hub required; only Hub/Book-inator supported), active module ID, Book-inator selection identity (library UUID plus book UUID, never title or path alone), Hub geometry (Qt geometry bytes as hex plus normal rectangle, maximized flag, and screen name/available rectangle for recovery). Do not store search text, filters, viewer process IDs, file-reading positions, recovery payloads or dialogs. Library identity guards selection only: restoration does not silently change the configured library.

Actual current arrangement is fixed Hub/Book-inator tabs; validate against that supported arrangement. Do not add tab dragging, docking or floating windows. Unknown module IDs from a newer schema are not instantiated.

Use validated bounded JSON reads (1 MiB), shape/type/range checks and atomic QSaveFile commits, following SettingsStore. Reject duplicate IDs, more than five names, invalid startup references and malformed geometry. Preserve corrupt/unsupported originals, report the problem and disable workspace mutations until explicit repair; do not replace them automatically. Use the existing single-instance ownership plus a workspace-store lock/revision check to reject stale writes. Commit failure retains the last valid file and reports unsaved state.

On first use with no workspace file, derive Last Session from existing bookinator_open/geometry and selection only after catalog UUID lookup. Default startup to Last Session. Preserve existing settings and do not overwrite them merely because a workspace file is absent. Once initialized, workspace structure is authoritative; existing settings remain compatible preference storage.

## Named management and startup

Save captures a coherent current snapshot only when no critical operation is active. Names are trimmed, nonempty, at most 80 characters, and unique case-insensitively; duplicate names offer explicit overwrite or Cancel, never implicit replacement. Rename preserves ID and snapshot. At capacity, show five choices with Replace / Cancel; replacement creates a new ID. Delete requires confirmation. Deleting/replacing the startup-selected ID changes startup to Last Session in the same atomic transaction. Explicit overwrite of the same workspace preserves its ID/startup reference.

Automatic Last Session writes never modify named snapshots. Debounce geometry changes using the existing 250 ms pattern; save module/active-tab/selection changes promptly. Keep named saved_at tied to explicit snapshot saves; renames and maintenance do not pretend snapshot progress was saved. Save startup choice immediately without replacing the layout snapshot.

Startup chooses the named snapshot or Last Session; invalid/missing named selection falls back to Last Session with explanation. Restore only Hub/modules. Missing workspace storage falls back to existing settings. Treat an invalid existing workspace file conservatively as above rather than silently repairing it.

## Restore transaction and existing protections

1. Validate target completely and capture current layout/context before any visible change.
2. Reject while metadata operations, imports, bulk writes, database/file operations or another restore are active. Report operation and require a later explicit retry; never queue an unexpected restore. Defer ordinary catalog reads until idle to avoid stale selection callbacks.
3. Review unsaved metadata with Save / Discard / Cancel, reusing editor validation and conflict/recovery handling. Save must finish with no outstanding draft before proceeding. Failed/partial saves stop restore. Cancel preserves the layout/context and outstanding work; already committed writes from a prior attempted Save are not rolled back.
4. Existing module-close checks remain prerequisites, but workspace restoration must not call the current global close flow unchanged: it offers reader termination and task interruption, both inappropriate here. Refactor review into a workspace-preserving mode. Leave existing external/owned viewers alive under original ownership; do not attach, launch, close or reposition them. If protection cannot be satisfied without such changes, refuse restore and explain.
5. Suppress structural autosaves while applying tabs, geometry and active tab. Stage selection until the target catalog is loaded, using a restore-generation token so older asynchronous loads cannot overwrite it. Commit resulting Last Session only when restore completes. On structural failure, restore the pre-restore layout/context; keep named snapshot intact and report failure. Do not roll back committed metadata.
6. On app shutdown, capture Last Session before tabs are dismantled. Suppress teardown events from recording an empty session. Cancelled shutdown keeps normal tracking active. Release timers and pending restore callbacks on module disposal.

## Selection and shared preferences

Resolve selection using configured library UUID and book UUID. A mismatched library or absent book yields no selection plus an explanation, without changing libraries or blocking remaining layout restoration. Retain the target selected UUID when active shared filters hide it. Display hidden-selection notice with Clear All Filters / Keep Filters. Only explicit Clear All modifies persisted shared criteria; do not make grid row -1 erase the saved selection. Bulk selection is existing transient working state and is not captured in workspaces.

## Monitor fallback

Use QGuiApplication screens and availableGeometry in logical pixels, not fixed physical-pixel assumptions. Attempt saved geometry on a matching available display, then verify the resulting normal rectangle and accessible title bar. If screen missing or geometry unusable, choose current/primary available screen, bound size to available space, center/clamp the window and reapply maximization if requested. Do not claim exact top-level positioning on Wayland: compositor placement may override coordinates; acceptance is visible, accessible windows. Handle screen removal while running as well as startup. Keep fallback changes in Last Session; never silently rewrite a named snapshot.

## Integration points and verification

Planned components: workspace model/store, restore coordinator, lightweight named-workspace management UI and startup selector. Hub currently owns tabs, geometry persistence, reader lifecycle and close reviews; Book-inator owns catalog selection/filtering. Avoid putting restore logic into the Calibre adapter. Help must explain shared filters, five-state replacement, busy-operation blocking, reader independence and startup fallback.

Required tests: schema/size/corruption/atomic-write failures; revision conflicts; five-name replacement Cancel; startup-ID rename/delete/replace/overwrite behavior; Last Session versus named snapshots; dirty Save/Discard/Cancel and partial failures; active writes prevent mutations; external reader untouched; delayed catalog/selection resolution and filter-hidden selection; missing book/library mismatch; geometry clamp/monitor loss; shutdown ordering; M9 regressions and installed KDE acceptance. Test negative paths as well as success. M10-G PASSED / CLOSED; no elapsed-time requirement.
