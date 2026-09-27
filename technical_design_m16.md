# M16 technical design — Hub foundation

Status: first implementation candidate; desktop acceptance pending. M15 remains Everyday. M16 has independent settings, data and deployment.

## Confirmed appearance decisions

- Scope: current user profile and device, independent of named workspaces. Workspace switching does not change appearance.
- Theme: System / Light / Dark; default System.
- Accent: System plus a curated, tested palette; default System. No RGB/HEX or arbitrary color picker. Proposed palette: Blue, Green, Purple, Orange, Red; exact accessible light/dark variants are implementation details requiring validation.
- UI Size: one combined Small / Default / Large / Extra Large control; default Default. Scale application fonts, icons, row minimums, control spacing and dialog layout minimums together relative to system defaults. Do not change KDE display scaling or multiply a size already scaled by this control.
- Density: Compact / Normal / Comfortable; default Normal. Density adjusts spacing, not a second font multiplier.
- Every change applies and saves immediately. No Apply or Save buttons and no unsaved-appearance prompts. On persistence failure, restore the last successfully saved appearance and present an explanation with Retry / Close.
- Reset appearance requires confirmation because it resets all four controls. Cancel changes nothing; confirm restores System theme, System accent, Default UI size and Normal density only.

## Preservation boundaries

Application-owned controls in Hub, Book-inator and metadata/bulk/history/settings dialogs inherit appearance. Reader presentation, external apps, playback, thumbnails, sort orders, columns and tool-specific state remain local. UI sizing may adjust minimum layout requirements but must not rewrite saved user geometry or workspace layouts as a reset side effect. Keep controls reachable on the current screen through suitable layouts/scrolling.

The owner’s reader-default/accessibility/layout and workspace examples guide long-term ownership. They do not add reader controls, new accessibility toggles or a workspace schema overhaul to M16. In particular, existing per-library saved searches are not migrated into workspaces by this appearance change.

## Hub and module baseline

Tabs only. Hub remains open; close retains coordinated suite exit. Repeat launch focuses an existing module tab. Book-inator is available; Music, Movie, Game, Paper, Document, Stamp, Picture and Currency modules appear as disabled Planned tiles. Paper is for scientific research papers; Document is for other documents. Planned tiles cannot launch, including via restore or launch-all.

Use an internal registry with stable module IDs and explicit availability; no executable/plugin discovery or module installation UI. Book-inator adapter delegates to existing launch, close, recovery, activity and workspace paths.

## Proposed implementation choices

Extend validated atomic preferences with an appearance section; missing section uses defaults without replacing profile identity or unrelated settings. Preserve unsupported/corrupt files and report errors under existing settings policy. Named workspace snapshots do not capture or overwrite appearance.

A central appearance controller derives every rendered size from captured system baseline values plus the selected UI-size factor. A theme-aware palette supplies readable foregrounds, selection and focus states for all supported accents. System mode follows desktop changes where supported, with a documented fallback if an accent cannot be obtained. Apply styles to application-owned UI only; OS-owned title bars remain under KDE control.

Test combinations of three themes, six proposed accent choices, four UI sizes and three densities with targeted pairwise/boundary coverage plus ordinary KDE acceptance. Cover open and newly opened dialogs, repeated size changes without cumulative growth, reset/cancel, restart, workspace switching, save failures and unchanged external/tool settings.

## Confirmed Hub layout

The Hub home presents ecosystem module tiles first, then the existing collapsible Activity panel, with a dedicated visible Settings entry. Tiles represent Book-inator and the agreed planned ecosystem modules. The owner’s Catalog/Reader/Metadata/Imports sketch illustrates action-first layout, not new standalone modules or approval to duplicate Book-inator tools in the Hub. Preserve recovery notices and existing Activity/history actions when collapsed.

## Confirmed appearance transaction

1. Retain the last successfully persisted appearance.
2. Apply the requested appearance immediately as a preview, including Settings controls and existing application dialogs.
3. Attempt the existing atomic settings persistence while preserving unrelated settings.
4. On success, advance the saved appearance baseline.
5. On failure, restore the previous saved appearance AND corresponding Settings control values. Present “Unable to save appearance settings. The previous appearance has been restored.” with Retry / Close and optional error details.
6. Retry reapplies the same requested change against current unrelated settings and attempts persistence again. Close dismisses the error; the previous appearance stays active. Do not discard other unsaved catalog work or close the Settings window/application as a side effect.

Reset appearance first requests confirmation. Cancel does nothing. Confirmation uses the same preview/persist/rollback transaction for all four defaults together. Never reset layouts, module configuration, reader/tool preferences or workspace state.

KDE/system scaling remains the foundation; application UI size is a relative adjustment derived from baseline values, not cumulative changes to already-scaled values.

Tests must cover consecutive successful changes followed by failure, failed reset, Retry after unrelated settings change, repeated failure, Close after failure, and control/rendered-state agreement with persisted appearance. Error handling must not recursively trigger preference writes through widget signals.

## Remaining technical specification work

- Concrete scaling factors, accessible palette values, System-accent fallback, settings schema validation and adapter interfaces will be specified during design; no speculative controls.

## First candidate implementation

- Internal immutable registry uses stable module IDs; launch guard rejects unknown/planned IDs. Book-inator delegates to existing lifecycle paths. Hub Activity starts collapsed with recovery notices retained outside it.
- Optional validated `appearance` section in schema 1 keeps existing preferences compatible. Missing section supplies defaults without replacing identity. Atomic QSaveFile persistence preserves unrelated in-memory settings.
- UI factors: Small 0.9, Default 1.0, Large 1.2, Extra Large 1.4. Density padding: 2/4/7 logical pixels before UI adjustment. Font baseline captured once per process; table row minima derive from font metrics. Book thumbnails remain local.
- Curated accents: Blue #245ca6, Green #226b43, Purple #75449c, Orange #914900, Red #aa3038. Selection foreground chooses black/white from WCAG relative luminance. System accent uses startup Qt highlight; restart picks up desktop accent changes. System theme follows Qt color-scheme notifications, using the startup platform palette when no scheme is reported.
- KDE visual acceptance is still required for real platform styling, display scaling, keyboard focus and small-window reachability. Offscreen tests do not establish desktop acceptance.
