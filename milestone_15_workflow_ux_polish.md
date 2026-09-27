**Current deployment: M15 Everyday; M14 stopped Rollback. Promotion complete; see test_data/m15_polish/promotion.json. Historical development-status statements below are superseded. The obsolete seven-day observation is retired.**

# M15 — Workflow & UX Polish

**M15-G PASSED.** Accepted development build: **0.1.0a1-47d071de892ca535**. Implementation and focused owner acceptance complete; M14 remains Everyday. M15 has not been promoted. M16 is Hub Integration and is not included here.

Priority: bulk-editor clarity; search versus filter clarity; progress/status; metadata review feedback; evidence-based small usability improvements; packaging gaps if demonstrated.

## Design and acceptance

- Keep existing storage, query semantics, preview/confirmation, conflicts, recovery and Calibre compatibility.
- Distinguish returning from batch results from closing the entire editor. Completed work must never be described as cancelled when leaving its results.
- Persistently label saved searches, text search and filter values. Explain that filters apply after Add condition; prevent accidental duplicate conditions. Preserve AND/OR behavior.
- Show accurate visible/hidden selection counts and explain review acknowledgment without hiding missing metadata.
- Retain M14's tested loading/scan activity and cancellation feedback; avoid speculative new progress systems.
- Verify package installation and retained state using the established isolated checks. Existing packaging is already complete; add changes only for demonstrated gaps.
- Use isolated M15 data restored from verified M14 pre-promotion backup. No live M14 writes or automatic promotion.
- Gate requires regressions, installed-package verification and focused owner desktop checks. Seven-day observation remains outstanding; include actual findings when available.

## Final evidence

260 source tests and 115 isolated installed tests pass. Installation preserved 490 retained files. Owner desktop checks pass for labels, duplicate-filter feedback, hidden selection counts, review actions, completed-result dismissal, editor close, resizing and restart. Read-only verification confirms 104 books, no manual test flags, and all retained bulk items complete. See test_data/m15_polish/acceptance.json. M14-UI-01 is resolved in this M15 build; the frozen M14 Everyday build is unchanged. Seven-day observation remains outstanding and has not been waived.

Owner decision: the historical seven-day observation is obsolete and retired, not an outstanding condition. This supersedes earlier pending-observation statements; it does not claim the trial was performed.
