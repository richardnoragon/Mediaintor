# M14 — Library Discovery & Metadata Productivity

Status: **M14-01–M14-08 COMPLETE; M14-G PASSED. Accepted development build: 0.1.0a1-9cf2b6503ae20a40.** M14 promoted to Everyday; M13 retained as stopped Rollback. M12 remains retained. M14-UI-01 remains explicitly deferred; M15 remains provisional.

## Goal and priority

Primary workflow: organize and find books quickly in a growing library. Secondary workflow: review and correct metadata efficiently. Prioritize stability, library management, metadata quality and maintainability.

## Approved behavior

1. Advanced filters cover reading status, missing metadata, series and tags. One visible Match all / Match any choice applies AND/OR across conditions. Repeated conditions are allowed; nested groups are deferred. Existing text search narrows either result. Unknown reading status remains distinct from explicitly known Unread; absent progress never implies Unread.
2. Saved searches store named filter definitions per library in Media-inator. Support create, rename, update and delete. Results recalculate after catalog refresh; deleting a saved search never affects books. Provide searchable tags and series browsers. Manually maintained virtual collections are deferred.
3. Metadata review includes missing title, missing author, known import fallback values, missing cover, import warnings and a manual Needs Review flag. Missing series is optional, defaults off, and its preference is remembered. Recalculate factual reasons after metadata changes. Mark reviewed clears the manual flag and acknowledges reviewable warnings but never conceals objectively missing fields.
4. A review table/workbench presents the review queue or search results, supports inspection and multiple-book selection, and dispatches existing bulk operations. Reuse tag, series and author operations with existing previews, confirmations, conflict handling and recovery. Additional editable fields and a major editor expansion are deferred.
5. Duplicate review is read-only and limited to books already in the current library. Separate identical-content results from potential similar-title/author matches. Compare exact file content within the same format. Start scans explicitly, show progress and support cancellation; ordinary discovery never waits for the scan. No automatic actions, merging, deletion or edition grouping. Files awaiting intake remain outside this feature and retain the existing import duplicate checks.

## Protected behavior

Preserve the reading workflow, library structure/storage model, proven backup/restore and safety mechanisms, and accepted Calibre compatibility requirements. Existing import behavior remains unchanged. Development and 10,000-book tests use independent disposable data, never shared writable Everyday data. No publication or promotion is implied by scope approval.

## Work plan

| Task | Status | Deliverable |
| --- | --- | --- |
| M14-01 technical design | COMPLETE — [design](technical_design_m14.md) | Catalog/index model, filter semantics, persisted search schema, review reason/acknowledgment model, duplicate matching and cancellation, UI/data migration design. |
| M14-02 isolated setup and scale fixture | COMPLETE — [fixture and baseline measurements](test_data/m14_discovery/baseline_report.md) | Independent development installation and deterministic approximately 10,000-book fixture; baseline correctness and performance measurements. |
| M14-03 discovery | COMPLETE — [evidence](test_data/m14_discovery/implementation.md) | AND/OR filters, searchable tags/series browsers and responsive result presentation. |
| M14-04 saved searches | COMPLETE — [evidence](test_data/m14_discovery/implementation.md) | Per-library lifecycle, refresh behavior and persistence checks. |
| M14-05 review productivity | COMPLETE — [evidence](test_data/m14_discovery/implementation.md) | Factual/manual review reasons, optional missing-series setting, review workbench and existing bulk-action integration. |
| M14-06 duplicate review | COMPLETE — [evidence](test_data/m14_discovery/implementation.md) | Explicit read-only scans, exact/similar categories, progress, cancellation and independent discovery responsiveness. |
| M14-07 regression and installed verification | COMPLETE — [evidence](test_data/m14_discovery/implementation.md) | Correctness, scale measurements, existing workflow protection and isolated package verification. |
| M14-08 owner KDE acceptance and gate review | COMPLETE — [checklist](test_data/m14_discovery/desktop_acceptance.md) | Repeatable desktop workflows, persisted-result checks and final evidence review. |

## M14-G acceptance

All criteria below pass with automated, installed-package and owner KDE evidence. See desktop_acceptance.json and its linked reports.

- [x] At approximately 10,000 books, common searches, filters, saved searches and review queue operations normally produce visible results within approximately one second on the acceptance machine after loading/indexing. Measure input-to-visible-results, document machine and workload, and report repeat-run timings; do not substitute backend-only timings.
- [x] AND/OR and text-search narrowing return correct results, including repeated conditions and Unknown versus Unread.
- [x] Saved-search lifecycle is per-library, survives restart and reflects metadata changes after refresh without modifying books.
- [x] Review membership reflects missing fields, import warnings and manual flags accurately. Acknowledgment cannot hide factual missing data. Missing-series preference defaults off and persists.
- [x] Users inspect and select multiple books in the workbench and safely apply existing bulk actions without opening each book individually.
- [x] Duplicate categories are correct on known fixture matches/nonmatches; scans show progress, permit cancellation and leave library contents unchanged. Search stays responsive during scans.
- [x] Initial loading/indexing and duplicate scans are excluded from the approximate one-second completion target; longer loading/scans remain responsive, show progress and support cancellation.
- [x] Reading, import, save/conflict/recovery, bulk/revert, backup/restore, workspace and compatibility regression checks pass.
- [x] Independent data, package verification and owner KDE checks demonstrate that M13 Everyday remains protected.

No calendar-duration gate. No change to historical M7's separately retained observation condition. Acceptance does not automatically promote M14.
