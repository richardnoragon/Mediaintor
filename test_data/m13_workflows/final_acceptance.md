# M13 final acceptance

M13-G CLOSED — accepted on 2026-09-24. Acceptance criteria unchanged.

Accepted build: `0.1.0a1-db6a7fb8885f9bd9`. All tracked M13 issues are resolved. Owner confirmed final restart: 104 books loaded, no recovery warning, Quick Start Guide selected. Recovery, import/path entry, operation feedback, workspace regression, both bulk-tab layouts and keyboard focus checks passed.

Validation: 240 source tests and 92 isolated installed tests; installation/data-retention checks passed. Final saved-data review verifies SQLite integrity, discarded test draft with no test tag saved, original recovery save retained, imported EPUB matching its source, saved reading position, completed original/revert journals unchanged, and named workspace retained. All 770 M12 baseline entries remain unchanged.

Evidence: [owner acceptance](desktop_acceptance.json), [saved-data review](final_saved_data_review.json), [package verification](recovery_finish_package_verification.json), [installation and backup](installed_recovery_finish_candidate.json), [recovery fixes](recovery_finish.md).

Subsequent owner-authorized promotion completed: M13 is Everyday; M12 is stopped and retained as Rollback. See [promotion](promotion.md). Isolated package tests use host system packages rather than a freshly installed OS; actual owner KDE checks provide the desktop evidence.
