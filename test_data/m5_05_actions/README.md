# M5-05 — Shared recovery actions

Current disposition: **M5 COMPLETE; M5-G PASSED / CLOSED**. [Final gate review](../m5_acceptance/gate_review.md). The stage status and remaining-work notes below record the state at that earlier verification.

Status: **M5-05 DONE/CLOSED** for its implementation scope. **M5-G OPEN**. Automatic emergency preservation/close handling remain M5-06; full desktop acceptance remains M5-07.

Evidence:

- [Unit/UI output](unit_tests.txt): 119 tests passed, including 26 additional shared-action tests.
- [Disposable Calibre report](report.json): 13 checks passed on a fresh copy of the M5-03 disposable fixture; seed hashes unchanged. The original library was not used.
- [Rendered Activity actions](recovery_actions.png): unresolved work has Delete History disabled. This is offscreen evidence, not user desktop acceptance.

Reproduce unit/UI tests:

```sh
QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s tests
```

Reproduce the integration checks while Calibre/readers are closed:

```sh
QT_QPA_PLATFORM=offscreen python3 tests/verify_m5_actions.py
```

The script requires the earlier disposable seed from the M5-03 report and never substitutes the original library if it is unavailable. Calibre's local lock mechanism may require execution outside the sandbox. It creates a new `/tmp/mediainator-m5-05-*` library for every run.

## Verified safeguards

Review selects a specific import/bulk journal, reconciles uncertain writes and never executes pending catalog changes. Recovery reconstructs a single-book draft and detects real external conflicts; a separate Save commits it and resolves the preserved copy. Partial Save keeps only the unfinished fields. No-op resolution rereads current values. Registration failures do not claim successful recovery.

Dismiss survives restart without losing payload/history/retry. Discard requires a matching review revision and refuses uncertain writes. Cancel applies no discard/deletion. Completed fields/imports and past failure outcomes remain. Discarding a local recovered draft does not abandon its durable copy.

Delete is separate from discard and blocks unresolved recovery. Import metadata-review provenance survives deletion. Cleanup intents survive failed unlink/index updates; retry checks owned paths/content hashes and retains changed files. Known alternate-location generations are cleaned only after resolution. Deletion markers prevent stale history projections from resurrecting removed entries. Revert descendants remain independent and display that their ancestor history was removed.

Reader retry cancellation never launches a reader. Busy operations and cancelled metadata review block conflicting routes. Opening history/details/startup summary never starts work.

## Remaining stage boundaries

M5-06 must implement automatic initial emergency preservation after failed Save/Retry and automatic continuation of an already-requested close. M5-07 must run the full application/desktop acceptance workflow. No M5-G acceptance boxes are marked passed by this stage alone.
