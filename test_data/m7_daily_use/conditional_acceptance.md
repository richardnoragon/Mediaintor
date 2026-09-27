# M7-G conditional acceptance — 2026-09-22

The owner confirms that all planned tests have been performed, logged and passed. For business reasons, planned testing is closed and M7-G is **CONDITIONALLY ACCEPTED**. Subsequent work may proceed immediately.

## Evidence and limitation

- [Test record and findings](README.md): setup, workflows, persistence, recovery and focused task checks.
- [RC1 qualification](rc1_pretrial.md): frozen deployment and acceptance evidence.
- [Backup, restore and retained-data validation](manual_restore.md).
- [Final focused review](day7_final_review.json).

These tests do not demonstrate seven consecutive days of normal use. The observation period has neither been completed nor waived. No daily PASS results are created by this decision. No unresolved critical defect is recorded; new findings must be assessed when reported.

## Remaining condition and next steps

1. Continue normal-use observation on frozen RC1 and record actual dates, activities and findings in the daily log. This does not block subsequent development or milestone planning.
2. Keep subsequent development separate from the frozen candidate. A change to the observed candidate restarts its observation under the existing M7 rule.
3. Once the seven-day observation is complete, review findings and record final owner sign-off to remove the condition. Until then, report M7-G as conditionally accepted, not unconditionally passed.

## Future milestone policy

Future gates are based on explicit, reproducible tests and pass/fail acceptance criteria, without mandatory calendar-duration requirements. Once required tests pass and findings meet the agreed acceptance criteria, work can proceed. Observation may be collected as non-blocking follow-up. This policy does not erase M7's explicitly retained condition.

This decision changes planning and acceptance records only. It does not change the frozen package, publish a release, or authorize an external tester program.
