# M18 — Music-inator Foundation

Review update (2026-09-26): real PyQt6 full suite **381 passed**, M18/M19 native Wayland tests **35 passed**, and installed M18/M19 tests **86 passed** after test-harness corrections. Targeted review also reproduced preservation defects; **acceptance remains OPEN**. See [compliance review and outstanding items](test_data/m18_m19_review/review.md). Earlier stand-in-only status below is historical evidence, not the latest verification result.

Status: **Implemented and automatically verified candidate (2026-09-27); follow-up owner desktop checks passed; M18-G formal closure pending.** See [final implementation and test evidence](test_data/m18_m19_review/completion.md). Isolated acceptance launchers are available; Everyday is unchanged.

## Purpose

Make Music-inator the third working Hub module, following the Book-inator and Movie-inator path: a clear, robust catalog foundation first, with usage tracking and complex features deferred. Prove that the M16 registry, tabs, workspaces, close review, activity and help carry a third module, and that Movie-inator's Work → Edition → Copy pattern holds for music.

## Owner decisions (2026-09-26)

| Topic | Decision |
| --- | --- |
| Canonical model | **Album → Edition → Copy**, consistent with Movie → Edition → Copy. An edition (original CD, 2011 Remaster, Deluxe Box, Japanese pressing, vinyl) has its own disc structure and track list, because remasters and deluxe editions often differ in tracks, bonus material and discs. A copy is a physical item or a set of digital files (FLAC files, MP3 files, CD rip, physical CD). |
| Artists | Stored as album fields, searchable and filterable, **not** separate records in M18: primary artist, other album artists and additional artists. Full artist pages (merging, name changes, featuring artists, soundtracks) are a later milestone (M19/M20) and can be derived from these fields without migrating the model. |
| Browsing | The user can browse by **Albums, Artists, Genres or Years**; the data structure stays Album → Edition → Copy. |
| Personal data (per profile) | **Rating 1–10** (shown as stars plus `n/10`) and **Favourite** (yes/no). Rating = quality, Favourite = personal meaning. |
| Playback | **Play album** opens the album in the configured player or the system default. External player only. |
| Explicitly not in M18 | Listening history, listened status, track ratings, built-in player, scrobbling, play counts, playlists, library synchronisation, Last.fm. |
| Process | Full M18 candidate: decisions, milestone document, technical design, code, Hub integration, tests, help/README/CHANGELOG and constitution update; Qt tests run on the owner's KDE machine, as for M17. |

**Metadata precedence — owner confirmed.** Import uses embedded music tags as the primary metadata source. Only missing fields are filled from folder structure, then file names, then explicit unknown-value labels. Folder or filename parsing must not replace populated tag values. This confirmation resolves the outstanding tags-first versus folder-first decision; grouping mechanics below remain separately documented implementation choices.

Implementation choices made by Claude within those decisions:

- **Artist fields.** `artists` holds the album artist(s) with the **primary artist first** (the editor has *Primary artist* and *Other album artists*); `additional_artists` holds featured artists, orchestra, conductor and guests. Track-level artists (compilations) are kept on tracks. The Artists browser lists every credited name.
- **Notes.** Album *Private notes* stay a catalog field, as in Movie-inator. No separate per-profile notes were added.
- **Catalog location.** `AppLocalData/Music/catalog.sqlite`, shared catalog fields separate from per-profile favourite/rating. `--music-catalog PATH` selects a disposable catalog for testing; `--sample`/test Hubs without it show a read-only sample catalog.
- **Scanning.** Tags first (ffprobe), then folder and file names: `Artist - Album (Year)`, `Artist - Year - Album`, `Artist/Album (Year)`, and disc subfolders `CD1`/`Disc 2` join the album above. The files of one album folder form one copy; copies with the same edition hint and track list share one edition (a FLAC and an MP3 rip of the same release become one edition with two copies); different track lists become separate editions. Compilations (compilation tag, or several track artists without an album artist) are grouped under *Various Artists*.
- **Matching the catalog.** Same primary artist + album title (accents/case ignored, year not part of the identity) proposes *Add to existing*; a copy whose track list matches an existing edition is added to that edition instead of creating a new one.
- **Playback.** *Play album* writes `now-playing.m3u8` into Media-inator application data (never into a music folder) and opens it with the desktop default, or starts the configured command with the tracks (`{playlist}`, `{files}`, `{file}` placeholders). The player is not tracked or closed.
- **Editing.** Album details use a draft with Save / Discard / Cancel and revision conflict review. Edition, track-list and copy changes save immediately, with confirmation for removals.
- **Moved files.** *Locate…* asks for the folder the files are in now and matches them by relative path, then by file name; the catalog is updated, the files are not touched.

## Delivered in the first candidate

- Registry: Music-inator tile Available; repeat launch focuses one tab; tab close leaves the Hub; reopened after restart.
- Catalog tab: Grid (covers) / List, search (album, all credited artists, track titles, year), genre/format/*Favourites & rating* filters, Browse by Albums/Artists/Genres/Years, sorts (artist, album, year, rating), remembered state, detail pane with editions, copies and track list, favourite and rating.
- Album editor with validation and revision-based conflict review; optional first edition with physical location and/or an album folder (tags fill empty fields).
- Editions, tracks & copies dialog: add/edit/remove editions with record label, catalog number, discs and a track-list table (disc, number, title, track artist, length; fill from a copy's files); add physical copies and digital folders; edit copy condition/quality/notes; locate moved files; remove copies.
- Import: files/folders/drag-and-drop → background scan → reviewable preview (create / add to existing / add to another / skip; editable album, artist, year; editions and matched copies shown) → Confirm. Revalidation before each write; per-album transactions; stop after current; activity record.
- Optional ffprobe tags and technical details (codec, bit depth, sample rate, bitrate, length); quality labels such as `FLAC 16-bit/44.1 kHz` or `MP3 320 kbps`.
- Hub integration: combined close review (Music-inator, Movie-inator, then Book-inator), cooperative shutdown guard, activity guidance and catalog-reload retry, workspaces (module sets with any combination of Book-, Music- and Movie-inator; active tab; album selection by catalog UUID), `--music-catalog`.
- Help: User guide section “Music-inator (M18 Development)”.

## Work breakdown

| Item | Deliverable | Status |
| --- | --- | --- |
| M18-01 decisions | Owner decisions above recorded; constitution updated (section 8a) | Done; tags-first precedence confirmed |
| M18-02 technical design | `technical_design_m18.md` | Done |
| M18-03 core | Model, SQLite store, scan planner, player launcher + `tests/test_music_core.py` | Done; 22 tests pass |
| M18-04 module UI | `music_ui.py` tab, album editor, edition/track dialog, editions & copies, import | Implemented; real Qt/Wayland and installed-package tests pass |
| M18-05 Hub integration | Registry, tabs, close review, settings, workspaces, activity, recovery, CLI | Implemented; real Qt/Wayland and installed-package tests pass |
| M18-06 regression | Full existing suite + M18 tests on the owner's machine | Passed; see final evidence and run scope |
| M18-07 isolated environment and package | Independent M18 Development install/data from the Everyday baseline | Verified frozen candidate; isolated acceptance launcher prepared |
| M18-08 owner acceptance | Desktop checks below; M18-G record | Pending |

## Proposed M18-G acceptance

- Music-inator launches from the Hub, focuses on repeat, closes without closing the Hub, and reopens after restart; Book-inator, Movie-inator and all M16/M17 regressions unchanged.
- Manual add, edit, conflict review, editions/tracks/copies and removal work; removing never deletes, moves or retags files.
- Scanning a real music folder reads tags, falls back to folder names for untagged albums, joins CD1/CD2 subfolders into one edition, groups a FLAC and an MP3 rip of the same release as two copies of one edition, groups compilations under Various Artists, skips files already catalogued, proposes adding to matching albums, and writes nothing before Confirm.
- Browse by Artists, Genres and Years narrows the album list and is remembered.
- Favourite and rating save immediately, per profile, without changing the catalog revision.
- Play album opens the configured/default player with the tracks in order; no playlist is written into the music folder; Locate… repairs a moved album folder.
- Hub close/tab close review unsaved album details and running imports; Cancel stops the close.
- Named workspaces restore Book-/Music-/Movie-inator tabs, active tab and selected album.
- Appearance settings apply to Music-inator controls.

## Explicitly deferred

Artist pages and artist records; listening history, listened status, play counts, scrobbling; track ratings; internal player, queues and playlists; online metadata providers and cover download; tag writing, renaming or moving files; loans; reports, statistics, exports and CD-cover printing; wish lists; custom fields; multiple catalogs; relocatable catalog; audiobooks (Book-inator question); bulk editing; tracking or closing external players.
