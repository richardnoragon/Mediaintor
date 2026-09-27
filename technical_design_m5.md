# M5 — Hub Activity & Recovery technical design

Current M5 status: **M5 COMPLETE; M5-G PASSED / CLOSED** following final evidence review and user desktop acceptance. [Gate review](test_data/m5_acceptance/gate_review.md). All M5-01–M5-07 tasks are complete. Earlier dated/stage checkpoints are historical; no release is implied.

Status: M5-01–M5-06 are implemented/verified for their bounded scopes. [M5-06 evidence](test_data/m5_06_emergency/README.md) covers automatic preservation and close handling. M5-07 full application and desktop acceptance are complete; M5-G is PASSED / CLOSED. Earlier checkpoint sections describe historical stages.

## Current integration map

| Existing component | Current behavior | M5 change |
| --- | --- | --- |
| `ImportStore` / `ImportDialog` | Schema-1 per-library journals; pending imports, explicit preview, review flags stored in import items | Project journals into Activity by stable batch ID; open a selected journal for review; preserve book-review flags independently before allowing journal deletion |
| `BulkStore` / `BulkDialog` | Schema-1 before/after history, partial results, uncertain writes, revert links, guarded deletion | Reference existing batch IDs; do not duplicate executable plans; route Retry through fresh review; share Dismiss/Discard/Delete controls |
| `MetadataEditor` | In-memory baseline/draft; successful fields committed, failures retained; normal close blocks failed Save | Emit save-attempt outcomes; track draft revision and explicit retry; preserve outstanding edits durably; open recovered edits as a draft |
| Metadata helper | Locked, version-bound writes; identity checks; per-field read-back and cover restoration | Reuse explicit Save/conflicts and Calibre 9.2.1 safeguards; do not perform direct database writes |
| `Bookinator.loaded` | Automatically opens the pending import dialog; separate bulk pending notice | Replace automatic dialog opening with one Hub summary; no automatic retry or launch |
| `Hub.review_close` / editor review | Scoped metadata/task/reader review; no forced writer termination | Carry a close intent through save/retry/preservation; continue it only when its captured draft is protected; retain other task/reader decisions |
| `Hub.persist` / `SettingsStore` | Atomic settings saves, status-bar errors | Record actionable save failures; suppress successful preference events and coalesce repeated identical storage failures |
| Refresh / reader launch | Best-effort access guards and immediate failure messages | Add recoverable failure/interruption outcomes only; no successful launch/refresh telemetry |

## Storage and identities

Use `QStandardPaths.AppLocalDataLocation` for M5 Activity and `Recovery/Single Book Edits`. Keep existing preference storage and import/bulk journal locations compatible. Add separate schema-1 M5 files rather than silently changing hub settings schema 1.

Activity operation identity is stable across retries: operation ID, owning profile/device IDs, module, operation type, library UUID and canonical path where applicable, source-journal ID, and related original/revert IDs. Individual attempts have separate IDs and timestamps. Keep outcome (success/partial/failure/interrupted), pending work, recovery availability and dismissal as separate values; dismissing or discarding must not rewrite an actual failure into success.

An operation record contains summaries and references, not copied ebook libraries. Preserve existing import/bulk journals as the authoritative execution/reconciliation sources. For single-book saves, persist attempt summaries separately from an emergency payload. An emergency payload holds schema, recovery ID, operation ID, profile/device/library/book identity, captured draft revision, outstanding proposed fields, baseline values only for those fields and required series/name dependencies, and verification uncertainty. Embed the bytes of an unsaved cover replacement; do not depend on a temporary file or the original image path. Preserve pending HTML exactly.

Existing records lack some profile/device/timestamp information. In this one-profile/device scope, register them under the current local installation with explicit legacy provenance. Do not invent historical attempt dates from file modification times. Display unknown history dates as unknown; newly observed attempts get real timestamps. Future multi-profile migration is outside M5.

## Recovery durability and discovery

1. Capture a stable draft revision after failed Save and failed explicit Retry. Do not treat user-input validation errors or cancelled conflict review as disk-write failures.
2. Produce an envelope with payload and SHA-256 integrity digest. Use JSON with explicit schema validation; no executable serialization. Recovery is not encryption, and the digest detects accidental corruption rather than providing authenticity.
3. Write a same-directory temporary file, flush/fsync, atomically replace the target and fsync its directory. Read back and validate the payload, digest and identities.
4. Persist and read back the discovery registration, including an alternate location when chosen. Only then report successful preservation. A payload file existing after a failed commit/registration does not authorize closing.
5. If any step fails, keep the editor/close intent pending and offer **Preserve Elsewhere…**. If application storage itself cannot register the alternate copy, remain open and explain that the file may exist but cannot yet be reliably discovered. No false success.

Default recovery copies are independently discoverable by scanning the managed folder, so a damaged/missing activity index does not silently lose them. Alternate copies require a durable pointer; never search arbitrary user folders. Corrupt, unsupported-schema or wrong-owner files are retained, listed as unavailable where possible, and never loaded as editable drafts. A missing external destination is a recovery problem, not proof that work was discarded.

Maintain payload generations by draft revision. If the user keeps editing after preservation, the new revision is unprotected until saved or preserved again. An older copy must not authorize closing a newer draft. Do not erase the previous valid generation before the new one is durably verified. Invalid raw editor input must remain in the editor; no forced close bypasses validation or preservation failure.

## Save, retry, close and recovery state transitions

A single save chain tracks failed attempts for the current draft revision. Save failure keeps edits available; explicit Retry re-reads current Calibre values and performs conflict review. A failed retry invokes emergency preservation of remaining edits. Successful partial field writes remain committed and are excluded from the recovery intent; uncertainty after a lost acknowledgement is retained until fresh reconciliation.

When preservation succeeds:

- With an already-confirmed close intent, complete that tab close or orderly Hub/application shutdown automatically, subject to its other agreed task/reader controls. Briefly display “Unsaved edits preserved in an emergency copy,” record the Activity result, and retain the next-startup recovery notice.
- Without a close intent, leave the editor open. Keep the unsaved draft distinguishable from a successful catalog save.

If preservation fails, stay open. Cancel before combined close confirmation applies no save/discard/task/reader actions. No emergency workflow force-closes third-party applications. Unexpected termination before preservation is not protected by this design; continuous draft autosave is outside the agreed scope.

Review Recovery verifies ownership/library/book identity and reads current values via a private snapshot. Reconstruct a draft, compare only affected fields and coupled series/name context, and present conflicts. Matching already-committed values become no-op fields rather than repeated writes. Preserve unrelated changes. Review and Retry never write to Calibre; a new explicit Save is required. The existing adapter revalidates under the database lock at Save, including changes that happened after review.

Only verified completion resolves the corresponding recovery payload. Partial recovery retains the unfinished subset and latest comparison baseline. A failure to durably mark recovery complete leaves a reconcilable record; it must not cause an automatic replay after restart.

## Activity projections and UI routing

Group by module/operation for the current profile/device. Use an operation's attempt history to derive latest success and latest actual failure; interruptions and dismissal do not replace these markers. Counts operate on distinct operation IDs. Pending/failed/recovery indicators may overlap, so the overall count is the union rather than their sum. Dismissed tasks are excluded from the active panel and startup attention count but remain available under Show dismissed/full history.

The default Hub panel is collapsible and has **View Full History**. Show detailed counts, affected items, error text and actionable next steps. Successful routine preference writes, successful automatic refreshes, successful background maintenance and successful reader launches are excluded. Aggregate repeated identical actionable storage/refresh failures into one unresolved operation with attempt information rather than flooding the panel. Storage-reporting failure must fall back to a visible in-memory notice, not recursively try to record its own failure indefinitely.

On startup, inspect local records without executing them. Present one summary with **Open Activity / Review Recovery / Dismiss**. Replace the current automatic import-dialog opening. Summary dismissal only hides attention; it never discards work. A selected Retry routes to its existing import/bulk review, single-book recovery editor, or explicit refresh/launch/settings retry screen. A refresh/reader retry must still require a deliberate action; it must not launch a reader simply because the user opened Activity.

## Discard, deletion and migration

Dismiss preserves journal, payload and retry availability. Discard Pending first requires review of unresolved recovery (including uncertain-write reconciliation), then a separate confirmation explaining that pending work cannot be resumed. Committed library results remain; retry is removed only for abandoned work. Delete History is disabled until recovery is resolved or explicitly discarded. It has a separate confirmation explaining loss of review/revert capability.

Deletion must coordinate Activity references with operation journals and recovery payloads. Use a durable deletion intent and restart-safe cleanup: after user confirmation, mark the intent, delete only explicitly owned associated state, then finalize the activity removal. A filesystem failure reports incomplete cleanup without claiming complete deletion. Never delete source ebooks, original library content or another operation's payload. Shared/original/revert links must not cascade-delete separate operations; retained descendants show that an ancestor history record was explicitly removed.

M3 review flags are book state, not disposable operation history. Before enabling deletion of an import journal, migrate its missing-metadata provenance and explicit Reviewed status to a library/book-UUID store, verify the migration, and switch review queries to that store. Deleting Activity must not clear Needs Metadata Review or change calculated completeness. Existing journal-based fallback remains readable until migration succeeds; a migration failure blocks destructive cleanup.

Existing M4 journals have no independently enforced “reviewed before discard” marker. M5 must implement the reviewed-revision guard in the shared action coordinator; displaying a list alone must not allow accidental irreversible discard of an unseen emergency copy. No history migration or deletion is performed by the validation script on user data.

## Validation boundary and implementation handoff

[Disposable validation](test_data/m5_validation/README.md) exercises real Calibre partial writes/conflicts plus a small candidate recovery protocol. It is intentionally outside `mediainator/` and is not a shipped recovery implementation. It validates storage/identity/conflict feasibility and documents the import-review coupling; it does not validate the future panel, complete migration transaction, production startup routing or OS shutdown integration.

M5-03–M5-07 must implement and test those application contracts, including corrupt indexes, multiple simultaneous records, interrupted cleanup/migration, persistent attempt aggregation, close cancellation, revision changes after preservation, alternate-path unavailability, existing reader/task ownership, and user desktop acceptance. M5-G remains unchecked until the corresponding application evidence exists.

## M5-03 implementation checkpoint

`activity.py` now provides `ActivityStore` and the non-recursive `ActivityBridge`. Stores are partitioned by profile/device ownership, protected with Linux advisory locks and atomically replaced JSON. Operations keep separate attempt IDs, outcomes, pending/recovery flags and source-journal references. Journal scans are idempotent; legacy dates remain unknown. Current settings/refresh failures coalesce; successful housekeeping is not logged.

`recovery.py` provides validated, integrity-checked payloads, revisioned generations, atomic verified discovery registration, alternate destinations, default-folder discovery and conflict-reviewed draft reconstruction. `MetadataEditor.preserve_recovery()` is an explicit integration API. It is not automatically called by the existing Save/Retry/close controls yet. Recovery resolution and deletion coordination remain M5-05/M5-06.

`ImportStore.review_records()` atomically migrates stable batch/operation identities to a separate `book-review/state.json` store beside the existing journals. Both metadata completeness and explicit Reviewed status survive journal removal. The editor and review filter now use this store. Pending journals or migration failures block the new storage-level `delete_history()` API; shared confirmation/review/cleanup orchestration is still M5-05.

The normal entry point uses Qt's AppLocalDataLocation for new Activity/recovery stores. Direct test/embedded Hub construction defaults to a `data` folder beside its supplied settings, keeping disposable sessions isolated. Existing settings schema and import/bulk journal schemas are unchanged. Startup records existing work and does not open recovery dialogs automatically; the summary UI is M5-04.

Verified: 85 unit/UI tests and 14 actual disposable integration checks; original-library hashes unchanged. M5-03 is complete. Earlier future-tense descriptions in this design remain contracts for M5-04–M5-07 where not listed as implemented here.

## M5-04 implemented presentation

`activity_panel.py` provides the default expanded panel, operation grouping, distinct attention counts, latest actual success/failure markers, read-only full history and attempt details. ActivityBridge mutation notifications schedule a coalesced Qt refresh; reads do not recursively notify. Storage errors remain visible without overwriting damaged files. Interrupted attempts cannot replace actual failure markers. Full History includes resolved and dismissed entries, with Show dismissed and Unresolved work only filters.

One non-modal recovery-summary widget sits above the tabs, visible even when Book-inator is selected. Startup reads local journals without opening Calibre or executing work, including when the module is closed. The same summary updates as discovery completes; Dismiss suppresses that banner for the rest of the session, preserving all records. Opening history or details never retries jobs. Review Recovery currently selects unresolved history; actual recovery routing and task dismissal/discard/deletion remain M5-05. Automatic emergency preservation and close continuation remain M5-06.

[93 unit/UI tests and rendered evidence](test_data/m5_04_activity/README.md) verify M5-04. M5-G remains open; full application acceptance is not claimed.

## M5-05 implemented shared actions

`RecoveryActions` owns revision-checked cleanup and `ActivityController` routes explicit UI actions. Activity details offer Review / Retry, Dismiss, Discard Pending and Delete History. Existing production import/bulk discard/history controls use the same coordinator. Busy workers block state-changing actions; cancelled editor review does not reuse an old operation dialog.

- Review selects the exact journal. Import/bulk review reconciles uncertain outcomes without executing pending writes. Retry rebuilds normal preview; execution still requires confirmation. Single-book recovery checks current library/book/owner identities, offers field conflict choices and loads an editable draft. Save revalidates via the existing adapter. Reader/refresh/settings retries require an additional explicit confirmation.
- A session-local review token hashes authoritative journal/payload state. Discard refuses unreviewed, changed or uncertain state. Successful writes remain committed; abandoned pending work is recorded as discarded, never as successful execution. Discarding a recovered editor's local draft leaves its durable copy available for the separate Discard Pending action.
- Successful verified recovery saves resolve registration; partial saves preserve only outstanding fields with an updated comparison baseline/generation. Resolution/preservation failure retains a reconcilable copy and reports the problem. No automatic initial emergency preservation or close continuation is introduced here.
- Dismiss persists independently of operation outcomes/payloads. Dismissed entries remain inspectable/retryable through Full History.
- Delete History is disabled for pending/recovery work and separately confirmed. Import book-review provenance is migrated before cleanup. A durable intent captures owned paths and content hashes; only unchanged owned files are unlinked and their parent directories synced. Cleanup failures retain the intent and attention entry. Delete History explicitly resumes confirmed cleanup after restart; nothing resumes automatically. A final deletion marker suppresses stale projections. Separate revert descendants remain and identify their deleted ancestor.
- Recovery registrations track known alternate-location generations so explicit history deletion can clean those owned copies too. Unknown external folders are never scanned. Corrupt or changed cleanup targets are retained and reported.

Verification: 119 unit/UI tests, including fault injection, plus 13 actual Calibre checks on a fresh copy of the previous disposable fixture. [Evidence](test_data/m5_05_actions/README.md). M5-05 is complete; M5-G remains open.

## M5-06 implemented preservation and close handling

The editor tracks failed Save attempts against the current draft contents. User changes reset the failed-attempt chain; validation errors (including invalid cover images) and cancelled conflicts do not count as failed writes. A second failed explicit Save/Retry invokes durable emergency preservation. Verified partial results first update the baseline and remove committed fields; unverified results retain the outstanding intent for fresh reconciliation during later recovery.

A successful payload write plus registration/read-back records the protected draft revision and contents. The close guard also checks that the registered copy still exists, is unresolved and matches the captured payload. A stale revision, missing copy, failed registration or failed preservation cannot authorize closing. Stable recovery identity survives an unsuccessful default-location attempt followed by an alternate-location attempt. A failed Save after preservation can still be retried; later verified completion resolves the preserved copy.

Close intent is scoped to the active close-review call. Choosing Save may lead to an explicit Retry Save / Keep Editing / Cancel prompt; a failed retry preserves automatically. Successful preservation returns to the already-requested close without another close command. Preserve Elsewhere is available on preservation failure; cancellation leaves the editor open and clears the close intent. Ordinary Save/Retry never closes the editor. Tab and Hub closure reuse this path after their existing combined reader/task review; cancellation before confirmation applies no save/discard/reader/task actions. Reader timeouts never force termination. Settings-save failure can still prevent Hub exit after edits are protected.

The editor and Hub display that edits were preserved, not saved to Calibre. Recovery Activity/history and the next-startup summary retain the recovery notice. Actionable preservation failures are recorded and cleared from attention after successful preservation, Save or explicit local discard; historical failures remain inspectable.

Qt `commitDataRequest` uses the same Hub close path when interaction is allowed. Without interaction, dirty/busy work or owned-reader activity vetoes cooperative shutdown; clean preferences are persisted without prompting. This covers cooperative session requests where the desktop supplies them, not forced termination, power loss or draft autosave. Actual KDE/Wayland logout behavior remains part of M5-07 desktop acceptance.

Verification: 143 unit/UI tests plus 14 real-Calibre disposable checks. The live adapter test uses a valid replacement image and a file occupying the test cover-backup directory to cause a real storage failure after a successful title write. The pending cover alone is preserved, an already-requested Hub close continues, and restart discovers the copy without applying it. [Evidence](test_data/m5_06_emergency/README.md). M5-06 complete; M5-G remains open.

## M5-07 native Wayland close verification

Installed KWin 6.6.6 was exercised in a private D-Bus/virtual Wayland session. The real compositor closes application windows; no `commitDataRequest` signals were observed. Cancel retained the draft and blocked window completion; Save/Retry/preservation completed the close. Because KWin may close both Hub and editor, the accepted Hub close now authorizes only the matching protected editor revision to close without another Save dialog. New edits or unavailable protection invalidate that authorization. Unit and real-compositor regression checks pass.

[Evidence](test_data/m5_acceptance/README.md): 147 unit/UI tests, 21 application/scale checks, two isolated KWin scenarios. Desktop acceptance is user-confirmed, including successful close and startup recovery without automatic editor opening or cover application. The user accepts isolated KWin evidence as sufficient; host logout/poweroff was not performed. M5-07 is complete and M5-G is PASSED / CLOSED after final evidence review.
