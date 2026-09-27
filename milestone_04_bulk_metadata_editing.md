# Milestone 04 — Bulk Metadata Editing

Status: **M4 COMPLETE; M4-G PASSED/CLOSED.** M4-01–M4-07 DONE. The user confirmed all desktop checklist items on 2026-09-21. M1–M3 remain complete for their agreed scopes. Existing G1/G2/G3/G4 technical-gate names are retained. See [acceptance evidence](test_data/m4_acceptance/README.md) and [technical design](technical_design_m4.md).

## Operations and boundary

Include adding tags, removing tags, setting series, clearing series and replacing a specified author across selected books. Preserve unrelated fields, author order and unordered-tag semantics. Retain comma validation for tags and Calibre-managed path reconciliation after author changes. No direct file-management commands. Each batch performs exactly one operation: Add Tags, Remove Tags, Set Series, Clear Series or Replace Author. Combined operations are deferred.

Author replacement uses exact matches only, replaces only the selected author, preserves co-authors and their order, and leaves a single occurrence when the replacement author already exists. No fuzzy author matching is permitted.

Bulk title, description, cover, ISBN and file-level metadata edits are excluded. Existing title/description/cover editing remains single-book. ISBN and file-level editing were deferred previously; this milestone does not silently introduce new single-book support for them.

M5 remains Hub Activity / Recovery. M4 must deliver its own necessary batch history, pending-work recovery and revert controls without waiting for M5's shared presentation.

## Selection and number assignment

Support individual selection, Select All Search Results and Clear Selection, with a persistent selected-book count. Selection survives paging, filtering and sorting until explicitly cleared. Preserve book identity independently of visible rows; filtered-out selections remain selected and must be visible in the batch review. Select All Search Results covers the entire result set, not only a displayed page. Ordinary selection is library-specific working state and clears when Book-inator closes, including application exit; it is not restored after restart. Durable pending batches remain recoverable independently of ordinary selection.

For Set Series, offer:

1. Keep existing numbers.
2. Assign a single number to all selected books.
3. Sequential numbering in an explicit user-reorderable list, with chosen start and increment.

Order is explicitly reviewed before preview; incidental catalog sorting must not silently change the sequence. Existing M2 rules accept finite non-negative numbers and ignore hidden Calibre indices when no series exists. Keep Existing Numbers preserves visible numbers associated with an active series; when absent, assign 1 and ignore hidden/orphaned Calibre indices. Sequential numbering accepts a finite start >= 0 and finite decimal increment > 0. Exclusions and conflicts leave the approved numbers of other books unchanged, even when gaps result; execution never renumbers them.

## Preview, conflicts and execution

Every multi-book write requires preview and explicit confirmation, including retry/revert plans. Display each affected book and current/proposed values. Allow per-book exclusion and return to operation settings; changed settings invalidate the old preview.

Revalidate before each book is changed. Process unaffected books and queue conflicted books for explicit review instead of stopping the entire batch. Report counts and outcomes, for example “198 updated; 2 require review.” Do not silently force local values or lose unrelated external changes. M2 field-level validation/read-back and partial-success rules still apply within a book.

Finish the current book if safely possible on interruption; keep verified successes and record unfinished/unverified work. After restart offer **Review Pending / Retry Pending / Discard Pending**, with no automatic resume. Retry revalidates and requires confirmation. Discard abandons only unfinished work, never reverses successful writes.

## Revert Batch

Revert is included in M4. Persist previous values and verified post-batch values per affected field, with stable library/book identity and per-field outcomes. Restore only fields actually changed successfully by the selected batch, not an entire stale record. An unverified original write must be reconciled before inclusion.

Revert has its own mandatory preview, per-book exclusions, conflict review and explicit confirmation. Compare current values against the stored post-batch values before restoration; if changed since the batch, require user review. Preserve unrelated metadata changes. Revert is not a silent rollback and must retain its own verified/failed/pending outcomes so interrupted reversion can be reviewed/retried safely. Historical records must distinguish original batch results from subsequent reversions.

Batch history is library-specific, survives restart and remains available indefinitely until explicitly deleted by the user. M4 imposes no automatic expiry or retention limit. Deleting a batch record requires confirmation with this warning:

> Deleting this batch history permanently removes the ability to revert this batch.

History deletion is distinct from Discard Pending and never reverses committed metadata.

## Implementation passes

| ID | Status | Deliverable |
| --- | --- | --- |
| M4-01 | DONE — decisions recorded | Operation semantics, six clarification decisions and acceptance fixture plan agreed |
| M4-02 | DONE — automated verification passed | Disposable validation of multi-book field writes, author path effects, per-book conflicts and original/revert recovery |
| M4-03 | DONE — automated verification passed | Stable multi-selection, count, operation controls and explicit sequence ordering |
| M4-04 | DONE — automated verification passed | Mandatory per-book preview/exclusion and confirmed execution with isolated conflicts |
| M4-05 | DONE — automated verification passed | Durable per-field before/after history; interruption/restart and pending review/retry/discard |
| M4-06 | DONE — automated verification passed | Reviewed batch revert with conflict checks, exclusions and recoverable partial outcomes |
| M4-07 | DONE — user desktop sign-off recorded | Catalog-scale/failure/revert acceptance, M1–M3 regressions and user desktop sign-off |

## M4-G acceptance gate

- [x] M4-G01: Operation/selection/numbering/revert edge cases agreed and supported write behaviour validated on disposable data.
- [x] M4-G02: Individual/all-results/clear selection and visible count work across filtering, sorting and paging; hidden selected books remain explicit in review; closing/reopening clears ordinary selection without losing pending batches.
- [x] M4-G03: Only agreed bulk operations are offered; unrelated metadata and format associations are preserved, including author-related path updates, exact author matching, co-author order and replacement deduplication; only one operation is permitted per batch.
- [x] M4-G04: All three number modes and explicit ordering produce the reviewed values, with absent-number default 1, ignored orphan indices, finite start >= 0, increment > 0 and preserved numbering gaps after exclusions/conflicts.
- [x] M4-G05: Every write/revert requires current/proposed preview and confirmation; exclusion and returning to settings are supported; cancellation before execution writes nothing.
- [x] M4-G06: Changed values isolate conflicted books for review while unaffected books continue; no blind overwrite or hidden loss of external changes.
- [x] M4-G07: Partial saves preserve verified successes; restart offers Review Pending / Retry Pending / Discard Pending with no automatic resume or duplicate application.
- [x] M4-G08: Durable original before/verified-after values support field-scoped revert; later external changes cause conflict review, and per-book exclusion is respected. Library-specific history survives restart without expiry; deletion requires the agreed warning and confirmation.
- [x] M4-G09: Interrupted/failed revert retains accurate outcomes and supports safe reviewed retry without undoing unrelated changes.
- [x] M4-G10: Representative-scale, invalid-input, missing-book, access-contention and recovery tests pass; M1–M3 regressions pass and user desktop acceptance is recorded.

## Disposable acceptance fixture plan

The six product clarifications are resolved. The following fixture coverage is implemented; executed evidence and remaining desktop checks are linked above:

- Authors: exact target with co-authors; replacement already present; near-match that must remain unchanged; verify order, identity, format hashes and Calibre-managed paths.
- Series: active number 0 or 2.5; absent series with a retained internal index; fixed number; sequential start 0 and increment 0.5; exclude/conflict in the middle and verify gaps remain. Reject negative/non-finite starts and non-positive/non-finite increments.
- Selection and preview: selections across pages/filters/sorts, hidden selections, all search results, per-library isolation, close/reopen reset, one-operation enforcement and cancellation without writes.
- Recovery: field-level partial success, interruption before/after commit, changed book after preview and restart without automatic resume; ordinary selection reset must not discard pending work.
- Revert/history: before/verified-after values, unrelated later edits, conflicting affected fields, per-book exclusion, interrupted revert, persistence and confirmed history deletion without changing book metadata.

M4-02 adapter checks and automated M4-03–M4-07 coverage passed: 64 unit/UI tests, 25 application checks and 8 injected-failure checks. Both disposable runs preserved original-library hashes. The current catalog is unpaginated; selection covers all matching rows and is independent of visibility/order. M4-G10 passed following user confirmation of all desktop checklist items on 2026-09-21. The existing Calibre/reader access policy remains unchanged.

Links: [implementation plan](implementation_plan_hub_bookinator.md), [release scope](first_release_scope.md), [completed M3](milestone_03_safe_ebook_imports.md).
