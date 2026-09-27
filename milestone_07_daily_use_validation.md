# M7 — Personal Daily-Use Validation

**M7 planned testing COMPLETE; M7-G CONDITIONALLY ACCEPTED.** The owner confirms all planned tests passed and authorizes subsequent work to proceed immediately for business reasons. The seven-day normal-use observation remains an outstanding, non-blocking condition; it has not been completed or waived. RC1 remains frozen. Future milestone gates use explicit tests and pass/fail criteria, with no mandatory elapsed-time requirement. Nothing was published. [Acceptance decision](test_data/m7_daily_use/conditional_acceptance.md).

## Goal and boundary

Establish whether the accepted package can be used reliably every day in the owner's normal Ubuntu 26.04.1 KDE account. Install the accepted package inside a Docker container, with durable host-backed test data. This user decision supersedes native normal-account application installation. Native KDE windows are confirmed, with a host KDE menu shortcut launching the Docker-contained application. Native display and KDE menu integration are qualified in M7-02. Start with a dedicated testing library. Retain M6's exact dependency compatibility, private-copy browsing, original-file opening, exclusive-access restrictions and always-redacted diagnostics.

Include reading, title/author search, imports, single-book metadata edits, bulk edits/revert, Activity/recovery, repeated startup/close, upgrade and removal/reinstallation with retained data. Exercise existing file associations only if applicable; adding associations or changing default readers is not authorized by this scope.

During the formal week no new features, UI changes or schema changes are permitted. Only fixes for critical defects preventing normal use may be implemented; any candidate change restarts the period. Noncritical defects and usability improvements are recorded for later. The owner additionally approved pre-trial Compose, a self-contained local bundle and tested backup/restore scripts. Capture feature requests separately for later consideration. No new modules, built-in backup feature, synchronization, external testers, public release or major architectural changes are approved. M8 small-tester validation is a possible later decision, not committed scope.

## Library and preservation sequence

1. Inventory the normal-account installation, settings and application data before installation. Preserve existing state and avoid conflicts with acceptance sessions. Use the accepted artifact checksum from the M6 gate review.
2. Create a durable dedicated testing library and independent source fixtures. Do not depend on temporary acceptance directories for a week-long trial.
3. Validate backup/restore and existing recovery procedures using test data. Use manual copies of the complete test library and application data/configuration, including settings, history and recovery. Close writers before copying. Restore into a separate isolated location without overwriting the original test environment. Verify metadata, books, settings and indexes remain intact and usable; document a repeatable procedure and evidence. This does not introduce product backup controls. Restored settings/journal paths must be inspected before opening or retrying work so they cannot target the original environment.
4. Once confidence is established, a copied snapshot of the real library may supply additional validation. Record its source and verify source preservation. Never substitute the live library silently. Live-library use is outside this milestone's agreed test sequence.
5. Removal/reinstallation affects program integration only. Demonstrate retained settings, library data, history and recovery. Do not deliberately damage the sole copy of valuable data to test recovery.

## Validation period

The user approved **seven consecutive days of normal use on the final candidate build**, with a brief daily-use record. Record artifact hash, runtime versions, dates, workflows, observations and defects. Time passing alone is not evidence of use; historical M6 tests do not count toward the week.

Any code, package or configuration fix that changes the candidate build resets the period. Day 1 begins again on the first day using the corrected build. Documentation-only changes outside the packaged candidate do not reset it; a rebuilt candidate with changed packaged documentation does. Routine user preference changes are normal-use testing, not candidate-build fixes. Record the candidate SHA-256 and all resets. Do not start the clock until the working installation and dedicated test environment are ready. A day without recorded normal use cannot count toward seven consecutive use days.

Distribute reading, search, imports, metadata editing, bulk edit/revert and recovery checks across the period. Include routine menu launch and close/reopen cycles. Record non-use days honestly. Preserve completed observations when restarting a trial; identify which build each observation tested.

## Work plan

| ID | Status | Work and evidence |
| --- | --- | --- |
| M7-01 | DONE | [Existing-state inventory and durable test/backup/restore locations prepared](test_data/m7_daily_use/preparation.md); 101-book copy and accepted artifact preserved. |
| M7-02 | DONE | Prepare Docker deployment and qualify exact runtime, GUI access, filesystem locking and persistent mounts; install accepted package inside container and verify agreed KDE access, dependencies and restart. |
| M7-03 | DONE — [evidence](test_data/m7_daily_use/manual_restore.md) | Validate agreed backup/restore procedure, existing recovery, upgrade and removal/reinstallation using preserved testing data. Record exact artifacts and retained-data checks. |
| M7-RC1 | QUALIFIED / FROZEN; personal handoff confirmed | [Compose, local bundle and backup/restore scripts](test_data/m7_daily_use/rc1_pretrial.md); 18 extracted-bundle checks passed. |
| M7-04 | TESTS COMPLETE — normal-use observation remains a non-blocking follow-up | Conduct and log the full one-week normal-use period on the final candidate. Optional additional copied-real-library validation follows initial confidence. |
| M7-05 | Planned-test findings reviewed; observation findings remain follow-up | Triage findings; during the trial fix only critical defects preventing normal use, verify the fix and restart the period. Backlog noncritical/usability requests and new features. |
| M7-06 | Conditional acceptance recorded; final observation sign-off pending | Update known limitations, review all evidence and obtain personal sign-off before formal M7-G closure. |

M7-04/05 may repeat. Installation is approved within M7 scope, but work must respect filesystem permission requirements and preserve existing normal-account data. No installation has been performed merely by recording this plan.

## M7-G acceptance

Owner decision: all planned tests passed. M7-G is conditionally accepted, authorizing further work immediately. G06 remains pending as a non-blocking observation condition; G08 is conditional rather than unconditional final sign-off. See [decision](test_data/m7_daily_use/conditional_acceptance.md).

- [ ] G01: Docker-contained installation, persistent data mounts and agreed KDE access work with correct version and verified dependencies; container replacement preserves data.
- [ ] G02: Routine reading, search, import, metadata and bulk workflows operate reliably on the dedicated test library.
- [ ] G03: Restart/reopen preserves settings and history; pending work never resumes automatically.
- [ ] G04: Manual library/application-data backup and separate-location restore succeed; books, metadata, settings and indexes are complete and usable, source environment untouched, and procedure repeatable/documented. Existing recovery passes with no unresolved data-loss or recovery defects.
- [ ] G05: Upgrade/removal/reinstallation preserve usable libraries, settings, history and recovery data.
- [ ] G06: Final candidate completes seven consecutive days of recorded normal use; code/package/configuration fixes changing the build restart Day 1. Build identity, daily outcomes and reset history are recorded.
- [ ] G07: No unresolved critical defects; known limitations and noncritical findings have explicit dispositions. Feature requests remain outside M7.
- [ ] G08: Owner accepts the final results; evidence and instructions are current. Publication and external testing remain separate decisions.

Links: [M6 closure](test_data/m6_07_acceptance/gate_review.md), [living implementation plan](implementation_plan_hub_bookinator.md), [first-release scope](first_release_scope.md).

Tracking: [daily-use log and defect register](test_data/m7_daily_use/README.md). Day 1 baseline and Day 2 focus evidence are recorded; no full calendar day has been completed yet.

Deployment change: Docker installation requested after M7 scope approval. [M7-01 evidence and Docker handoff](test_data/m7_daily_use/preparation.md). Docker is not currently available at the inspected CLI/default socket. Container setup and SQLite writable-access qualification remain M7-02; no installation or trial has started.

Testing/development separation: the authoritative M7 root is now `../Mediaintor-M7-Testing/`, with independent package, library, persistent home, backup/restore and evidence locations. [Verified separation](test_data/m7_daily_use/separation_report.json). Docker must install from its pinned local artifact, with no development-checkout mount or automatic rebuild. Development branches may change independently; only changes to the tested candidate restart its trial. Container installation remains pending.

Display decision: user selected native KDE windows. Hub and Calibre viewer run inside the container and display on the host KDE desktop. No browser desktop is planned. M7-02 must verify display access, reader lifecycle and menu launch without mounting the development checkout.

M7-02 checkpoint: Docker build/entrypoint/verification/native-Wayland launcher files are prepared in the independent testing directory, syntax-checked but not built or runtime-qualified. Host SQLite write/lock and normal read-only catalog checks pass outside the sandbox. Docker is still absent; administrator installation requires the user to run commands in Konsole. Image build, exact-runtime checks, viewer/display acceptance, menu integration and persistence remain pending. [Setup status](test_data/m7_daily_use/docker_setup_status.json).

Docker installation update: user supplied successful Docker 29.1.3 Client/Server output. Normal-user access remains denied (not a docker-group member), so image build and KDE launcher validation await account access setup. M7-02 remains IN PROGRESS.

Latest M7-02 checkpoint: Docker 29.1.3 is available to the normal user. The pinned independent image is built and package 0.1.0a1 installed into its persistent home. Exact runtime/Calibre versions, native Wayland connection, SQLite locking, 101-book integrity, private snapshot and disposable Calibre write/read-back/restore pass. Host KDE menu entry installed; running-container mounts exclude the source checkout and live library. Personal catalog/viewer/menu-restart confirmation is pending. [Current setup evidence](test_data/m7_daily_use/docker_setup_status.json). Earlier installation-blocker notes are historical. Seven-day trial NOT STARTED; M7-G OPEN.

M7-02 COMPLETE: user confirmed all three desktop checks — native 101-book catalog, EPUB/MOBI/PDF viewer navigation/close behavior, and KDE menu relaunch retaining List view. Automated and personal evidence is in the [setup report](test_data/m7_daily_use/docker_setup_status.json). Earlier checkpoint statuses are historical. Next: M7-03 manual backup/isolated restore, recovery and retained-data lifecycle validation. Seven-day trial NOT STARTED; M7-G OPEN.

M7-03 COMPLETE: 16 copy/restore/recovery/lifecycle checks passed. Found and fixed M7-DEF-001 (helper-generated bytecode blocked installer integrity checks); corrected candidate is installed with retained-data hashes unchanged. [Procedure, fix and build identity](test_data/m7_daily_use/manual_restore.md). Existing suite (177 tests) plus the new helper-inventory regression passed. Original M6 artifact remains historical; no publication. Trial remains unstarted; next is a brief corrected-build smoke check and M7-04 Day 1 agreement.

Corrected candidate personal smoke check PASSED: user confirms KDE menu launch, catalog and book navigation. Ready for M7-04 start-date agreement. Trial remains NOT STARTED; M7-G OPEN.

Owner proposed seven daily themes and additional Compose/packaging work. [Adapted proposed schedule](test_data/m7_daily_use/seven_day_schedule.md) separates preparation from fixed-build validation. Decisions on Compose/local bundle, security scope and backup scripts await clarification; no expansion, version bump or publication is assumed. The trial remains unstarted.

Latest scope decision supersedes earlier pending-addition notes: owner approved RC1 Compose/deployment bundle and backup/restore scripts before Day 1. [RC1 freeze and evidence](test_data/m7_daily_use/rc1_pretrial.md). Git tagging unavailable (no repository); checksums identify the candidate. Personal Compose handoff pending; trial NOT STARTED and M7-G OPEN. No publication.

Trial handoff rule confirmed: only the six user-defined RC1 startup/reader/restart/persistence/no-manual-Docker checks precede counting Day 1. Proposed start: 2026-09-22, conditional on personal confirmation that all six passed; earliest Day 7: 2026-09-28 if uninterrupted. No additional development is required for handoff. The sample PASS log is an example, not completed daily evidence. [Start record](test_data/m7_daily_use/trial_start.json).

Current trial status: user confirmed all six RC1 checks and authorized Day 1 on 2026-09-22. Earliest Day 7 is 2026-09-28 if uninterrupted. [Daily log and rules](test_data/m7_daily_use/README.md). No completed day is inferred; M7-G OPEN. Earlier pending-start notes are historical.
