# M17 technical design — Movie-inator foundation

Status: first implementation candidate; Qt/KDE verification pending. Constraints: Python 3.14, PyQt6 6.10, no new dependencies. `ffprobe` is optional.

## Modules

| File | Role | Qt? |
| --- | --- | --- |
| `movie_catalog.py` | Frozen dataclasses `Movie`, `Edition`, `Copy`; samples; `find_movies`; filename parsing and title normalisation | No |
| `movie_store.py` | SQLite catalog, validation, revisions, per-profile activity | No |
| `movie_scan.py` | File discovery, ffprobe probing, grouping into a reviewable plan, revalidation | No |
| `movie_player.py` | External player command validation and detached launch | No |
| `movie_ui.py` | `Movieinator` tab, `MovieEditor`, `EditionsDialog`, `MovieImportDialog`, `ScanWorker` | Yes |

Hub changes: `modules.py` (available + launch), `window.py` (`open_movies`, `remove_movies`, `movie_store`, generic tab close, `review_close` = Movie-inator then `review_books_close`, shutdown guard, focus refresh), `settings.py` (optional keys), `workspaces.py` / `workspace_ui.py` / `workspace_restore.py` (module sets, active tab by widget, optional `movie_selection`), `activity_panel.py` guidance, `recovery_actions.py` catalog reload retry, `__main__.py` `--movie-catalog`.

## Storage

`AppLocalData/Movies/catalog.sqlite` for the live Hub; `--movie-catalog PATH` overrides; non-live Hubs without an explicit catalog use read-only samples and create nothing.

Schema 1 (`meta.schema = '1'`, plus `catalog_uuid`, `created_at`):

- `movies(id, title, original_title, year, directors, cast_list, genres, runtime, synopsis, cover, notes, revision, added_at, modified_at)`; lists stored as JSON arrays.
- `editions(id, movie_id → movies ON DELETE CASCADE, label, format ∈ Digital/DVD/Blu-ray/4K UHD/VHS/Other, notes, position)`.
- `copies(id, edition_id → editions CASCADE, kind ∈ file/physical, path UNIQUE (canonical, resolved), location, size, container, duration, width, height, video_codec, audio JSON, subtitles JSON, added_at)`.
- `personal(profile_id, movie_id → movies CASCADE, watched, rating 1–10, modified_at)`, primary key (profile, movie).

Every write is one `BEGIN IMMEDIATE` transaction (5 s busy timeout) that rolls back completely on any error. A file with foreign tables, a missing/unsupported schema or a newer schema is refused and left byte-identical. An empty file left by a rolled-back first write is treated as an empty catalog.

Catalog edits increment `movies.revision`; edition/copy edits increment their movie's revision. `update_movie(id, expected_revision, changed_fields)` raises `ConflictError(current)` on mismatch. The editor sends only fields changed from its baseline, so “Save my values” after a conflict never overwrites unrelated concurrent changes. Personal activity does not change the revision.

Removal deletes catalog rows only. No code path deletes, moves or renames media files.

## Scan and import

1. `discover`: explicit files plus recursive folders (`os.walk`, no symlinked or hidden folders); extensions from `VIDEO_EXTENSIONS`; canonical paths deduplicated.
2. Files already in the catalog (`known_paths`) are reported, not planned.
3. `probe`: size always; ffprobe JSON (20 s timeout) for duration, first non-cover video stream, audio and subtitle languages. Failures become warnings, never exceptions.
4. `parse_filename`: year = last plausible 19xx/20xx after some title text; scene tags end the title; dots become spaces; edition hints (Director's Cut, Extended…); only a `Title (Year)` parent folder is trusted. Only a *trailing* CD/Part/Disc marker means a multi-part file, so “Part 1 (2010)” titles survive.
   Edition labels: `<hint or Digital> (<CONTAINER> <SD|720p|1080p|4K>, <source>)`, where source is Remux / Blu-ray rip / WEB / DVD rip / TV recording when named in the file.
5. Grouping key `(normalize_title, year)`; a matching catalog movie pre-selects “Add to existing”.
6. Preview in `QThread` (worker emits progress; cancellation flag). Confirm applies each checked group through `apply_group` in its own transaction after `revalidate` (file still present, same size, not catalogued meanwhile). Completed groups stay committed; stop takes effect between groups. One activity record per import (`kind=movie_import`).

## Player

`''` → `xdg-open FILE`; otherwise `shlex` parsed command, executable resolved with `which`, `{file}` substituted or file appended. `Popen(start_new_session=True)`, all standard streams to `/dev/null`. The process is not tracked; close review does not include it. Failures are recorded (`kind=movie_play`, pending) and shown.

## Settings (schema 1, optional keys)

`movieinator_open` bool; `movie_view` Grid/List; `selected_movie` str|null; `movie_player` str ≤1000; `movie_search` {text, genres[], formats[], statuses[], expanded, sort}. Absent keys use defaults, so existing settings files load unchanged.

## Workspaces

Allowed module sets: hub; hub+bookinator; hub+movieinator; hub+bookinator+movieinator. `active` is resolved by widget, not tab index. Optional `movie_selection {catalog_uuid, movie_id}` is restored only when the catalog UUID matches. Snapshots without the key remain valid. **Compatibility note:** M16 builds reject snapshots that include Movie-inator; keep M17 data isolated from M16 Everyday, as with earlier milestones.

## Tests

- `tests/test_movie_core.py` (no Qt): parsing, search, store round trip/validation/atomicity/conflicts/per-profile activity/removal/foreign and newer files, scan grouping/parts/attach/revalidation, ffprobe parsing and failures.
- `tests/test_m17_movieinator.py` (Qt): sample read-only mode, add/edit/review, personal status, search persistence, import preview/apply, removal keeps files, Hub launch/focus/close, restart reopen, workspace snapshot, Hub close review, settings validation.

## Known limits

No TV series, providers, internal player, loans, reports or file management. Cover images are referenced by path, not copied. ffprobe output depends on the installed FFmpeg. Scan preview for very large folders is limited by ffprobe speed (about one file per probe call).
