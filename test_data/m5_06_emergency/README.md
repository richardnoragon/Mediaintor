# M5-06 — Automatic emergency preservation and close handling

Current disposition: **M5 COMPLETE; M5-G PASSED / CLOSED**. [Final gate review](../m5_acceptance/gate_review.md). The stage status and remaining-work notes below record the state at that earlier verification.

Status: **M5-06 DONE** for its implementation scope. **M5-G OPEN**; full application and desktop acceptance remain M5-07.

Evidence:

- [Unit/UI results](unit_tests.txt): 143 tests passed, including 24 added emergency/close tests.
- [Real-Calibre report](report.json): all 14 checks passed on a fresh copy of the M5-05 disposable fixture. Seed hashes unchanged; the original library was not used.

Reproduce:

```sh
QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s tests
QT_QPA_PLATFORM=offscreen python3 tests/verify_m5_emergency.py
```

The integration script requires the prior disposable fixture and closed Calibre/readers. It never substitutes the original library if the fixture is missing. Calibre's local locking mechanism may require execution outside the sandbox.

## Verified behavior

First failed Save retains the draft without automatic preservation. A failed explicit Retry preserves it durably and leaves ordinary editing open. A requested editor/tab/Hub close continues automatically after current-revision protection succeeds. Cancel/Keep Editing leaves no latent close intent. Settings-save failure still blocks Hub exit. Combined reader-review cancellation performs no writes or reader close requests.

Changed drafts and missing copies invalidate old protection. Invalid input, invalid cover images and cancelled conflicts do not count as failed writes. Registration failure keeps closure blocked even if a payload file exists. Alternate-location preservation keeps the same recovery identity, requires registration, and can complete the requested close. Cancelling the location picker retains the draft.

Pending cover bytes and description content are embedded. Partial save successes are excluded from emergency payloads; later verified Save resolves the preserved copy. Successful Save or discard clears old preservation-failure attention without erasing historical failures. Restart discovers copies without replay or automatic recovery dialogs.

The real adapter test uses a valid image and deliberately places a file at the test cover-backup directory path. This creates a storage failure after the title is saved. The original cover remains unchanged, only the pending cover is preserved, the requested Hub close succeeds, and restart discovers the copy without applying it. An initial invalid-image experiment was rejected before writes; the final test correctly exercises storage failure, and a unit test now prevents invalid images from counting as failed writes.

## Acceptance limits

Cooperative Qt session-manager callbacks are unit-tested, including cancellation when interaction is unavailable and work is outstanding. Actual KDE/Wayland logout delivery, visual desktop flows and the full M5 acceptance checklist remain M5-07. Forced termination or power loss before successful preservation is not covered by draft autosave. No M5-G boxes are passed by this stage alone; no release was published.
