# M16 — Hub Foundation & Module Integration

Status: **M16-G PASSED; promoted to Everyday.** Build `0.1.0a1-c663cfd06375b1f1`. M15 is stopped Rollback; M14 and older installations are unchanged. See `test_data/m16_hub/acceptance.json` and `promotion.json`. Earlier stage notes below are historical and superseded.

## Purpose

Make the Hub the ecosystem's common control centre and module launcher, not a second book catalog. Support future modules without embedding their specialist collection behavior in the Hub.

## Source review

- `mediaintor hub/constitution_hub.md`: product authority, module boundaries, immediate preference persistence, safety and future ecosystem requirements.
- `mediaintor hub/mediainator hub overview.md`: central launch/control role and module family.
- `mediaintor hub/mediainator hub features.md`: launch, lifecycle, activity, settings and help workflows.
- `mediaintor hub/mediainator hub config.md`: shared preference inheritance and local layout/view choices; numerous future defaults remain open.
- `mediaintor hub/m16 draft.md`: updated owner-supplied planning conversation reviewed. It supports prioritizing ecosystem integration, presents candidate module visibility/shared-settings choices, and records the owner’s explicit request for configurable post-launch behavior. Copilot recommendations are proposals rather than automatically accepted requirements. Historical M12/M13/RC-trial claims in the transcript do not override the current accepted M15 baseline or reinstate the retired observation condition.
- Current code: `mediainator/window.py` already provides Hub, Book-inator tab launching, workspace/help menus, activity/recovery and coordinated shutdown. `mediainator/settings.py` provides validated atomic preference saving. Existing functionality is a baseline, not new M16 deliverables.

Older documents contain historical M5/M10 checkpoints and broader planning promises. Their presence does not mean those features shipped or must all ship in M16. Latest explicit owner decisions take precedence.

## Decided appearance boundary

Shared global UI presentation includes ONLY:

1. Theme: System, Light, Dark.
2. Accent color.
3. Base font size / UI scaling.
4. Density: Compact, Normal, Comfortable.

The Hub owns these common controls. Proposed default: preserve system appearance, system accent/font/scale and Normal density. Exact scaling mechanism and safe range are technical-design work; do not apply two independent multipliers accidentally.

Global appearance must not overwrite tool-specific preferences or serialized layouts. Catalog grid/list choices, thumbnail size, panel layout, workspace geometry and bulk-editor window sizing remain local to their owning tool. Reader fonts, EPUB/PDF colors, playback preferences and external application themes remain outside Hub appearance control. Media-inator must not change system-wide KDE settings or another application's configuration.

Owner-approved inheritance: ordinary buttons, labels, fields, checkboxes, radio buttons, dropdowns, tables/lists, application-controlled dialog chrome and general spacing in metadata, bulk-edit, history, settings and other application dialogs inherit all four global appearance settings. Feature-specific options, preview/editor state, geometry, columns, sort order, thumbnail sizes and media layouts remain local. OS-controlled title bars remain governed by the desktop; no KDE-wide appearance changes are implied.

Window decoration/rounding modes are not included in the final four-setting decision. Custom theme designers, translated UI catalogs and new playback interfaces are not implicitly included.

## Updated-draft reconciliation

- Strategic recommendation incorporated into this proposal: focus M16 on proving the ecosystem foundation; limit Book-inator additions to bug fixes and demonstrated integration needs. No unrelated book-feature expansion.
- Explicit owner decision in the transcript: post-launch Hub behavior should be configurable with a default. The actual choices/default remain unresolved; Minimize as default and Close as an option were Copilot recommendations.
- Owner subsequently explicitly approved disabled future-module tiles labelled Planned. Include an explanatory tooltip; no launchable placeholders or release-date promises.
- Owner explicitly limited functioning common settings to theme, accent color, font/UI scaling and density. Language translation, logging controls, update channels and storage/backup-location controls are out of M16 scope until their underlying workflows are designed and implemented.
- Docker and network preferences are recommended for later work; no current scope requires them.
- A Hub-only launch, stable module identities, availability status and repeat-launch focus fit the proposed foundation. They do not require runtime plugin installation or Docker discovery.

### Decided M16 launch and lifecycle behavior

Owner selected Option 1: M16 uses a tab-based Hub. Book-inator and future available modules open inside the Hub interface. The Hub remains the primary application window and stays open while modules are in use. Opening a module selects its tab; launching it again focuses that existing tab. The Hub is not automatically minimized or closed after launching a module.

Hub close continues to initiate suite exit with existing edit/task/reader review. Closing an individual module remains scoped to that module and leaves Hub open. Existing workspace restoration continues to apply to tabs.

Independent/detached module windows and Hub-independent operation are deferred to future milestones, without committing them to a particular milestone number. The earlier request for configurable post-launch behavior remains a future requirement for separate-window delivery; M16 must not add an inert or misleading Stay open / Minimize / Close selector.

## M16 delivery scope

- Hub module launcher showing available modules and clearly distinguishing future modules. Book-inator is the first working integration.
- A small internal module registry/adaptor boundary for identity, availability, opening/focusing, lifecycle review, activity and help. No downloadable plugin marketplace or arbitrary executable launcher.
- Repeated Open Book-inator focuses the existing tab; no duplicate instances or accidental reader launch.
- Shared appearance settings with immediate persistence, live updates where safe, and clear failure feedback.
- Existing Book-inator tab behavior, named workspaces, activity/recovery and help remain accessible through the Hub.
- Explain what settings are global and what remain local. Do not expose disabled controls as if future capabilities work.
- Isolated M16 environment from a verified accepted baseline, with independent writable data and explicit gate/promotion separation.

## Decided ecosystem names

| Module | M16 availability / purpose |
| --- | --- |
| Book-inator | Available; first working Hub integration |
| Music-inator | Planned |
| Movie-inator | Planned; correct name, no Video-inator module |
| Game-inator | Planned |
| Paper-inator | Planned; scientific research papers |
| Document-inator | Planned; recording/saving other documents in other formats |
| Stamp-inator | Planned |
| Picture-inator | Planned |
| Currency-inator | Planned |

The ecosystem remains extensible. Paper-inator and Document-inator are separate modules, not alternate names. Their detailed features are outside M16. Use stable internal IDs independent of display labels. Only Book-inator is launchable in this milestone; other tiles are disabled and marked Planned.

## Proposed later work

Separate/docked module windows and Hub-independent operation; multi-person profile switching and shared permissions; cross-module search and its favorites/history; movable dashboard panels; new reader/player restoration capabilities; synchronization; automatic backups and new catalog/media restore workflows. Existing supported workspaces and backup procedures stay intact. These are broader product requirements retained for later scope decisions, not rejected requirements.

## Work breakdown

| Work item | Deliverable | Exit evidence |
| --- | --- | --- |
| M16-01 source reconciliation and scope | Confirmed module/appearance/lifecycle boundaries, explicit later-work list | Owner decisions linked to source requirements |
| M16-02 technical design | Registry, Book-inator adaptor, preference schema/migration, styling ownership, lifecycle integration | Reviewable design and failure cases |
| M16-03 isolated environment | Independent deployment and baseline backup | Mount isolation and baseline hashes |
| M16-04 Hub launcher | Available/planned module presentation and Book-inator focus/open behavior | Behavior and lifecycle tests |
| M16-05 common appearance | Four global settings with local-tool boundaries | Persistence, live-change, accessibility and boundary tests |
| M16-06 integration and help | Workspaces/activity/recovery/help preserved; settings scope documented | Regression and help review |
| M16-07 packaged verification | Install/upgrade/reinstall and retained-state checks | Isolated installed tests and artifacts |
| M16-08 owner acceptance | Desktop checks and saved-state review | M16-G gate record |

## Proposed M16-G acceptance

- Hub exposes common settings and module launching without requiring Book-inator to be open.
- Only actually available modules launch; repeated launch focuses one instance; planned modules are plainly unavailable and do not create empty sessions.
- Closing a module preserves Hub; Hub exit retains existing guarded review, cancellation and external-reader ownership behavior.
- Theme/accent/font-or-scale/density update supported application controls consistently, survive restart, and never rewrite catalog records or external-reader settings.
- Tool-specific views, geometry and saved workspaces remain independent. Named workspace restoration does not unexpectedly overwrite global appearance.
- First use adopts system-compatible defaults; existing preference files load with safe new defaults, preserve identity and settings, and remain recoverable. Unsupported/corrupt settings are not silently discarded.
- A failed preference save clearly reports non-persistence; do not claim success. No restart is needed for ordinary safe appearance changes.
- Normal keyboard navigation, contrast, readable focus/selection and reachable controls work at supported scaling/density combinations on the acceptance KDE setup.
- M15 reading/import/bulk/revert/recovery/search/workspace and Calibre compatibility regressions pass; accepted Everyday data remains unchanged.
- Verified package and focused owner checks pass before gate closure. Gate closure does not automatically promote M16.

## Definition outcome and technical-design choices

No product-scope questions remain from the clarification round. Technical design should specify validated appearance ranges, system defaults, accessible accent handling, density metrics, migration and error behavior, registry contracts and tests. These routine implementation choices can be proposed without reopening the decided scope; ask only if evidence requires changing it.

The updated draft resolved the earlier source discrepancy; no NAS migration belongs to M16.

## Decided module availability presentation

Unimplemented modules appear as disabled tiles with an identifiable icon/artwork and a visible **Planned** badge. Tooltip: “This module is planned for a future release and is not yet available.” Keep the label readable; do not rely on fading or color alone. Planned tiles cannot launch through mouse, keyboard or restored workspace references, and must not open placeholder windows. Existing module availability checks must still reject unavailable launches even if a UI control is bypassed.

Available modules can launch; opening an already-open module focuses its tab. Planned modules are excluded from “launch all” and first-run restoration of available modules. Their presence in the catalog is not a claim they are installed.

Experimental and Disabled are useful proposed future states. Do not invent experimental-mode, licensing, installation or dependency-management workflows for M16 solely to populate these states. Technical design may reserve extensible state identifiers, while M16 implements the agreed Available/Planned behavior and truthful errors for failed launches.

## Decided common-settings scope

M16 implements exactly Theme, Accent color, Font/UI scaling and Density as functioning common settings. A setting is exposed only when it controls an implemented workflow. No inactive language, logging, update-channel or storage/backup-location controls. Existing help, diagnostics, package procedures and backups remain available; this scope decision does not remove existing capabilities. External reader/player settings remain untouched.

## Appearance boundary acceptance examples

- A theme/accent/font/density change is reflected in open and subsequently opened metadata, bulk-edit, history and settings controls, including readable focus, selection and disabled states.
- The same change preserves draft edits, pending previews, selected columns, sort orders, saved dialog geometry and workspace data. Density may change rendered row/spacing metrics without rewriting those preferences.
- No EPUB fonts/themes, PDF presentation, audio/video/subtitle preferences or external application settings are modified.
- Only application-owned chrome is styled; operating-system window decorations are not claimed to be under application control.

## Confirmed technical-design inputs

Owner approved profile/device-scoped appearance independent of workspaces; one combined UI Size control; curated accents plus System; defaults System/System/Default/Normal; immediate apply and persistence; Reset appearance confirmation only. See [technical design](technical_design_m16.md). Reader controls and new workspace semantics are not added by the ownership examples.

Owner technical-design decisions: module tiles first, existing collapsible Activity below, dedicated Settings entry; appearance changes preview immediately then persist, reverting to last saved appearance on failure with Retry / Close. Reset affects only appearance. These settle the outstanding layout and save-failure behavior questions. Concrete internal interfaces, palette/scaling values and verification plan remain technical specification work.

## First implementation candidate (2026-09-26)

Hub registry/tiles, disabled Planned modules, dedicated Settings, existing Activity integration, shared appearance, atomic-save rollback/Retry and confirmed reset are implemented. M16 Development is isolated from a verified closed M15 backup. M15 Everyday is unchanged. Source/package evidence lives in `test_data/m16_hub`. Desktop acceptance remains OPEN; no promotion authorized or performed.
