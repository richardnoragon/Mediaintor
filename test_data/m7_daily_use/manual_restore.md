# M7-03 — Manual backup, isolated restore and retained-data validation

**COMPLETE. M7-G OPEN; seven-day trial NOT STARTED.**

[16 checks passed](m7_03_report.json). The active environment stayed unchanged throughout isolated testing. The verified helper-cache fix was then installed separately; [promotion evidence](cache_fix_promotion.json) confirms all active library/settings/history/recovery bytes were retained.

## What was verified

- Closed-container manual copies of the entire `active/` tree: library, persistent home (including installed program, configuration, viewer state, Activity and recovery), and import sources. File hashes, symlink targets and regular-file modes match the backup and initial restore.
- Restored 101-book database integrity, saved view/geometry and profile/device identity read through installed APIs. Stable internal paths preserve library-specific indexes without rewriting references.
- A preserved single-book draft, pending real import preview and pending bulk batch were created only in the first restored environment. That enriched environment was manually backed up again and restored into another location.
- Fresh containers rediscovered these journals without replay. Review opened the recovered metadata as a dirty draft without writing; explicit Save committed it and marked recovery resolved. The test tag was then restored to its original value.
- A prior M6-05 build installed into the restored home, followed by upgrade to the corrected M7 candidate, uninstall and reinstall. Retained-data hashes and API read-back passed. Uninstall removed the program launcher while retaining libraries/configuration/history/recovery. This is a distinct-build test within version 0.1.0a1, not a schema migration.
- Original active data and the primary manual backup were unchanged after the isolated tests. No live library or development checkout was mounted.

## Defect found and fixed: M7-DEF-001

Calibre starts its own Python interpreter. The metadata/import helpers allowed local imports to generate `__pycache__` inside the installed release. The installer's strict inventory check correctly refused subsequent upgrades/uninstall.

Both helpers now disable bytecode writing before local imports. No installer integrity check was relaxed. The 177 existing tests passed, and a new regression test covering both helpers passed with normal bytecode-enabled child interpreters. Real Calibre operations followed by upgrade/uninstall/reinstall and release-manifest checks also passed.

For existing installations, caches were **quarantined**, not silently ignored: every tracked program file was first verified against the installation manifest; only extra `mediainator/__pycache__/*.pyc` files were permitted, symlinks refused, and the cache directory moved into evidence. Unexpected changes would have stopped the repair. The active candidate received this repair only after the restored-copy lifecycle passed and its full original backup was verified.

Corrected candidate package SHA-256: `3252cc4b6d8a04e696d7b1449347920e6fd42982d0453ec5d88f72635cde2702`.

Docker image: `sha256:da0d06cee1517cbbc0b0b8910c3303b6ad3b47377445a76e47994e977f885783`.

Installed build: `0.1.0a1-c08faf149723f3c0`. Original M6 artifact and pre-fix candidate record remain preserved. M6 reports describe their historical candidate; this fix is M7 stabilization work. No public release/version bump occurred. The trial was unstarted, so no completed trial days are discarded.

## Repeatable manual-copy procedure

1. Close the Hub and all readers normally. Verify no container mounts the environment being copied. Do not copy a running SQLite library as a recovery backup.
2. Create a new, dated directory under `Mediaintor-M7-Testing/backups/`. Copy the complete `active/` contents, preserving files, permissions and symlinks. Do not follow the installation's `current` symlink into a different path. Include externally preserved test recovery files if any; no such alternate destination was used here.
3. Record and compare inventories: file SHA-256, symlink target and file mode. Confirm the source stayed unchanged. Keep a backup read-only by convention: never launch the application against it.
4. Copy that backup into a new `restores/` directory. Verify its inventory before opening. Do not overwrite `active/` or an older restore.
5. Launch the pinned image with **only** the selected restored `home`, `library`, and `import-sources` mounted at `/home/mediainator`, `/data/library`, and `/data/import-sources`. Keep these internal paths unchanged so settings/recovery indexes resolve to the restored environment. Do not mount active state alongside it.
6. Read settings and run database integrity/catalog checks. Confirm book/format/cover files and required referenced files exist via the inventory; inspect saved metadata, settings and pending history through the application APIs. Opening/discovery must not automatically resume jobs.
7. Review a recovery draft before saving. Exercise destructive recovery or uninstall tests only on this restore. Compare the original backup and active environment afterwards.
8. Save the inventory, image/package identities, results and any limitations. Retain the source backup even if a restore attempt fails.

The standalone repeatable qualification driver is `../Mediaintor-M7-Testing/deployment/recovery_validation/verify_restore.py`; run it from a KDE Wayland session with the M7 Hub closed. It creates new dated copies, runs installed APIs and logs results under the independent root's `evidence/`. It is test automation around manual filesystem copying, not a built-in backup feature. Source copies of the driver are retained in [recovery_validation](recovery_validation).

Earlier attempts corrected verifier assumptions (List versus actual Grid, directory instead of metadata.db, and a duplicate import fixture). Their records/logs are retained; they were not product data-loss failures. The helper-cache issue was the actual product defect.

## Limits and next step

Backups are on the same disk as the test environment; this validates copying and recovery, not whole-disk-loss protection. Historical M7-02 personal desktop acceptance covered the previous build. Do a brief corrected-build menu/reader smoke check and agree Day 1 before M7-04. Seven consecutive days must use the final candidate, identified by package/image/deployment hashes. M7-G stays open.
