# M6-G final evidence review and closure

**2026-09-22 — M6 COMPLETE; M6-G PASSED / CLOSED.** All M6-01–M6-07 tasks are complete. Readiness is for the approved personal-use environment only. No release was published and no version bump was made.

## Accepted artifact

`mediainator-0.1.0a1-ubuntu26.04-x86_64.tar.gz`

SHA-256: `30e99d0e6b9659ef43785587a427e8ad05afdfbec81462503652a1a2ad967584`.

The [final audit](gate_audit.json) confirms that a fresh build from current source exactly reproduces the accepted artifact, M6-06 and M6-07 identify this same artifact, and every application Python module is byte-identical to the M6-05 diagnostics-qualified archive. Historical report hashes remain historical; they are not relabeled as current builds. All inspected report checks pass. No application change or repeated library-write test was necessary for closure.

## Criterion decisions

| Criterion | Result | Evidence |
| --- | --- | --- |
| M6-G01: approved design/scope | PASS | [Technical design](../../technical_design_m6.md), exact runtime baseline, per-user bundle, external Calibre prerequisite, no compatibility override and mandatory diagnostic allowlists. |
| M6-G02: reproducible install and desktop launch | PASS | [Package qualification](../m6_package/README.md), [clean installation](../m6_06_installation/report.json), final reproducibility audit, and [installed desktop acceptance](desktop_acceptance.json). The installed desktop file is syntax-validated; its exact Exec command launches outside checkout with isolated HOME/XDG data. User confirmed About 0.1.0a1. Real-account menu discoverability was not tested or required by writing into the working account. |
| M6-G03: compatibility blocking | PASS | [Compatibility evidence](../m6_03_compatibility/README.md): exact Calibre 9.2.1, missing/unverified/mixed/failed checks, guarded adapters/helpers and explicit recheck without replay. Subsequent regression suite and installed workflow checks pass. |
| M6-G04: first-run/help/restrictions | PASS | [First-run evidence](../m6_03_compatibility/report.json), [installed help evidence](../m6_04_help/README.md), shipped installation/user/troubleshooting guides and user-confirmed help/search/version checks. |
| M6-G05: redacted diagnostics | PASS | [Diagnostics evidence](../m6_05_diagnostics/README.md): private-marker/exception tests, frozen exact preview, cancel, owner-only atomic export and no uploads. Application modules unchanged; user confirmed installed preview/cancel/export. |
| M6-G06: upgrade and retained data | PASS | [14 clean-runtime checks](../m6_06_installation/report.json), distinct prior-build upgrade, retained state read-back, unchanged library/recovery bytes, uninstall/reinstall discovery and interrupted transaction repair. |
| M6-G07: installed M1–M5 regression | PASS | [21 application checks](application_report.json), [two isolated real-KWin checks](kde_report.json), unchanged disposable seed, and user-confirmed EPUB/MOBI/PDF navigation. |
| M6-G08: personal acceptance and current evidence | PASS | User confirmed “all four pass” for catalog/help/readers/diagnostics/recovery, then “all three pass” for Grid restoration, retained Activity and no automatic recovery/resumption. [Confirmation record](desktop_acceptance.json). Documentation aligned with closure; publication remains separate. |

## Evidence limits retained after closure

- Supported personal baseline: Ubuntu 26.04.1 KDE, x86_64; Python 3.14.4, PyQt6/Qt 6.10.2, SIP 13.11.0 and Calibre 9.2.1. Other environments/Calibre versions require qualification.
- Clean-runtime evidence uses 194 extracted Ubuntu packages, not a booted VM. Upgrade is between distinct builds of 0.1.0a1, not a schema migration. Interruption tests are process/fault tests, not physical power-loss tests.
- KWin checks use a private real Wayland compositor/bus, not host logout. This preserves the previously accepted isolated KDE approach.
- Desktop launch was tested using the installed desktop entry's exact command in an isolated user prefix. The owner's working menu/installation was not modified. No claim of real-account menu search/discoverability is made.
- Browsing remains based on a private library copy; original book files are opened. Calibre/readers must be closed for protected operations. The documented viewer keypress issue remains deferred.
- Scope excludes automatic resumption, synchronization, backups, extra modules and public/tester distribution. Diagnostic exports remain always redacted.

## Closure and next decision

M6 and M6-G are formally closed on the evidence above and the user's acceptance. This establishes personal-use release readiness for the identified artifact; it does not publish it, install it into the working account or authorize a release/version change. Next choose a working-account personal installation or define a later milestone (such as small-tester validation). Neither is performed by this review.
