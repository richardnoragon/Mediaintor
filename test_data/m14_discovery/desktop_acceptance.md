# Promotion status: M14 Everyday

M14 promoted after owner authorization and verified backups. M13 is retained as stopped Rollback. See [promotion evidence](promotion.md). Earlier no-promotion statements below describe acceptance history.

# M14-08 — owner KDE acceptance PASSED

**Final status: M14-G PASSED on build 0.1.0a1-9cf2b6503ae20a40.** All required checks in desktop_acceptance.json pass. M13 remains Everyday; no promotion. M14-UI-01 remains explicitly deferred. Earlier entries below preserve the acceptance history.

Current build: **0.1.0a1-e9f972a567136e89** (earlier workflow checks used 63a8595f440ca5ac). Automated checks passed. Owner has confirmed the correct build and usable Find / review table; keyboard and subsequent checks remain pending. M14-G remains OPEN. Use only **Media-inator M14 Development**. M13 Everyday is unchanged.

1. **Opening and keyboard access.** Confirm the title/build, the copied 104-book catalog and Find / review table. Check ordinary window sizing and Tab/Shift+Tab through the new controls.
2. **Discovery and saved searches.** Add known tag/series conditions through the searchable value box, switch Match all/any and check narrowing. Save a named search, modify it without updating, then explicitly Update/Rename. Close/reopen M14 and confirm its definition persists. Delete the test search and confirm the book count remains unchanged.
3. **Review workbench.** Flag a complete copied book Needs Review, filter to the queue, then Mark reviewed. It should leave if no factual/warning reasons remain. A book missing cover/author/title must remain after Mark reviewed, with its reason visible. Toggle missing-series inclusion and verify the setting persists. Select two books, hide one with filters, and verify the selected count still includes it.
4. **Bulk integration.** On the copied 104-book library only, hand selected books to Bulk edit selected. Confirm the preview targets match, add a unique temporary tag using existing preview/confirm controls, reload and verify. Remove that tag using the same guarded workflow and verify saved values. Do not use the read-only scale fixture for writes.
5. **Scale browsing and duplicate review.** Choose existing library `/data/m14-scale` (10,000 books; read-only fixture). Observe loading progress and cancellation/retry. After loading, search `M14 Fixture`, use tags `Tag 03` / `Group 3`, and open review/saved searches; common results should feel approximately one second or faster. Synthetic reading/manual-warning overlays used by automated tests are not installed here: Unknown is expected, and queue counts can differ. Start Duplicates explicitly, continue searching, cancel/restart, and check separate exact/potential groups and clear completion status. No merging/deletion controls should exist.
6. **Final restart.** Return to `/data/library` (M14's copied 104-book library), close normally and reopen M14. Confirm intended selection/view, retained saved searches/preferences, and no unintended pending recovery. Report any slowdown, disappearing editor, focus issue, clipped controls or unclear feedback.

After owner confirmation, recheck persisted state and review evidence before closing M14-G. Promotion is a separate owner decision. M7’s prior nonblocking observation condition remains unchanged.

Owner update: saved-search update, restore and persistence after normal Hub restart PASS. Live text search PASS. Rename/delete and remaining desktop workflows are still pending. M14-G remains OPEN.

Owner update: manual flag → review queue inclusion → Mark reviewed removes complete Quick Start Guide from queue PASS. Factual missing-field retention remains pending.

Owner update: factual missing-field retention PASS. Mark reviewed on M13 Final Acceptance removes its import warning while Missing title remains and the book stays in the queue.

Owner update: optional missing-series queue inclusion and preference persistence after normal Hub restart PASS. Queue expands from 3 to 100 books when enabled; the preference remains checked after restart.

Owner update: multiple/hidden selection PASS. A Christmas Carol remains visible after filtering; both it and A Doll’s House remain selected, with 2 selected explicitly reported. Review-workbench checks now pass; bulk handoff/apply verification remains pending.

Owner update: workbench bulk handoff, apply and guarded revert PASS. Both selected books (including hidden selection) were updated then restored. Read-only saved-data verification confirms exact original tags, no remaining M14 Bulk Acceptance associations and 104 books retained; see bulk_revert_readback.json.

Owner update: fresh explicit duplicate scan on 104-book M14 library PASS: 0 exact groups, 0 potential title/author groups, 0 errors; clear completion message. Previous refresh invalidation did not recur on the fresh scan. Large-fixture desktop checks remain pending.

Owner update: 10,000-book loading with activity indication, specific-title live search (one result within roughly one second), Tag 03 AND Group 3 (35 results), and OR (1,627 results, quick response) PASS.

Duplicate-refresh retest build: **0.1.0a1-e9f972a567136e89**, installed with verified backup and 488 retained data files unchanged. Scan the 10,000-book fixture and leave results visible for at least 60 seconds to cover an ordinary periodic refresh. M14-G remains open.

Owner update: M14-DUP-01 retest PASS. Screenshot confirms 100 identical-content groups, 240 potential title/author groups, 0 errors and no books changed. Owner explicitly confirms results remained visible for more than one minute. Cancellation and remaining desktop checks are still pending; M14-G remains OPEN.

Owner update: 10,000-book scan cancellation PASS. Screenshot reports Cancelled — incomplete, 0 exact groups, 240 potential title/author groups, 0 errors, no books changed. This confirms cancellation, not a complete exact-duplicate result. Visible progress and concurrent discovery interaction remain to be confirmed. M14-G remains OPEN.

Owner update: explicit retry after cancellation completes normally with 100 exact groups, 240 potential title/author groups, 0 errors and no books changed. Restart-after-cancellation PASS. M14-DUP-02 waiting-message feedback remains OPEN; successful retry does not fix it.

Owner update: saved-search creation and rename on the 10,000-book fixture PASS. M14 Scale Renamed retains query M14 Fixture 09999 and the correct single result. Delete-without-changing-books remains pending.

Owner update: saved-search deletion without changing books PASS. After deleting M14 Scale Renamed and clearing the retained text filter, the screenshot shows Unsaved search and 10000 of 10000 books. Saved-search lifecycle checks now PASS; M14-G remains OPEN.

Owner update: keyboard navigation PASS. Owner confirms Tab and Shift+Tab move through buttons and fields. Window-sizing check remains pending.

Owner update: window sizing PASS. Enlarged and reduced workbench screenshots and owner confirmation show accessible search fields, bottom buttons and scrollable table. Keyboard/sizing checks now PASS.

Owner update: 10,000-book review-queue responsiveness PASS. Owner reports almost instantaneous update, much quicker than one second. Screenshot shows 2683 qualifying books, missing-series preference off, and Missing cover / Missing author reasons. This is observed desktop timing, not an instrumented measurement.

Owner update: return from scale fixture to /data/library PASS. Screenshot shows 104 of 104 books and 0 selected; owner reports less than one second to load. Final normal restart remains pending.

Owner update: normal restart PASS on build e9f972a567136e89. Owner confirms 104 of 104 books restored without recovery warnings; screenshot shows Workspace restored. M14-G remains OPEN for M14-DUP-02, remaining scan interaction evidence and final persisted-state readback.

M14-DUP-02 installation: build 0.1.0a1-9cf2b6503ae20a40 installed after owner-confirmed normal shutdown. Backup, package integrity and smoke check passed; all 490 retained data files unchanged. M14 relaunched; owner desktop retest pending. M13 Everyday unchanged; M14-G remains OPEN.

M14-DUP-02 owner retest PASS on 0.1.0a1-9cf2b6503ae20a40. Owner explicitly confirms the new Library loading — no new scan has started… notice appears briefly, not the old waiting text, and normal controls return after the quick refresh. Waiting-feedback defect RESOLVED. M14-G remains OPEN pending remaining scan interaction evidence.

Owner update: post-fix regular-library duplicate scan PASS on 9cf2b6503ae20a40: 0 exact groups, 0 potential groups, 0 errors, no books changed.

Owner update: scan/search interaction PASS by owner observation of responsive windows. Screenshot on 9cf2b6503ae20a40 shows correct single result for M14 Fixture 09999 and completed scan (100 exact / 240 potential / 0 errors; no books changed). The screenshot records completion rather than proving simultaneous timing.
Final owner evidence: scan activity bar visible; responsive scan/search interaction; returned to regular 104-book library on final build. Source regression: 258 passed; isolated installed regression: 110 passed. Verified backup/install preserved 490 files. Saved-state readback found 104 books, no temporary tag associations and all 12 retained bulk items complete. M14-08 and M14-G complete.
