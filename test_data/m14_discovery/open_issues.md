# Promotion status: M14 Everyday

M14 promoted after owner authorization and verified backups. M13 is retained as stopped Rollback. See [promotion evidence](promotion.md). Earlier no-promotion statements below describe acceptance history.

# Current open work after M14 implementation

**Current status: M14-G PASSED; M14-01–M14-08 complete. M14-DUP-01 and M14-DUP-02 resolved and owner accepted. Only M14-UI-01 remains open within M14 follow-up work, explicitly deferred by the owner. M13 remains Everyday; M14 not promoted. Historical entries below are retained for traceability.**

- **M14-08 / M14-G:** owner desktop acceptance in progress. Correct build and usable workbench confirmed. Saved-search lifecycle, keyboard/sizing, review/bulk workflow, scale/duplicate interaction and final restart remain to be confirmed; final saved-state readback follows. [Live record](desktop_acceptance.json).
- **M7 historical observation condition:** planned tests previously passed and gate conditionally accepted; seven-day normal-use observation remains nonblocking and has not been completed or waived. No elapsed-day evidence is inferred from this development session.
- **M15:** provisional future work, not an approved implementation milestone. It is not silently included in M14.

M12 and M13 gates are closed. The previously reported picker, import-feedback, workspace reload, local-discard/editor closing and recovery-guidance issues were resolved and accepted in M13; their tests remain passing in M14. M13 is still Everyday and M12 is still Rollback. M14 has not been promoted or published.

No known failing automated M14 check remains. 257 source tests, 109 installed tests and the 10,000-book correctness/performance checks passed. [Evidence](implementation.md).

## M14-UI-01 — ambiguous bulk-editor close controls

OPEN; owner explicitly requests addressing later. During KDE acceptance, Close batch preview was confused with Close bulk editor. The former cleared completed revert results and displayed Preview cancelled while leaving the window open; the latter successfully closed it. Saved revert results were verified intact. Revisit labels, placement and completed-result feedback so leaving a result view cannot be mistaken for closing the editor or cancelling completed work. Do not classify this as user error or mark it fixed.

Duplicate desktop check remains pending: owner screenshot shows “Catalog refreshed — previous evidence is stale; start another scan.” This is invalidated evidence, not a successful zero-duplicate result. Request a fresh scan; investigate if invalidation recurs without an intervening catalog change.

## M14-DUP-01 — duplicate results cleared by unchanged periodic refresh

RESOLVED in build 0.1.0a1-e9f972a567136e89; owner stability retest passed. Reproduced in owner desktop acceptance: completed results disappeared and the catalog-refreshed warning replaced them. Root cause: the 30-second catalog refresh unconditionally invalidated and emptied duplicate results.

Tested fix compares the refreshed catalog and coherent source-file inventory (size, modification time, inode, change time) with the scan baseline. Unchanged refreshes preserve results. Genuine or unverifiable changes mark results stale, retain visible evidence and require explicit rescan. In-flight progress cannot overwrite the stale warning. No scan result is advertised current merely by ignoring refreshes.

257 source and 109 installed tests pass. Installed-candidate real-fixture scan survived two independent unchanged 10,000-book snapshots, retaining 100 exact and 240 potential groups with 0 errors. The raw desktop fixture has no synthetic missing-title provenance overlay; independent raw_duplicate_oracle.json explains the difference from the 180-group overlay benchmark. Fix ready for M14-only backup/install once owner closes M14 normally. Deferred M14-UI-01 is unchanged.

M14-DUP-01 installation update: build 0.1.0a1-e9f972a567136e89 installed after owner-confirmed normal shutdown. Backup and inventory verified; 488 retained data files unchanged. Owner desktop retest remains pending.

M14-DUP-01 owner retest PASS: expected 100 exact / 240 potential groups, 0 errors, no books changed; owner confirms results stayed visible for more than one minute. This resolves the refresh defect. M14-G remains OPEN for remaining desktop checks; M14-UI-01 remains deferred and OPEN.

## M14-DUP-02 — scan blocked by refresh leaves persistent waiting feedback

OPEN. After cancellation, owner clicked Scan library during a library load. The dialog displayed “Wait for the current library load to finish.” for more than one minute, with no scan activity visible. Source inspection confirms scan() returns without queuing work when loader.active, and unchanged catalog refresh does not replace that waiting message. The message alone does not prove the loader is still active. Restart-after-cancel acceptance remains pending. Fix should clearly report that no scan started and restore actionable feedback when loading finishes; preserve existing scan results and stale-evidence safety.

Owner update: explicit retry after cancellation completes normally with 100 exact groups, 240 potential title/author groups, 0 errors and no books changed. Restart-after-cancellation PASS. M14-DUP-02 waiting-message feedback remains OPEN; successful retry does not fix it.

M14-DUP-02 fix prepared: 0.1.0a1-9cf2b6503ae20a40. Library-loading notice is separate from evidence status; Scan library is disabled during loading and re-enabled afterwards. Previous cancellation/completion/staleness evidence is retained, and no scan is silently queued. All 258 source and 110 installed regression tests pass. Package verification and installer are ready; installation requires normal M14 shutdown for a consistent backup. Owner retest remains pending.

M14-DUP-02 installation: build 0.1.0a1-9cf2b6503ae20a40 installed after owner-confirmed normal shutdown. Backup, package integrity and smoke check passed; all 490 retained data files unchanged. M14 relaunched; owner desktop retest pending. M13 Everyday unchanged; M14-G remains OPEN.

M14-DUP-02 owner retest PASS on 0.1.0a1-9cf2b6503ae20a40. Owner explicitly confirms the new Library loading — no new scan has started… notice appears briefly, not the old waiting text, and normal controls return after the quick refresh. Waiting-feedback defect RESOLVED. M14-G remains OPEN pending remaining scan interaction evidence.

M15 follow-up: M14-UI-01 resolved in accepted M15 Development build 0.1.0a1-47d071de892ca535. Owner confirmed Return to batch history retains completed-result wording and Close bulk editor closes in one click while Hub stays open. M14 Everyday itself remains frozen; fix is available in M15, not retroactively installed into M14.

Owner decision: the historical seven-day observation is obsolete and retired, not an outstanding condition. This supersedes earlier pending-observation statements; it does not claim the trial was performed.
