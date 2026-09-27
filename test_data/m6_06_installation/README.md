# M6-06 — Installation, upgrade and retained-data verification

Status: **M6-06 COMPLETE; M6-G OPEN.** No publication or working-account installation. Version remains 0.1.0a1.

## Upgrade and retention evidence

[Clean-runtime report](report.json): **14 checks passed**. Installed the preserved [real M6-05 artifact](artifacts/prior-m6-05.tar.gz), populated application data through its installed APIs, then upgraded to a distinct new build. Both builds retain the same preview version; this is a build-to-build upgrade, not a claimed schema migration or version-number release.

Populated state includes saved layout/view and profile/device identity, Activity history, a pending import, a pending bulk edit and a registered unresolved single-book recovery draft. A copied Calibre library and an external import-source fixture are retained separately from program files. The test verifies byte-for-byte preservation across upgrade, uninstall and reinstall; current APIs rediscover the same journals and reconstruct the retained draft without saving or replaying it. Unknown settings schemas are refused and retained. The previous program release remains available after upgrade, and uninstall removes program/menu/launcher entries only.

## Clean Ubuntu runtime qualification

[Runtime inventory](clean_root.json) records 194 Ubuntu dependency packages, exact selected versions and archive hashes. A fresh root was assembled from downloaded distribution packages. The namespace mounts neither host /usr nor /etc, the source checkout nor the original home. It has a private network namespace. Installation, installed Hub startup and native offscreen/Wayland plugin dependency resolution pass on this runtime.

This is an isolated Ubuntu userspace assembled from package contents, not a booted VM or a newly configured KDE desktop. Package maintainer scripts/services were not run; `/usr/bin/sh` was explicitly linked to the extracted bash for POSIX shell invocation. The initial missing-shell and optional-ldd issues were verification-environment issues: setup now provides the shell and checks dependencies with the runtime's own ELF loader. Full interactive KDE and installed library workflows remain M6-07.

Ubuntu package downloads and extraction occurred only in temporary directories. No packages were installed into the working system. The original Calibre library was never used; the earlier marked disposable library supplied read-only fixture input.

## Interrupted installation repair

The prior installer could leave integration files inconsistent after process termination. Installation/uninstall now records a durable transaction before integration changes. `repair` explicitly completes that recorded action, rechecking owned paths, file hashes and current-release identity. Changed files stop repair without overwriting them. Program activation and directory updates are synced; successful completion removes the transaction. The updated launcher refuses to start while an action is pending. This does not replay application jobs or modify user-data schemas.

[Unit/UI output](unit_tests.txt): **177 tests passed**, including three transaction suites. Isolated child installers are terminated after menu, state and current-pointer writes; repair itself is also interrupted and retried. Confirmed uninstall is interrupted and repaired. Changed-file refusal, launch blocking, repeated repair and retained-data protection pass. These are process-termination/fault tests, not physical power-loss experiments. Pre-transaction staging can leave an unused `.staging-*` directory; it is never selected as a running release.

Use the installer extracted from the trusted bundle if the launcher/current pointer was already removed:

```sh
/usr/bin/python3 -I ./package_install.py repair
```

Do not delete settings/recovery data or edit installation JSON to bypass a repair refusal.

## Reproduce

```sh
python3 tools/build_package.py
QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s tests
python3 tests/prepare_m6_runtime.py
python3 tests/verify_m6_installation.py
```

Runtime preparation downloads packages to /tmp and does not run apt install. Download/namespace sandbox approval may be required. Repository version changes can require requalification; the recorded inventory is the evidence for this run. The verifier creates new isolated user data each time and preserves the earlier M6-05 archive as its upgrade baseline.

Next: M6-07 full installed application and personal desktop acceptance. M6-G remains open; no release is published.
