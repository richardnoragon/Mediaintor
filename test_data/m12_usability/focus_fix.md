# M12 KDE recovery focus follow-up

Owner clarified that no second Review / Retry was required: clicking the Hub background revealed the draft. This suggests visibility/activation rather than failure to reconstruct the draft. Runtime logs did not show an error.

Ready recovery presentation now hides matching read-only Activity details and history, then shows, raises and activates the editor and focuses the title. Preserved data remains unchanged; no Save is triggered. Existing metadata review also uses this handoff. The activity history can be reopened normally.

220 source regression tests passed, including Activity visibility assertions in the recovery handoff scenario. Nine isolated package checks passed, including 61 installed test executions. Offscreen verification does not prove Wayland focus; owner KDE retest remains required.

Replacement build: `0.1.0a1-254fe2288bf7b39a`.
SHA-256: `e799506e5f2127b03063d8b6b8358b7802fa71ad38928f00eea70543c106ca4a`.
[Package checks](focus_package_verification.json), [installation/backup](installed_focus_candidate.json), [regression](focus_regression.log).

Previous artifact is retained under dist/m12; replacement under dist/m12-focus. Only M12 upgraded after normal close and verified backup. M11 unchanged. M12-G OPEN; no promotion.
