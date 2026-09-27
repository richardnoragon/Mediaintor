# Music-inator Constitution

Status: Planning baseline; first-release decisions accepted 2026-09-26 (section 8a). Inherited hub requirements are agreed; module-specific reference features and proposed modelling principles require confirmation. This document authorises no code. Initial delivery direction is personal use on Linux, books first, one device, and synchronisation later; detailed feature scope remains open. See [First Release Scope](../first_release_scope.md).

## 1. Authority and scope

Music-inator is the specialist music-collection module within Media-inator. Its reference material covers albums, tracks, artists, physical recordings, digital audio, discographies, locations, and playback.

The [hub constitution](../mediaintor%20hub/constitution_hub.md) governs common behaviour. Explicit user decisions take precedence. “Must” below describes inherited requirements; “candidate,” “proposed,” and “open” do not mean approved features. Resolve conflicts through the recorded decisions and update affected documents together.

The module's existing overview, features, and configuration files are captured third-party reference material, not specifications already approved for Media-inator. Their product versions, supported formats, provider integrations, operating systems, shortcuts, and settings defaults must not be copied as commitments.

## 2. Required integration with the hub

- Launch through the hub, with tabs by default and support for docked or separate module windows. First-use startup and profile switching follow the hub's user/device fallback rules.
- Inherit common font, theme, and language preferences while permitting module overrides. Save settings immediately; remember layout and window geometry by person, module, and device.
- Participate in suite-wide profile switching, restoring the destination profile's selection and layout. Personal activity and ratings remain distinct from shared catalog information.
- Apply the shared owner/editor/viewer model. The scope of owner approval and direct editor changes remains deferred; this module must not invent a different policy.
- Make accessible collection results available to hub search even when the module is closed. Selecting a result opens this module at the selected item. Hub search-history and favourite limits are suite policies, not separate per-module allocations.
- Participate in the hub's five named states and automatic last-session saving. Do not create an independent five-state allowance per module. Named states change on explicit saves; maintenance must not alter last-saved timestamps or replacement order.
- Report task activity by operation/module and person/device, including detailed outcomes, latest success/failure, and a separate interrupted status. Retain completed work and expose unfinished work for Retry / Dismiss; dismissal retains inspectable history.
- Participate in settings transfer and the separate backup scopes for settings, catalogs/artwork/personal activity, and media files, for this module or the suite. Emergency edit copies are not backups of the whole catalog.

The hub retains responsibility for common controls and orchestration. Specialist metadata, collection editing, filters, and approved domain operations belong in module planning; no process boundary or storage implementation is implied.

## 3. Reference-derived candidate capabilities

These are a structured inventory for decisions, not mandatory scope or a release checklist.

| Area | Reference-derived candidates | Decision still needed |
| --- | --- | --- |
| Collection coverage | Albums and tracks on vinyl, CDs, cassettes, audio DVDs, and digital files. | Which collection types and audio formats are supported? |
| Adding music | Album-title lookup, audio-CD entry, barcode entry/scanning, audio-folder scanning, and manual editing. | Which methods and matching rules are wanted, including compilations and multi-disc releases? |
| Album and artist information | Covers, track lists, reviews, genres, biographies, photos, and discographies. | Which providers and fields are supported, and how are artist/release matches resolved? |
| Organisation | Search, filtering, custom lists/fields, physical location and disc numbering, wish lists, and loans. | How are releases, owned copies, files, and personal preferences distinguished? |
| Listening | Album/track playback through external players or an optional internal player. | What constitutes a saved listening session: track position, album order, queue, or playlist? |
| Reporting and transfer | Statistics, printable reports/CD covers, catalog exports, and backups. | Which outputs and migration formats are useful; are hardware-player catalogs wanted? |

## 4. Music-specific planning distinctions

The following are proposed modelling principles derived from the references, pending user confirmation; they are not a database schema:

- Distinguish album/release, disc, track, owned copy, and audio file. Remasters, compilations, and multi-disc editions require explicit grouping decisions.
- Treat artists and their discographies as information that may include music outside the owned collection; metadata retrieval must not silently establish ownership.
- Separate personal ratings/listening activity from shared album and artist metadata. Define whether preferences attach to tracks, albums, or releases before assuming one scope.
- Keep physical-copy locations, loans, digital paths, and playback positions separate. Do not inherit automatic loan returns on location changes from the reference product.

The hub's approved restoration rules apply: restore audio paused at its saved position where supported, and retain the original profile's ownership when an external session stays open across profile switching. Queue restoration, shuffle/repeat, gapless playback, playlists, and play-count rules have not been agreed. Audiobook cataloguing is a Book-inator reference capability; whether Music-inator also lists such files is an open cross-module question.

## 5. Restoration and external application ownership

The module must honour Locate / Retry / Skip for missing content while allowing available content to restore. Use once leaves stored locations unchanged; Update saved location updates every reference in the current profile, including named states.

Exclusion temporarily suppresses restoration across the profile while preserving associations. Excluded from Restoration allows re-enabling surviving associations; deleted, overwritten, or manually removed associations must not be recreated. Permanent removal destroys associations and is distinct from deleting media or catalog entries. Maintenance does not change state save timestamps.

Distinguish hub-launched applications from existing applications the hub attached to. Track originating profile/module ownership of sessions. Attached applications and unrelated content remain open; only hub-opened sessions may close where supported. Keep shared applications open while another module needs them and explain why. Keep open across profile switching retains original profile/progress ownership.

The combined review offers Keep open / Close and respects the hub's owner-count and global Close for all modules rules. Failed closure offers Retry / Leave open and continue / Cancel; avoid force-closing by default. Unsupported position restoration requires an explanation and an offer to Open normally, not a silent fallback.

## 6. Edits, interruptions, and recovery

Closing this module uses one review scoped to its unsaved edits, running tasks, and external sessions. Hub exit/profile switching combine affected modules in the same review. Save / Discard apply to catalog edits; Cancel stops the requested operation before pending actions execute. Show no review when nothing needs attention.

On failed catalog saves during hub exit/profile switching, permit retry and then preserve only unsaved edits in an emergency version if retry fails. Successful emergency saving permits continuation with an accurate banner and later Review and recover edits. If emergency saving fails, stop and offer an alternate location. Recovery conflicts show current/recovered values for user selection.

Emergency storage/retention, applying emergency recovery to individual module closure, and handling partially completed items remain open at suite level. This constitution does not resolve them independently.

## 7. Configuration boundaries

Synopsis length, pagination, album/artist previews, artwork sizing, sort/filter behaviour, provider/download choices, player associations, custom fields, scan options, and backup reminders are candidate settings. File-tag writing, naming rules, provider scripts, and playback-engine choices are not selected by this document.

Approved settings save immediately, unlike the captured reference products' explicit OK-to-save descriptions. Do not silently adopt reference behaviours such as making an item owned on metadata download or marking a loan returned after a location change. Define such choices explicitly if wanted.

Player/reader selection scope, provider credentials, import/export rules, preset precedence, and device-specific options require further planning. Reference password locks do not establish a Media-inator authentication design. No database, framework, schema, sync protocol, plugin runtime, or provider is selected here.

The rough scaffold's manual/automatic ingestion and later-sync goals are planning context. File copying, renaming, metadata extraction, and media storage policies need module-specific decisions; the scaffold's technical suggestions are not binding.

## 8. Documentation and change discipline

Module help, user documentation, and relevant release notes must explain inherited immediate settings saving, profile switching, named-state versus last-session behaviour, recovery, exclusions, and external-session ownership. Explain domain-specific restoration limitations accurately and distinguish collection information, owned media, and personal activity.

When a candidate becomes agreed scope, record the decision and update this constitution and the applicable module planning documents without presenting third-party reference prose as original requirements. Preserve the hub's shared rules and explicitly identify any requested amendment. Do not describe planned capabilities as shipped.

## 8a. Accepted decisions (owner, 2026-09-26)

These defaults are accepted for the first Music-inator release (M18). They supersede the matching open questions below; details are in [M18](../milestone_18_musicinator_foundation.md) and its [technical design](../technical_design_m18.md).

- **Structure:** Album → Edition → Copy is the canonical model, consistent with Movie-inator. An edition (original CD, remaster, deluxe, anniversary, regional pressing, vinyl) carries its own disc structure and track list; a copy is a physical item or a set of digital audio files. Album, edition, copy and file stay separate.
- **Artists:** stored as album fields (primary artist, other album artists, additional artists; track artists on tracks), searchable and browsable, but not separate records yet. Artist pages can be derived later without migrating the model.
- **Browsing:** by Albums, Artists, Genres or Years over the same album list.
- **Personal data:** per-profile rating 1–10 and Favourite flag. No listened status, listening history, play counts, scrobbling or track ratings.
- **Playback:** Play album opens the album in the configured or system default external player. No internal player, queues or playlists; nothing is tracked or closed.
- **Adding music:** manual entry, folder scan and drag-and-drop. No online metadata providers yet.
- **Metadata precedence (owner confirmed):** embedded tags first; folder structure, then filenames, then unknown-value labels fill missing fields only. Populated tags must not be overwritten by fallback parsing. Disc grouping, edition matching and compilation handling remain documented implementation rules, not additional decisions inferred from this confirmation.

The hub integration requirements of section 2 apply as implemented for Movie-inator: registry tile and tab, combined close review, settings saved immediately, workspaces with module/tab/selection, activity by operation and module, and retry of a failed catalog load. Section 5's position restoration does not arise in M18 because Music-inator starts external players only and keeps no playback position.

## 9. Open module decisions

- ~~Should the main organisation centre on albums/releases, tracks, or offer both equally?~~ Decided: albums, with editions and track lists (8a).
- ~~How should compilations, remasters, multi-disc releases, and duplicate audio files be grouped?~~ Decided: Album → Edition → Copy; remasters/deluxe are editions, multi-disc releases one edition, duplicate rips copies (8a).
- ~~Should restoration include a queue/playlist as well as the current track and position?~~ Not applicable to M18: external players only, no playback position (8a).
- Should audiobooks appear only in Book-inator or be accessible from both modules? (Open; Music-inator does not special-case audiobooks.)
- When and how should artists become separate records with their own pages?
- Which candidate metadata providers, imports, exports, custom fields, reports, and loan functions are wanted?
- What should scanning/matching do with ambiguous entries, duplicates, missing metadata, and user-edited values?
- Which defaults and first-release deliverables should be selected after the module scope is agreed?

Suite-level deferred questions remain deferred: owner-approval scope/editor rights and backup category/profile selection. Linux is the initial platform and Book-inator is the first module priority for personal use on one device. Synchronisation comes later; later platforms and LAN/cloud timing remain undecided.

## 10. Sources

| Source | Role |
| --- | --- |
| [Hub constitution](../mediaintor%20hub/constitution_hub.md) | Governing shared commitments |
| [Hub overview](../mediaintor%20hub/mediainator%20hub%20overview.md) | Shared purpose and summary |
| [Hub features](../mediaintor%20hub/mediainator%20hub%20features.md) | Workflows and remaining suite decisions |
| [Hub configuration](../mediaintor%20hub/mediainator%20hub%20config.md) | Settings, defaults, and scope |
| [Module overview](musicintor%20overview.md) | Reference collection types and domain purpose |
| [Module features](musicinator%20features.md) | Candidate specialist capabilities |
| [Module configuration](musicinator%20config.md) | Candidate settings, not adopted defaults |
| [Rough scaffold](../mediainator%20rough%20scaffold.md) | Historical goals and exploratory suggestions |
