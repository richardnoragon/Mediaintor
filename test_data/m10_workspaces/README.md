# M10 isolated workspace development

**M10 COMPLETE; M10-G PASSED / CLOSED.** [Final gate review](gate_review.md): automated verification and all owner desktop checks passed for installed build `0.1.0a1-a3a4679f39f4c255`. RC1/M9 remain unchanged. Nothing published. Earlier progress notes below are historical.

- [Technical design](../../technical_design_m10.md): owned/schema-validated storage, atomic persistence, named-state rules, restore sequencing, shared filters, reader protection and monitor fallback.
- [Setup evidence](setup.json): quiet-source M9 backup, verified independent restore, unchanged source comparison, installed inventory and packaged startup smoke passed.
- Separate root: `../Mediaintor-M10-Development/`; Compose project `mediainator-m10`.
- KDE launcher: **Media-inator M10 Development**. It now opens M10 workspace candidate `0.1.0a1-a3a4679f39f4c255`.
- Writable state is exclusively the M10 copied home/library/import-sources; existing internal paths preserve references. Runtime and candidate/installer mounts are pinned/read-only. No source checkout mount, no NAS or live library.
- Original baseline build was `0.1.0a1-184039712b870efd`; exact immutable runtime image reused without retagging. No upgrade to M9 or RC1.
- Backups retained under the new M10 root. Smoke checks used disposable offscreen windows; personal M10 KDE workspace acceptance is later.

M10-03 complete: [implementation and regression evidence](m10_03.md). Subsequent restoration work is recorded below. Future development builds must update only M10's package and explicit expected-build verifier, never the accepted M9/RC1 environments.

M10-04 core restoration, startup and automatic Last Session integration is complete in source. [Evidence and remaining robustness boundary](m10_04.md). Subsequent failure-path work is recorded below. No installed environment upgraded.

M10-05 failure-path/asynchronous restore protections and automated monitor recovery checks complete: [evidence](m10_05.md), 213-test regression passed. M10-06 package evidence follows. No physical monitor test or gate closure is implied.

M10-06 complete: [review and exact candidate](m10_06.md), [installed report](m10_06_package.json). **Next: M10-07**; no personal KDE acceptance or M10-G closure is claimed.

M10-07 in progress: [installation and 443 retained-file checks](m10_07_install.json), [pending desktop acceptance](m10_07_desktop.json). A verified pre-upgrade backup retains the original M10 deployment and data. RC1/M9 were not mounted or changed.

M10-07 owner confirms catalog/reader use, Last Session restart and named-workspace startup all passed on the installed candidate. Remaining management, protection, monitor and workflow checks are pending; M10-G remains open.

Owner also confirms named-workspace management/capacity, hidden selection with shared filters, and unsaved Save/Discard/Cancel all passed. Six desktop groups now have owner confirmation; busy operations, reader independence, KDE monitor recovery and installed workflow regressions remain pending. M10-G stays open.

Owner confirms reader independence and busy-operation protection passed. Monitor success is reported, with the actual test method awaiting clarification because the preceding question asked monitor availability. Installed import/bulk/recovery regressions remain pending. M10-G remains open.

Monitor clarification received: owner physically disconnected the docking station and external display during the previously reported successful test. Monitor recovery is recorded as passed. Final import/bulk/recovery acceptance fixtures are prepared using the installed candidate after a verified quiet backup; library database unchanged during preparation. See [fixture report](m10_07_workflow_fixtures.json). Workflow results and M10-G remain pending.

Final import/read, bulk-edit/revert and recovery/history checks: owner confirms all three passed. [Desktop acceptance](m10_07_desktop.json), [final integrity verification](m10_07_final_integrity.json). M10-07 and M10-G are closed.
