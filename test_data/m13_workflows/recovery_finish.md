# M13 recovery follow-up — installed, gate open

Installed `0.1.0a1-db6a7fb8885f9bd9` after owner confirmed normal shutdown. Verified backup retained; 482 non-installer files unchanged, runtime inventory and package smoke passed. See installed_recovery_finish_candidate.json.

## M13-RECOVERY-DISCARD-01

Owner observed two fades and closure after Discard local edits, then the test tag returned when reopening recovery. The recovery editor was Quick Start Guide while the catalog search was M13 Final Acceptance.

Reproduced cause: discard reread metadata, then called the save-refresh callback. Catalog completion reread metadata again and rendered the filtered catalog. Its selection reconciliation treated the filtered-out editor book as a user selection change and called editor.done(0). This accounts for the two disabled/read phases and unexpected closure; the durable payload was never discarded.

Fix: local discard performs its read without an unnecessary save-refresh callback. Catalog completion preserves the editor even when its book is outside the current filter. Explicit selection changes retain their existing editor-review behavior. Feedback now says that the preserved recovery draft remains available in Activity and requires a separate discard action. Neither the library-write path nor durable-recovery retention rules changed.

## M13-RECOVERY-GUIDANCE-01

Resolved recovery records now say recovery is resolved and history is retained, matching the disabled recovery action. Pending records still explain how to open a draft and explicitly save it.

## Verification

The regression reproduced the hidden-editor failure before the fix. It now checks actual Discard button activation, one metadata read for discard, clean saved values, preserved payload bytes and unresolved recovery, a background refresh with the book filtered out, editor visibility, and normal closing on explicit selection. Guidance is checked against resolved-state action availability.

- 240 source tests passed: recovery_finish_full_regression.log.
- 92 installed tests plus clean install, smoke, reinstall and uninstall/data-retention checks passed: recovery_finish_package_verification.json.
- Package SHA-256: ccb031455b9f257182536838c6a262b05f3fa692bc649c0869f9c08f57d1840d.
- Isolated installed checks use host system packages, not a fresh OS. Owner KDE checks remain required.

## Remaining owner checks (original acceptance unchanged)

After M13-only backup and installation, reopen the preserved Quick Start Guide draft while the M13 Final Acceptance filter remains. Click Discard local edits: editor stays open, test tag disappears from this editor, saved values and preservation feedback appear. Close editor separately. Reopen recovery: preserved test tag returns. Close without saving, then explicitly discard only the reviewed M13 Local Discard Check preserved fixture in Activity. Verify resolved guidance and close scopes. Complete any outstanding paste/keyboard/layout checks and final normal restart/saved-data review. M13-G remains OPEN; accepted M12 and M11 remain unchanged.

Owner KDE verification: local discard keeps the editor open and removes the test tag. Subsequent screenshots show pending recovery and the reopened Quick Start Guide draft containing M13 Local Discard Check as unsaved. Durable-copy preservation passes. Separate fixture discard and resolved-guidance checks remain pending; M13-G stays open.

Owner confirmed separate preserved-test-draft discard passes. Screenshot shows no unresolved records even with Show dismissed enabled. Resolved guidance and final verification remain pending.

Resolved-guidance KDE check passed: owner screenshot confirms Pending No, Recovery required No, discarded outcome, retained history and correct next steps. Recovery and preserved-discard actions are disabled.

Path-entry owner check passed on db6a7fb8885f9bd9: pasted full file path and pressed Enter; approximately one second with visible activity indicator; duplicate-only preview correctly disables confirmation.

Final bulk layout checks passed on db6a7fb8885f9bd9: full screenshots show both tab panels and bottom controls fitting; owner confirms Tab/Shift+Tab focus movement and only Hub/Bulk Edit windows open.
