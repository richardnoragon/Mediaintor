# M6-01 — First Release Readiness technical design

Current status: **M6 COMPLETE; M6-G PASSED / CLOSED (2026-09-22).** All M6-01–M6-07 tasks are complete. [M6-G closure review](test_data/m6_07_acceptance/gate_review.md). Version remains 0.1.0a1; nothing published. Earlier checkpoint notes are historical.

Status: **M6-01 COMPLETE (design and local inspection only). M6-02 package construction/isolated-user verification COMPLETE; M6-03 compatibility/first-run COMPLETE; M6-04 help/instructions COMPLETE; M6-05 diagnostics COMPLETE; M6-06 installation/upgrade verification COMPLETE; M6-07 COMPLETE; M6-G PASSED / CLOSED.** The design below is implemented for packaging in M6-02; compatibility guards and first-run guidance are implemented in M6-03; diagnostic export is implemented in M6-05. See [package evidence](test_data/m6_package/README.md). No release published or version bump approved.

## Package and runtime decision

Deliver a versioned `mediainator-<version>-ubuntu26.04-x86_64.tar.gz` per-user installation bundle. Include the application package, resources/help, installation and uninstall tools, desktop-entry template, dependency manifest, checksums, license notices and instructions. Exclude tests, disposable data, development state and user libraries. This is an installable application bundle, not a system `.deb` or a prebuilt virtual environment. Use the already-tested Ubuntu system Python/PyQt6 runtime; do not download replacement Qt wheels or mix an untested bundled Qt into it.

The installer runs without root, validates prerequisites before modifying the installation, and never invokes apt, pip, Calibre installation or automatic downloads. Missing runtime packages produce instructions for the user. Resolve and document the exact native dependency list during M6-02 clean-environment build verification. The current machine's successful imports alone do not prove that list is complete.

Application files live under `~/.local/share/mediainator-install/releases/<version>-<build-id>/`; `current` selects the active release. Install a stable launcher under `~/.local/bin/mediainator` and an application-menu entry under `$XDG_DATA_HOME/applications` (default `~/.local/share/applications`). Generate absolute desktop Exec/Icon locations with specification-correct escaping; never rely on shell expansion of `~` or `$HOME`. Launcher must run `/usr/bin/python3` with user site and inherited Python path disabled, explicitly load the selected release and work independently of the working directory. Retain system dist-packages for verified PyQt6. Guard against local-module shadowing and inherited Qt/Python overrides affecting the runtime.

Stage a new release in the installation tree, validate manifest/checksums, perform a non-library smoke check, then atomically replace `current`. Preserve the previous release until the user removes it. Serialize install/upgrade/uninstall with a dedicated lock and refuse changes while the application instance is running. Failed installation leaves the previous launcher/release usable. Reject archive traversal, external symlinks and manifest paths outside the managed tree. Checksums detect corruption; they are not a claim of publisher authentication.

Uninstall removes only manifest-owned program files and menu/launcher entries, with confirmation. Never remove Calibre, libraries, settings, Activity history, import/bulk journals or recovery data. Keep existing QStandardPaths application/organization identities (`Media-inator`) and storage locations; packaging must not silently create a second profile. Reinstall discovers retained state. Version switching back is permitted only when data schemas remain compatible; unknown newer schemas are preserved and blocked, never rewritten. M6 introduces no planned schema migration. Validate an upgrade from a separately identified earlier artifact with populated state in M6-06.

Build the bundle from an explicit file list with fixed archive order, timestamps and ownership; record source/artifact hashes and build inputs. Repeat the build and compare artifacts in M6-02. Include third-party notices and establish the project's own license/redistribution status before any later public distribution. Personal packaging is not publication authorization.

## Inspected versions and support policy

| Component | Local evidence | M6 decision |
| --- | --- | --- |
| App | pyproject.toml `0.1.0a1` | Keep until a separate version decision; “1.0 foundation” is not a version bump |
| OS / architecture | Ubuntu 26.04.1 LTS; x86_64; glibc 2.43 | Initial package target only |
| Python | `/usr/bin/python3`, runtime 3.14.4 | Verified runtime baseline; do not infer support from broad `>=3.11` project metadata |
| PyQt6 / Qt | PyQt6 6.10.2; compiled and runtime Qt 6.10.2 | Use system runtime; installed-package qualification still required |
| PyQt6-sip | 13.11.0 | Record and validate in package environment |
| KDE | plasma-workspace 6.6.6; prior KWin 6.6.6 protocol checks | Verified desktop baseline; no other desktop qualification implied |
| Calibre tools | calibre, calibredb, calibre-debug, ebook-viewer each 9.2.1 | Initial exact allowed upstream version: **9.2.1** |
| Build tooling | setuptools 78.1.1; pip/build/wheel not installed as distributions | Bundle design requires no runtime pip or venv; build tooling must be recorded if introduced |

Inspection used runtime imports, version commands, `/etc/os-release`, dpkg-query and M5 evidence. Python metapackage version is 3.14.3-0ubuntu2 while its interpreter reports 3.14.4: use the interpreter's runtime value. Debian Calibre package revision is 9.2.1+ds+~0.10.5-2build1; retain it as evidence, not as a substitute for upstream tool versions. The viewer's sandbox probe failed during Qt initialization; the authorized outside-sandbox version probe succeeded. This is not evidence of incompatibility.

The exact runtime tuple above is the initial qualified baseline. Changes require requalification before claiming support. Missing/unverified dependencies block affected operations. Do not force system downgrade or automatic package changes; explain detected versus verified values. An external OS update can invalidate a previously working installation; retain help, data and recovery files. Runtime import failure must produce a launcher-level diagnostic because Qt UI may not start.

## Compatibility service and guard placement

Introduce one shared compatibility service with structured states: verified, missing, unverified, inconsistent-toolchain and probe-failed. Maintain a shipped versioned manifest of verified versions/capabilities. Resolve the currently used `/usr/bin` tool paths and check executable availability and consistent versions. Do not silently select an unrelated PATH installation. Run bounded, argument-list probes without a shell or library arguments. Version output is parsed strictly, capped and not treated as trustworthy diagnostic text.

Probe before initial auto-refresh or viewer launch. Recheck tool/runtime identity at each protected operation and invalidate cached results when executable identity/stat changes; version checks must not silently use stale startup results after an external update. Helpers must validate their executing Calibre version before opening a library. A queued batch rechecks before each new book; if compatibility changes, finish verifying already-started work where safe, preserve uncertainty/pending state and block subsequent items. No forced process termination or rollback of committed work.

| Boundary | Existing integration | Required enforcement |
| --- | --- | --- |
| Snapshot/list/refresh | library.py, snapshot.py | Before snapshot creation or Calibre listing, including focus/idle refresh and test-library mode |
| Metadata read/save | metadata.py, calibre_metadata_helper.py | Before read/write/helper launch and inside helper; includes single-book recovery Save |
| Import/attachment | imports.py, calibre_import_helper.py | Before metadata extraction/preview requiring Calibre, execution and retry |
| Bulk/revert | Shared metadata adapter and bulk coordinator | Before initial/current-value reads and each protected write |
| Viewer | reader.py | Before launch; same verified toolchain and existing reader/access safeguards |
| Activity recovery | recovery_actions.py | Review that invokes Calibre is guarded; a local preserved-payload inspection is not a library operation |

UI uses the same result to disable affected controls with an explanation, but adapter/helper enforcement is mandatory even when invoked without the UI. Existing lock, identity, conflict and explicit-confirmation rules remain in addition to compatibility checks. There is no override.

While blocked, permit Hub/help/version information, sanitized diagnostics, existing in-memory catalog display clearly marked stale, local Activity/history, durable preservation and carefully reviewed local discard/deletion. Never apply recovery automatically. A blocked Save retains its draft and reports dependency failure; the established failed Save/Retry preservation workflow remains available. Local preservation and orderly close must not depend on a working Calibre installation. No reader or pending job is launched merely because compatibility later becomes valid; retries require normal review.

## Diagnostic schema and privacy boundary

Use a versioned JSON export generated from typed allowlisted fields, not a dump of logs/settings/environment. Include application/runtime/dependency version strings validated against restricted syntax; OS/KDE identity; booleans/enums for feature and validation states; bounded timestamps, counts and stable error codes. Exclude personal identifiers, host/user names, command lines, environment variables, library/book IDs, URLs with personal components, and the already-agreed titles/authors/ISBNs/paths/library names/metadata/notes/backup locations/recovery bytes.

Raw exceptions, subprocess stdout/stderr, Qt messages and Activity details are unsafe by default. Export safe error codes with static human-readable templates. Tracebacks contain only allowlisted application module/function symbols, line numbers and validated exception categories; omit filenames, source lines, exception arguments, locals and chained free-form messages. Unknown third-party frames use a generic omitted-frame marker. Do not attempt to guarantee privacy by regex replacement of arbitrary prose. Legacy raw logs are not exportable; sensitive-content opt-in is absent.

Collector produces a frozen sanitized object. Preview displays exactly its serialized bytes, with omitted-content counts and a clear explanation. Explicit Export selects a local destination and writes those same bytes atomically with user-only permissions. Never append destination paths to the report. Cancel writes nothing. Export failure leaves the preview intact and reports a safe local error. No network transport, automatic uploads or raw-log attachment path. Bound collection size and omit unsupported values instead of serializing arbitrary objects.

## Verification handoff

M6-02: package file inventory, deterministic builds, offline install, dependency failure with no partial activation, path escaping (spaces/non-ASCII), correct menu launch outside checkout and no root writes. Qualify the system runtime and native Qt plugins in the clean target environment.

M6-03: missing/mismatched/old/new/unparseable Calibre, probe timeout, binary replacement after startup, direct adapter/helper calls, queued batches, automatic refresh and recovery Save. Assert blocked operations do not touch the library or launch viewers; preservation/help remain available.

M6-05: inject distinctive book/author/library/path/recovery markers into exceptions, nested data, logs, settings, stderr and tracebacks. Assert no marker leaks, including Unicode/escaped/multiline forms; unknown strings are omitted. Verify preview/export byte equality, permissions, cancellation, no network activity and failure handling.

M6-06/07: install/upgrade/uninstall/reinstall on isolated user data; compare libraries and retained recovery/history; run installed M1–M5 workflows and personal desktop acceptance. These checks are now complete; see the M6-06 and M6-07 evidence records. The design alone was not acceptance evidence.

## Sources and rationale

Existing application integration and verified M5 evidence are the baseline. Python documents that virtual environments should be recreated rather than moved, supporting the decision not to distribute a copied environment: [Python venv documentation](https://docs.python.org/3.12/library/venv.html). If wheel packaging is introduced later, pip documents pinned/hash-checked installation bundles: [Repeatable installs](https://pip.pypa.io/en/stable/topics/repeatable-installs/). Desktop command escaping follows the [Desktop Entry Specification](https://specifications.freedesktop.org/desktop-entry/latest-single/).

Links: [approved M6 scope and gate](milestone_06_release_readiness.md), [M5 evidence](test_data/m5_acceptance/gate_review.md).

## M6-03 implementation checkpoint

[162 unit/UI tests and 10 disposable/installed checks](test_data/m6_03_compatibility/README.md) pass. Compatibility is enforced before library snapshots, adapters, helper database opening and reader launches. First-run checking is asynchronous; explicit Recheck never resumes blocked jobs. The initial system toolchain remains Calibre 9.2.1. KDE host-session acceptance is retained for M6-07; the platform/runtime checks do not claim validation of a newly installed desktop.

## M6-04 implementation checkpoint

Offline Help topics/search and About are implemented; installation, recovery and troubleshooting instructions ship in the bundle. Startup/settings/missing-file messages now offer actionable next steps. [166 tests and seven installed-help checks](test_data/m6_04_help/README.md) passed without library access. Diagnostic export remains M6-05; no raw error logs are approved for sharing.

## M6-05 implementation checkpoint

[174 unit/UI tests and seven installed checks](test_data/m6_05_diagnostics/README.md) passed. Help now offers a frozen exact diagnostic preview and explicit local JSON export. Dedicated version/enum/boolean fields and safe traceback symbols are allowlisted; raw historical logs and arbitrary strings are not exported. Current-session sanitized events are bounded to 50. Owner-only atomic writes, cancellation, failed export/retry and snapshot immutability are verified. No upload or sensitive-detail opt-in was added. M6-G stays open.

## M6-06 implementation and qualification checkpoint

[177 tests and 14 clean-runtime checks](test_data/m6_06_installation/README.md) pass. A fresh root assembled from 194 Ubuntu packages runs the installed Hub without host system-library mounts. The real M6-05 archive upgrades to the current distinct build with settings, identity, Activity, pending import/bulk journals and recovery retained; uninstall/reinstall preserves the same bytes and recoverability. Durable install/uninstall transactions and explicit repair now cover interruption between integration changes, with changed-file refusal and program-start blocking. No schema migration or physical power-loss test is claimed; full interactive KDE acceptance remains M6-07.

M6-07 installed acceptance checkpoint: [21 application and two isolated KWin checks passed](test_data/m6_07_acceptance/README.md) against the unchanged M6-06 artifact. A real installed launcher with isolated HOME/XDG directories is prepared for personal desktop checks. Personal acceptance passed on 2026-09-22, including restart persistence without automatic recovery/resumption. M6-07 is COMPLETE; M6-G is OPEN pending final evidence review and nothing was published.
