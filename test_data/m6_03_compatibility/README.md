# M6-03 — Compatibility guards and first-run guidance

Status: **M6-03 COMPLETE; M6-G OPEN.** No publication or version bump.

## Implemented

- One compatibility service checks the verified Ubuntu x86_64 / Python 3.14.4 / PyQt6 and Qt 6.10.2 / SIP 13.11.0 baseline and all four system Calibre tools at exactly 9.2.1. Missing, unverified, mismatched, malformed or failed probes block protected operations, without an override. Version probes use isolated Calibre configuration and no library arguments.
- Successful checks are cached against tool/Calibre module identities and revalidated at operation boundaries. A changed toolchain invalidates the cache; changes during probing fail closed. Helpers independently check the executing Calibre version before opening a library.
- Guards cover snapshots (before construction and before copying), catalog listing, metadata reads/writes, import preview/execution, bulk writes/reverts and viewer launch. Bulk work checks before recording the next write intent. Import compatibility failures stop the batch and retain unfinished items rather than attempting each remaining item. Existing ownership, locks, conflicts and explicit Save/confirmation remain required.
- Hub first-run guidance checks asynchronously before the initial live catalog load, identifies supported/detected versions, explains the private-copy/original-file workflow and offers existing-library selection and an official Calibre installation link. Recheck updates availability but does not replay blocked work. Local Activity, preserved drafts and close/preservation controls remain available.
- Catalog edit/import/reload/format controls follow the checked availability; adapters enforce guards independently of UI state. A later dependency change is caught when an operation is attempted, even before the user rechecks the panel. Existing open editors retain their drafts on dependency failure.

## Evidence

[Unit/UI output](unit_tests.txt): **162 tests passed**. New coverage includes exact-version acceptance, cached identity invalidation, old/new/mixed versions, missing dependencies, malformed output, timeout, changed-during-probe denial, direct adapter/snapshot blocking, helper version guards, first-run/recheck behavior and blocked catalog process launch. Existing reader/snapshot unit tests explicitly mock compatibility because they test those components in isolation; real compatibility evidence is below.

[Disposable/installed report](report.json): **10 checks passed**. Real tools report Calibre 9.2.1. Injected unverified versions block metadata/import/snapshot access and viewer launch. An explicit successful recheck permits a real helper read on a fresh private copy. Disposable seed hashes remain unchanged; no original library was used. A fresh per-user installation runs first-run guidance from installed files outside the checkout, with no library chosen and no loader started.

The first real-read test request omitted the required UUID and was rejected. The test fixture was corrected; no production guard was relaxed. Sandbox-only viewer initialization failures were separately rerun outside the sandbox, where real version checks passed.

## Reproduce and remaining scope

```sh
QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s tests
python3 tools/build_package.py
python3 tests/verify_m6_compatibility.py
```

Integration needs the earlier marked M5 disposable fixture and Calibre's local lock/desktop version-probe access; sandbox approval may be needed. The script creates another fresh library copy and temporary installation rather than touching the original library or working installation.

Installed first-run verification is automated/offscreen. User desktop acceptance, fresh-OS qualification, populated-state upgrades and final installed workflow regression remain M6-06/07. In-app help enhancements and diagnostic export remain M6-04/05. Compatibility verification is not authorization to upgrade Calibre automatically; other versions require a future recorded verification and code/manifest update. No automatic job resumption or diagnostics upload was added.
