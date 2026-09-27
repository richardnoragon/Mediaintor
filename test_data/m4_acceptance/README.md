# M4 acceptance evidence

Status: **M4 COMPLETE; M4-G PASSED/CLOSED.** Automated acceptance passed and the user confirmed all three desktop checklist groups on 2026-09-21. M4-07 is DONE. M1–M3 remain complete. No release was published.

## Verified

- [64 unit/UI tests](unit_tests.txt), including the existing M1–M3 regression suite, selection across search/sort/view changes, module-close selection reset, preview invalidation, numeric validation, field-scoped revert, damaged-history preservation and confirmed history deletion.
- [25 application checks](application_checks.json): 101-book reads, all five bulk operations, sequence gaps, isolated conflicts, stop/restart/retry, interrupted revert, lost acknowledgement reconciliation, exact author replacement, format/identity preservation, explicit history deletion, **101-book edit and 101-book revert**, and actual dialog preview/confirmation/exclusion.
- [8 Calibre fault checks](fault_checks.json): series/index partial writes, preserved earliest before values across retries, restoration of original coupled values, failed journal acknowledgement and reconciliation, library identity rejection and lock denial.
- Both [application](application_report.json) and [fault](fault_report.json) reports confirm original-library file hashes unchanged. All original format contents and book identities in the application copy were preserved, including author-related path changes.
- [Inspected dialog screenshot](bulk_preview.png).

The tests used Calibre 9.2.1 and fresh disposable copies. Earlier attempts encountered transient access contention; guards retained uncertain/pending work without bypassing the lock. The test driver explicitly reviewed and retried where necessary. This is not application automatic resume. Author near-match fixtures use genuinely distinct stored names because Calibre can canonicalize case-only author variants.

## Confirmed desktop acceptance

The user confirmed that all checklist items work and requested closure of M4 and M4-G. See the [desktop confirmation record](desktop_confirmation.json). The instructions below are retained for reproduction; Calibre/readers must be closed during library access. Run from the project directory:

```bash
python3 tests/launch_m4_desktop.py
```

This opens the verified disposable library with separate desktop settings and four selected books. The temporary library must still exist; otherwise rerun the application verification to create another copy.

1. Filter/sort and switch Grid/List. Confirm the selected count persists and hidden selections appear in **Bulk edit / history**. Choose Add Tags, add `M4 Desktop Review`, and build a preview. Confirm nothing changes before **Confirm changes**. Exclude one book and confirm the other three update.
2. Choose the resulting history record and **Revert Batch**. Confirm a fresh preview appears and, after confirmation, only that tag change is restored. For Set Series, choose Sequential, start 0/increment 0.5, reorder books and exclude one; confirm previewed numbers retain their gaps. Revert that batch afterwards.
3. Close/reopen Book-inator. Confirm ordinary selection clears while history remains. Confirm cancelling history deletion preserves the record and the warning explains loss of revert ability. Report whether these workflows are understandable and work correctly.

All three groups are user-confirmed; M4-G10 and M4 are complete. Automated interruption/conflict/fault scenarios are already recorded; no user should reproduce injected failures manually.

## Reproduce automated checks

```bash
QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s tests
QT_QPA_PLATFORM=offscreen calibre-debug -e tests/verify_m4_faults.py
QT_QPA_PLATFORM=offscreen python3 tests/verify_m4_application.py
```

Run Calibre integration checks sequentially with Calibre/readers closed. They require Calibre's local locking socket; restricted execution environments may need explicit approval. Test journal and library paths are recorded in the reports. The normal application never reads a disposable test report to choose a production library.
