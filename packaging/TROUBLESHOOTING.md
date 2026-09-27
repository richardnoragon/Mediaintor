# Troubleshooting

## Calibre is missing or unverified

Read the detected and supported versions in the Hub's prerequisite panel. The
verified version is Calibre 9.2.1; a newer version is not automatically supported.
Calibre is installed separately. Media-inator does not install, upgrade or
downgrade it. After resolving the prerequisite, choose Recheck prerequisites,
then explicitly reload the library or retry the operation. Recheck never resumes
jobs or saves drafts. There is no compatibility override.

## Library access is blocked

Close Calibre, its content server and ebook readers, then retry. Browsing uses a
private copy but still respects Calibre's access lock. Do not delete Calibre lock
files or force-close another application. The existing catalog may be stale.

## No books appear or a file is missing

Choose the existing library folder containing metadata.db, not an individual
book folder. Library selection does not import books or create a library.
If loading fails, check that the drive is connected and the folder is readable.
Reconnect the original location and reload. Existing displayed books may be out
of date. Do not delete metadata.db to repair a load error. A missing format must
be restored or corrected through Calibre before retrying its format button.

## Save failed or only some fields saved

Keep the editor open. Successful fields remain committed; remaining changes stay
in the draft. Retry rechecks current library values and may ask about conflicts.
Discard abandons only unsaved changes. After a failed Save and failed explicit
Retry, the app attempts emergency preservation. A preserved draft is not a saved
Calibre record. Use Activity to review recovery and explicitly Save later.

## Emergency preservation failed

Keep the editor open and choose Preserve Elsewhere with a writable location.
The copy must be registered successfully before it can protect the requested
close. Do not force termination while the app reports unpreserved work. Cancel
or Keep Editing stops the close request. New edits require new preservation.

## History or recovery looks missing

Use Open full activity history and Show dismissed. Hide from action list hides an entry; it does not
delete recovery. Open recovery draft or the operation-specific Review action opens a preview or draft, not a completed
save. Discard preserved draft/pending work and Delete this history record are separate confirmed actions. Do not
manually delete the application-data folder while investigating missing work.

## Settings cannot be saved or loaded

Check available disk space and permissions on the settings location shown by the
error. Close another running Media-inator instance. Existing settings are not
automatically overwritten when invalid. Retain a copy before manual repair;
do not remove the whole configuration or recovery directory to bypass an error.
If an unsupported schema is reported, use a compatible application version.

## Installation or upgrade stops

Run the per-user installer without sudo. Close all Media-inator windows first.
Use the prerequisite versions listed in Installation. A checksum mismatch means
the bundle should be replaced with a trusted intact copy, not bypassed. Modified
managed files or a changed installation pointer need review; do not delete user
libraries or application data. Interrupted install/uninstall actions retain a transaction record. Extract the
installer from the trusted bundle and run it with repair to complete the recorded
action. Modified files stop repair for review; no forced overwrite or schema
downgrade is provided.

## Menu entry or window does not start

Try ~/.local/bin/mediainator from a terminal and retain its error text locally.
A missing system Python/PyQt6 prerequisite can prevent any GUI from opening;
consult INSTALL.md. The supported target is Ubuntu 26.04.1 KDE, x86_64.
Reinstalling the same trusted bundle can restore intact managed launch files,
but the installer deliberately refuses to overwrite modified/unmanaged entries.

## Reader shows a blank or unreadable page initially

Press a key in the reader, then try page navigation. This known viewer behavior
is deferred. If it persists, close the reader and retry; do not open several
readers concurrently. Closing the reader does not close the Hub.

## Shutdown and diagnostics limits

Cooperative KDE close handling has isolated KWin evidence. Forced termination
or power loss before preservation is not protected by continuous draft autosave.
Full installed desktop acceptance remains M6-07. Use Help → Preview redacted diagnostics to inspect and explicitly export a
local JSON report. Nothing is uploaded. Current-session errors have fixed messages
and sanitized frames; historical raw logs are excluded. Do not share raw logs or
tracebacks assuming they are safe: they may contain paths or book information.
If export fails, choose a writable regular file destination; the preview remains
unchanged. About shows application/runtime versions without library contents.


### Recovery waiting for catalog

Wait for the current refresh to finish; do not discard a preserved record to work around a read error. A waiting recovery request expires with a retry message if the catalog does not finish. Close the module to cancel the request, or retry after Library loaded. If a specific permission, identity or corrupt-record message appears, resolve that cause while retaining the original recovery files. Opening Review never authorizes an automatic metadata save.


## Selecting the correct batch

Use Batch History and read its selected-batch summary before choosing Preview revert of selected batch. A completed revert selects its new record, not the original edit. Follow the related-batch selector to inspect the original or revert history without executing it. If a record disappears, choose a valid record explicitly; the application does not silently select another target.

If a file picker does not accept typing where expected, browse the folders or use File or folder path in the import window and choose Preview path. Path-entry behavior depends on the installed picker and focus; do not repeatedly press import confirmation to compensate.
