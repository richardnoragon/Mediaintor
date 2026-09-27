# M6-02 — Per-user installable package verification

Status: **M6-02 COMPLETE for package construction and isolated-user verification. M6-G OPEN.** This is an unpublished personal-use preview, not installed into the owner's working account.

Artifact: [Media-inator 0.1.0a1 bundle](../../dist/mediainator-0.1.0a1-ubuntu26.04-x86_64.tar.gz), with [SHA-256](../../dist/mediainator-0.1.0a1-ubuntu26.04-x86_64.tar.gz.sha256). Artifact identity and namespace evidence are in [report.json](report.json). The version is unchanged.

## Evidence

- [Unit/UI output](unit_tests.txt): 153 tests pass, including six package tests. Coverage includes deterministic bytes, exact inventory/checksums, traversal/symlink/duplicate rejection, corrupted content, unverified runtime, paths with spaces/non-ASCII/dollar signs, desktop syntax, launch outside the checkout with hostile Python/Qt environment settings, reinstall, modified-file refusal, broken replacement rollback, installation locks and uninstall preservation.
- [Isolated namespace report](report.json): seven checks pass. A fresh user directory, private mount/user/network namespaces, read-only system packages, no original home and no checkout. Package installs offline, runs the actual sample Hub offscreen, validates the desktop entry, reinstalls and uninstalls without removing a recovery sentinel.
- [System dependency inventory](system_packages.txt): installed package revisions supporting the verified runtime. Offscreen and Wayland Qt platform plugins resolve all native libraries on this host.
- Two builds from identical inputs produce identical archives; the public artifact checksum is recorded beside the bundle. No package or dependency was downloaded or published.

## Reproduction

```sh
python3 tools/build_package.py
QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s tests
python3 tests/verify_m6_package.py
```

The namespace check may require sandbox approval. It neither launches a viewer nor reads a Calibre library. The unit installation tests use temporary HOME/XDG values in child processes, never the working account's settings. The bundle can be installed with the trusted installer as described in [INSTALL.md](../../packaging/INSTALL.md); installation into the working account is not performed by this verification.

## Scope limits and next steps

This is a clean user environment on the host's installed system packages, not a fresh Ubuntu installation. The dependency inventory is directly verified here; fresh-OS package dependency closure remains M6-06. KDE menu interaction and installed library workflows remain M6-07. No populated-state cross-version upgrade acceptance is claimed from same-artifact reinstall or failure rollback tests.

Handled installation failures restore integration files and retain the previous selected release. Forced power loss between integration-file updates is not yet qualified; retain the old release and investigate installation metadata rather than deleting data. M6-06 must exercise interrupted upgrades and define repair behavior before readiness acceptance.

M6-03 must add Calibre operation-level version guards. M6-04/05 must add in-app help and always-redacted diagnostic export. Current installer checks Python/PyQt/Qt platform prerequisites; it does not claim those later features. Calibre remains externally managed. No application data schema changed.

Subsequent checkpoint: M6-03 added compatibility guards and first-run guidance and rebuilt the same preview version. The current artifact is identified by the [M6-03 installed verification report](../m6_03_compatibility/report.json); this M6-02 report retains its original build checksum as historical evidence.

M6-04 subsequently rebuilt the preview with offline help and revised guides. See the [latest installed-help artifact report](../m6_04_help/report.json); earlier package checksums remain historical evidence.

M6-05 subsequently rebuilt the preview with redacted diagnostics. The [M6-05 installed report](../m6_05_diagnostics/report.json) identifies the current artifact; earlier checksums describe their respective historical builds.

M6-06 supersedes the earlier interruption limitation: durable transaction repair and populated-state upgrades now pass. See the [installation/upgrade evidence](../m6_06_installation/README.md) and current artifact hash in its report. Full desktop acceptance remains M6-07.
