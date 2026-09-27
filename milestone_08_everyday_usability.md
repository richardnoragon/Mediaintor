# M8 — Book-inator Everyday Usability

Status: **M8 COMPLETE; M8-G PASSED / CLOSED.** All M8-01–M8-07 tasks complete following 185 regression tests, 16 disposable probes, eight installed checks and owner-installed KDE acceptance. [Final gate review](test_data/m8_usability/gate_review.md). RC1 unchanged; no publication. Earlier checkpoint notes below are historical.

## Objective and scope

Improve everyday Book-inator use in this order:

1. Viewer focus reliability: investigate and remedy the initial-keypress problem before navigation works. Reproduce focus, rendering and loading behavior separately; do not assume the cause or introduce unverified synthetic keypresses. This schedules TODO-VIEWER-01.
2. Richer searching and filtering across the catalog, including author, series, reading status and tags. Approved fields, matching and persistence are specified below.
3. Reading-progress integration: display and preserve position/progress consistently. Validate Calibre capabilities on disposable copies before choosing the adapter. Retain Unknown when no reliable reading status is available; do not invent progress or assume positions translate between formats.

Reading-progress integration is approved work even where new adapter or UI behavior is required. Unrelated new features, additional modules, synchronization, external testers and publication remain outside this milestone.

## RC1 protection

Use a separate M8 development installation and copied library, with distinct configuration, application data, recovery history, launcher, container identity and writable mounts. Do not change the RC1 package, image, launcher, configuration, observation data or working library. Verify separation before any write tests; record RC1 artifact identity before and after M8 validation. Do not rebuild or retag RC1 as M8.

RC1 observation continues independently. M7-G remains conditionally accepted with its observation condition outstanding; M8 work does not wait for elapsed observation time.

## Work plan

| Task | Status | Deliverable |
| --- | --- | --- |
| M8-01 | COMPLETE | Approved behavior below; source capabilities and status mapping remain technical verification in M8-05. |
| M8-02 | COMPLETE | Prepare separate installation, copied library and fixtures; verify mounts, paths, launchers and RC1 protection. |
| M8-03 | COMPLETE | Reproduce viewer-keypress issue on KDE; implement verified remedy and desktop regression checks. |
| M8-04 | COMPLETE | Implement approved search/filter rules with grid/list consistency and existing selection behavior preserved. |
| M8-05 | COMPLETE | Validate progress sources, persistence and resume behavior on disposable EPUB/MOBI/PDF files; document limitations. |
| M8-06 | COMPLETE | Implement approved progress integration and test restart, reader exit, failures and existing access guards. |
| M8-07 | COMPLETE | Run combined workflow/regression checks, owner desktop acceptance and documentation review; assess M8-G. |

## Approved behavior

### Search and filtering

- Free-text search covers Title, Author and Series.
- Independent multi-select filters cover Tags, Format and Reading Status.
- Match AND across active categories (including text search), OR among selected values within each filter category. An empty category imposes no restriction.
- Grid and list views use the same matching rules. Preserve explicit book selection across filter changes, as agreed in M4.

### Persistence and Clear All

- Restore the last search text, all active filters and filter-panel state (if present) at startup.
- Provide a prominent Clear All action that clears text and every filter, immediately updates the catalog view and persists the cleared state.
- Clear All clears search/filter criteria, not the separately managed selected-book set.

### Progress and resume

- Read progress from Calibre metadata when available; verify the actual supported storage/interface on disposable copies before implementing the adapter.
- Refresh progress after the reader closes and protected library access is safe.
- Display percentage when known and Unknown when unavailable. Missing data must not be presented as zero or as a confirmed unread status.
- Preserve independent saved positions per format and resume the selected format at its own saved location; never transfer positions between formats.
- EPUB, MOBI and PDF remain the supported M8 format set. The owner's PDF/CBZ example expresses format independence, not an expansion into comic support.
- Manual progress/status editing, advanced synchronization and multi-device conflict handling are deferred beyond M8.

### Approved per-format and book-card display

- Show **Saved position available** for a format with a valid, confirmed resume point, independently of percentage or status availability.
- Show **Progress: Unknown** when no reliable percentage exists and **Status: Unknown** when no reliable reading status exists. A saved position alone must not imply Reading, Currently reading, Unread or Completed.
- The book card summarizes the **most recently read format**, clearly labelling that format. Use reliable last-read evidence, not mere catalog selection or a format-button click; show last-read date only when known.
- Other formats and their independent saved positions remain accessible in the details panel. Never merge positions or use the highest percentage across formats as the summary.
- Missing or ambiguous last-read timestamps must not produce an invented latest format; deterministic handling remains part of adapter design and verification.

### Acceptance examples

1. Search `asimov`, Tags `Sci-Fi` or `Classic`, Format `EPUB` or `PDF`, Status `Reading`: include only books matching the text and at least one value from each active filter category.
2. A Series-only text match is discoverable. The same criteria produce the same books in grid and list views; unmatched criteria show an empty result without losing the catalog.
3. Restart restores text, filters and filter-panel state. Clear All immediately restores the unfiltered view; restart retains cleared criteria.
4. Read and close an EPUB, reopen it and verify its saved position. Read a different format of the same book and verify both positions remain independent across restart.
5. Verified progress updates after reader closure; unavailable progress shows Unknown. Protected-access deferral retains the current catalog and never fabricates a fresh progress value.
6. Existing selection, metadata editing, imports, bulk editing/revert and recovery remain functional with active filters.
7. A valid saved position without percentage/status displays Saved position available, Progress: Unknown and Status: Unknown simultaneously.
8. Given different reliable last-read timestamps for EPUB and PDF, the card summarizes and labels the later format; details still expose both independent positions. Selecting another format in the catalog alone must not change the summary.
9. Missing/invalid positions or timestamps do not fabricate resume availability, percentage, reading status or most-recent activity.

### Remaining technical verification

M8-05 must establish available Calibre position/percentage/status sources, supported-format coverage, refresh behavior and failures. Record any mismatch with the approved requirements before choosing a workaround. The owner has approved the most-recently-read-format summary and Unknown fallback for unavailable status/percentage. Verify timestamp selection, path changes, missing/corrupt records and any reliable reading-status mapping; seek clarification if supported sources leave conflicting semantics. Do not invent completed-status thresholds or equate missing progress with unread. These capability checks are not yet claimed as passed.

## M8-G acceptance

- [x] Approved behavior has explicit test cases and expected outcomes.
- [x] M8 installation/data are isolated; RC1 artifacts and protected locations remain unchanged by M8.
- [x] Viewer opens readable and accepts navigation without a preparatory keypress in the agreed desktop scenarios.
- [x] Search/filter examples pass in grid and list views, including combined filters, empty results, clearing and selection behavior.
- [x] Approved progress display/preservation/resume cases pass for supported formats; unavailable values and limitations are accurately shown.
- [x] Browse, metadata editing, imports, bulk edits/revert, Activity/recovery, restart and compatibility/access-guard regressions pass.
- [x] No unresolved blocking defects; limitations and deferred findings have explicit dispositions.
- [x] Owner desktop acceptance and final evidence review are recorded.

There is **no minimum testing duration**. Work may proceed when required tests and agreed acceptance criteria pass. Any unmet criterion requires explicit disposition; it is not silently removed. Publication remains a separate decision.

Technical evidence: [timestamp selection, rename and malformed-record verification](test_data/m8_usability/progress_edge_review.md). Library annotations are not a verified last-read fallback; viewer path-key reconciliation requires dedicated handling.

Latest regression review: [M8 search acceptance and limitations](test_data/m8_usability/search_acceptance.md). No minimum-duration requirement. RC1 and active M8 installation remain unchanged.

Installed candidate: **0.1.0a1-184039712b870efd**, eight isolated checks passed, including restored filters and restart persistence. [Evidence](test_data/m8_usability/installed_verification.json). This is automated installed-package verification, not personal KDE sign-off; M8-G remains open.
