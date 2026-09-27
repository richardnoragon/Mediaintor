# Promotion status: M14 Everyday

M14 promoted after owner authorization and verified backups. M13 is retained as stopped Rollback. See [promotion evidence](promotion.md). Earlier no-promotion statements below describe acceptance history.

# M14 implementation and automated verification

Accepted development build: **0.1.0a1-9cf2b6503ae20a40**. M14-01–M14-08 complete; M14-G PASSED. M13 stays Everyday. No promotion or publication.

## Delivered

- AND/OR condition filters, Unicode-normalized search, searchable tag/series choices, visible inherited catalog narrowing, and explicit format narrowing.
- Per-library saved-search create/update/rename/delete; versioned atomic state, identity checks, revision conflicts, restart persistence and refreshed results.
- Virtual catalog grid/table and review workbench, bounded cover cache, sorting, shared selected UUIDs for existing bulk actions, hidden-selection counts.
- Factual/manual/warning review reasons, missing-series preference, and shared editor/workbench acknowledgment. Factual missing metadata remains visible after review.
- Read-only existing-library duplicate scans: same-format byte hashes and conservative normalized title/author matches, explicit start/progress/cancel, uncertain/error states, refresh invalidation and close/library-switch cancellation.
- Cancellable library preparation with visible stage progress.

## Verification

- 255 source tests pass: [full log](current_regression.log). Fifteen new M14 rule/UI tests cover behavior and failure paths.
- 107 installed tests plus clean install, same-package reinstall, uninstall/reinstall retained-data checks, desktop validation and package smoke: [package report](package_verification.json). Project checkout and Everyday library were not mounted.
- Actual pinned Calibre 9.2.1/Qt 6.10.2 installed package used for scale verification. [Raw installed measurements](installed_performance.json), [output](installed_scale_output.log), [fixture oracle](scale_verification.json).
- 10,000 books; all six catalog and five advanced result sets matched the independent oracle across three warmups and twenty timed samples. Exact duplicate groups: 100; similar groups: 180. Searching continued during scanning.
- [Installed backup/readback](installed_candidate.json): 482 retained data files verified. [M13 isolation check](post_install_isolation.json): all 966 hashed files match the retained pre-development backup. New M14 files live only in its installation and project evidence.

## Performance

Same acceptance machine, Qt offscreen, actual query/render paths including event processing and repaint. This is not compositor or physical keyboard-to-screen KDE acceptance. Warm runs, no forced OS page-cache purge. Reading states and workflow flags in advanced tests are explicitly synthetic oracle overlays; the real library remains unchanged. Initial load and hashing are outside the one-second discovery completion target.

| Operation | Median ms | p95 ms | Maximum ms |
| --- | ---: | ---: | ---: |
| Catalog: all (10000 books) | 23.78 | 25.80 | 26.28 |
| Catalog: generated (9632 books) | 22.05 | 23.79 | 24.05 |
| Catalog: specific (1 books) | 4.73 | 5.31 | 5.84 |
| Catalog: tag (247 books) | 8.42 | 9.12 | 11.30 |
| Catalog: tag_any (494 books) | 7.85 | 8.81 | 9.43 |
| Catalog: unknown (10000 books) | 25.51 | 26.16 | 26.99 |
| unread_series_cover | 3.09 | 3.18 | 3.20 |
| missing_author_or_title | 3.08 | 3.17 | 3.19 |
| tags_all | 2.96 | 3.21 | 3.42 |
| tags_any | 3.14 | 3.37 | 3.41 |
| review | 4.43 | 4.70 | 5.20 |
| text_input_including_debounce | 149.77 | 163.97 | 164.75 |
| saved_search_apply | 4.04 | 4.57 | 6.02 |
| Search during duplicate scan | 4.31 | 5.08 | 17.13 |

All-books baseline median: 1.863 s; installed M14 median: 0.024 s. Peak RSS: 157.2 MiB (baseline 780.2 MiB). Snapshot: 3.011 s; Calibre listing: 0.543 s; parsing: 0.520 s; catalog loaded-to-paint: 0.156 s; workbench creation: 0.056 s.

## Resolved during verification

- Fixture oracle corrected: free samples 63 and 78 have Unknown authors and qualify as missing-author. Counts are 505 for missing author OR title and 3,092 for the default synthetic review queue. Book files were not changed. The generator now reproduces that classification.
- Shared editor review service now translates unavailable SQLite identity into a recoverable review error.
- Cover cache is invalidated on catalog replacement; changed covers cannot survive refresh from the previous generation.
- Legacy loader test double updated for progress/cancel; the subsequent complete suite passes.
- Advanced scale cases explicitly clear inherited Unknown catalog narrowing. Separate UI tests verify inherited narrowing is visible, persistent and clearable.

## Remaining work

Owner KDE acceptance only for M14: [desktop checklist](desktop_acceptance.md). Do not infer those results from offscreen tests. M14-G stays open pending owner evidence and final review. M7’s historical normal-use observation remains a separate nonblocking condition, not waived. M15 remains provisional, not an approved implementation task.

Final gate review: all required owner checks pass (desktop_acceptance.json). Final build has 258 passing source tests and 110 passing installed tests; verified install preserves 490 retained data files. Both duplicate-refresh defects resolved and owner accepted. Historical performance measurements below retain their original build attribution. M14-UI-01 remains explicitly deferred; M13 remains Everyday. No promotion.
