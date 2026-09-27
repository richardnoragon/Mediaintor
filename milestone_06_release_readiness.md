# Milestone 06 — First Release Readiness

Current status: **M6 COMPLETE; M6-G PASSED / CLOSED (2026-09-22).** All M6-01–M6-07 tasks are complete. [M6-G closure review](test_data/m6_07_acceptance/gate_review.md). Version remains 0.1.0a1; nothing published. Earlier checkpoint notes are historical.

Status: **Scope APPROVED; M6-01 technical design and M6-02 package build/isolated-user verification COMPLETE; M6-03 compatibility/first-run implementation COMPLETE; M6-04 help/instructions/error polish COMPLETE; M6-05 always-redacted diagnostics COMPLETE; M6-06 installation/upgrade/retention verification COMPLETE; M6-07 installed application and personal desktop acceptance COMPLETE; M6-G PASSED / CLOSED.** M1–M5 are complete. No release has been published. Publishing requires a separate user instruction.

## Approved boundary

Prepare an installable Media-inator package with an application-menu entry for personal use on the user's verified Ubuntu 26.04.1 LTS with KDE environment. Small-tester validation is deferred to a possible M7; public distribution is a later decision. Installation is for the current user account only; system-wide installation is outside M6. Select the package format during M6-01 technical design.

Retain private-copy catalog browsing, opening original book files, and the existing exclusive-access rules requiring Calibre/readers to be closed during protected operations. Preserve M1–M5 workflows and recovery safeguards. Do not add new modules, synchronization, backups, file-management features or automatic job resumption.

Include installation instructions, first-run library selection, in-app help, understandable error messages, version information and manually exported troubleshooting diagnostics. Document known limits, including the deferred viewer keypress issue. Packaging must not turn that deferred item into an undocumented prerequisite for closure.

## Calibre prerequisite

Calibre remains separately installed and managed by the user. Detect its installation and version, verify compatibility and explain missing requirements with instructions or links. Prevent unsupported operations when requirements are not met. Do not bundle, install, upgrade or manage Calibre automatically.

Existing Calibre 9.2.1 evidence is a tested baseline, not proof of a broader supported version range. M6 blocks protected operations for missing, incompatible or unverified Calibre versions, without an override. Explain the detected version (or absence), verified supported versions and reason for blocking. During M6-01, define the exact verified version list and map protected operations; verify these guards in the installed package. Retain access to help and preserved recovery data. Example version numbers in stakeholder discussion are illustrative, not a supported-version declaration.

## Diagnostics privacy

Export is explicit and local, with a preview of the exact content before export and no automatic uploads. Include application, OS, KDE and Python versions; relevant installed dependency versions; non-sensitive feature state; sanitized error logs and stack traces; and environment validation results.

Always exclude titles, authors, ISBNs, file paths, library names, recovery contents, metadata values, notes and backup locations. Error messages and tracebacks can contain these values: sanitize them too. Configuration export must use an allowlist rather than copying settings or environment wholesale. Include only relevant application dependencies, not an inventory of unrelated installed software. Do not export credentials or secrets.

No sensitive-detail opt-in is provided in M6. Richer diagnostics are deferred to M7 or later. Preview contains the already-redacted export; cancellation creates no export. Test with recognizable sensitive strings in settings, exceptions and nested diagnostic data. Omit unsafe free-form content when reliable sanitization cannot be established.

## Implementation passes

| ID | Status | Task and completion evidence |
| --- | --- | --- |
| M6-01 | DONE — [technical design](technical_design_m6.md) | Select a per-user package format, enumerate verified dependencies and protected-operation guards, and design always-redacted diagnostics; inspect current packaging and record technical design. |
| M6-02 | DONE — [package evidence](test_data/m6_package/README.md) | Build the chosen installable artifact, desktop entry and version metadata; document reproducible build and dependency requirements. |
| M6-03 | DONE — [compatibility evidence](test_data/m6_03_compatibility/README.md) | Add prerequisite checks and first-run guidance, including unavailable/incompatible Calibre and library selection; verify installed behavior. |
| M6-04 | DONE — [help evidence](test_data/m6_04_help/README.md) | Provide in-app help, installation/upgrade/uninstall instructions, troubleshooting and clear errors; describe operating restrictions and recovery limits. |
| M6-05 | DONE — [diagnostics evidence](test_data/m6_05_diagnostics/README.md) | Implement always-redacted diagnostic collection, exact export preview and cancellation; verify excluded content cannot be exported and no automatic uploads occur. |
| M6-06 | DONE — [installation evidence](test_data/m6_06_installation/README.md) | Validate clean installation, upgrade and uninstall in an isolated target environment; retain libraries, settings, journals/history and recovery payloads; verify retained data after reinstall. |
| M6-07 | DONE — [installed acceptance evidence](test_data/m6_07_acceptance/README.md) | Run installed-package M1–M5 regressions and end-to-end browsing, editing, imports, bulk editing/revert and recovery; obtain personal desktop acceptance and assemble M6-G evidence. |

Use disposable libraries and isolated application data for destructive/failure scenarios. Do not replace the user's working installation or modify the live library merely to test packaging. An upgrade test must use a documented prior artifact and populated state; clean installation alone is not upgrade evidence. Package selection must account for the existing Python/PyQt requirements rather than assume compatible system packages.

## M6-G acceptance gate

- [x] M6-G01: Package design implements approved per-user installation, strict compatibility blocking and mandatory redaction; scope remains personal use on the verified environment.
- [x] M6-G02: Installable artifact builds reproducibly and installs successfully; menu entry launches the Hub with correct version information outside the source checkout.
- [x] M6-G03: Calibre detection/version checks block protected operations for missing, incompatible or unverified versions without an override; guidance shows detected/supported versions and the reason, without managing Calibre.
- [x] M6-G04: First-run library selection, in-app help and instructions explain current workflow, protected access and known limitations.
- [x] M6-G05: Diagnostics always exclude sensitive content, including within exceptions/tracebacks; redacted preview and cancellation work; no sensitive-detail opt-in or automatic upload.
- [x] M6-G06: Upgrade retains usable settings, history and recovery state; uninstall retains libraries and application data; reinstall can discover retained state.
- [x] M6-G07: Installed-package automated and disposable end-to-end checks cover M1–M5 without regression or changes to source files outside authorized operations.
- [x] M6-G08: User confirms personal desktop acceptance; evidence, instructions and known limitations are current. Readiness is recorded separately from permission to publish.

## Final scope decisions

All product-scope questions are resolved: per-user installation only, protected-operation blocking for unverified Calibre without an override, and always-redacted diagnostics without sensitive-detail opt-in. M6-01 technical investigation and M6-02–M6-07 implementation/acceptance are complete. The final evidence review passes all eight gate criteria.

The phrase “1.0 foundation” describes the intended maturity, not an approved version bump. Release version selection and publication remain separate from this scope confirmation.

Links: [implementation plan](implementation_plan_hub_bookinator.md), [release scope](first_release_scope.md), [M5 closure](test_data/m5_acceptance/gate_review.md).

M6-01 completed: per-user versioned install bundle using the inspected system runtime; exact Calibre 9.2.1 compatibility baseline with operation-boundary guards; structured allowlisted diagnostics without raw free-form logs. See [technical design and verification handoff](technical_design_m6.md). Package/runtime acceptance remains pending in M6-02–M6-07.

M6-02 completed: deterministic per-user bundle, runtime preflight, versioned activation, protected uninstall and isolated-user Hub smoke verified. Clean-user tests use host system packages; fresh-OS dependency closure, interrupted/populated-state upgrades and KDE acceptance remain M6-06/07. M6-G stays open.

M6-03 completed: shared exact-version/runtime checks, operation-boundary and helper guards, asynchronous first-run guidance and explicit recheck without replay. 162 unit/UI tests and 10 disposable/installed checks passed. Next M6-04 help, installation/troubleshooting guidance and error polish. M6-G stays open.

M6-04 completed: offline in-app help/search, About/version information, installed guides and actionable startup/settings/missing-file guidance. 166 unit/UI tests and seven installed-help checks passed. Next M6-05 always-redacted diagnostic export. M6-G remains open.

M6-05 completed: frozen exact JSON preview, explicit local export, strict field/frame allowlists, bounded current-session safe error summaries, atomic owner-only writes and failure/cancel preservation. 174 unit/UI tests and seven installed diagnostic checks passed. Next M6-06 installation/upgrade/uninstall qualification. M6-G remains open.

M6-06 completed: 177 unit/UI tests and 14 clean Ubuntu userspace checks passed, including a distinct build upgrade from M6-05, retained-data read-back and unchanged library/recovery bytes through uninstall/reinstall. Added durable installation transactions and explicit validated repair after interruption. This is not a booted KDE VM; full installed application/personal desktop acceptance remains M6-07. M6-G stays open.

M6-07 checkpoint: the unchanged M6-06 artifact passed 21 full application checks from its installed modules and two private real-KWin close scenarios. The disposable seed stayed unchanged. Personal desktop acceptance passed on 2026-09-22, including saved Grid view, retained Activity history and no automatic recovery/resumption after restart. M6-07 is COMPLETE; M6-G remains OPEN pending final evidence review. Nothing was published.
