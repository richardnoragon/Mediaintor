# M11 backup, isolated fallback and return

Validated against build `0.1.0a1-a3a4679f39f4c255`.

- `../Mediaintor-M11-Everyday/backups/m10-promotion-source/`: verified current M10 snapshot at promotion.
- `../Mediaintor-M11-Everyday/backups/m11-installed/`: verified initial M11 snapshot after explicit installation and data checks.
- `restore-validation/`: independent restore of M11 state; package smoke, library integrity, formats/covers, identities, workspace/progress and recovery/history checks passed.
- `fallback-validation/`: independent restore of the pre-promotion source; same checks passed. Promotion reuses the exact same accepted package, so this validates snapshot fallback, not a version downgrade.

Before any later rollback, close Hub/readers normally and create a fresh verified snapshot of current M11 state. Existing backups do not contain later edits/imports. Restore into a new unused directory, configure a separate Compose project with identical internal paths and distinct host mounts, and validate before launch. Never point two running deployments at the same writable state.

Return to the preserved current M11 state or another fresh isolated restore of it. Do not copy old settings/databases over newer data and do not treat the accepted M10 source as disposable. Tested restore/fallback operations left M10 and active M11 unchanged; RC1/M9 were not mounted.

Personal native KDE use of the promoted installation remains pending. Automated restore checks used offscreen package smoke plus installed data validation, not simulated owner confirmation.
