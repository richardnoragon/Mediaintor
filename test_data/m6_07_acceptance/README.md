# M6-07 — Installed application and personal KDE acceptance

Status: **M6-07 COMPLETE — automated installed checks and personal desktop acceptance PASS (2026-09-22). M6-G PASSED / CLOSED (2026-09-22). Nothing published.**

## Artifact and isolation

- Version `0.1.0a1`; unchanged M6-06 archive SHA-256 `30e99d0e6b9659ef43785587a427e8ad05afdfbec81462503652a1a2ad967584`.
- [Installation/run identity](report.json) records the fresh temporary per-user installation and release directory.
- Application verification imports only the installed release, asserts module provenance, and runs outside the checkout. Fresh-process recovery discovery also imports that release explicitly.
- A fresh copy of the marked M4 101-book fixture is used. Original library and working installation are untouched; the disposable seed hashes are unchanged. A successful test import produces 102 books for desktop acceptance.
- Test journals retain their absolute fixture paths. Standard Qt configuration/data directories in the temporary HOME link to those fixtures. These links do not touch the real user's directories.
- Production application/package files did not change. Only acceptance drivers and documentation changed.

## Automated evidence

[Application report](application_report.json): **21 checks passed**. Covers the 101-book catalog, all covers and format paths, title/author search, multi-format grouping, grid/list agreement and Unknown reading status; real single-book save/restore, four-book bulk edit/revert, copy-only import with metadata-review warning, review flag surviving history cleanup, preserved unsaved draft without library write, fresh-process recovery discovery, startup attention counts and 1,000-operation/4,000-attempt history rendering.

[KDE report](kde_report.json): **2 checks passed** using installed application modules and real KWin native Wayland close requests on a private bus/compositor. Cancel retains the dirty editor and KWin waits. Save/Retry failure preserves the draft and completes the close without a duplicate Save prompt. No host logout, restart or shutdown was performed. This is the isolated KDE evidence approach previously accepted for M5; it is not a full desktop logout test. Private portal warnings are in the logs and did not prevent the close scenarios passing.

Prior [M6-06 evidence](../m6_06_installation/README.md) covers 177 unit/UI tests, clean dependency runtime, upgrade/uninstall/reinstall and retained data on this same artifact. [M6-03](../m6_03_compatibility/README.md), [M6-04](../m6_04_help/README.md) and [M6-05](../m6_05_diagnostics/README.md) record feature-specific verification on earlier builds; installed desktop checks below verify the current build's presentation.

Reproduce automated checks with `python3 -I -B tests/verify_m6_acceptance.py` after closing Calibre/readers. This creates a new disposable installation/fixture and replaces this run's reports. Launch/relaunch its desktop with `python3 -I -B tests/launch_m6_desktop.py`. The latter executes the exact installed desktop entry's Exec command outside the checkout. It preserves settings on relaunch. A global application-menu entry is deliberately not registered in the real user's account; personal menu discoverability is not yet claimed.

## Personal desktop checklist — completed; confirmation record below

1. Installed Hub opens with the disposable catalog (102 books), one recovery summary and Activity history. No editor opens or recovery applies automatically.
2. Help/F1, topic selection and search work; About reports `0.1.0a1`.
3. The Time Machine EPUB, MOBI and PDF open and navigate, sequentially. Closing a reader leaves the Hub open. The documented optional viewer keypress workaround remains deferred.
4. Diagnostics show a readable redacted preview. Cancel creates no export. Export matches preview and contains no book information, library names, paths or recovery contents.
5. Review the prepared single-book recovery (`M5 Desktop Recovery` tag, a reused fixture label). It opens as an unsaved draft and writes only on Save. Verify dismissal/full history and bulk review/discard remain usable.
6. Change Grid/List preference, close normally, then relaunch. The view preference and remaining history/recovery survive; no pending work resumes automatically.

The prior installed session exited normally (code 0). The same installed session was reopened with existing settings and journals. Questions now cover the earlier catalog/help/readers checks, diagnostics preview/cancel/export, and single-book recovery review/Save. View-preference persistence across another close/relaunch remains pending. See [desktop acceptance tracking](desktop_acceptance.json). Record each actual answer before marking acceptance complete; normal process termination and automated results do not establish personal approval.

2026-09-22: User confirmed **“all four pass”** for the requested catalog/help/version, EPUB/MOBI/PDF reader, diagnostics cancel/export and recovery draft/explicit Save checks. This does not independently confirm the additional dismissal/bulk actions listed above. Automated coverage remains in the application report. Next: change Grid/List, close, relaunch and confirm retained preference/history without automatic pending-work resumption. M6-07 remains in progress; M6-G OPEN.

Restart preparation, 2026-09-22: user selected Grid and closed the reader and Hub. Saved settings contain `view: Grid`; the installed Hub exited with code 0. Reopening the same installation for visual confirmation of retained view/history and no automatic pending-work resumption.

## Final M6-07 acceptance — 2026-09-22

User confirmed **“all three pass”** after relaunch: Grid view restored, Activity history retained, and no recovery editor or pending work resumed automatically. Together with the earlier **“all four pass”**, this completes the requested personal desktop acceptance. The [structured confirmation record](desktop_acceptance.json) distinguishes user observations from automated evidence. Earlier progress notes above are historical.

M6-07 is COMPLETE. The package is unchanged; no rebuild or publication occurred. Next: final M6-G evidence review, including the documented limits of isolated KWin testing and desktop-entry launch versus real-account menu discoverability. M6-G remains OPEN.

Final review: **M6 COMPLETE; M6-G PASSED / CLOSED**, 2026-09-22. [Criterion-by-criterion closure and retained limitations](gate_review.md). Earlier progress notes are historical. No release was published.
