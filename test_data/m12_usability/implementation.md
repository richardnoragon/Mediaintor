# M12 isolated setup and initial implementation

**M12-02 complete. M12-03–M12-06 implemented in source with automated verification; package and KDE acceptance remain M12-07/M12-08. M12-G OPEN.**

## Isolated setup

[Setup report](setup.json): verified quiet M11 backup, independent restore into `../Mediaintor-M12-Test/`, distinct `mediainator-m12` Compose project and **Media-inator M12 Test** launcher. Baseline installed inventory and offscreen startup passed; copied data matched source. M11 source file hashes rechecked after development: unchanged.

The M12 launcher currently uses the copied accepted build `0.1.0a1-a3a4679f39f4c255`. **New M12 source changes are not installed yet.** Compose is configured to supply `MEDIAINATOR_INSTALLATION_LABEL=M12 Test` once the new candidate supports it. No M11 or RC1 upgrade, promotion or publication.

## Source changes

- Recovery handoff defers refresh while reviewing/closing the previous editor and reading the new editor's metadata. The replacement remains hidden until a draft is reconstructed; failed reads retain the payload and expose the actual reason rather than leaving an empty editor visible.
- Review can await an existing catalog refresh with a visible status and bounded wait. Duplicate waiting requests are rejected. Module/library changes and close cancel pending intent; stale completion is ignored. Payload revision is revalidated after reads. Explicit Save remains mandatory.
- Save feedback identifies the verified book and fields, including no-op, incomplete and unverified outcomes. Successful field writes remain committed.
- Revert preview and execution have distinct text and a Confirm revert button. Completed/failed/pending counts are exclusive; conflicts/unverified are pending subsets, exclusions/discards separate. Journal outcomes are inspected even after failed worker responses. No-change cancellation is claimed only without write evidence.
- Deployment label and actual manifest build appear in the window/About; invalid labels fall back safely. Removed obsolete M6-open About text. Installation identity stays outside user/workspace data.
- Offline help and troubleshooting updated. No library schema change or book/file deletion feature.

## Verification

**220 tests passed**: [full regression log](implementation_regression.log). The suite includes the isolated [real Qt handoff scenario](../../tests/check_m12_recovery_handoff.py): first-click recovery, dirty-draft Cancel, active refresh completion, duplicate review, cancellation/stale callback and explicit metadata-access failure. Payload stays unchanged; recovery remains unresolved until Save. [Scenario output](handoff_regression.log).

Additional tests cover mixed revert counts, cancellation with uncertain writes, preview versus completion, field-specific partial-save feedback and valid/invalid deployment labels. Existing editor, recovery, import, bulk, workspace and diagnostic tests pass.

The historical M12-01 reproduction script documents the old failure and is expected not to reproduce it against fixed source. Its replacement success regression is included in the test suite.

## Next

M12-07: review new implementation, build and verify a separate installed M12 candidate, including target runtime and deployment identity. M12-08: personal KDE acceptance with explicit readback of saved evidence. Automated source tests do not establish real desktop/Calibre acceptance. M11 remains the unchanged reference; promotion remains a separate decision.
