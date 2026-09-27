# M2 technical design and verification

Status: implemented; automated verification passed. Final user desktop acceptance is complete. M1's G2 viewer-lifecycle gate is passed for Calibre 9.2.1; see the recorded M1 desktop confirmations and current regression tests. G2 is not a new metadata-write gate.

## Boundaries and data flow

The hub remains the entry point. Catalog browsing and editor reads use full private snapshots. Only an explicit metadata Save writes to the selected library, using its original book ID and verified UUID. Sample mode has no metadata writes. Test mode uses a registered disposable library.

`metadata_rules.py` handles draft validation, dirty fields and three-way comparison. `editor.py` provides one single-book draft editor, ordered author entries, unordered tags, basic description formatting, cover selection/removal, and conflict review. Untouched HTML is returned from the baseline without Qt serialization.

`MetadataWorker` keeps snapshot creation and helper execution off the UI thread. Each operation starts the installed `/usr/bin/calibre-debug` with JSON request/response files and isolated Calibre configuration. `calibre_metadata_helper.py` checks Calibre 9.2.1, acquires Calibre's `singleinstance('db')` lock and calls the database API. It never writes SQL directly. Library symlinks and changed record UUIDs are rejected.

The UI blocks conflicting operations while a metadata request is running. Reads have a subprocess timeout; writes are not forcibly killed mid-commit. Closing while a write is running waits for the user to retry after verification, rather than interrupting a potentially partial commit. An unverified helper failure retains the draft and advises revalidation on Retry.

## Save, conflicts and failures

Save sends only dirty fields. Under the Calibre lock, the helper reads current values, checks identity, validates intended fields and image data, and compares baseline/current/pending values. Conflicts return without intended writes. The user selects per-field values or either global shortcut, or cancels. A subsequent Save revalidates against the values displayed in the conflict review.

Successful fields are read back and retained. Failed fields remain in the draft, with Retry Failed Changes, Keep Editing and Discard. Discard reads current values when access is available; if access is blocked, it abandons the local draft using the last verified baseline and clearly defers the fresh read. No successful writes are rolled back. Covers are compared through Calibre's expected image conversion, accounting for re-encoding and resizing.

Cover backup JSON files are stored under `metadata-recovery` beside hub settings, identifying library, book UUID/ID and original image bytes. On a failed cover write, the helper restores the original through Calibre and checks the bytes. Failure to restore is reported with the retained backup path. Backups are retained for recovery; no automated retention/deletion policy is introduced. A failed cover operation does not roll back successful text fields.

Clearing Series hides/ignores the retained internal index. A new series explicitly defaults to 1. Numbers must be finite and non-negative. Tags containing commas are rejected before save; author commas and author order are preserved.

## Refresh and lifecycle

Focus regain and a 30-second timer trigger refresh when the editor is clean and access is available. Dirty drafts defer replacement; database/WAL size and modification-time changes produce the external-change message. This detector is advisory; authoritative conflict checks occur on every Save/Retry. Access contention retains the catalog and retries on later refresh triggers, never automatically commits drafts.

Book selection, explicit Refresh, editor/module/hub close and library changes review unsaved edits. Cancel stops the action. When metadata and an owned reader or active catalog refresh need review together, a combined dialog provides metadata and reader choices and explicit refresh interruption. Saving requires readers to close. Running metadata writes cannot be interrupted through this dialog.

## Verified scope and limits

- 41 automated tests pass, including the 23 original M1 tests and combined close/conflict dialog tests.
- 16 Calibre adapter integration/fault checks pass on a complete disposable 101-book copy. Injected write failures exercise real partial commits and cover corruption/recovery; restoration failure is deliberately injected, not an actual disk-full event.
- 17 real hub/editor application checks pass on another disposable copy; original-library hashes unchanged. Catalog count, format grouping, actual saves/path refresh, series rules, external conflict/cancel/discard, cover changes and untouched HTML are covered.
- The separate final user desktop review is accepted. No new original-library mutation was performed by these checks.
- Calibre version upgrades require revalidation. Process checks and the Calibre lock do not coordinate arbitrary tools that bypass Calibre's locking, or guarantee concurrent viewer writes. Keep Calibre and readers closed for metadata operations.
- No application/schema version change, migration or release publication occurred. Library format files are not intentionally modified by metadata editing, although Calibre changes their paths after title/author edits.

Evidence: [M2 acceptance](test_data/m2_acceptance/README.md), [M1 desktop confirmation](test_data/m1_acceptance/desktop_confirmation.json), [M2 requirements](milestone_02_metadata_editing.md).
