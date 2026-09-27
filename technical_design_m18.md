# M18 technical design — Music-inator foundation

Status: first implementation candidate; automated real Qt/KDE verification passed; owner desktop acceptance pending. Constraints: Python 3.14, PyQt6 6.10, no new dependencies. `ffprobe` is optional. Same structure as [M17](technical_design_m17.md).

## Modules

| File | Role | Qt? |
| --- | --- | --- |
| `music_catalog.py` | Frozen dataclasses `Album`, `Edition`, `Track`, `Copy`, `AudioFile`; samples; `find_albums`, `browse_values`; folder/track/edition name parsing; durations. Reuses `normalize_title`/`sort_key` from `movie_catalog`. | No |
| `music_store.py` | SQLite catalog, validation, revisions, per-profile favourite/rating, relocation | No |
| `music_scan.py` | File discovery, ffprobe tag/stream probing, copy units, grouping into a reviewable plan, edition clustering, quality labels, revalidation, `files_for` for manual copies | No |
| `music_player.py` | M3U playlist in application data, player command placeholders, detached launch, moved-folder matching. Reuses `validate_command`/`PlayerError` from `movie_player`. | No |
| `music_ui.py` | `Musicinator` tab, `AlbumEditor`, `EditionDialog` (fields + track table), `EditionsDialog`, `MusicImportDialog`, `ScanWorker` | Yes |

Hub changes: `modules.py` (Music-inator available + launch), `window.py` (`music_catalog` argument, `music_store`, `open_music`, `remove_music`, tab close, `review_close` = Music-inator → Movie-inator → Book-inator, shutdown guard, focus refresh, shutdown), `settings.py` (`validate_music_settings`, optional keys), `workspaces.py` (generated module sets, optional `music_selection`), `workspace_ui.py` (capture, busy guard), `workspace_restore.py` (open/close, active tab, selection restore, rollback keys, editor review), `activity_panel.py` guidance, `recovery_actions.py` catalog reload retry, `__main__.py` `--music-catalog`.

## Storage

`AppLocalData/Music/catalog.sqlite` for the live Hub; `--music-catalog PATH` overrides; non-live Hubs without an explicit catalog use read-only samples and create nothing. Play album writes only `…/Music/playlists/now-playing.m3u8` beside the catalog.

Schema 1 (`meta.schema = '1'`, `meta.kind = 'music'`, `catalog_uuid`, `created_at`). The `kind` key means a Movie-inator catalog (or any other SQLite file) passed as `--music-catalog` is refused and left byte-identical.

- `albums(id, title, artists JSON, additional_artists JSON, year, genres JSON, cover, notes, revision, added_at, modified_at)` — `artists[0]` is the primary artist.
- `editions(id, album_id → albums CASCADE, label, format ∈ CD/Vinyl/Cassette/Digital/SACD/DVD-Audio/Blu-ray Audio/Other, release_year, record_label, catalog_number, disc_count, notes, position)`.
- `tracks(id, edition_id → editions CASCADE, disc 1–99, number 1–999|NULL, title, artist, duration, position)` — the edition's track list, independent of files.
- `copies(id, edition_id → editions CASCADE, kind ∈ digital/physical, location, quality, notes, added_at)`.
- `files(id, copy_id → copies CASCADE, path UNIQUE (canonical, resolved), size, disc, number, title, duration, codec, bitrate, sample_rate, bit_depth, channels, position)` — a digital copy has ≥1 file; a physical copy has none.
- `personal(profile_id, album_id → albums CASCADE, favourite, rating 1–10, modified_at)`, primary key (profile, album).

Every write is one `BEGIN IMMEDIATE` transaction (5 s busy timeout) that rolls back completely on any error. Foreign, kind-less, damaged or newer files are refused and left unchanged; an empty file left by a rolled-back first write is treated as an empty catalog.

Album edits increment `albums.revision`; edition/track/copy/file edits increment their album's revision. `update_album(id, expected_revision, changed_fields)` raises `ConflictError(current)` on mismatch; the editor sends only changed fields. `update_edition(id, fields, tracks=None)` replaces the track list only when `tracks` is given; `disc_count` never drops below the highest track disc. `relocate_files(copy_id, {file_id: path})` is all-or-nothing and allows swaps (two-step update under the UNIQUE constraint). Personal activity does not change the revision.

Removal deletes catalog rows only. No code path deletes, moves, renames or retags audio files.

## Scan and import

Owner-confirmed metadata precedence: embedded tags → folder structure → filename → explicit unknown label. Fallback sources fill missing fields only and must not overwrite populated tag values. This is the governing requirement; implementation and tests must preserve it.

1. `discover`: explicit files plus recursive folders (no symlinked or hidden folders); `AUDIO_EXTENSIONS`; canonical paths deduplicated. Files already catalogued (`known_paths`) are reported, not planned.
2. `probe`: size always; ffprobe JSON (20 s timeout): format and stream tags (case-insensitive: album, album_artist/albumartist/TPE2, artist, title, track, disc, date, originaldate, genre, compilation), first audio stream codec, sample rate, channels, bit depth, bitrate. Failures become warnings, never exceptions.
3. `album_folder`: the file's folder, or its parent when the folder is a disc folder (`CD1`, `Disc 2`, `disk-3`); the disc number is kept as a hint.
4. Copy units: files grouped by (album folder, normalised album tag) so one flat folder holding several albums is split. `build_unit` decides per unit:
   - title: most common album tag, else folder name (`parse_album_folder`); bracketed edition words (Remaster, Deluxe, Edition, Anniversary, Japan, Mono…) become the edition hint; technical brackets (`[FLAC 24-96]`) are dropped; ordinary brackets stay in the title.
   - artist: album-artist tag → *Various Artists* for compilation tags or several track artists → artist tag → folder artist (`Artist - Album`, or a non-generic parent folder that is not a scan root).
   - year: date tag → originaldate → bracket year → folder year. Genres: split tag values.
   - tracks: disc = tag → disc folder → file name → 1; number = tag → file name; title = tag → file name; track artist only when it differs from the album artist.
5. Groups: key `(normalize(primary artist), normalize(title))` — the year is not part of the identity. A matching catalog album pre-selects *Add to existing* and keeps its editions for matching.
6. `ScanGroup.editions(existing)`: units clustered by (hint, `tracklist_signature`); each cluster is one edition (`label` = hint or *Standard*, format *Digital*, release year, disc count, tracks) with one digital copy per unit (`quality` label). A cluster whose signature (and hint, when present) equals an existing edition's track list carries that `edition_id`, and `apply_group('attach')` adds only its copies. Duplicate labels get “(n tracks)”.
7. Warnings: probe failures, untagged albums, missing artist, duplicate or missing track numbers, folders partly catalogued already.
8. Preview runs in a `QThread` (progress, cancellation flag). Confirm applies each checked group through `apply_group` in its own transaction after `revalidate` (file present, same size, not catalogued meanwhile). Completed albums stay committed; Stop takes effect between albums. One activity record per import (`kind=music_import`).

## Player

`launch_album(command, files, playlist_folder)`: every file must exist (otherwise a message suggests Locate…); writes `now-playing.m3u8` atomically (`#EXTINF` with title and length); `''` → `xdg-open playlist`; otherwise `shlex` command, executable resolved with `which`, `{playlist}` / `{files}` / `{file}` substituted, or the tracks appended. `Popen(start_new_session=True)`, standard streams to `/dev/null`; not tracked; close review does not include it. Failures are recorded (`kind=music_play`, pending) and shown.

`match_moved(files, folder)` proposes new paths by relative path below the old common folder, then by unique file name anywhere below the chosen folder.

## Settings (schema 1, optional keys)

`musicinator_open` bool; `music_view` Grid/List; `selected_album` str|null; `music_player` str ≤1000; `music_search` {text, genres[], formats[], personal[], expanded, sort}; `music_browse` {mode, value|null}. Absent keys use defaults, so existing settings files load unchanged.

## Workspaces

`MODULE_SETS` is generated: `hub` plus every subset of (bookinator, musicinator, movieinator) in registry order, so all M17 sets remain valid. Optional selections are declared in `MODULE_SELECTIONS`: `movie_selection {catalog_uuid, movie_id}` and `music_selection {catalog_uuid, album_id}`, each valid only with its module open and restored only when the catalog UUID matches. **Compatibility note:** M16/M17 builds reject snapshots that include Music-inator; keep M18 data isolated from Everyday, as with earlier milestones.

## Activity

Module `musicinator`. Kinds: `music_catalog` (load failure, pending; retry = open tab and *Reload catalog*), `music_play` (pending), `music_import` (summary), `music_save`. Removals are recorded under `music_catalog` as success.

## Tests

- `tests/test_music_core.py` (no Qt, 22 tests): folder/track/edition parsing, durations, search/filters/browse, store round trip, validation atomicity, duplicate files, conflicts, per-profile activity, removal keeps files, edition/track/copy management, relocation (swap, clashes), foreign/newer/Movie-inator catalogs untouched, scan (tags first, folder fallback, disc folders, compilations, FLAC+MP3 = one edition two copies, deluxe = separate edition, attach to matching edition, known files, revalidation), ffprobe parsing (format and stream tags) and failures, quality labels, playlist and player placeholders, missing files, moved-folder matching.
- `tests/test_m18_musicinator.py` (Qt, 15 tests): sample read-only mode, add/edit/review, favourite/rating, list columns and sorts, browse by artist/genre/year and persistence, import preview/apply with discs and attach, play writes the playlist outside the music folder, locate, edition/track dialog validation, editions dialog and removal keeps files, Hub launch/focus/close with three modules, restart reopen, workspace snapshot and module sets, Hub close review, sample Hub creates nothing, playlist location, settings validation, catalog failure activity and retry.

Verification update (2026-09-27): real PyQt6/Wayland and installed tests pass; see [final evidence](test_data/m18_m19_review/completion.md) for exact counts, scope, and remaining owner acceptance. The previous stand-in results are superseded by these runs.

## Known limits

No artist records, providers, internal player, playlists, loans, reports, tag writing or file management. Cover images are referenced by path, not copied or extracted from files. Without ffprobe, albums are recognised from folder/file names only and quality/length stay empty. Scan speed is bounded by one ffprobe call per file. Track lists of editions are not re-derived when files change; use *Fill from a copy's files*.
