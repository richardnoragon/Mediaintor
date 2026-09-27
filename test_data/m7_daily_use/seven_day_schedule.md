# Proposed M7 seven-day schedule

**RC1 pre-trial additions approved, implemented and qualified; personal handoff/start date pending. No trial days completed. M7-G OPEN.**

[Current RC1 evidence](rc1_pretrial.md) supersedes the pending-addition discussion below. Daily themes remain the proposed schedule; no authentication/TLS scope was added.

This adapts the owner's suggested daily themes to the approved personal, native-KDE Docker application. The final candidate must receive seven consecutive days of use. Creating or changing its Docker/Compose configuration, application package or runtime during the week resets Day 1. Development work in the separate checkout does not reset the trial unless adopted into the tested candidate.

## Preparation before Day 1

Already complete: independent test locations, Dockerfile/image, persistent container home/library, native KDE menu launch, exact-runtime qualification, manual backup/isolated restore, recovery and retained-data upgrade/uninstall/reinstall tests. A helper-cache defect was fixed and the corrected candidate passed a personal smoke check.

Pending decisions:

- Add Compose and a local deployment bundle before Day 1, or validate the existing launcher. Compose is proposed additional deployment work, not yet implemented or accepted.
- Keep security review within local desktop scope. Authentication, authorization services, TLS and reverse proxies are not current application features; introducing them would require a separate scope decision.
- Keep approved manual-copy recovery instructions, or explicitly expand scope to tested backup/restore scripts before Day 1. No script additions are assumed.

If Compose is selected, qualify its fresh installation, UID/GID and Wayland access, persistent mounts, single-instance behavior, image identity and compatibility checks before starting the week. Environment variables should configure necessary deployment paths/identity only; they must not override application compatibility guards. Any .env example must contain placeholders, not private paths or credentials.

The proposed `docker compose up -d` experience must state its prerequisites: a compatible Linux/KDE Wayland session, Docker/Compose availability and configured display/persistent paths. This is a native desktop application, not a browser service. Do not promise that command is sufficient on an arbitrary machine. A future distribution bundle must be tested as an independent artifact before making such a claim.

## Daily schedule

Every day: launch from the agreed KDE entry point, perform some normal library/reading work, close/reopen as appropriate, and record date, candidate identity, activities, problems, recovery actions and pass/fail. The themes below supplement normal use; paperwork alone is not a use day.

| Day | Focus | Actions and evidence |
| --- | --- | --- |
| 1 | Core workflow and baseline | Confirm installed build/runtime; browse/search, open a book, edit/save/discard metadata; record manual steps, limitations and baseline responsiveness. Installation itself is preparation, not work deferred into the trial. |
| 2 | Container startup and persistence | Validate the already-prepared deployment in a fresh test home; reopen the daily environment, confirm persistent settings/history and container replacement behavior. Do not rebuild the candidate. |
| 3 | Backup, restore and upgrade procedures | Follow the documented manual-copy procedure with writers closed; use a separate restore and verify books/metadata/settings/recovery. Use the existing distinct-build upgrade fixture only in isolation, ending on the fixed candidate. Do not change the daily-use candidate to an unvalidated newer build. |
| 4 | Local security review | Review container user, mounts, network exposure, access permissions and redacted diagnostics. Optionally run a dependency/image scan with a recorded tool/database date and triage findings; no automatic remediation or “no vulnerabilities” claim from scan absence. No authentication/TLS service implementation. |
| 5 | Performance and stability | Record CPU/memory/disk observations during normal reading and catalog operations, a longer session and repeated orderly restarts. Unexpected-termination tests belong only in a separately backed-up disposable environment; never deliberately interrupt the sole active copy. Verify recovery and data integrity afterwards. |
| 6 | Documentation walkthrough | Follow installation/quick-start/deployment/recovery instructions while using the fixed candidate; correct external documentation and record missing steps. Changes inside the packaged candidate require a restarted trial. |
| 7 | Final workflows and evidence review | Repeat main workflows, review issues/limitations and the seven daily records. Verify candidate/package/image hashes remain the same. Inventory existing local artifacts; do not create a different release candidate and count it as week-tested. Request M7-G review only after actual completion. |

## Packaging and publication boundary

A Compose file, .env example, local archive, backup.sh and restore.sh are proposals, not delivered artifacts. Any approved additions must be prepared and qualified before the week. There is no approved 1.0.0 version bump, tester program or publication. Producing a local package and distributing it are separate actions. A new package created on Day 7 does not inherit seven-day acceptance automatically.

Keep [daily evidence](README.md), [defect/restore evidence](manual_restore.md), and the [M7 scope](../../milestone_07_daily_use_validation.md) aligned. Choose dates after the preparation decisions are settled. No short automated run can substitute for seven days of personal use.
