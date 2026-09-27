# M8-G final evidence review and closure

**M8 COMPLETE; M8-G PASSED / CLOSED.** Owner confirmed “all three issues pass” for the installed KDE acceptance checks and previously authorized closure when all tests pass. Final evidence review completed; no unresolved reported blocking defects. No publication is implied.

Candidate: **0.1.0a1-184039712b870efd**. Archive SHA-256: `a649ebab6fe334929cc2e42e15ab998710cf5bdcc776d24242de4bccd3d96b14`.

| Criterion | Evidence / current disposition |
| --- | --- |
| Explicit scope and tests | Approved M8 specification, search tests, progress probes and acceptance examples recorded. |
| Isolation | Separate installed-acceptance home and copied library; private namespace excludes source checkout, RC1 and active M8. Installed file hashes verified. |
| Viewer focus | Owner previously passed EPUB/MOBI/PDF immediate readability and first-arrow navigation. Original issue not reproduced; no claimed focus patch. Installed desktop navigation also passed. |
| Search/filtering | AND/OR rules, series matching, both views, persistence and Clear All automated tests pass. Source-run desktop checks passed. Installed automated restart restores two matching tag-filtered books. Personal installed menu/restart checks passed. |
| Progress/resume | Three-format desktop independence passed; real Calibre rename and persistent provenance probes passed. Source-run integrated rename desktop acceptance passed. Installed rename desktop check passed. |
| Regression | 185-test suite passed; eight installed-package automated checks passed. |
| Defect disposition | Reported refresh blocker closed after owner confirmed success; controlled save/refresh reproduction also passed. No remaining reported blocking defect. |
| Final owner acceptance | Owner confirms all three installed KDE checks passed; recorded in installed_desktop_acceptance.json. |

## Accepted scope limits and review qualifications

- Percentage and status remain Unknown where the verified source lacks them; saved-position availability is independent.
- Equal reliable timestamps show tied formats rather than an invented unique latest format.
- Unobserved external renames, changed format contents, missing history and invalid records do not establish safe rename handoff.
- Tests cover the 101-book fixture; large-library performance is not qualified.
- Installed namespace uses the verified host dependencies; it is not a clean-OS installation test.
- Existing compatibility/exclusive-access requirements remain; no override is added.

## Closure decision

All eight gate criteria are satisfied by the recorded automated and personal evidence, with the scope limits above retained. The owner explicitly confirmed all three installed checks passed. Archive hash was rechecked at closure and matched the accepted candidate. No rebuild, promotion into active M8, RC1 change, or publication was performed.

Evidence: [installed owner acceptance](installed_desktop_acceptance.json), [eight installed automated checks](installed_verification.json), [185-test regression](regression_final.txt), [16 disposable capability checks](progress_edge_results.json), and earlier three-format/integrated desktop records.

M8-01–M8-07 are complete. The initial-keypress defect did not reproduce in accepted desktop tests; closure records verified behavior, not an invented root cause or patch. M7-G remains conditionally accepted with its separate observation condition outstanding. Future milestone definition or distribution requires its own scope decision.
