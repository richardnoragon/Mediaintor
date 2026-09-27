# M2 acceptance and G2 closure record

Status: automated implementation verification passed; final user desktop confirmation is recorded. M2 and G2 are COMPLETE for the agreed scope.

## Evidence

- `QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s tests -v`: **41 passing tests**, including all 23 M1 tests and 18 M2 draft, validation, conflict, refresh and combined-review tests.
- [Adapter report](adapter_report.json): **16 passing checks** using the actual Calibre helper on a fresh 101-book copy. Seven fields, cover removal/replacement, accepted retained series index, explicit new-series default, conflict no-write, preservation of external values, partial saves, retry conflicts, damaged-cover restoration, failed recovery with retained backup, invalid-input rejection, lock denial, UUID and every format hash checked.
- [Application report](application_report.json): **17 passing checks** through the real Qt hub/editor and subprocess helper on a separate 101-book copy. Catalog/search/grouping, draft/cancel/save, path refresh, series clearing, external-change deferral, conflict cancellation, Discard, cover removal/replacement and HTML preservation passed.
- Original-library file hashes unchanged in both integration runs. Source: `/home/sproket01/Calibre Library`.
- [Editor screenshot](editor.png), [hub screenshot](hub.png).
- [Desktop review session](desktop_session.json): separate disposable copy and settings prepared for the user. The user confirmed all review groups: metadata persistence/series, controls/cover/validation, and Save/Discard/Cancel. See [desktop confirmation](desktop_confirmation.json).

## Reproduction

Run from the repository root with Calibre 9.2.1, Python and PyQt6 installed. Integration scripts create new disposable copies and never write the source library:

```sh
QT_QPA_PLATFORM=offscreen CALIBRE_CONFIG_DIRECTORY=/tmp/mediainator-m2-integration-config calibre-debug -e tests/verify_m2_calibre.py
QT_QPA_PLATFORM=offscreen python3 tests/verify_m2_application.py
```

Calibre needs its local lock socket; sandbox-denied runs are not substantive failures of the application. The successful runs were authorized outside the sandbox. The adapter test acquires the real Calibre lock once, then mocks repeated acquisition inside that same process; the application test exercises actual subprocess lock acquisition. Failure injections are confined to the disposable library. They are not proof of every possible OS/filesystem failure.

## G2

G2 is the existing viewer-lifecycle gate from the M1 technical design. **PASSED/CLOSED for Calibre 9.2.1**: detached viewer survival and handled close were verified, the user confirmed EPUB/MOBI/PDF readability/navigation and both hub Cancel/Close reader outcomes, and current M1 regression tests still pass. [Recorded user evidence](../m1_acceptance/desktop_confirmation.json). The initial-keypress issue remains the accepted non-blocking TODO-VIEWER-01. G2 does not certify simultaneous writers, other Calibre versions or every media type.

## Closure

The user accepted the desktop review. M2-01–M2-07 and M2-A01–M2-A17 are complete for the agreed scope; G2 remains closed for Calibre 9.2.1. Broader first-release work remains outside this milestone. No release was published.
