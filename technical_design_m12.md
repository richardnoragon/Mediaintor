# M12 technical design — everyday usability and reliability

**M12-01 COMPLETE; M12-G OPEN.** Design and controlled reproduction only. Application code, accepted packages and installations remain unchanged. [Scope](milestone_12_everyday_usability_reliability.md), [reproduction](test_data/m12_usability/recovery_reproduction.json).

## 1. Reproduced recovery failure

Current path: `ActivityController.review` finds an existing metadata editor, reviews its edits, then calls `editor.done(0)`. The synchronous `finished` handler `Bookinator.editor_finished` clears the editor and calls `auto_refresh`. That starts the catalog loader. The same review call then invokes `edit_metadata`, which returns early while the loader is active. The controller sees no editor/baseline and emits “Current metadata could not be read; recovery was retained.” No recovery metadata read actually started on this path.

The characterization script uses real Hub, Bookinator, MetadataEditor, ActivityController and RecoveryStore objects. Only catalog loading and metadata reading are controlled. It proves the existing-editor handoff starts refresh, prevents opening the recovery editor, preserves the recovery bytes and succeeds after simulated refresh completion. Explicit Save is still required. It uses temporary sample data, no Calibre library or accepted installation. This establishes a reproducible cause consistent with the M11 symptom, not retrospective proof of every original desktop event.

## 2. Recovery review transaction

Implement orchestration in `recovery_actions.py`, with small explicit lifecycle hooks in `window.py` and result/error reporting in `editor.py`. Keep storage/adapter authorization and library ownership checks intact.

States: idle → validate intent → review current edits → wait for catalog if necessary → read current metadata → combine preserved draft → ready for explicit Save. Each waiting/reading stage also supports cancelled or failed. Review is a transient operation, not an automatic recovery job.

- Capture recovery ID, revision/checksum, profile/device/library/book identity and a monotonically increasing request token. A second click on the same in-progress request focuses its status; it must not open a second editor or apply data twice.
- Block while imports, bulk writes or unrelated protected writes run, with the active operation described. Catalog refresh alone may be awaited after an explicit review request, with visible “Waiting for catalog refresh before reviewing recovery”. Do not wait invisibly or resume an operation on startup.
- Establish the handoff guard **before** calling the existing editor's Save/Discard/Cancel review: Save/Discard can also request refresh. Cancel keeps that editor and draft intact and ends the recovery request.
- Defer automatic refresh requests caused by this handoff rather than dropping them. Coordinate all entry points including focus/timer refresh and `editor_finished`. Release the guard in a guaranteed cleanup path. Service deferred refresh when it is safe; retain existing dirty-draft refresh deferral.
- Await any already-running catalog load using success/failure signals, not a nested GUI sleep or polling loop. Use a bounded catalog wait (35 seconds, matching workspace-restore convention); timeout leaves recovery intact with a Retry action. Metadata read retains its existing read timeout. No new writer timeout/force-kill behavior.
- Resolve the book by library UUID and book UUID after loading. Construct/load the recovery editor without presenting an empty editable form. Display an explicit loading state; show the editable draft only after a successful read, identity checks and conflict resolution.
- Re-read the preserved record and verify its revision/checksum before applying it. If it changed, require fresh review. Never mark a missing/corrupt/inaccessible draft as recovered. Missing book/library mismatch has a distinct explanation.
- Guard completion with request token, current module/editor instance and current library/profile identity. Ignore stale callbacks after module close, library change, cancellation or a newer request. Disconnect callbacks and release refresh deferral on every exit path.
- A pending review can be cancelled; cancellation does not discard preserved work. Existing close handling and critical-operation protections remain authoritative.
- Opening/retrying reconstructs a draft only. Existing explicit Save, partial-save retention, conflict handling and recovery-resolution-after-verification rules remain.

Error messages separate: no preserved draft; permission denied/access unavailable; corrupt/unsupported draft; book missing; wrong library; metadata-read failure; catalog timeout. Carry the actual safe local failure reason from the read result rather than substituting a generic “could not read” message. Paths/book metadata may appear where needed locally but must not leak into always-redacted diagnostic exports. Display a recovery time only when the record actually contains one.

## 3. Save feedback contract

Build feedback from stable book identity plus verified response, not from current selection or merely clicking Save. Capture the original title for an in-progress edit; after a successful title change show the verified title, with old title context where useful. Do not infer success from a missing error alone.

- Success: “Saved tags for The Time Machine.” For several fields, show book title and friendly field names.
- No-op: “No changes to save for …”. Recovery reconciliation may still require the existing read/resolve verification.
- Partial: identify book, fields saved and remaining failed/conflicted fields. Preserve successful commits and outstanding draft; retain Retry/Keep Editing/Discard behavior.
- Unverified response: “Save result could not be verified for …”; retain edits and direct the user through current re-read/retry checks.
- Keep feedback visible in the editor after save/refresh; unrelated catalog messages must not overwrite its result. Optional status-bar echo must use the same verified result.

Prefer a pure feedback formatter with table-driven tests. Book-specific feedback is local UI only. No new diagnostic fields containing title, author, library path or draft contents.

## 4. Bulk revert states and counts

Use one pure outcome summarizer for dialog feedback and acceptance assertions; inspect current journal state and field-level `applied` evidence. Retain existing journal schema where possible. Per-attempt stop/error context can be added as optional backward-compatible information; never reinterpret old records as proven cancellation without evidence.

UI phases: preview ready (confirmation required), executing, stopping after current-book verification, completed, interrupted, failed, or cancelled before writes. The confirm button should identify revert execution, such as “Confirm revert”, while ordinary bulk edits retain their appropriate wording. Reopening history must not display a completed operation as an unconfirmed preview.

Count each included book once in the headline totals:

| Journal state | Headline bucket | Additional detail |
| --- | --- | --- |
| complete | completed | Report unchanged/no-op books separately so “completed” does not imply a write. |
| failed | failed | Indicate partial field changes where `applied` evidence exists. |
| conflict | pending | Conflicts awaiting explicit review; do not double-count as failed. |
| pending | pending | Not completed; may retain prior verified partial changes. |
| inflight/unverified | pending | Explicit “verification required” subset; never imply no writes occurred. |
| excluded/discarded | separate excluded/discarded totals | Outside current included-work totals; retain history of prior writes if present. |

Define included total as completed + failed + pending; show excluded/discarded separately. Display counts from the entire current batch, with attempt-specific details only if reliably available. A partially saved book is not counted as completed until all requested fields are verified.

“Cancelled — no books changed” is allowed only with positive evidence that no write was attempted and no prior applied/unverified work exists, e.g. cancelling a fresh preview. After any write or uncertain response, display actual counts and retained work. Completed means no failed/pending included work. Interrupted means an explicit stop with unfinished work. Failed means execution failed, with any completed books still reported. Preview count is not completion evidence. Never roll back verified successes automatically.

## 5. Installation identification

Use deployment-owned `MEDIAINATOR_INSTALLATION_LABEL`, defaulting to “Development” for an unlabeled checkout and “Installed” for an unlabeled installed package. M12's isolated launcher sets “M12 Test”; keep window and KDE launcher labels consistent. Whitespace-trim, bound to 80 printable characters, reject controls/newlines and use a safe fallback for invalid input. Treat as display data, never a shell command or path.

Read actual installed version/build ID from the package manifest. Display the label in the main title and build in About (optionally the title). A source checkout shows “development/unpackaged”, never a fabricated installed build. Label is not a profile identity, workspace setting, permission or trust signal. It must not be copied from M11 preferences or restored by a workspace.

Keep M11 and prior launchers/files untouched. M12-G does not change a label to “Everyday”, switch a default launcher or promote a build. Promotion is a later explicit decision preserving newer M11 data.

## 6. Isolation and implementation sequence

M12-02: consistent snapshot of a closed M11 source into a new sibling M12 Test root, independent mounts/configuration/library/backups and launcher. Verify package, identities and copying; record M11 source hashes. No NAS or shared writable data. Coordinate normal closure before copying; never force-stop writers.

Then implement recovery (03), save feedback (04), revert presentation/counting (05), and installation identification (06). No changes to recovery data semantics or Calibre write policy merely to simplify presentation. If journal metadata changes prove necessary, add backward-compatible reads and fixture coverage before packaging.

M12-07 builds a new candidate only after appropriate checks pass. Existing accepted M10/M11 artifact is immutable. Verify real installed imports and startup, label/build identity, preserved ownership and no source-checkout dependency. M12-08 uses exact-candidate personal KDE checks plus persisted-result review before closing M12-G.

## 7. Verification matrix

- Recovery: existing clean editor; dirty Save/Discard/Cancel; partial save; existing catalog load; editor-finished refresh; load failure/timeout; missing/permission-denied/corrupt record; wrong library/book; changed payload revision; duplicate clicks; module/library switch and stale completion. Verify payload untouched and no catalog save before explicit Save.
- Convert the M12-01 characterization into a success regression in M12-03: first valid Review must reach preserved draft without a manual second attempt after its own editor handoff.
- Save: single/multiple fields, renamed title, no-op, partial save, conflict, unverified save, cover operations, and wrong-selection prevention. Redacted diagnostics remain data-free.
- Revert: preview versus execution, stop before writes, stop after success, partial fields, conflicts/exclusions, uncertain write, failed result, mixed counts and restart/history. Verify database fields and journals rather than trusting labels alone.
- Identification: valid/missing/invalid labels, real installed manifest versus checkout, side-by-side stable/test launchers, workspace/restart does not replace deployment identity.
- Regression: metadata/tag management, cover replacement/removal, workspace actions/removal, eligible history removal, imports, search/filter and review/retry. Book/file deletion remains excluded.
- Desktop: correctly labeled M12 window, recovery without losing drafts, meaningful saved-book feedback, unambiguous revert confirmation/completion, restart and persisted evidence. Record actual artifact hash; no elapsed-time requirement.

## Remaining boundary

This completes technical design and controlled reproduction only. It is not a production fix, real Calibre fault-injection result, new installed package, physical KDE acceptance or promotion. M12-02 through M12-08 remain open.
