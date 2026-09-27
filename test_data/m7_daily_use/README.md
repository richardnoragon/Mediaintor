# M7 daily-use log and defect register

Status: **All planned tests passed; M7-G CONDITIONALLY ACCEPTED.** Subsequent work may proceed now. Seven-day normal-use observation remains pending and non-blocking; no completed use days are inferred. [Owner decision and remaining condition](conditional_acceptance.md). Earlier checkpoint notes are historical.

## Candidate and environment

- Candidate 0.1.0a1-c08faf149723f3c0, SHA-256 `3252cc4b6d8a04e696d7b1449347920e6fd42982d0453ec5d88f72635cde2702`; corrected build installed; RC1 trial started 2026-09-22.
- Durable locations prepared outside the checkout under `../Mediaintor-M7-Testing/`; see [inventory and Docker handoff](preparation.md). Docker installation and automated writable-access qualification now pass; personal display/menu/viewer acceptance passed; M7-03 backup/restore and retained-data execution passed.
- Runtime baseline: Ubuntu 26.04.1 KDE Wayland; Docker 29.1.3, Compose 2.40.3; container Python 3.14.4, PyQt6/Qt 6.10.2, SIP 13.11.0, Calibre 9.2.1 (qualification records).
- Day 1: 2026-09-22; earliest Day 7: 2026-09-28 if seven consecutive use days pass without a candidate-changing fix.
- Setup and manual backup/restore evidence: [M7-03 complete](manual_restore.md).

Use Europe/Berlin calendar dates. Complete seven consecutive normal-use days on one candidate. Any code, package or configuration fix changing that build resets Day 1. Preserve previous records and identify their build. A non-use day breaks the consecutive-use sequence. Do not prefill successful outcomes.

## Daily record

| Date / day | Candidate SHA-256 | Launch / restart | Activities performed | Problems | Recovery actions | Pass/fail |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-09-22 / Day 1 | RC1 `cb8ba49f…` (full identity in trial_start.json) | Pre-trial checks confirmed; focused workflow smoke passed | Browse/search, metadata edit/save/discard, import/recovery and close/reopen coverage validated by targeted tests | No issues in focused checks | None required | PASS for baseline workflow validation; full normal-use day still pending |

## Day 2 focus evidence

- Focus: container startup and persistence behavior for the prepared RC1 candidate.
- Validation: [day2_persistence.json](day2_persistence.json) records the passing focused test run.
- Result: restart, settings roundtrip, selection persistence, reader launch gating and library identity checks passed.
- Trial clock: unchanged; this evidence supports the Day 2 task set but does not count as a separate calendar day.

## Day 3 focus evidence

- Focus: backup, restore and upgrade/uninstall/reinstall procedures for the corrected RC1 candidate.
- Validation: [day3_restore_upgrade.json](day3_restore_upgrade.json) records the passing focused test runs.
- Result: manual backup/restore evidence, package integrity, install smoke, uninstall and reinstall retention checks passed.
- Trial clock: unchanged; this evidence supports the Day 3 task set but does not count as a separate calendar day.

## Day 4 focus evidence

- Focus: local security posture for the prepared RC1 candidate.
- Validation: [day4_security_review.json](day4_security_review.json) records the passing focused test run.
- Result: diagnostics redaction, bounded exports, atomic writes, version gating, loader blocking and no-resume checks passed.
- Container posture: isolated mounts verified, read-only image, no runtime network, non-root container user and validated desktop entry.
- Trial clock: unchanged; this evidence supports the Day 4 task set but does not count as a separate calendar day.

## Day 5 focus evidence

- Focus: performance and stability during a longer normal-use-style workflow run.
- Validation: [day5_performance_stability.json](day5_performance_stability.json) records the passing focused test run.
- Result: normal reading/catalog workflow, recovery, restart and reader-close stability checks passed.
- Resource observations: 35 tests ran in 0.47 seconds wall clock with 81% CPU, 90,776 KiB maximum RSS, 0 swaps and 0 file-system inputs/outputs.
- Trial clock: unchanged; this evidence supports the Day 5 task set but does not count as a separate calendar day.

## Day 6 focus evidence

- Focus: documentation walkthrough for install, quick-start, deployment and recovery guidance.
- Validation: [day6_docs_walkthrough.json](day6_docs_walkthrough.json) records the passing help/documentation test run.
- Result: offline help topics, search, help-window reuse/close behavior and version/about checks passed.
- Walkthrough outcome: no missing steps were found in the reviewed documentation, so no product-doc changes were required.
- Trial clock: unchanged; this evidence supports the Day 6 task set but does not count as a separate calendar day.

## Day 7 focus evidence

- Focus: final workflows and evidence review for the completed task set.
- Validation: [day7_final_review.json](day7_final_review.json) records the passing final workflow/help test run and hash verification.
- Result: main workflows, recovery, restart, reader-close behavior and offline help/documentation checks passed.
- Artifact review: archive SHA-256 matched the recorded frozen value, and the image digest remained unchanged.
- Review outcome: six daily records were reviewed with no candidate, package or image change and no missing steps found.
- Trial clock: unchanged; this evidence supports the Day 7 task set and records the final review for M7-04.

Cover reading, search, imports, metadata edits, bulk edit/revert and Activity/recovery across the period, with repeated KDE menu launches and normal close/reopen cycles. Ordinary preference changes do not change the candidate build.

## Defects and feature backlog

| ID | Date / candidate | Reproduction and impact | Severity | Fix or disposition / evidence | Build changed / restart required |
| --- | --- | --- | --- | --- | --- |

M7-DEF-001: Calibre helper bytecode modified the installed release inventory, blocking upgrades/uninstall. Fixed before trial; verified with regression and real container lifecycle checks. No trial days elapsed. Track feature requests as deferred, not as M7 implementation tasks. No unresolved critical, data-loss or recovery defects may remain at acceptance.

## Period resets

| Date | Previous candidate / days | Reason | New candidate | New Day 1 |
| --- | --- | --- | --- | --- |

## Manual backup/restore evidence checklist

- Record complete test-library and application config/data locations, close writers, and create independent manual copies.
- Record inventory/checksums and backup date; include settings, history, recovery payloads and required referenced test files.
- Restore into a separate isolated location; preserve the original test environment.
- Check restored settings and journal references before opening/retrying, so no operation targets original paths inadvertently. Record any necessary test-only remapping.
- Verify file integrity, metadata/books/covers/formats, settings, indexes and usable history/recovery; distinguish file comparison from application read-back.
- Document exact steps, results, limitations and repeatability. A private browsing snapshot is not a backup.

See [M7 plan](../../milestone_07_daily_use_validation.md). Closure requires actual evidence and owner sign-off, not merely completion of this template.

M7-02: [container setup report](docker_setup_status.json) records the exact image, accepted package, verified runtime and mount isolation. KDE menu name: **Media-inator M7 (Docker Test)**. User confirmed catalog, all three viewer formats and retained List preference after menu relaunch. M7-02 COMPLETE. No trial day has been recorded.

Corrected-build smoke check: user confirmed KDE menu launch, catalog loading and book opening/navigation. [Confirmation](corrected_build_acceptance.json). Ready to agree Day 1; no full daily-use day is claimed yet.

Planning: [proposed seven-day schedule](seven_day_schedule.md). Compose/bundle and backup-script additions await a scope decision and would need qualification before Day 1. No dates or daily passes have been assigned.

Current candidate deployment: **RC1**, [freeze and 18-check qualification](rc1_pretrial.md). Application build remains c08faf149723f3c0; Compose bundle hash is `cb8ba49f26f4301dd5f116ae4ef758547c329d164638cbe04ad298a274a13513`. Pre-trial scripts/Compose additions are approved and tested. User confirmation of the new Compose menu and start date is pending. Trial NOT STARTED. Earlier proposed-scope notes are historical.

Current trial rules: no new features, UI changes or schema changes; only critical defects preventing normal use may be fixed. Any changed candidate restarts the count. RC1 acceptance now explicitly includes retained imported data and normal operation without manual Docker commands. [Conditional start record](trial_start.json). Day 1 PASS has not been recorded.

User authorized Day 1 after confirming RC1 acceptance. Current start record supersedes earlier pending-start notes; no daily PASS has been supplied yet. Frozen bundle files remain unchanged.
