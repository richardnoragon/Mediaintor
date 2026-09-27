# M13 implementation and installed verification

M13-02 complete; M13-03–M13-06 implemented and automated regression passed; M13-07 installed verification complete. M13-08 personal KDE acceptance pending. M13-G OPEN.

## Independent setup

[Setup](setup.json): quiet accepted M12 copy, verified backup/restore, 770 matching file/link entries, independent writable mounts, independent `Media-inator M13 Development` launcher. The initial copied baseline was M12 build `0.1.0a1-f59e8af9b043f304`.

## Implemented behavior

- Activity actions identify recovery drafts, pending imports/batches, local versus durable discard, hidden summaries/entries and history deletion. History group headers cannot launch record actions; explicit Close history/Close details controls. Resolved recovery does not advertise an available draft. Guidance distinguishes successful preservation from still-pending recovery.
- Author/tag controls identify their fields; metadata Save/Retry/Discard labels specify local intent. Workspace controls identify snapshots and separate startup choice from restore actions.
- New Bulk Edit and Batch History have dedicated preview/result areas. Operation-relevant settings are shown; catalog selection count explicitly includes hidden books. Preview targets are pinned across tabs/history and cannot be silently changed.
- Completed edit/revert selects its own journal. Background history refresh preserves selection; missing selected records do not fall back to another destructive target. Original/revert links navigate read-only without rewriting original outcomes. Partial/excluded linked reverts do not claim full reversal.
- Bulk/import/editor titles reflect operation phases and verified results; late Stop after full completion does not falsely claim interruption. Historical values are labeled Recorded values. Existing backend guards, journal formats and explicit confirmation remain intact.
- Packaged help matches the new controls and paste/browse picker workflow. No new picker, exports, NAS features, catalog operations or journal migrations.

## Verification

[Full source regression](implementation_regression.log): **230 tests passed**. New behavioral coverage includes separate tabs, preview target locking, selected executed batch, missing record safety, bidirectional read-only links, reverted result selection, interrupted/late-stop states and recovery action dispatch.

[Isolated package verification](package_verification.json): nine checks passed, including **82 installed targeted test executions**, install/reinstall/uninstall retained-data checks and no project/original library mounted. Host dependency isolation is not a fresh OS installation. Offscreen layout inspected using temporary sample data; personal KDE usability remains unclaimed.

[Installation](installed_candidate.json): build `0.1.0a1-911ac9451958810d`; archive `dist/m13-final/mediainator-0.1.0a1-ubuntu26.04-x86_64.tar.gz`; SHA-256 `cef447a41872dda3fd13f2da4f07a7717283809d3a1f6da1e34405fbe57ec531`. Verified pre-install backup; 469 non-installer files unchanged; runtime inventory and smoke passed. Earlier `dist/m13` is an uninstalled superseded package and must not be used for acceptance.

[Source protection](source_preservation.json): 769 M12 baseline file hashes unchanged after setup and installation. M11 not modified or mounted by M13 operations.

## Desktop fixtures and remaining work

[Fixtures](desktop_fixtures.json): Quick Start Guide unsaved tag `M13 Recovery Acceptance`, and `/data/import-sources/M13 Final Acceptance.epub` with enough text for page navigation. Created only in M13; library DB unchanged by preparation. Neither fixture constitutes user acceptance or a saved edit/import.

[KDE checklist](desktop_acceptance.md) and final persisted-result review remain. Direct file-picker typing has not been diagnosed as a defect; paste/browse instructions reflect observed behavior. Test label fit, focus and navigation on actual KDE before gate closure. M13 is not promoted; M12 remains everyday.
