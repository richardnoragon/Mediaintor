# M6-04 — Help, instructions, troubleshooting and error polish

Status: **M6-04 COMPLETE; M6-G OPEN.** Version remains 0.1.0a1; no release published.

## Delivered

- Help menu with User guide (F1), Installation and upgrades, Troubleshooting and About Media-inator. One reusable, non-modal help window has topic selection and in-topic search. Documentation is local; opening it does not probe Calibre, launch subprocesses, access library contents or fetch remote content. About shows application/Python/PyQt/Qt versions and preview status.
- The bundle includes all three guides. Source and installed help use the same files; the installed UI resolves them independently of the project checkout. A missing/unreadable help file gives a reinstall instruction that explicitly preserves settings and recovery data.
- Instructions cover per-user installation without a checkout, upgrades, uninstall from the installed package, retained data, prerequisite versions, current access restrictions, single-book edits, imports, bulk/revert workflows, partial saves and recovery. Troubleshooting explains what to do about blocked versions, library locks, missing formats, failed settings, failed preservation, hidden recovery entries and the deferred viewer keypress issue.
- Startup/settings and missing-format messages give actionable next steps. The installed launcher reports an application-runtime import failure with installation guidance instead of only an import traceback. No save/discard, ownership, compatibility or recovery policy was relaxed. Raw error information is not described as safe diagnostic export; M6-05 remains pending.
- Accepted Hub close also closes its help window so it cannot keep the application open after exit.

## Evidence

[Unit/UI output](unit_tests.txt): **166 tests passed**, including four help tests for offline topics/search, missing-file fallback, window reuse/close and version consistency.

[Installed report](report.json): **seven checks passed** in a disposable user installation outside the checkout. All topics render, search works, About reports the expected version and help closes with the Hub. Calibre probes and subprocess launch were patched to fail if help attempted them. No library was chosen or accessed. The report identifies the rebuilt artifact by SHA-256.

[Rendered troubleshooting window](help.png) was visually reviewed for readable text and controls. It is offscreen evidence, not human KDE desktop acceptance.

## Reproduce

```sh
python3 tools/build_package.py
QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s tests
python3 tests/verify_m6_help.py
```

The verifier installs only into a fresh temporary user prefix. Current application data and original Calibre libraries are untouched. M6-05 diagnostic export, M6-06 fresh-OS/upgrade verification and M6-07 full desktop acceptance remain outstanding. M6-G stays open.
