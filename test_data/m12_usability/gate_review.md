# M12-G final evidence review — PASSED / CLOSED

Decision: M12 complete, M12-G passed/closed on 2026-09-23. Personal-use acceptance only. No promotion, publication or replacement of M11.

Accepted build: `0.1.0a1-f59e8af9b043f304`.
Archive SHA-256: `21af3e215de06a32d1088ad6a980f189407af99b5dcbce3074d081448aad458b`.
All 44 installed manifest files match the verified artifact.

## Evidence

- [Source regression](workspace_feedback_regression.log): 223 tests passed, including safe busy deferral, asynchronous restore completion and real failure reporting.
- [Isolated package verification](workspace_package_verification.json): nine checks passed, including 64 installed targeted tests, installation/reinstallation, retained-data uninstall and no checkout/original library mounted.
- [Upgrade](installed_workspace_candidate.json): verified pre-upgrade backup, 459 retained files unchanged and runtime smoke passed.
- [Desktop acceptance](desktop_acceptance.json): owner screenshots/confirmations demonstrate installation identity, first-click recovered draft visibility, explicit Save with book/field feedback, resolved recovery, workspace restoration, distinct bulk preview/cancellation/completion, actual tag-add/revert, import preview/confirmation, readable EPUB, viewer controls, normal close and KDE menu restart.
- [Final readback](final_saved_data.json): 103 books; imported EPUB exists; original source hash unchanged; import journal complete; Quick Start Guide recovery tag saved and recovery state recovered; Persuasion original tags restored with edit/revert journals complete; named workspace, Last Session selection and imported reading position retained.
- M11 protection: all 622 baseline file hashes checked unchanged. M12 operations did not mount or upgrade RC1/M9/M10/M11.

## Evidence boundaries

Recovery focus and Save were personally accepted on the preceding focus-fix build. Recovery actions, editor, main window and feedback components are byte-identical in the final archive; final installed tests and persisted-result checks corroborate that evidence. Workspace correction and bulk/import/restart were personally accepted on the final build.

Existing regression coverage combines automated tests and prior accepted baseline evidence with targeted current desktop workflows. This review does not claim every failure was manually injected on KDE. The single-page import fixture proves launch and readable rendering, not multipage navigation. Isolated package tests use installed host dependencies rather than a newly installed operating system.

## Known usability follow-ups

- Repeated generic button labels and dense dialogs remain confusing; directions currently identify exact windows and control locations. This has not been fixed by the workspace change and should be considered in the next usability milestone.
- Owner reports the file picker supports pasting a path or folder navigation, but not direct path typing in their workflow. Instructions should reflect this; cause not independently reproduced.
- Bulk history does not automatically select the latest completed batch; users must explicitly select the intended batch before reverting.
- Window title “preview required” remains static after completion; the result message gives the actual verified operation state.

These observations do not invalidate the verified M12 recovery/data-protection and outcome-reporting requirements. They remain documented follow-up work rather than claims of a friction-free interface.

No further M12 gate-blocking acceptance checks remain. Promotion remains a separate owner decision; M11 stays the everyday reference.
