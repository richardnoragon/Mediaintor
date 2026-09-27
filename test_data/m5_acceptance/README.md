# M5-07 — Application and desktop acceptance

Status: **M5-07 COMPLETE — automated checks passed and desktop acceptance user-confirmed. M5 is COMPLETE and M5-G is PASSED / CLOSED.** See the [final evidence review](gate_review.md). No release is claimed.

## Recorded evidence

| Area | Result | Evidence |
| --- | --- | --- |
| M1–M5 unit/UI and fault regressions | 147 passed | [Test output](unit_tests.txt) |
| Fresh 101-book application regression | 21 passed; disposable seed unchanged | [Application report](application_report.json) |
| Full history scale | 1,000 operations / 4,000 attempts; 0.031 seconds to construct panel/history on this machine | Application report |
| Real KWin 6.6.6 Wayland shutdown window-close path | Cancel and preservation scenarios passed on a private bus/runtime | [KDE report](kde_report.json) |
| Human desktop workflows | Activity/history, review/save, discard/delete, successful close and restart recovery confirmed | Checklist below |

The application run checks all 101 books, covers and format paths; title/author search; three-format grouping; Grid/List; Unknown reading status; actual single-book Save/restore; four-book bulk edit/revert; explicit import preview, real copy import and independent review status after history deletion; recovery without writes; fresh-process discovery; grouped attention counts and scale. The import fixture adds one book, so the prepared desktop library contains 102 books. No original library was used or modified.

Earlier stage evidence supplies additional partial-write, corrupt-index, interrupted-cleanup, registration-failure and alternate-destination tests: [M5-05](../m5_05_actions/README.md), [M5-06](../m5_06_emergency/README.md). All corresponding unit tests were rerun in the 147-test suite.

## KDE findings

Installed KWin/Plasma version: 6.6.6; native Wayland. The isolated test invokes KWin's actual `closeWaylandWindows` method on its own private D-Bus session and virtual Wayland socket. It never invokes host logout, poweroff, login1 or systemd session shutdown. It verifies that Cancel retains the dirty Hub/editor and KWin waits, while Save → Retry → emergency preservation accepts the close.

Both runs observed zero Qt `commitDataRequest` signals: native Wayland delivered window-close requests. This matches the [KDE shutdown implementation](https://github.com/KDE/plasma-workspace/blob/master/startkde/plasma-shutdown/shutdown.cpp) and [KWin close handling](https://github.com/KDE/kwin/blob/master/src/sm.cpp). Qt's session-management callback remains supported for environments that deliver it; it is not the sole Wayland protection mechanism.

The real KWin test exposed and verified a fix for duplicate Save prompts when KWin closes the Hub and editor separately. A completed Hub close now grants only its current protected editor revision permission to finish closing. Editing afterward invalidates that permission. Final KDE evidence records exactly one Save and one Retry Save, with no duplicate Save prompt.

This is real compositor-protocol testing, not a full logout of the user's desktop. In a host KDE logout, cancelling the application close keeps its draft open; KDE may also offer **Cancel Logout** or **Log Out Anyway**. Choose Cancel Logout to stop logout. Forcing logout can override cooperative application protection. The host logout/poweroff sequence has not been run.

## Human desktop checklist — acceptance confirmed

Launch from the project directory:

```sh
python3 tests/launch_m5_desktop.py
```

The launcher requires all automated application checks to pass and uses only the prepared disposable library, settings and recovery data. A lock prevents two acceptance windows from sharing this fixture.

1. **Activity/history — USER CONFIRMED:** Confirm one startup recovery summary, grouped operations, counts and detailed outcomes. Dismiss the Single-book recovery item, then find it through Full History with Show dismissed. Confirm the recovery is still available.
2. **Review/save — USER CONFIRMED:** Choose Review / Retry for that recovery. Confirm the proposed `M5 Desktop Recovery` tag appears as an unsaved draft; choose Save and verify completion. Close the editor.
3. **Discard/delete safeguards — USER CONFIRMED:** Review the pending Bulk edits entry without confirming execution. Return to Activity details, choose Discard Pending and confirm its warning. Confirm Delete History becomes available afterward. Cancel deletion and verify the history remains. These steps do not undo already committed library results.
4. **Emergency close/restart — USER CONFIRMED:** Successful close and restart recovery were confirmed; no editor opened and no cover was applied automatically. Reproduction steps: Close the acceptance Hub, then run:

   ```sh
   python3 tests/launch_m5_desktop.py --emergency
   ```

   A valid cover and a blocked *test-only* backup destination are prepared. Click Save, then Retry. Confirm the failed cover is preserved, ordinary editing stays open and the message distinguishes preservation from saving to the library. Close the Hub and choose Save if prompted. Confirm it closes after preservation. Reopen the normal launcher and confirm the recovery summary appears without automatically applying the cover.
5. **KDE scope — USER CONFIRMED:** The user accepts the isolated real KWin evidence as sufficient. A host logout test is not required; host logout/poweroff was not performed.

The recorded user results complete M5-07. The subsequent requested final evidence review closes M5-G; all 11 criteria pass.

## Reproduce automated checks

```sh
QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s tests
QT_QPA_PLATFORM=offscreen python3 tests/verify_m5_acceptance.py
python3 tests/verify_m5_kde.py
```

Calibre/readers must be closed for integration checks. Sandbox approval may be required for Calibre's local lock and the private KWin session. Rerunning application verification creates a fresh disposable copy and resets the desktop fixture; do not rerun it while a desktop acceptance window is open.

## Close-time lifecycle regression

The first desktop session aborted during closure because a snapshot worker was still running when its owning widgets were destroyed. Accepted close now suppresses queued automatic refreshes, stops the refresh timer, cancels the owned read and joins its snapshot worker before widget destruction. Cancel restores normal refresh behavior. Three added regressions pass in the 147-test suite; both isolated KWin scenarios pass again. The user confirmed the corrected desktop close, and the launcher exited with code 0. The user also confirmed recovery discovery after restart without automatic editor opening or cover application.
