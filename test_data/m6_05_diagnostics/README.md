# M6-05 — Always-redacted diagnostic export

Status: **M6-05 COMPLETE; M6-G OPEN.** Unpublished personal preview remains version 0.1.0a1.

## Delivered behavior

Help → Preview redacted diagnostics creates a frozen, read-only JSON preview. Export JSON opens an explicit local save dialog. The exported bytes are exactly the previewed bytes; later events cannot silently change them. Closing the preview or cancelling the picker writes no export. Failure retains the preview for retry and displays a safe message without echoing destination paths. Files are written atomically with owner-only permissions (0600); symlink destinations are refused. No upload mechanism or sensitive-detail opt-in exists.

The schema allowlists validated app/OS/KDE/Python/PyQt/Qt versions, relevant dependencies, safe feature booleans, the last displayed compatibility state and strictly parsed tool versions when available. It does not run Calibre probes or read library data. Compatibility results are explicitly labeled as a previous check, not a fresh guarantee.

A bounded current-session ring holds at most 50 sanitized error events. Metadata/import failures, Activity storage errors and operation failure/partial/interruption summaries are recorded using fixed codes/messages. Tracebacks retain only allowlisted application module/function symbols and bounded line numbers; filenames, source code, locals, exception messages/arguments/chains and unknown symbols are omitted. Unknown frames and dropped older events are counted. Raw historical logs, settings dumps, environment dumps and recovery files are not read for diagnostics. There is no claim to reconstruct raw errors from earlier application sessions.

Always excluded: titles, authors, ISBNs, library names, paths, metadata values, notes, backup locations, recovery contents, user/host identifiers and secrets. Unsupported strings are omitted rather than scrubbed with heuristic regexes. Version regexes validate only dedicated version sources; they are not used to redact arbitrary prose.

## Verification

- [Unit/UI output](unit_tests.txt): **174 tests passed**, including eight diagnostic tests. Coverage includes private Unicode/path/metadata markers in arbitrary and nested inputs, unsafe version/status strings, exception messages/locals/chains, safe-frame projection, bounded logging, exact Calibre-version parsing, atomic failure cleanup, existing-file preservation, symlink rejection, mode 0600, preview equality, cancel, failed export/retry and frozen snapshots. Activity details are not copied into error summaries.
- [Installed report](report.json): **seven checks passed** in a disposable user installation outside the checkout. Preview/export bytes match; private injected exception content is absent; versions and fixed summaries appear; cancelled export creates no file; later events do not change the approved snapshot; permissions are 0600; Hub close closes the diagnostic window. Python socket creation and Calibre probing were blocked during this workflow. No original library was accessed.
- [Preview rendering](preview.png) was visually reviewed. This is automated/offscreen evidence, not final KDE desktop acceptance.

Reproduce:

```sh
python3 tools/build_package.py
QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s tests
python3 tests/verify_m6_diagnostics.py
```

M6-06 installation/upgrade qualification and M6-07 full application/personal desktop acceptance remain outstanding. M6-G stays open. No automatic upload, publication or working-account installation was performed.
