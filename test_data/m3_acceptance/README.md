# M3-G application acceptance

Status: **M3 and M3-G COMPLETE for the agreed scope.** Implementation, automated verification and all three user desktop confirmations passed.

## Automated evidence

- [Unit/workflow results](unit_tests.txt): 50 passing tests, including the 41 prior M1/M2 tests and nine import planning/journal/review cases.
- [Real application report](application_report.json): 23 passing checks through the actual import dialog and Calibre subprocess helper. Preview/no-write, EPUB creation, MOBI/PDF attachment, duplicate protection, isolated invalid input, fallback flags, changed source/library refusal, fresh preview, partial-record repair, stop/restart, same-journal retry, commit-before-ack reconciliation and preservation checks.
- [101-book hub report](catalog_report.json): five checks passed. Import increased count to 102; review filtering, saved completeness, persistent review status and explicit Mark Reviewed worked through the real hub/editor.
- [Import screenshot](imports.png), [catalog screenshot](catalog.png).
- Original library and prepared input fixtures were unchanged by the integration run. Mutation targets were new temporary libraries.

The initial enhanced application run exposed a journal bug in partial-record repair: a completed repair did not copy its destination UUID into the result. It was fixed; the full 23-check run passed afterwards. Stale source extraction and similar-title detection were also included in the final helper checks. Test runs requiring Calibre's lock socket ran with authorization outside the sandbox.

## Desktop review

The user completed review in a separate clearly labelled disposable window. [Session](desktop_session.json), [confirmed answers](desktop_confirmation.json).

1. Mandatory preview, fallback warning and explicit confirmation/import: **user confirmed correct**.
2. Completeness and user-controlled review status: **user confirmed correct**, including explicit Mark Reviewed.
3. Imported/attached EPUB, MOBI and PDF readable and navigable through the hub: **all three user confirmed**.

No original-library use is required for these confirmations. The test record “Externally changed after preview” is a copy of The Time Machine with three imported/attached formats.

## Reproduce

```sh
QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s tests -v
QT_QPA_PLATFORM=offscreen python3 tests/verify_m3_application.py
QT_QPA_PLATFORM=offscreen python3 tests/verify_m3_catalog.py
```

The integration scripts require the prepared fixtures/baseline in `test_data/m3_validation/workspace.json`; recreate them if temporary storage has disappeared. They create new disposable targets. Runtime Calibre version is 9.2.1. Capability/protocol tests alone do not substitute for these application checks or final desktop confirmation.

## Closure

M3-01–M3-07 and M3-G01–M3-G11 are complete within the documented scope. Final user answers are recorded in desktop_confirmation.json. M4 Bulk Metadata Editing is next for detailed planning; M5 remains Hub Activity / Recovery. No release or schema migration of hub settings was performed. New import journals have their own version-1 schema.
