# M5-04 — Hub Activity presentation verification

Current disposition: **M5 COMPLETE; M5-G PASSED / CLOSED**. [Final gate review](../m5_acceptance/gate_review.md). The stage status and remaining-work notes below record the state at that earlier verification.

Status: implementation complete; 93 unit/UI tests passed. M5-G remains OPEN pending the remaining implementation and application acceptance. No release or final desktop acceptance is claimed.

Run:

```sh
QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s tests
```

Evidence: [test output](unit_tests.txt), [Hub rendering](hub_activity.png), [full-history rendering](full_history.png). Screenshots use synthetic records in a fresh temporary application-data folder. No original Calibre library was read or written for these presentation checks. Earlier real-Calibre integration evidence remains in [M5-03](../m5_03_integration/README.md).

Eight additional tests cover:

- Live counts without double counting overlapping pending/failed/recovery indicators; default expanded panel and collapse/expand.
- One summary, session-only dismissal, retained pending records and notice on a subsequent session.
- Latest actual failure and success retained across interruption; links open the selected attempt.
- Full history includes resolved and dismissed operations, with dismissed/unresolved filters.
- Read-only detail/history navigation, including counts, items, errors, library and next steps; literal text is not interpreted as HTML.
- Visible storage-corruption notice and preservation of the damaged file.
- Summary visible above the selected Book-inator tab; Open Activity selects the Hub; no import dialog opens automatically.
- Local pending journals discovered when Book-inator stays closed, without opening Calibre.

Review Recovery currently opens unresolved history for inspection. Existing Import ebooks and Bulk edit / history remain the routes to their review workflows. Shared Retry, task Dismiss, Discard Pending and Delete History controls belong to M5-05. Automatic emergency preservation and requested-close continuation remain M5-06. The startup banner's Dismiss does not dismiss individual tasks or discard work.
