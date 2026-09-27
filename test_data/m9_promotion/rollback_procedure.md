# M9 snapshot rollback and return procedure

Verified by [runner](verify_migration_rollback.py) and [results](migration_rollback_results.json).

1. Close the M9 Hub/readers normally and verify no writer mounts the target environment. Take a new consistent backup of the newer state before an actual future rollback. Never overwrite it with older data.
2. Restore `backups/pre-upgrade-c08faf149723f3c0` into a NEW separate destination using the verified backup/restore utility. It refuses existing/overlapping destinations.
3. Run the restored installation with that destination's home/library/import-sources mounts at the same internal paths. The tested `rollback-check` copy launched old build `0.1.0a1-c08faf149723f3c0` successfully.
4. Keep the current M9 active environment and post-upgrade backup separate. Old software must not run against newer application data as an assumed-compatible in-place downgrade.
5. Return by selecting the preserved M9 environment, or explicitly upgrade the rollback copy using the verified accepted archive. The latter was tested: `rollback-check` upgraded to `0.1.0a1-184039712b870efd` and its packaged startup passed.
6. Compare data hashes and verify library integrity. The automated test confirmed unchanged rollback-library bytes, unchanged M9 active bytes, and unchanged M8 source bytes. No cross-version merge of edits made after rollback is implied.

M9 active remains the current validation environment. The rollback/functional copies contain validation artifacts and must not be mistaken for authoritative user-state sources. No automatic fallback or silent data replacement is configured.
