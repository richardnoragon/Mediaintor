# Import responsiveness and progress feedback — open owner findings

Build: `0.1.0a1-594c20d70805c834`. Evidence: owner report and screenshot during KDE acceptance, 2026-09-23. M13-G remains OPEN; original acceptance criteria unchanged.

## M13-IMPORT-RESPONSIVENESS-01 — slow response

Owner confirms typed text appears in File or folder path but reports that response is slow. Screenshot shows `/data/` and a completed preview containing import sources and existing library files, including non-ebook files. It does not establish whether the delay occurred during keystroke display, directory discovery, metadata inspection or table rendering. No duration measured; cause unconfirmed.

Action: reproduce and measure input latency separately from preview preparation/rendering, using one file and a broad directory on isolated data. Inspect GUI-thread work, event handling and directory traversal. Improve the measured bottleneck while preserving validation and explicit write confirmation. Check that typing alone does not launch a scan; establish whether the owner clicked Preview path or pressed Enter.

Verification: repeat the reported KDE interaction, record timing and input responsiveness, and confirm no import occurs without explicit confirmation. Do not invent a numeric acceptance threshold or mark performance accepted from this screenshot.

## M13-IMPORT-PROGRESS-01 — no apparent loading indicator

Owner reports no loading indicator during the delay. Screenshot captures only the completed preview, so it cannot establish which transient title/status was visible while preparing it.

Action: provide promptly painted, persistent preparation feedback while discovery/validation/rendering runs; use an indeterminate indicator when total work is unknown, and meaningful counts only when available. Ensure the interface remains responsive and distinguishes preparation from import execution. Check stop/cancel labels against their actual scope.

Verification: exercise a sufficiently long preview in installed KDE and confirm visible feedback throughout, correct transition to preview/error, no stale indicator, and unchanged preview/confirmation safeguards.

## Related observation to investigate

The `/data/` preview includes the existing library and non-ebook files. This is not evidence of an import or data loss: the UI says no files imported. Investigate scan scope, invalid-file presentation and accidental activation/default-button behavior. Avoid confirming this broad preview. Clarify triggering input before assigning a root cause.

## Owner clarification

The delay occurs **after clicking Preview path**, not while typing. The owner explicitly clicked Preview; this report does not demonstrate accidental activation. The submitted path was `/data/`, and the resulting preview includes import sources and library files. Focus investigation on directory discovery, validation/metadata inspection and table rendering; measure these phases separately. Missing visible loading feedback applies to this preview-preparation interval. Exact duration and bottleneck remain unmeasured.

## Single-file comparison

Owner reports previewing `/data/import-sources/M13 Final Acceptance.epub` was almost instantaneous and faster than the prior `/data/` preview. This is a qualitative comparison, not a timed benchmark. The reported slowdown is associated with the broad directory preview; no general text-input or single-file latency defect is established. Investigate discovery, per-file validation and rendering cost as directory size grows. M13-IMPORT-RESPONSIVENESS-01 remains open for broad-folder diagnosis; M13-IMPORT-PROGRESS-01 remains open for visible feedback during longer previews.

## Installed KDE retest — 2026-09-24

On build ffbaa166eaebf2fe, owner reports /data/ preview took roughly two seconds and showed an activity indicator and preparation messages during the wait. M13-IMPORT-PROGRESS-01 resolved. Broad-folder performance improvement has owner-observed timing evidence; this is not an instrumented benchmark or a new numeric acceptance criterion. Confirm owner considers responsiveness acceptable before closing M13-IMPORT-RESPONSIVENESS-01.

Owner explicitly confirmed the response time feels appropriate for everyday use. M13-IMPORT-RESPONSIVENESS-01 resolved on 2026-09-24. This acceptance applies to the observed KDE workflow, not a universal performance guarantee. M13-G remains open for the other outstanding checks.
