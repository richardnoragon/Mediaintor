# M17 — Movie-inator Foundation

Status: **First implementation candidate in source (2026-09-26). Development only; M17-G OPEN.** Pure catalog/storage/scan tests pass. Qt/Hub tests are written but must be run on the owner's KDE machine; installed-package and desktop acceptance have not happened. No promotion, packaging or publication.

## Purpose

Make Movie-inator the second working Hub module, following the Book-inator path: a clear, robust foundation first, with complex features deferred. Prove that the M16 registry, tabs, workspaces, close review, activity and help carry a second module without Book-inator-specific assumptions.

## Owner decisions (2026-09-26)

| Topic | Decision |
| --- | --- |
| Coverage | Movies only. TV series (seasons, episodes, specials, per-episode status) are a later milestone. |
| Structure | Movie → Edition → Copy. Movie, edition and owned copy/file stay separate to avoid later migrations. A copy is a physical item or a digital file. |
| Watched status | Manual flag only: Not watched / Watched. No playback-derived tracking. Watching / partially watched / rewatch are later. |
| Playback | External player only. Movie-inator manages the library, not playback. |
| Adding movies | Manual entry, folder scan and drag-and-drop (a convenience layer on import). No online metadata providers yet. |
| Movie identity on scan | Files with the same title and year become **one movie with several copies/files** (`Alien (1979).mkv` + `Alien (1979).mp4`). |

Follow-up owner decisions (2026-09-26, same day):

| Topic | Decision |
| --- | --- |
| Catalog location | Internal catalog in Media-inator app data only for M17. A relocatable catalog is a later advanced option. |
| Editions from scanning | Distinct formats/qualities/sources stay separate editions (e.g. `Digital (MKV 1080p)`, `Digital (MKV 4K)`, `Digital (MKV 1080p, Blu-ray rip)`); multi-part CD1/CD2 files share one edition. |
| Rating | Personal rating 1–10, stored as the number and shown as stars plus `n/10`. |
| Process | After the internal test run passes: isolated M17 install, acceptance checklist, disposable testing, sign-off — as for earlier milestones. |
| Future (not M17) | Consider a *Last watched* date alongside the Watched flag. |

Implementation choices made by Claude within those decisions:

- Catalog stored in Media-inator application data (`AppLocalData/Movies/catalog.sqlite`), shared catalog fields separate from per-profile watched/rating.
- Each distinct scanned file becomes its own edition labelled from container, resolution (SD/720p/1080p/4K) and any release source in the file name (Remux, Blu-ray rip, WEB, DVD rip, TV recording); trailing CD1/CD2/Part N files share one edition.
- Personal rating 1–10 alongside the watched flag.
- Player: desktop default application unless a player command is set; the launched player is not tracked or closed.
- Edition/copy changes save immediately (with confirmation for removals); movie details use a draft with Save / Discard / Cancel.
- `--sample` / test Hubs show a read-only sample catalog; `--movie-catalog PATH` selects a disposable catalog for testing.

## Delivered in the first candidate

- Registry: Movie-inator tile Available; repeat launch focuses one tab; tab close leaves the Hub; reopened after restart.
- Catalog tab: Grid/List, search (title, original title, director, cast, year), genre/format/watched filters, title/year sorts, remembered state, detail pane with editions and copies, watched and rating.
- Detail editor with validation, revision-based conflict review (save only my changed fields, or use catalog values).
- Editions & copies dialog: add/edit/remove editions, add physical copies and files, change shelf location or file location, remove copies.
- Import: files/folders/drag-and-drop → background scan → reviewable preview (create / add to existing / add to another / skip, editable title and year) → Confirm. Revalidation before each write; per-movie transactions; stop after current; activity record.
- Optional ffprobe technical details (resolution, codec, duration, audio, subtitles).
- Missing files show Locate…; relocation updates the catalog only.
- Hub integration: combined close review, cooperative shutdown guard, activity guidance and catalog-reload retry, workspaces (module set, active tab, movie selection by catalog UUID).
- Help: User guide section “Movie-inator (M17 Development)”.

## Work breakdown

| Item | Deliverable | Status |
| --- | --- | --- |
| M17-01 decisions | Owner decisions above recorded; constitution updated | Done |
| M17-02 technical design | `technical_design_m17.md` | Done |
| M17-03 core | Model, SQLite store, scan planner, player launcher + `tests/test_movie_core.py` | Done; 16 tests pass |
| M17-04 module UI | `movie_ui.py` tab, editor, editions, import | Implemented; logic smoke-tested against a Qt stand-in only |
| M17-05 Hub integration | Registry, tabs, close review, settings, workspaces, activity | Implemented; `tests/test_m17_movieinator.py` to run on KDE |
| M17-06 regression | Full existing suite + M17 tests on the owner's machine | **Pending** |
| M17-07 isolated environment and package | Independent M17 Development install/data from the M16 Everyday baseline | Pending |
| M17-08 owner acceptance | Desktop checks below; M17-G record | Pending |

## Proposed M17-G acceptance

- Movie-inator launches from the Hub, focuses on repeat, closes without closing the Hub, and reopens after restart; Book-inator behaviour and all M16 regressions unchanged.
- Manual add, edit, conflict review, editions/copies and removal work; removing never deletes files.
- Scanning a real folder groups same-title/year files into one movie, skips files already catalogued, proposes adding to matching movies, and writes nothing before Confirm.
- Watched and rating save immediately, per profile, without changing catalog revision.
- Play opens the configured/default player; Locate… repairs a moved file.
- Hub close/tab close review unsaved movie details and running imports; Cancel stops the close.
- Named workspaces restore Book-inator/Movie-inator tabs, active tab and selected movie.
- Appearance settings apply to Movie-inator controls.

## Explicitly deferred

TV series; relocatable catalog location; last-watched date; online metadata providers; automatic/partial/rewatch tracking; internal player and position restore; loans; reports, statistics and exports; renaming/moving files; custom fields; multiple catalogs; hardware-player catalogs; bulk editing for movies; tracking or closing external players.
