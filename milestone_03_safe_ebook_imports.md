# Milestone 03 — Safe Ebook Imports

Status: **M3 COMPLETE; M3-G PASSED/CLOSED.** All implementation tasks, automated checks and final user desktop confirmations passed. See [acceptance record](test_data/m3_acceptance/README.md).

## Confirmed scope

Manually select or drag and drop local EPUB/MOBI/PDF files or choose a folder (including subfolders), prepare an import preview, explicitly confirm, and add ebooks to the existing Calibre library through supported Calibre operations. Report outcomes and refresh the catalog so successful imports can be browsed and opened.

- **Copy-only:** preserve original files, filenames and locations. No move, rename or deletion of originals. Calibre manages destination organization; this is not a user file-management command.
- **Mandatory preview and confirmation for every import**, including clean batches. The hybrid/automatic flow discussed earlier is not the selected M3 behaviour.
- Preview identifies duplicates, similar existing titles, missing metadata and validation failures. Show proposed actions and unresolved decisions; never silently merge based on title similarity.
- Only identical file contents count as duplicates. Skip and report them regardless of filename/location. Metadata similarity is an association question, not duplicate identity.
- Preserve completed work after failures/interruption, clearly report unfinished work, and make retry safe. Implement the operation-level recovery M3 requires; broader shared hub activity/recovery presentation is M5.
- Excluded from M3: bulk metadata editing, automatic/trusted imports without preview, conversion, export, direct move/rename/delete-original commands and a full suite activity dashboard.

Milestone sequence: **M3 imports → M4 bulk metadata editing → M5 hub activity/recovery**. M4/M5 detailed scope and acceptance are not yet defined. The future preference to skip confirmation is unassigned, not automatically included in M4 or M5. Deferred file-management features retain their place in the backlog.

## Implementation passes

| ID | Status | Action / required evidence |
| --- | --- | --- |
| M3-01 | DONE — requirements planning | Confirmed decisions, preview actions and disposable fixture matrix recorded below; no implementation implied |
| M3-02 | DONE — capability/protocol evidence | Validate Calibre copy/import APIs on disposable libraries; verify metadata extraction, destination paths, identical-content detection and failure outcomes |
| M3-03 | DONE — implemented and automated checks passed | Implement file/drop/folder selection and recursive discovery; validate readability/formats and build a preview without library/source mutation |
| M3-04 | DONE — implemented and automated checks passed | Implement duplicate checks and explicit association decisions; confirm the reviewed plan and revalidate stale files/library state before writes |
| M3-05 | DONE — implemented and automated checks passed | Execute confirmed copy imports with per-item verification, progress and safe interruption; preserve completed records and sources |
| M3-06 | DONE — implemented and automated checks passed | Implement outcome reporting and retry/recovery without duplicate re-import; refresh catalog and resolve imported formats to valid paths |
| M3-07 | DONE — automated and user desktop acceptance | Run full disposable-data acceptance, M1/M2 regressions and user desktop review; close M3-G only with recorded evidence |

## M3-G — Import acceptance gate

Status: PASSED / CLOSED — automated checks and all user desktop confirmations complete. This milestone-specific gate does not rename existing technical gates G3/G4.

- [x] M3-G01: Scope decisions and supported Calibre import behaviour documented before live-use enablement.
- [x] M3-G02: File selection, drag/drop and recursive folder intake handle EPUB/MOBI/PDF and report unsupported/unreadable inputs without losing unrelated entries.
- [x] M3-G03: Every batch requires preview/confirmation; cancelling before execution changes neither library nor source files. Preview flags duplicate/similar-title/missing-metadata/validation issues truthfully.
- [x] M3-G04: Identical-content duplicates are skipped/reported across the target library and batch; different contents sharing metadata are not treated as exact duplicates. Users explicitly select the existing record when attaching a format; an occupied format is never overwritten automatically, including if it appears after preview.
- [x] M3-G05: Source file contents, names and locations remain unchanged; verified imports have correct metadata/format associations and existing library records remain intact except explicitly approved format additions. Attaching a format must not silently replace the existing record’s metadata.
- [x] M3-G06: Changes after preview trigger revalidation/review rather than silently executing a stale plan.
- [x] M3-G07: Partial failures/interruption preserve completed work, identify unfinished items, and permit retry without duplicate re-import. After restart, show completed/pending counts and Review / Retry / Discard Pending without automatic resumption. Retry revalidates and requires preview/confirmation. Unverified in-flight outcomes are reconciled before retry. Access contention respects the existing exclusive-access policy.
- [x] M3-G08: Imported books appear in the catalog and representative EPUB/MOBI/PDF files open correctly; M1/M2 regressions pass.
- [x] M3-G09: User desktop acceptance and remaining limitations are recorded; all required tasks pass before milestone/gate closure.

## Confirmed import behaviour

### Additional formats

Allow explicit attachment of an imported format to an existing Calibre book. Similar titles may suggest candidates but must not select a destination automatically. Show the chosen record and proposed format in preview. Never overwrite an existing format automatically; recheck immediately before writing so a change after preview cannot cause an overwrite. Same-format replacement has not been approved as an M3 feature; surface the collision and require a revised plan instead. Preserve the existing record's metadata when adding a format.

### Missing metadata

Allow import with fallbacks: missing title uses the source filename; missing author uses **Unknown**. Show the effective values and a missing-metadata warning in preview. Mark the resulting book as **Needs metadata review** so the user can find and correct it through M2. Do not treat fallback values as evidence that metadata is complete. For an attachment to an existing book, preserve that record's metadata rather than replacing it with the incoming file's fallback values.

The review marker survives restart in application-owned import journals. Metadata Completeness is calculated independently from saved fields and fallback provenance. Review Status remains Needs Metadata Review after edits until the user explicitly chooses Mark Reviewed; that action never changes completeness or book metadata. The editor shows both states and the catalog has a Needs Metadata Review filter. No hidden Calibre tags/custom columns are added.

### Interruption and restart

Stop taking new items when interruption is requested. Finish verifying the current item if possible, preserve completed imports and record unfinished items durably. On restart, show a summary such as **Previous import interrupted — Completed: 3; Pending: 7**, with **Review / Retry / Discard Pending**. Never resume writes automatically.

- **Review:** inspect completed, pending, failed and unverified results, including warnings and intended actions.
- **Retry:** reconcile any uncertain previous write, recheck source files, duplicates and destination state, then show the mandatory preview and request confirmation before execution.
- **Discard Pending:** abandon only unfinished work. Keep completed imports and source files; do not roll back successful copies or erase their outcomes.

A crash can occur after Calibre commits but before the result is recorded. Such an item must remain unverified until reconciled, not be blindly imported again or counted as a verified success. This operation-level recovery belongs to M3; the shared activity dashboard remains M5.

## Disposable validation fixture matrix

M3-02 must cover:

- Valid EPUB, MOBI and PDF; selected files, drag/drop, recursive folders and mixed supported/unsupported inputs.
- Identical contents under different names/locations, within a batch and already in the library; distinct contents with matching title/author.
- Explicit attachment of a missing format, occupied same-format destination and destination changes after preview.
- Missing title, missing author and both missing: preview fallbacks, persisted review marker and later M2 editing.
- Cancelled preview; unreadable/disappeared/changed sources; denied library access and injected partial write failures.
- Interruption between items and during verification; restart with completed/pending/unverified items; retry after a commit that was not journaled; Discard Pending preserving completed records.
- Source hashes/names/locations, existing record/format integrity, catalog refresh and representative viewer launches.

## Additional gate criteria

- [x] M3-G10: Missing title/author produce filename/Unknown fallbacks, visible preview warnings and a persistent Needs metadata review marker; imported items remain editable through M2.
- [x] M3-G11: Format attachment preserves existing metadata and formats; collisions never silently overwrite content. Retry and Discard Pending preserve completed results and original files.

Links: [implementation plan](implementation_plan_hub_bookinator.md), [release scope](first_release_scope.md), [completed M2](milestone_02_metadata_editing.md).

## Validation preparation checkpoint

Prepared a coherent 101-book baseline, three independent disposable working libraries and ten input fixtures, with SHA-256 manifests and unchanged original-library hashes. [Validation workspace and case plan](test_data/m3_validation/README.md) define import, attachment and recovery checks. Calibre attachment replacement defaults were inspected; runtime validation remains outstanding. Application code is unchanged. M3-02 is ACTIVE; M3-G remains OPEN / NOT RUN.

## M3-02 completion

All thirteen disposable capability/protocol checks passed after an initial parser finding was documented and independent EPUB validation added to the harness. Imports, no-overwrite attachments, partial-record repair and commit-before-ack reconciliation were verified; original-library/baseline/fixture hashes remained unchanged. See [results and adapter safeguards](test_data/m3_validation/RESULTS.md). Metadata extraction alone does not prove input validity, and failed imports can leave metadata-only records. M3-02 is DONE; M3-03–M3-07 and all M3-G application acceptance criteria remain open. Application code was not changed.

## M3-G implementation checkpoint

M3-03–M3-06 are implemented; 50 tests, 23 actual import/recovery checks and five 101-book hub checks pass. User confirmed independent completeness/review behaviour. Mandatory preview/import and imported three-format reader confirmations are now user-confirmed. M3-07 is DONE and M3-G PASSED/CLOSED based on implementation, automated evidence and desktop acceptance. See [acceptance evidence](test_data/m3_acceptance/README.md) and [technical design](technical_design_m3.md).
