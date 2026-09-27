# Media-inator personal preview

Start Media-inator from the application menu. The Hub starts Book-inator as a
tab. Select your existing Calibre library; the catalog is browsed through a
private temporary copy. Books open from their original locations in Calibre's
viewer. Close Calibre and other readers before refreshes, viewer launches or
protected metadata/import operations. Open one reader at a time. A deferred
viewer issue may require a keypress before its content becomes readable.

Search title, author or series, switch Grid/List and choose an EPUB/MOBI/PDF format button.
Use Filters to select tags, formats and reading statuses. A book must match every
active category, but any selected value within a category is sufficient. Text
search is a literal, case-insensitive match. Search text, filters, metadata-review
filter and filter-panel visibility are remembered. Clear All resets every search
criterion immediately and saves the cleared state; it does not clear bulk selection.
Selected values remain visible even if the current library has no matching books.

Reading details show independent saved positions per format. The card/list summary
labels the most recently read format when timestamps establish one; equal timestamps
are shown as a tie. Saved position available does not imply a known percentage or
reading status: these remain Unknown without reliable data. Invalid or missing
records do not establish a reading status. Calibre readers must be closed before
protected refresh; dirty edits can defer that refresh.

For an observed book with unchanged format contents, title/author path changes can
retain resume through application-owned identity records. An unobserved external
rename, changed ebook contents, invalid records or missing history may prevent this
handoff. The application does not rewrite Calibre's annotation files.
Unavailable reading status is shown as Unknown. Metadata editing uses explicit
Save/Discard; leaving changed edits offers Save/Discard/Cancel. Imports copy
sources and require a preview. Bulk edits/reverts also require preview and
confirmation; successful partial results remain committed.

Hub Activity shows operational history and actionable failures. Open recovery draft,
Review pending imports and Review pending batch open the corresponding draft or
preview without applying changes. Hide from action list retains history and recovery.
Discard preserved draft / Discard pending imports / Discard pending batch changes
require review and confirmation, and abandon only unfinished work. Delete this
history record is separate and unavailable while recovery remains unresolved. Deleting history can remove future revert capability.

After a failed metadata Save and failed explicit Retry, emergency preservation
protects only outstanding edits. This is not a successful save to Calibre.
Ordinary editing stays open; an already-requested close can continue once the
current draft is protected and other close checks pass. If preservation fails,
keep the editor open and use Preserve Elsewhere. On restart, inspect the Hub's
recovery summary and explicitly review/save. Nothing resumes automatically.
Forced termination before preservation does not guarantee recovery.

This package remains an unpublished personal preview with M6-G open. Calibre
9.2.1 and the verified system runtime are checked before protected operations.
Missing or unverified dependencies block library access without an override.
Use Recheck prerequisites after fixing the installation; pending work does not
resume automatically. Use Help → User guide, Installation and upgrades, or Troubleshooting (F1 opens
the guide). About Media-inator shows app/runtime versions. Help works offline
and does not read your library. Use Help → Preview redacted diagnostics for a local export. Installation and removal instructions: INSTALL.md.


## Editing and importing

Edit one book's title, ordered authors, tags, cover, series/number or description.
Use Add/Remove/Reorder for authors and Add/Remove for tags. Individual tags cannot
contain commas because Calibre treats them as separators. Clearing series hides
its number; a newly assigned series starts at 1. Zero and positive decimal series
numbers are allowed. Covers can be replaced or removed. An untouched description
keeps its existing HTML. If current Calibre values changed, review conflicts before
saving. Title/author saves can reorganize paths through Calibre; direct file move,
rename and deletion commands remain outside this release scope.

Import EPUB, MOBI or PDF through file selection, folder selection (including
subfolders) or drag/drop. Review every preview before confirming copy imports.
Original files remain untouched. Identical file contents count as duplicates.
Explicitly attach another format to an existing book; existing formats are never
automatically overwritten. Missing metadata uses filename/Unknown fallbacks and
flags Needs Metadata Review. Completeness and review status are independent;
choose Mark Reviewed after checking the record. Editing metadata does not silently
remove that flag. Interrupted imports retain completed work and require review
before retry; there is no automatic restart.

## Bulk changes and reverts

Select individual books or all search results; the selected count includes items
hidden by subsequent filtering. Selection survives sorting/filtering until cleared,
but is not restored after closing Book-inator. Each batch performs one operation:
add/remove tags, set/clear series or replace an exact author while preserving the
other authors and their order. Series can retain visible numbers, use one fixed
number, or assign a sequence in the reviewed order. Exclusions leave the approved
numbering unchanged. Review and confirm every batch; unaffected books may finish
while conflicts wait for review. Batch history supports reviewed reversion and is
kept until explicitly deleted; deleting it can remove the ability to revert.


## Redacted diagnostics

Choose Help → Preview redacted diagnostics. Review the exact JSON before selecting
Export JSON and a local destination. Closing the preview or cancelling the file
picker creates no export. Nothing is uploaded. Close and reopen the preview to
capture a newer snapshot; changes after preview do not change the exported bytes.

Reports include validated runtime versions, safe feature flags, the last displayed
compatibility result and up to 50 sanitized events from this application session.
They do not run a fresh compatibility check: use Recheck prerequisites first if
needed. Error summaries use fixed messages; stack frames omit filenames, source
text, locals and exception messages. Unknown frames and older events are counted
as omitted. Historical raw logs are not read or attached.

Book titles, authors, ISBNs, paths, library names, metadata, user notes, backup
locations and recovery contents are always excluded. There is no sensitive-data
opt-in. Exported files are owner-readable/writable only. If export fails, the
preview remains unchanged: choose a writable regular file location and retry.

## Named workspaces (M10 development)

Workspaces → Manage named workspaces saves layout and selected-book context without copying search/filter preferences or external-reader state. Keep up to five snapshots. Save new workspace at capacity asks which snapshot to replace; Cancel changes nothing. Overwrite and Delete require confirmation; Rename preserves the saved snapshot. Library operations must finish before workspace changes. A damaged workspace file is retained and management disabled until repaired; After repairing storage or restoring a valid copy, Reload workspace list validates the file and re-enables workspace saving.

Restore applies a saved workspace; Use selected workspace at startup selects a named snapshot. Use Last Session at startup returns to automatic session restoration. Last Session tracks the current supported layout without overwriting named snapshots. Workspaces restore Hub/modules only, not external readers. Hidden selected books do not clear your filters: use Clear All explicitly if desired. Busy operations prevent restoration, and unsaved edits require review.

Workspace behavior has automated and prior installed KDE acceptance. New candidates require their own installed verification; accepted installations are not automatically upgraded.

Workspace restore waits for catalog loading before committing Last Session. A failed or timed-out load returns to the previous workspace and explains the failure. Wait for critical operations before retrying. A pending restore is cancelled before changing libraries or closing its module; repeat the requested action once cancellation finishes. Failed or partial metadata saves must be resolved before switching. Existing external readers remain untouched.

If the saved display is missing or geometry is off screen, the Hub bounds the window to an available display. KDE Wayland controls exact placement. Named snapshots retain their saved geometry; automatic Last Session records the usable current arrangement.


## M12 workflow clarity

The main window identifies its deployment (for example M12 Test) and build; About also shows the identity. Use the matching KDE launcher. An installation label does not grant permissions or promote a test build.

Open recovery draft reconstructs a preserved draft and never saves it automatically. If catalog refresh is running, review waits with a visible status; closing the module cancels the waiting review without discarding recovery. Missing/inaccessible drafts and failed metadata reads keep preserved data and explain why review cannot finish. Explicit Save commits the reviewed draft.

Save feedback identifies the book and verified fields. Partial failures list saved and remaining fields; successfully committed fields stay saved.

A revert preview requires Confirm revert. Completed/failed/pending counts describe actual journal outcomes; conflicts and uncertain writes remain pending. Excluded/discarded books are shown separately. Cancelled — no books changed is used only when no write was attempted. Closing a preview never undoes prior saved changes. Inspect completion feedback and history before assuming a revert ran.

M12-G acceptance and everyday promotion are separate decisions. M11 remains the stable reference.


## Clearer everyday workflows (M13)

Use the window title and deployment label to identify the installation. Metadata editor controls name their field: Add author, Remove author, Add tag and Remove tag. Save metadata writes the draft; Discard local edits only abandons unsaved local changes and retains separate recovery. Close editor uses the existing unsaved-change review.

In the Hub, View recovery list opens unresolved history. Select an actual record, then Open selected record; group headings are not operations. Open recovery draft reconstructs preserved edits. Only Save metadata commits them. Close details and Close history close those windows only. Hide startup summary does not dismiss or discard individual records.

Bulk edit / history opens two tabs. New Bulk Edit shows operation settings and a dedicated preview/result area. The selected count includes books hidden by catalog filters. Choose one operation, build its preview, review affected books, then Confirm bulk changes. Batch History has a separate result area and a visible selected-batch summary. Selecting a record never performs writes. Review pending changes rebuilds review; Preview revert of selected batch prepares a new revert preview. Confirm revert is the separate write action.

While reviewing a preview, the target cannot be changed by switching history records or tabs. Use Edit bulk settings or Cancel revert preview to leave it. Completed operations select their own history record. Revert records show their original batch; related-record navigation is read-only. A partial or excluded revert does not imply all original changes were undone. Deleting a record removes its future availability; links do not recreate it.

Titles distinguish preparing a preview, preview awaiting confirmation, running, completed, interrupted and outcomes requiring review/verification. Stopping finishes verification of the current item; it does not roll back saved changes. Always inspect actual result counts.

For imports, use Choose ebook files or Choose folder and subfolders. Browse directories in the picker, or type/paste an absolute file or folder path into File or folder path in the import window and choose Preview path. Preview first, then Confirm and import copies. Rebuild import preview does not itself import anything. Close imports closes that dialog only.

Import previews show an activity indicator while finding files, preparing the private library copy and validating inputs. Large folders include subfolders and can take longer than a single file. Duplicate-only or invalid-only previews show nothing to import and disable confirmation. File selection and preview never import automatically.


## Library discovery and metadata review (M14 Development)

Find / review opens a table of the loaded library. Add Reading status, Missing metadata, Series or Tags conditions and choose Match all or Match any. Type in the value box to search tags or series. Text search and format narrowing apply to both modes. Any inherited catalog tags/statuses are displayed separately and can be cleared. Unknown reading status does not mean Unread.

Save new search creates a per-library definition; Update selected changes it explicitly. Rename and Delete search never change books. Definitions include text, conditions, format/catalog narrowing, sorting and the review-queue choice. Reload refreshes catalog/workflow information; library metadata changes appear after Reload library completes.

Needs Review queue includes factual missing fields, import warnings and manually flagged books. Missing series is optional and defaults off. Flag Needs Review and Mark reviewed affect Media-inator workflow state only. Mark reviewed does not hide factual missing title, author or cover. Select multiple rows using their checkboxes, then Bulk edit selected to use the existing preview and confirmation workflow. The count includes selections hidden by current filters.

Duplicates opens a read-only review window. Scan library explicitly checks existing library books; intake files are excluded. Identical-content groups compare file bytes within the same format. Similar groups match normalized title and author and require human review. There are no merge/delete actions. You can continue searching during the scan, cancel it, or close the duplicate window. Cancelled/error results are incomplete; refreshed-catalog results are stale until explicitly rescanned. Scans never change book files.

Large-library loading shows preparation progress and a Cancel library load button. Cancelling leaves source files untouched and retains previous results with a stale-status message. M14 Development remains separate from the accepted M13 Everyday installation.

## Hub and shared appearance (M16 Development)

The Hub launches Book-inator in a tab. Selecting it again focuses the existing tab.
Other ecosystem modules are labelled Planned and cannot launch yet. Activity is
below the module tiles; collapse it when not needed. Recovery notices remain visible.

Open Settings on the Hub for Theme, Accent color, UI size and Density. Changes apply
and save immediately for this profile/device, independently of workspaces. Reader
presentation and tool preferences are unaffected. UI size adjusts the application
relative to desktop scaling; it does not change KDE scaling. System accent uses the
highlight color supplied by Qt at startup (the platform default if unavailable).
Restart after changing the desktop accent. System theme follows Qt desktop theme
notifications where supported.

If saving fails, the previous appearance and selected settings are restored. Retry
attempts the requested change again; Close dismisses the error. Reset appearance
asks for confirmation and resets only these four settings, leaving layouts and
module preferences intact.

## Movie-inator (M17 Development)

Open **Movie-inator** from its Hub tile. It opens as a tab beside Book-inator;
opening it again focuses the existing tab, and closing the tab leaves the Hub open.
The tab is reopened after restart and is included in named workspaces.

**How movies are organised.** A *movie* is the work (Alien, 1979). An *edition*
is a release or version of it (Blu-ray Director's Cut, 4K UHD, MKV rip). A *copy*
is something you own: a physical disc on a shelf or a video file on disk. One movie
can have several editions, and one edition can have several copies (for example a
film split into CD1 and CD2 files).

**Where the catalog lives.** The catalog is Media-inator application data
(normally `~/.local/share/Media-inator/Media-inator/Movies/catalog.sqlite`), not
your media folders. Video files are referenced where they are: Movie-inator never
copies, moves, renames or deletes them. Removing a movie, edition or copy removes
only the catalog record.

**Adding movies.**
- **Add movie…** enters a movie by hand, optionally with a first edition (format,
  label, shelf location and/or a video file).
- **Import files / scan folder…** takes video files or folders (scanned with their
  subfolders; hidden and symlinked folders are skipped). You can also drop files or
  folders onto the Movie-inator tab or the import window. **Build preview** reads
  the files and proposes one movie per title and year: `Alien (1979).mkv` and
  `Alien (1979).mp4` become one movie with two editions. Files inside a
  `Title (Year)` folder use that folder's title and year. Files already in the
  catalog are left out. When the title and year match a movie you already have,
  the preview proposes **Add to existing**; you can instead create a new movie,
  choose another movie or skip. Double-click a title or year to correct it.
  Nothing is written until **Confirm and import**. If a file changed after the
  preview it is not imported; build the preview again.
- If FFmpeg's `ffprobe` is installed, resolution, codec, duration, audio tracks and
  subtitle languages are filled in. Without it, importing still works.
- There is no online metadata lookup; add synopsis, cast and cover yourself.

**Browsing.** Search matches title, original title, director, cast and year.
Filters combine genres, edition formats and watched status (every active category
must match; any selected value within a category is enough). Sort by title or year;
switch Grid/List. Search, filters, sort, view and selection are remembered.

**Watched and rating.** Tick **Watched** and choose **Your rating** yourself; they
save immediately. They belong to your profile and are kept apart from the shared
catalog details. Playing a file does not mark it watched.

**Playing.** Each file shows a **Play** button. Movies open in an external player:
the desktop default application, or the command set with **Player: …** (for example
`mpv` or `vlc --fullscreen`; `{file}` marks where the file name goes). Movie-inator
does not track, adopt or close the player. If a file was moved or its drive is
disconnected, the button reads **Locate…**; choose where the file is now to update
the catalog.

**Editing.** **Edit details…** edits title, original title, year, runtime,
directors, cast, genres, synopsis, cover image and private notes as a draft.
**Save** writes; leaving changed edits offers Save / Discard / Cancel. If the movie
was changed elsewhere since you opened it, you choose **Save my values** (only the
fields you changed are written) or **Use catalog values**. **Editions & copies…**
adds, edits and removes editions, physical copies and files; each of those actions
saves immediately and removals ask first.

**Closing.** Closing the tab or the Hub reviews unsaved movie details
(Save / Discard / Cancel) and a running import (stop after the current movie).
External players stay open.

**Activity.** Imports, failed catalog loads and failed player launches appear in
Hub Activity under Movie-inator.

Not yet included: TV series, online metadata, automatic watched tracking, an
internal player, loans, reports/exports and file renaming.

## Music-inator (M18 Development)

Open **Music-inator** from its Hub tile. It opens as a tab beside Book-inator and
Movie-inator; opening it again focuses the existing tab, and closing the tab leaves
the Hub open. The tab is reopened after restart and is included in named workspaces.

**How music is organised.** An *album* is the work (Pink Floyd — The Wall, 1979).
An *edition* is a release of it (original CD, 2011 Remaster, Deluxe Box, a vinyl
pressing), with its own discs and track list. A *copy* is something you own: a
physical CD, record or cassette on a shelf, or a set of audio files on disk (for
example a FLAC rip and an MP3 rip of the same edition are two copies). Artists are
album details: the primary artist, other album artists and additional artists
(featured artists, orchestra, conductor). Compilations use *Various Artists*, with
the artist of each track on the track list.

**Where the catalog lives.** The catalog is Media-inator application data
(normally `~/.local/share/Media-inator/Media-inator/Music/catalog.sqlite`), not your
music folders. Audio files are referenced where they are: Music-inator never copies,
moves, renames, retags or deletes them. Removing an album, edition or copy removes
only the catalog record.

**Adding albums.**
- **Add album…** enters an album by hand, optionally with a first edition (format,
  label, release year, shelf location and/or an album folder). Choosing a folder
  fills empty fields from the files' tags or the folder name.
- **Import files / scan folder…** takes audio files or folders (scanned with their
  subfolders; hidden and symlinked folders are skipped). You can also drop files or
  folders onto the Music-inator tab or the import window. **Build preview** reads
  tags first and falls back to folder and file names such as
  `Artist - Album (Year)/01 - Title.flac` or `Artist/Album (Year)/…`. Disc folders
  (`CD1`, `Disc 2`) join the album above them. Each album folder becomes one copy;
  folders with the same album and the same track list become copies of one edition,
  while a different track list (for example a deluxe edition) becomes its own
  edition. Files already in the catalog are left out. When the artist and album
  match an album you already have, the preview proposes **Add to existing**, and a
  copy whose track list matches one of its editions is added to that edition. You
  can instead create a new album, choose another album or skip. Double-click an
  album, artist or year to correct it. Nothing is written until
  **Confirm and import**. If a file changed after the preview it is not imported;
  build the preview again.
- If FFmpeg's `ffprobe` is installed, tags, track lengths and audio quality (for
  example `FLAC 16-bit/44.1 kHz` or `MP3 320 kbps`) are read. Without it, albums are
  recognised from folder and file names only; importing still works.
- There is no online metadata or cover lookup; add missing details yourself.

**Browsing.** **Browse** switches between Albums, Artists, Genres and Years: choose a
name, genre or year in the list on the left to narrow the albums. Search matches the
album title, every credited artist, track titles and the year. Filters combine
genres, edition formats and *Favourites & rating* (every active category must match;
any selected value within a category is enough). Sort by artist, album, year or
rating; switch Grid/List. Search, filters, browsing, sort, view and selection are
remembered.

**Favourite and rating.** Tick **★ Favourite** and choose **Your rating** yourself;
they save immediately. They belong to your profile and are kept apart from the
shared catalog details. Music-inator keeps no listening history and does not count
plays.

**Playing.** Each digital copy shows a **Play** button. **Play** writes a small
playlist into Media-inator's application data (never into your music folder) and
opens it with the desktop default application, or starts the command set with
**Player: …** (for example `audacious`, `mpv --no-video` or `vlc {playlist}`;
`{playlist}` is the playlist, `{files}` all tracks, `{file}` the first track;
otherwise the tracks are added at the end). Music-inator does not track, adopt or
close the player. If the files were moved or their drive is disconnected, the button
reads **Locate…**; choose the folder where they are now to update the catalog.

**Editing.** **Edit details…** edits album title, artists, year, genres, cover image
and private notes as a draft. **Save** writes; leaving changed edits offers
Save / Discard / Cancel. If the album was changed elsewhere since you opened it, you
choose **Save my values** (only the fields you changed are written) or
**Use catalog values**. **Editions, tracks & copies…** adds, edits and removes
editions (with record label, catalog number, discs and the track list), physical
copies and digital folders; each of those actions saves immediately and removals
ask first. **Fill from a copy's files** builds a track list from a digital copy.

**Closing.** Closing the tab or the Hub reviews unsaved album details
(Save / Discard / Cancel) and a running import (stop after the current album).
External players stay open.

**Activity.** Imports, failed catalog loads and failed player launches appear in
Hub Activity under Music-inator.

Not yet included: artist pages, listening history or play counts, track ratings, an
internal player and playlists, online metadata and covers, tag editing and file
renaming, loans, reports/exports and wish lists.

## Paper-inator (M19 Development)

Open **Paper-inator** from its Hub tile. It opens as a tab beside the other modules;
opening it again focuses the existing tab, and closing the tab leaves the Hub open.
The tab is reopened after restart and is included in named workspaces.

**What it is for.** Paper-inator helps you collect research sources, keep your own
understanding of them, connect ideas and use them in projects. The main object is a
*Knowledge Item*: a research paper, conference paper, proceedings, thesis, report,
white paper, dataset, book chapter, standard or web resource. An item can hold
several *versions* of the same work (preprint, accepted manuscript, published
version), each with its documents and attachments. *Notes* can belong to an item or
stand on their own. *Projects* (optional) gather items and notes for an
investigation; *collections* group items. Nothing is duplicated: an item can be in
several projects at once.

**Your own library, on this computer.** Each Hub profile has its own Paper-inator
library in Media-inator's application data
(normally `~/.local/share/Media-inator/Media-inator/Paper/profiles/<profile>/`).
Notes, reading state, flags, projects and saved searches belong to that profile.
Nothing is uploaded and no account is needed; this milestone makes no network
requests at all.

**Sections.** The list on the left switches between **Home** (Inbox, Continue
reading, Needs review, Recently opened, Active projects, Recent notes), **Library**,
**Notes**, **Projects** and **Trash**. Choose what opens first with **Start with**
(Home Dashboard, Library, Projects or Restore Last View).

**Bringing documents in.**
- **Import PDFs / folder…** takes PDF files or folders (scanned with their
  subfolders; hidden and symlinked folders are skipped), or drop them onto the tab.
  **Build preview** inspects each file locally: the title, authors and keywords
  stored in the PDF and a DOI printed on the first page are *proposed*, with their
  source shown. Double-click a title, authors (separated by `;`), year or DOI to
  correct it. Identical files already in the library are skipped. When a file looks
  like another version of an item you have (same DOI or title), you can choose
  **Add as new version of …**; nothing is merged unless you choose it.
- Choose the file handling before confirming: **Managed copy** copies each file into
  your Paper-inator library and leaves the original exactly as it was;
  **Referenced file** leaves the file where it is and records its location.
- **Confirm and import** writes the checked documents. New items go to the Inbox;
  items with missing authors or year, or a title taken from the file name, are
  flagged *Needs Review*. If a file changed after the preview it is not imported.
- **Add item…** enters an item by hand; it does not need a document (for example a
  web resource with only a URL).
- If Poppler's `pdfinfo` and `pdftotext` are installed (package `poppler-utils`),
  proposals are better and the text inside PDFs becomes searchable. Without them,
  titles come from file names and only details and notes are searched. Scanned,
  image-only PDFs have no searchable text; Paper-inator does not perform OCR.

**Organising.** Every item has three independent dimensions: *Reading* (Unread,
Reading, Read), *Handling* (Inbox, Active, Archived) and the flags *Needs Review*,
*Key Reference* and *Favorite*. Archiving never resets reading progress. The
controls under the list apply to every selected item (select several with Ctrl or
Shift). **Organize selected…** adds or removes tags, changes states and flags and
adds the items to a project or collection, listing exactly which items it affects.

**Finding.** Search matches titles, authors, abstracts, keywords, tags, DOI, file
names, your notes and — with `pdftotext` — the document text. Filters (type,
reading, handling, flags, tags, project or collection) combine: every active filter
group must match, any chosen value within a group is enough, and all chosen flags
must be set. **Save search…** stores the criteria (not a frozen list), so a saved
search always shows the current library; **Update** and **Remove** change or delete
it. **Clear All** shows everything again.

**Documents and versions.** **Open document** opens the preferred version's document
in the external reader (desktop default, or the command set with **Reader: …**, for
example `okular` or `zathura {file}`). Paper-inator does not track or close the
reader, and positions or annotations made there are not synchronised; the built-in
reader follows in a later milestone. **Versions & files…** adds versions, sets the
preferred version (this never changes the item details), adds documents or
attachments as managed copy or referenced file, opens files and **Locate…** a
referenced file that was moved. A file with different content is only accepted if
you confirm it. **Propose metadata from PDF…** shows what the document offers next
to the current values; only the fields you tick are changed, and fields that
already have a value are unticked by default.

**Editing.** **Edit details…** edits an item as a draft. **Save** writes; leaving
changed edits offers Save / Discard / Cancel. If the item was changed elsewhere,
choose **Save my values** (only the fields you changed are written) or
**Use library values**. Invalid input (for example a malformed DOI) is reported and
your edits stay in the window.

**Notes.** **New note…** (or **Add note…** on an item) opens a Markdown editor with
buttons for bold, italic, headings, lists, quotes and code, and
**Link to item, note or project…**, which inserts a link that keeps working when
titles change. The preview beside the text shows the result; it never loads images
or other content from the internet or your disk. Links in the preview and in item
details take you to the linked item, note or project; web links open only after you
confirm. Notes can be summaries, findings, methodology, limitations, questions,
research ideas, meeting notes or experiment results. **Export as Markdown…** writes
the selected notes as readable `.md` files into a folder you choose; existing files
are never overwritten, and the library keeps the authoritative notes.

**Connections.** **Connect…** (on an item, note or project) links it to another
item, note or project as *Supports*, *Contradicts*, *Extends*, *Uses*,
*Derived From*, *References* or *Related To*. Choose the direction; the window
explains the connection in a sentence before you add it. Connections appear on both
ends with the matching wording (for example *Uses* / *Used by*) and can be removed
there.

**Projects and collections.** Create them on the **Projects** page. Projects have a
status (Active, Paused, Completed) and hold items and notes; collections hold items.
Add items with **Organize selected…**, notes with **Add to project…** on the Notes
page. **Show items in Library** filters the library to the project;
**Remove selected members** takes members out without removing them from the
library.

**Trash and permanent deletion.** **Move to Trash…** first shows what is affected.
An item takes its own notes along; its connections, project memberships, reading
state and flags are kept and come back with **Restore**. No file is moved or deleted
by moving to Trash. **Delete permanently…** (on the Trash page) shows exactly which
records and managed copies will be deleted and states that referenced files and the
originals you imported from remain on disk; nothing else is deleted. If deletion is
interrupted, it is completed the next time the library is loaded. Trash is not a
backup.

**Closing.** Closing the tab or the Hub reviews unsaved item details and notes
(Save / Discard / Cancel) and a running import (stop after the current document).
External readers stay open.

**Activity.** Imports, failed library loads, failed document opening, Trash and
permanent deletions appear in Hub Activity under Paper-inator.

Not yet included: the built-in PDF reader, highlights, bookmarks and reading
positions; citations, bibliographies and BibTeX/RIS/CSL JSON export; DOI lookup and
other online metadata; backup and restore; importing Zotero/EndNote/Mendeley
libraries; links to Book-inator books; a knowledge graph view.


### M18/M19 review and import safeguards

Music imports use embedded tags first; folder and filename parsing fill missing values only. Paper-inator uses logical recoverable Trash: managed files stay at their existing paths until separately confirmed permanent deletion. Referenced originals are never deleted.

When several drafts or modules need attention on exit or workspace changes, review their choices together. Cancel applies no choices. Confirmed saves occur before discards; a failed save stops continuation and completed saves remain saved. Running tasks can be stopped from the review, after which close again when they finish.

Paper document imports apply in the background. Stop cancels unfinished copying where possible and retains completed documents. The result list identifies completed and unimported documents. Recovery validates profile ownership first and defers staging cleanup during an active file operation.
