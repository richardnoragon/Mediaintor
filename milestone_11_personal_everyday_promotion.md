# M11 — Promote M10 for Personal Everyday Use

Status: **M11 COMPLETE; M11-G PASSED / CLOSED.** Correct-installation desktop acceptance and stored evidence verified. [Final review](test_data/m11_promotion/gate_review.md).

## Objective

Promote the accepted M10 package into a separate personal everyday installation using Docker and native KDE windows, preserving current M10 user state and its copied test library. Complete promotion and acceptance before new feature development.

## Approved decisions

- Reuse accepted build `0.1.0a1-a3a4679f39f4c255`, archive SHA-256 `edc96793ca09a37db7a15bbd1036db96f2c771cff43b16563796590a8805b1f4`. Verify identity against [M10 closure](test_data/m10_workspaces/gate_review.md); no rebuild is needed for promotion.
- Retain the proven Docker runtime and native KDE display integration, with a distinct everyday-use launcher.
- Copy the current M10 local test library into the new environment. Do not share writable library, configuration or application-data paths with M10.
- Preserve settings, named workspaces, Last Session, preferences, per-format reading positions, bookmarks/annotations where present, history and recovery records. Validate library/book and profile/device identities before accepting copied references.
- Review acceptance-test books, tags and workspaces before cleanup. Retain all items by default; remove only specifically identified items the owner confirms obsolete, and only from the everyday copy using supported operations. This approval does not authorize blanket removal based on names. Unresolved recovery remains protected by existing review/discard requirements.
- Make a verified current backup before promotion. Earlier M10 snapshots predate acceptance changes and are not substitutes for the current source snapshot.
- Keep RC1, M9 and accepted M10 unchanged and available. Restore/rollback validation uses additional isolated copies; do not downgrade or overwrite newer everyday data.
- Personal use only. Existing Calibre compatibility and protected-access rules remain, including private-copy browsing, original-format launching and closed Calibre/readers during protected operations.
- M11-G is based on demonstrated behavior and owner acceptance, with no minimum observation period. M7's independent observation condition is unchanged.

## Deployment plan

Accepted target: sibling `../Mediaintor-M11-Everyday/`, separate Compose project `mediainator-m11`, KDE launcher **Media-inator Everyday (M11)**. Validate that these destinations are unused before creating them; do not overwrite a pre-existing installation.

Keep existing internal container paths where possible so copied references remain valid. Pin the accepted image/package and maintain separate writable mounts. Retain accepted launchers alongside the new one. Review test artifacts in the copied environment, without editing the accepted source.

## Work plan

| Task | Status | Required result |
| --- | --- | --- |
| M11-01 — inventory and promotion design | COMPLETE — source discrepancy identified; see evidence | Read-only inspection of installation, artifact, source data, identities and references; inventory cleanup candidates and unresolved recovery; confirm available storage and unused target paths. |
| M11-02 — verified backup and independent copy | COMPLETE — hashes verified; source unchanged | Coordinate normal Hub/reader closure, verify writers stopped, snapshot current M10, verify hashes and restore into separate M11 state; verify source unchanged. |
| M11-03 — everyday deployment and launcher | COMPLETE — installed package and owner KDE restart verified | Install exact accepted package in the isolated M11 Docker deployment; verify runtime/inventory, native KDE startup and dedicated launcher without altering accepted environments. |
| M11-04 — preservation and cleanup review | COMPLETE — owner chose current backed-up M11 baseline; all items retained | Verify library/formats, settings, workspaces, progress and history/recovery references; present specific cleanup candidates. Retain unapproved items; record any confirmed cleanup and validation. No new removal feature. |
| M11-05 — backup recovery and rollback | COMPLETE — isolated restore/fallback and current-state validation passed | Back up M11 state; restore into a distinct location and verify readable books, metadata, settings, workspaces and recovery. Test fallback/return using isolated copies and document how to preserve newer state. |
| M11-06 — personal KDE acceptance | COMPLETE — fresh desktop checks and stored results verified | Owner validates launcher/restart, reading, editing, import, workspace restore and recovery/history in the everyday copy; record exact build and results. |
| M11-07 — final evidence review | COMPLETE — final gate review recorded | Reconcile all checks, retained limitations, cleanup decisions and isolation evidence; close M11-G only after required results pass. |

## M11-G acceptance

- [x] Exact accepted package installs and passes runtime/inventory checks.
- [x] Dedicated KDE launcher starts and reopens the correct everyday environment.
- [x] Current copied library and user state are preserved, with valid identity references.
- [x] Reading, editing and importing work under the existing protected-access rules.
- [x] Last Session and named workspace restoration work; shared filters and reader behavior remain consistent.
- [x] Recovery/history remains accessible and no pending work automatically resumes.
- [x] Manual backup restores successfully to an isolated location, retaining usable data.
- [x] Isolated rollback/fallback and return procedures pass without overwriting newer data.
- [x] Cleanup review is recorded; unapproved items remain intact.
- [x] RC1, M9 and accepted M10 remain unchanged; owner acceptance and known limitations are recorded.

## Excluded

New features, major architectural changes, NAS integration, live NAS writes, library restructuring, multiple users, additional media modules, external testers, publication and distribution. Later feature work or NAS adoption requires a separate milestone decision.

Current evidence: [final gate review](test_data/m11_promotion/gate_review.md). M11-G passed / closed.
