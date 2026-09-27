# Media-inator Hub and Book-inator — Living Implementation Plan

**M14 — Library Discovery & Metadata Productivity: M14-01–M14-07 complete; development build installed with 255 source and 107 installed tests passing; M14-08 owner KDE acceptance pending; M14-G OPEN.** [Approved scope and tasks](milestone_14_library_discovery_metadata_productivity.md). Discovery first, metadata review second; approximately 10,000-book acceptance target. M13-G is CLOSED and **Media-inator Everyday (M13)** is promoted; M12 is retained as Rollback. [M13 acceptance](test_data/m13_workflows/final_acceptance.md) and [promotion](test_data/m13_workflows/promotion.md). M15 remains provisional. No publication.

**M12 — Everyday Usability and Reliability COMPLETE; M12-G PASSED / CLOSED.** Accepted installed build `0.1.0a1-f59e8af9b043f304`: 223 source tests, 64 installed targeted tests, personal KDE acceptance and final saved-data verification passed. [Final gate review and known usability follow-ups](test_data/m12_usability/gate_review.md). M11 unchanged; no publication. Owner-authorized [everyday promotion is complete](test_data/m12_usability/promotion.md); accepted package and current data retained.

**M11 — Promote M10 for Personal Everyday Use COMPLETE; M11-G PASSED / CLOSED.** Use **Media-inator Everyday (M11)**. Exact accepted M10 build installed separately; backup/restore, owner KDE checks and persisted workspace/import/edit/bulk-revert/recovery results verified. [Final gate review](test_data/m11_promotion/gate_review.md). RC1/M9/M10 retained; no publication. Next: personal use or define M12.

**M10 — Hub Workspace Save and Restore COMPLETE; M10-G PASSED / CLOSED.** Accepted build `0.1.0a1-a3a4679f39f4c255`: 215 regression tests, isolated package verification, installed KDE workspace/monitor acceptance and final import/bulk/recovery checks passed. [Final gate review](test_data/m10_workspaces/gate_review.md). RC1 and M9 remain unchanged; nothing published. M11 promotion scope is now approved.

**M9 — Everyday Installation and Safe Upgrade COMPLETE; M9-G PASSED / CLOSED.** Accepted M8 package installed and validated in the separate Docker/KDE test environment, with verified data preservation, snapshot rollback/return and owner desktop acceptance. [Final review](test_data/m9_promotion/gate_review.md). RC1 and the M8 source remain unchanged; M7 observation remains independent. No NAS/live-library deployment or publication.

**M8 — Book-inator Everyday Usability COMPLETE; M8-G PASSED / CLOSED.** Owner confirms all three installed KDE checks passed for candidate `0.1.0a1-184039712b870efd`. Search/filter persistence, progress display and rename/resume are accepted, backed by 185 regression tests, 16 disposable probes and eight installed checks. [Final gate review](test_data/m8_usability/gate_review.md). RC1 and M7 observation remain unchanged; nothing published.

**M7 planned testing COMPLETE; M7-G CONDITIONALLY ACCEPTED.** The owner confirms all planned tests passed and authorizes subsequent work to proceed immediately for business reasons. The seven-day normal-use observation remains an outstanding, non-blocking condition; it has not been completed or waived. RC1 remains frozen. Future milestone gates use explicit tests and pass/fail criteria, with no mandatory elapsed-time requirement. Nothing was published. [Acceptance decision](test_data/m7_daily_use/conditional_acceptance.md).

Current status: **M6 COMPLETE; M6-G PASSED / CLOSED (2026-09-22).** All M6-01–M6-07 tasks are complete. [M6-G closure review](test_data/m6_07_acceptance/gate_review.md). Version remains 0.1.0a1; nothing published. Earlier checkpoint notes are historical.

Completed milestone: **M6 — First Release Readiness**, approved for personal use on Ubuntu 26.04.1 with KDE: per-user installation only, protected operations blocked for unverified Calibre versions without an override, and always-redacted diagnostics with no sensitive-detail opt-in. [Scope, tasks and M6-G](milestone_06_release_readiness.md). M6-01 [technical design](technical_design_m6.md) is complete; M6-02 [package build and isolated-user verification](test_data/m6_package/README.md) is complete; M6-03 [compatibility guards and first-run guidance](test_data/m6_03_compatibility/README.md) is complete; M6-04 [help, instructions and error polish](test_data/m6_04_help/README.md) is complete; M6-05 [always-redacted diagnostic export](test_data/m6_05_diagnostics/README.md) is complete; M6-06 [installation, upgrade and retention verification](test_data/m6_06_installation/README.md) is complete; M6-07 is COMPLETE: [installed application/KWin checks and personal desktop acceptance passed](test_data/m6_07_acceptance/README.md). M6-G is PASSED / CLOSED following final evidence review. No release published; publishing requires separate instruction.

Current M5 status: **M5 COMPLETE; M5-G PASSED / CLOSED** following final evidence review and user desktop acceptance. [Gate review](test_data/m5_acceptance/gate_review.md). All M5-01–M5-07 tasks are complete. Earlier dated/stage checkpoints are historical; no release is implied.

Status: **M1–M5 COMPLETE for their agreed scopes. G1/G2, M3-G, M4-G and M5-G passed.** M4 desktop acceptance is user-confirmed. M5 Hub Activity / Recovery technical design and disposable protocol validation are complete; M5-03 production integration is complete; M5-04 Activity UI is complete; M5-05 shared recovery actions are complete; M5-06 emergency preservation/close handling is complete; M5-07 automated application/KWin checks pass and desktop acceptance is user-confirmed; M5-01–M5-07 are DONE, with M5-G PASSED / CLOSED; broader first-release phases remain open.

This document turns the agreed product direction into an ordered implementation backlog. It does not itself start coding, choose an unverified technology stack, or declare every planned feature part of the first release. Update it as decisions, implementation, and verification progress.

## 1. Target and governing documents

Build for the project owner's personal use on one device running Ubuntu 26.04.1 LTS with KDE, with the hub as entry point and Book-inator as the first module. Test with approximately 100 books from the existing Calibre library. EPUB, MOBI, and PDF are the initial formats; paper books, audiobooks, other modules, and multi-device synchronisation are later work.

The required book workflow is manual drag-and-drop or recursive folder intake, previewed copy/move/rename operations, management of the existing Calibre library, import of available Calibre metadata and reading information, metadata write-back, automatic refresh, and reading through Calibre's e-book viewer.

Authority and detailed requirements:

- [First-release scope](first_release_scope.md).
- [Hub constitution](mediaintor%20hub/constitution_hub.md), [overview](mediaintor%20hub/mediainator%20hub%20overview.md), [features](mediaintor%20hub/mediainator%20hub%20features.md), and [configuration](mediaintor%20hub/mediainator%20hub%20config.md).
- [Book-inator constitution](bookinator/bookinator_constituion.md).
- Existing [book overview](bookinator/bookinator%20overview.md), [features](bookinator/bookinator%20features.md), and [configuration](bookinator/bookinator%20config.md) are reference-product captures. Preserve them as references; create clearly identified first-party specifications during Phase 0.
- [Versioning policy](Versioning/Versioning%20%20Standard%20%20Policy.md) and [enforcement checklist](Versioning/Versioning%20%20Enforcement%20Checklist.md).

User decisions override this proposed sequencing. A feature deferred from an early milestone remains a requirement in the backlog unless explicitly removed. In particular, personal use does not silently remove shared collections, multiple profiles, or any agreed hub behaviour.

## 2. How to maintain this plan

Use task IDs permanently. Task states are **TODO**, **ACTIVE**, **BLOCKED**, **DONE**, and **DEFERRED**. Unchecked tasks are TODO unless another status is recorded. Checked planning tasks have their evidence linked; they do not imply implementation is complete. Mark completion only with a deliverable and verification evidence; planning a task is not completing it.

After each work session:

1. Update the active task and completed checkboxes.
2. Record changed decisions, the affected requirements, and evidence paths or commit references.
3. Record blockers with the next action, not just the symptom.
4. Update “Next work session” with the next executable task.
5. Add a progress-log entry. Reopen affected tasks if later changes invalidate their verification.

Each phase uses three passes: **A — decide/design**, **B — implement after coding is authorised**, **C — verify and document**. Use additional numbered passes for fixes; do not repeat successful checks without a relevant change or unresolved concern.

Do not invent implementation dates or estimates. Assign them after the technical direction and first usable milestone are defined. The user owns product decisions; the implementer records execution and evidence. Routine implementation details within agreed scope do not require repeated product approval.

## 3. Current dashboard and dependencies

| Phase | Outcome | Depends on | Status |
| --- | --- | --- | --- |
| P0 | Bounded first milestone and decision register | Existing planning | ACTIVE — M1 agreed |
| P1 | Verified Calibre integration capabilities | P0 integration questions | ACTIVE — M1/M2 capabilities verified within exclusive-access policy; later intake/progress/concurrency work remains |
| P2 | Technical design and development foundation | P0, P1 | ACTIVE — M1/M2 designs and runnable foundation verified; packaging and broader architecture remain |
| P3 | Hub shell, Book-inator window, profile/settings persistence | P2 | ACTIVE — accepted M1 shell/settings complete; broader shared settings remain |
| P4 | Read existing Calibre library and browse/search books | P3, P1 read capability | ACTIVE — M1 library browsing/search accepted; broader hub search/location workflows remain |
| P5 | Metadata edits, write-back, automatic refresh, conflicts | P4, P1 write capability | DONE within M2 — implementation, automated checks and user desktop sign-off complete |
| P6 | Previewed intake and file management | P4, P5 consistency rules | ACTIVE — M3 copy-only intake accepted; move/rename and broader file operations deferred |
| P7 | Viewer sessions and reading progress | P4, P1 viewer capability | TODO |
| P8 | Saved states, exclusions, docking, panels | P3, P4, P7 | TODO |
| P9 | Unified lifecycle, task activity, emergency recovery | P5–P8 | TODO |
| P10 | Backup/restore, migration, versioning | P2 data model, P5–P9 | TODO |
| P11 | Remaining hub commitments and scope audit | P8–P10, relevant decisions | TODO |
| P12 | Ubuntu/KDE packaging, acceptance, personal pilot | Selected scope verified | TODO |

P9 is the integration pass for recovery and closing behaviour, not permission to omit protections in P5–P7. Each earlier mutating workflow must include its own failure handling before it is exercised on data. P10 release-level backup verification is not a substitute for protecting the test library before P1.

### M1 execution route

[Milestone 01](milestone_01_browse_and_read.md) is the agreed first usable increment. Execute P0, the read/launch subset of P1, the minimal P2/P3 foundation, P4 browsing, and the viewer-launch/ownership subset of P7 with applicable P9 lifecycle handling. Progress capture and shared-position logic are later P7 work. P5/P6, full P8–P11, and unneeded write experiments do not block M1. Stage the capability report accordingly while preserving checks before each later mutating phase.

## 4. Decision register

Resolve only questions needed by the next task. Keep the two explicitly deferred questions pending until their dependent phase is selected.

| ID | Decision needed | Blocks | Handling |
| --- | --- | --- | --- |
| D01 | M1 boundary settled: browse/find/open, one remembered library/profile, grid/list, automatic last session; broader release subset remains open | Release checklist | See milestone document; no progress updates or editing/intake in M1 |
| D02 | Presentation settled: one book card with format buttons, grid/list switch; identity/linking and editions still open | P2 model, P7 shared progress | Calibre-record grouping validated on 15 multi-format records; cross-record identity remains later work |
| D03 | Calibre-compatible meaning of copy/move/rename, destinations and collisions | P6 | Validate capabilities first, then present feasible product choices |
| D04 | Refresh timing, concurrent Calibre use, failed writes, available reading data | P1, P5, P7 | Capability report followed by decisions where behaviour is unresolved |
| D05 | Shared percentage updates, rereading/reset, and importing progress into a profile | P7 | User clarification; retain per-file positions |
| D06 | Working direction: Python/PyQt6 Widgets, versioned JSON settings, in-memory catalog, Calibre command adapter; snapshot/exclusive-access strategy accepted; packaging and integration validation open | P2 | See M1 technical design; validation gates remain |
| D07 | Emergency destination/retention and application to single-module closure | P9 | User clarification |
| D08 | Backup category combinations and profile/shared-collection selection | Relevant P10 options | Explicitly deferred; ask again when this work is scheduled |
| D09 | Shared-collection approval scope and editor rights | Shared editing in P11 | Explicitly deferred; ask again when this work is scheduled |
| D10 | Remaining defaults, named-state device handling, presets, retention | Relevant P3/P8/P9 controls | Decide progressively; do not import reference-product defaults |

Decisions already settled must not be reopened without a conflict: identical contents alone define duplicates; skip/report them. Reading progress is shared within a profile, with percentage/status and separate per-file positions when exact mapping fails. Conflicting metadata edits require a comparison and user choice.

## 5. Phased work

### P0 — Turn scope into a buildable milestone

- [ ] **P0-A1:** Write first-party Book-inator requirements separate from the captured Booknizer pages; classify each feature as agreed initial scope, agreed later scope, candidate, or unresolved.
- [x] **P0-A2:** M1 scope agreed and documented: hub startup → one remembered Calibre library → grid/list browsing and finding books → selected-format viewer launch. Evidence: [Milestone 01](milestone_01_browse_and_read.md), including workflow, deferrals, and acceptance checklist. No coding completed.
- [ ] **P0-A3:** Define the next milestone M2: edit/write back metadata → automatic refresh/conflict handling → preview and complete an import → inspect its result.
- [ ] **P0-A4:** Decide D01/D02 and write acceptance examples for M1/M2. Keep named states, full docking, richer panels, sharing, and other hub commitments explicitly scheduled rather than silently omitted.
- [ ] **P0-C1:** Trace each agreed requirement to a phase and list remaining first-release scope decisions.

**Exit evidence:** first-party requirements, milestone boundary, decision register, and paper walkthroughs. The user has now authorized foundation implementation; G1 still gates live-library access and full workflow acceptance.

### P1 — Validate the installed Calibre environment

- [ ] **P1-A1:** Record actual OS/KDE desktop session and Calibre versions, viewer availability, library location, and supported integration interfaces using local inspection and current official documentation.
- [ ] **P1-A2:** Prepare a disposable copy of representative library data before write experiments. Include all three formats, identical bytes under different names, different contents sharing a title, multi-format books, missing files, and conflicting metadata examples.
- [ ] **P1-A3:** Produce a capability matrix for library discovery, stable record/file identity, reading metadata/covers, editing metadata, adding formats, copy/move/rename semantics, automatic change detection, concurrent use, viewer launch/position/close, and reading-progress access.
- [ ] **P1-B1:** Once coding is authorised, use small bounded experiments only for unresolved capabilities. Do not treat a prototype as production architecture.
- [ ] **P1-C1:** Document results as verified, unsupported, or unresolved, with versions and evidence. Translate unsupported operations into concrete choices for the user.

**Exit evidence:** capability report and disposable-library experiment results. Do not choose arbitrary filesystem renaming or direct Calibre database mutation as the integration method without this investigation. No assumption that EPUB/MOBI/PDF expose equivalent progress or viewer control is allowed.

### P2 — Select architecture and establish the foundation

- [ ] **P2-A1:** Record a technical decision covering language/UI toolkit, local storage, Calibre integration method, background task execution, and Ubuntu/KDE packaging, based on P1 and the docking/tray needs.
- [ ] **P2-A2:** Define conceptual entities: profile, device, collection, book identity, individual format file, Calibre identity, reading progress, per-file position, state, exclusion, task attempt, and external session ownership.
- [ ] **P2-A3:** Specify authoritative ownership of Calibre metadata versus hub settings/personal data. Define how unsaved edits coexist with refreshed values and how file locations are reconciled.
- [ ] **P2-A4:** Define integration boundaries for library access, viewer control, file operations, persistence, and task reporting. Preserve room for later sync without implementing a server or sync protocol now.
- [ ] **P2-B1:** Scaffold the chosen project, development commands, diagnostics, meaningful test infrastructure, schema migration tracking, and version metadata.
- [ ] **P2-C1:** Verify reproducible local build/start and initial persistence/migration checks. Record decisions, not just dependency names.

**Exit evidence:** architecture/data model decisions, runnable foundation, build instructions, and migration strategy. A database product alone does not satisfy future-sync planning.

### P3 — Build the smallest real hub shell

- [ ] **P3-A1:** Specify startup profile selection, first-use behaviour, module availability, immediate settings saving, and a minimal settings screen. Define how unavailable future modules are represented.
- [ ] **P3-B1:** Implement hub entry, Book-inator launching, default tabbed presentation, and profile/device identity. Do not add nonfunctional movie/music modules solely to satisfy “all modules.”
- [ ] **P3-B2:** Persist common preferences and module overrides; keep unsaved catalog edits separate. Save active session selection without shutdown overwriting it with an empty list.
- [ ] **P3-C1:** Verify restart persistence, first-use fallback, cancellation with no side effects, and no unnecessary close prompt in an idle session.

**Exit evidence:** a real hub opening Book-inator with persisted settings; no library mutation yet.

### P4 — Browse the existing library

- [ ] **P4-A1:** Define library selection, loading/empty/unavailable states, and book/file rows using D02. Specify source identifiers needed for later writes.
- [ ] **P4-B1:** Read titles, authors, tags, covers, and available reading information from the selected Calibre library without modifying it.
- [ ] **P4-B2:** Implement collection browsing and details, M1 title/author text search, Unknown for unavailable reading status, and hub search access while the module window is closed. Selecting a result opens the correct item.
- [ ] **P4-B3:** Show unavailable content with Locate / Retry / Skip; implement location/exclusion persistence before offering those persistent actions.
- [ ] **P4-C1:** Compare the approximately 100-book test collection with Calibre. Verify missing covers/metadata and unavailable files do not remove unrelated entries or prevent browsing.

**Exit evidence:** M1 browsing/search portion passes with observed import counts and documented exceptions.

### P5 — Edit metadata and refresh automatically

M2 implementation and automated evidence: [acceptance report](test_data/m2_acceptance/README.md). Checked tasks below are complete within M2; user desktop sign-off is tracked separately as M2-07. Shared suite activity presentation remains P9 work.

- [x] **P5-A1:** Specify refresh triggers, dirty-field handling, write acknowledgements, retries, and behaviour when Calibre is unavailable or in use, based on P1.
- [x] **P5-B1:** Implement title/author/tag/cover/series/series-index/comments edits and supported write-back; mark edits saved only after the relevant write succeeds.
- [x] **P5-B2:** Refresh Calibre-side changes automatically without discarding local unsaved values. Compare conflicting values and apply the user's selection.
- [x] **P5-B3:** Preserve failed edits and integrate task/error reporting. Implement the necessary recovery protection before mutation tests; complete the shared presentation in P9.
- [x] **P5-C1:** Verify both directions on the disposable library, same-field conflicts, unavailable library, failed writes, and repeated refresh without duplicate changes.

**Exit evidence:** round-trip metadata comparisons and conflict/failure results. Do not add network synchronisation to implement same-device refresh.

### P6 — Add books and manage files

- [ ] **P6-A1:** Resolve D03: where imported content goes, what move removes, supported naming rules, filename collisions, existing-library file operations, and source/destination recovery.
- [ ] **P6-B1:** Implement file drag-and-drop and folder selection with subfolders. Classify unsupported/unreadable files and show their outcomes.
- [ ] **P6-B2:** Detect identical file contents independently of filename/path; skip and report duplicates. Different contents with matching metadata are not auto-skipped duplicates.
- [ ] **P6-B3:** Build preview showing operation, source, destination, proposed name, duplicate status, and errors. Allow copy/move selection and confirmation before changes.
- [ ] **P6-B4:** Execute confirmed operations through the verified integration path. Recheck stale previews/collisions and track partial completion so retry does not repeat completed destructive actions.
- [ ] **P6-C1:** Verify recursive intake, mixed formats, renamed duplicates, different-content same-title files, cancellation, permission/space failures, and interruptions. A move must not remove its source before the agreed successful destination/library update conditions are met.

**Exit evidence:** M2 import workflow, per-file outcome report, and failure-recovery checks on the disposable library.

### P7 — Open and restore reading sessions

- [ ] **P7-A1:** Define available progress capture and D05 book identity/progress rules. Shared percentage must not be presented as an exact cross-format location.
- [ ] **P7-B1:** Open the selected file in Calibre's e-book viewer. Distinguish newly launched versus attached applications and track originating module/profile ownership.
- [ ] **P7-B2:** Restore the saved page/location where supported. For unsupported restoration, explain and offer Open normally. Retain format-specific positions alongside shared completion status/percentage.
- [ ] **P7-B3:** Implement external-session Keep open / Close behaviour, shared-application explanations, and failure choices. Sessions kept open across profile switching retain their original profile.
- [ ] **P7-C1:** Verify EPUB/MOBI/PDF separately, attached versus launched sessions, shared application use, and progress attribution across profile switching. Unsupported capabilities must have a tested fallback, not a fabricated success result.

**Exit evidence:** complete M1 reading flow and a version-specific viewer capability/fallback record.

### P8 — Complete workspace restoration and customisation

- [ ] **P8-A1:** Resolve relevant D10 defaults and document states versus reusable preference presets.
- [ ] **P8-B1:** Implement five named states, explicit state updates, automatic last session, oldest-last-saved replacement, and fallback to Restore last session if its selected named state is overwritten.
- [ ] **P8-B2:** Implement the collections-only versus playback/reading restoration choice and profile-wide saved-location maintenance.
- [ ] **P8-B3:** Implement Excluded from Restoration as suppression, restore surviving associations when re-enabled, and keep permanent association removal distinct. Maintenance must not alter save timestamps.
- [ ] **P8-B4:** Add separate/docked window arrangements, per-device geometry, monitor return behaviour, and tray minimisation only after separate-window launches.
- [ ] **P8-B5:** Add movable/resizable optional panels and five recent searches/five pinned favourites. A sixth favourite asks what to replace; a sixth named state follows its different automatic rule.
- [ ] **P8-C1:** Verify restoration after restart/profile change, excluded items in edited/deleted/overwritten states, unchanged maintenance timestamps, unavailable displays, and retained last-session progress while a named state is selected.

**Exit evidence:** state transition examples, persistence checks, and manual KDE window/tray verification.

### P9 — Integrate lifecycle, activity, and emergency recovery

- [ ] **P9-A1:** Resolve D07 and retention/partial-item decisions. Define ordering when a confirmed operation later fails; do not claim completed saves can always be undone by a later Cancel.
- [ ] **P9-B1:** Unify Save / Discard, task interruption warnings, and external Keep open / Close into one review, scoped appropriately for module closure, profile switching, or global exit.
- [ ] **P9-B2:** Complete task categories, latest success/failure links, interrupted status, Retry / Dismiss, and Show dismissed/history.
- [ ] **P9-B3:** Implement failed-save retry, emergency unsaved-edit copy, alternate destination on failure, truthful success banner, and later Review and recover edits with conflict comparison.
- [ ] **P9-B4:** Enforce external ownership rules, zero-owner close eligibility, explicit Close for all modules, attached-session boundaries, and Retry / Leave open and continue / Cancel without default force-close.
- [ ] **P9-C1:** Verify no-change/no-task/no-app exit has no prompt; pre-confirmation cancellation has no effects; task interruption retains completed work; emergency success and failure take their specified paths.

**Exit evidence:** lifecycle matrix covering all three review categories and failure branches, with recovery files verified readable and associated with the correct profile.

### P10 — Backup, restore, migrations, and release discipline

- [ ] **P10-A1:** Resolve required backup/restore details and revisit D08 only when scheduling those options. Define destination, retention, restoration conflicts, and scope before enabling controls.
- [ ] **P10-B1:** Implement selected module/suite backup scopes, settings transfer, and restoration. Keep media files, catalog/artwork/activity, settings, and emergency edits distinct.
- [ ] **P10-B2:** Track hub-owned schema changes with ordered migrations and a tested rollback/recovery path. Keep Calibre-managed structures under the verified integration contract.
- [ ] **P10-B3:** Apply the versioning policy: Semantic Versioning by default, appropriate prerelease labels, categorized changelogs mapped to commits, build identity, and release checks. Public API/container rules apply if those artifacts exist; do not introduce them just to satisfy a template.
- [ ] **P10-C1:** Restore into a separate location and verify records, artwork, settings, activity, and selected media. Verify upgrade and rollback/recovery using representative data.

**Exit evidence:** a successful restore exercise, migration evidence, version/changelog checks, and documented recovery instructions.

### P11 — Audit remaining hub commitments

- [ ] **P11-A1:** Compare implementation with every constitution section. Mark each requirement verified, open, or explicitly deferred to a named milestone.
- [ ] **P11-A2:** If shared editing is selected, revisit D09 and specify submissions, owner acceptance/rejection without alteration, and the visible record history.
- [ ] **P11-B1:** Complete selected profile/sharing, settings/preset, search/panel, and help features. Do not silently treat multi-device search-history scope as implemented on one device.
- [ ] **P11-C1:** Verify profile isolation and personal progress ownership, viewer/editor/owner behaviour where delivered, and documentation consistency.

**Exit evidence:** an honest release-scope matrix. Undelivered constitutional commitments remain tracked; shipping an early milestone does not mark the entire suite complete.

### P12 — Package, accept, and pilot personally

- [ ] **P12-A1:** Finalise the first personal release checklist from verified scope. Use the versioning rollout/migration templates proportionately for one owner and one installation.
- [ ] **P12-B1:** Produce the selected Ubuntu installation package for KDE and documented install/start/update/uninstall procedures, preserving user data according to the agreed rules.
- [ ] **P12-C1:** Run the complete workflow on the approximately 100-book test copy: startup, browse/search, viewer, progress, edits/refresh/conflicts, intake/duplicates, restoration, and backup recovery for the selected scope.
- [ ] **P12-C2:** Record startup/load/search/import measurements and agree tolerances based on the actual machine. Verify responsiveness during file operations rather than inventing unmeasured speed promises.
- [ ] **P12-C3:** Complete relevant help and release notes, list integration limits, and review the personal pilot against acceptance evidence before using the live library.

**Exit evidence:** installable personal pilot, acceptance report, recovery evidence, changelog, and a prioritised next-pass backlog. No automatic publication or wider rollout is implied.

## 6. Acceptance examples to expand during implementation

| ID | Scenario | Required result | Primary phase |
| --- | --- | --- | --- |
| A01 | Start with no user/device settings | Hub and available initial modules open in tabs | P3 |
| A02 | Search while Book-inator window is closed | Accessible results appear, closed module is indicated, selection opens the item | P4 |
| A03 | Calibre changes a locally edited field | Compare values; user chooses; no silent overwrite | P5 |
| A04 | Add identical bytes under a different name | Skip and report duplicate | P6 |
| A05 | Add different bytes with matching title/author | Do not auto-skip as duplicate | P6 |
| A06 | Cancel an import preview | No file/library changes | P6 |
| A07 | Switch formats without exact position mapping | Shared status/percentage, separate file position, no false exact-location claim | P7 |
| A08 | Keep reader open while switching profiles | Session/progress remain owned by original profile | P7/P9 |
| A09 | Repair paths in several named states | References update; save timestamps and replacement order do not | P8 |
| A10 | Re-enable excluded item after one state was overwritten | Restore surviving associations only | P8 |
| A11 | Save sixth state / pin sixth favourite | Oldest-last-saved state replaced / user chooses favourite replacement | P8 |
| A12 | External application was already open | Leave application/unrelated content open; close only hub session where supported | P9 |
| A13 | Normal save and retry fail | Emergency copy of unsaved edits; continuation only if copy succeeds | P9 |
| A14 | Emergency destination fails | Stop exit/switch and offer alternate location | P9 |
| A15 | Restore backup in separate location | Chosen backup scope is recoverable and verified | P10 |

Use focused automated checks for data identity, persistence, timestamps, conflicts, and recovery; integration checks for Calibre; and manual checks for actual KDE windows, tray, monitors, drag-and-drop, and the viewer. Do not substitute mocks for evidence that the real integration works.

## 7. Risks and responses

| Risk | Response / decision point |
| --- | --- |
| Calibre cannot support a desired rename, simultaneous edit, or reader-control operation | P1 capability evidence; revise mechanism or ask about user-visible alternatives before implementation |
| Path changes disconnect a Calibre record from its file | P1/P6 verified integration, preview, and reconciliation checks |
| Shared progress is applied to the wrong book or person | D02/D05 identity rules, session ownership, explicit conflicts, per-file positions |
| Interrupted move or stale preview loses data | P6 completion conditions, recorded outcomes, retry/recovery checks |
| New UI features indefinitely delay the first working workflow | M1/M2 vertical milestones; record later requirements explicitly |
| Prototype assumptions become undocumented architecture | P2 decisions and version-specific P1 evidence |
| Backup exists but cannot restore | P10 restore exercise before personal pilot |

## 8. Next work session

M1 is complete. See the [acceptance report](test_data/m1_acceptance/README.md). All 12 milestone acceptance criteria passed; 23 automated tests pass. The accepted snapshot/single-reader restriction and known limitations remain in force.

1. M5-G evidence review is complete: all 11 criteria passed. M6 release-readiness scope is approved. All scope decisions are confirmed. M6-01 technical design is complete. M6-02 package build and isolated-user verification are complete. M6-03 compatibility guards and first-run guidance are complete. M6-04 help, instructions and error polish are complete. M6-05 always-redacted diagnostic export is complete. M6-06 installation, upgrade and retained-data verification are complete. M6-07 full installed application and personal KDE desktop acceptance are complete. M6-G final evidence review is complete; the gate is PASSED / CLOSED. See the [closure record](test_data/m5_acceptance/gate_review.md).
2. Preserve M1–M4 passing regressions and source-preserving/exclusive-access rules. M3-G is closed with [recorded desktop acceptance](test_data/m3_acceptance/README.md).
3. M5 remains Hub Activity / Recovery. Move/rename/delete-original commands, trusted automatic imports, packaging and deferred viewer-keypress work remain outside the completed milestones.

## 9. Progress and decision log

| Entry | Work / decision | Evidence | Next action |
| --- | --- | --- | --- |
| Calibre validation pass 1 | P1/M1-01 ACTIVE; copy-based listing/search passed, EPUB rendering confirmed by user; remaining coverage documented. | [Capability report](calibre_capability_validation.md) | Clarifications now resolved; continue remaining capability checks |
| Environment/library confirmed | Target is Ubuntu 26.04.1 LTS with KDE. Existing configured library is correct; more books will be added later. Format/scale acceptance remains pending. | Capability report and first-release scope | Continue read/launch design with current sample; repeat broader checks when data is available |
| M1 technical design | Working architecture and ownership model documented; installed Python/Qt and KDE Wayland inspected. No code written. | [Technical design](technical_design_m1.md) | G1/G2 validation; later authorised scaffold |
| 2026-09-20: G1/G2 pass 2 | Copy-based listing/search caused no persistent changes; viewer annotation write isolated; simulated lock rejection and detached survival passed. User confirmed readability after a keypress; targeted handled close saved artifacts and exited. | Capability report, pass 2 | Choose production library-read boundary; later test actual hub lifecycle; keypress issue deferred to TODO-VIEWER-01 |
| Initial plan | Created phase sequence, task IDs, decision register, acceptance examples, and maintenance process. No coding tasks completed. | This document and linked requirements | P0-A1/P0-A2 |
| M1 scope agreed | User selected browse/find/open, one remembered library, one book card with format buttons, grid/list views, one profile, last-session restoration, and deferred progress updates. P0-A2 DONE. | [Milestone 01](milestone_01_browse_and_read.md) | M1-01 capability validation |
| M1 defaults confirmed | User confirmed Unknown for unavailable reading status and title/author text search; acceptance checks updated. | Milestone checks M1-A05/M1-A07 | M1-01; no coding started |

For subsequent entries record the date, task IDs, status change, deliverable or commit, verification outcome, newly discovered limitation, and next action. Put unresolved blockers beside their phase and decision ID; do not hide them in a release summary.

Supporting release templates: [rollout](Versioning/Versioning%20Rollout%20Plan%20Template.md), [migration](Versioning/Versioning%20Migration%20Plan%20Template.md), and [governance review](Versioning/Versioning%20%20Governance%20Review%20Template.md).

## Deferred viewer usability TODO

- [ ] **TODO-VIEWER-01 — Initial keypress before readable display:** Investigate why the Calibre viewer needed a keypress before the opened book became readable on KDE Wayland. User explicitly accepted deferring this annoyance; it does not block M1 or initial integration. Schedule in a later usability pass, with no milestone assigned yet. Reproduce with the installed version, distinguish focus from rendering/loading behaviour, and record the cause and remedy. Verify readable display without an extra keypress, or document any remaining external-viewer limitation. Do not assume a cause or add synthetic keypresses as an unverified workaround.

Dataset preparation (2026-09-20): imported 100 user-requested free titles using supported Calibre commands, with a pre-import backup and 120 verified file hashes. This authorizes and records test-data preparation, not application implementation or unrestricted live-library integration. P1-A2 remains partial: missing-file/conflict/duplicate fixtures and broader acceptance are still needed.

Expanded validation (2026-09-20): fresh-copy checks passed for 101 records/covers, 121 format paths, 120 imported hashes, title/author/no-result queries, and 15 multi-format groups. EPUB/MOBI/PDF viewer launches succeeded; the user confirmed readability and page navigation in all three. Concurrent launch exposed annotation database-lock errors in EPUB/PDF; the completed sequential/staggered comparison is recorded below; production contention/failure handling remains open. Evidence is linked in the capability report. No application acceptance or implementation task marked complete.

Annotation follow-up: TEST-SIMULTANEOUS bookmarks persisted locally and in the copied library for all three formats, before and after verified handled closes, with no new lock errors. User actions were staggered while three viewers were open; this does not establish simultaneous-write safety or automatic retry. The sequential control subsequently passed for all three formats; see the final comparison. See [annotation investigation](test_data/free_ebooks_100/annotation_validation/README.md).

Sequential annotation control: EPUB bookmark persistence passed in local storage and the copied library before/after handled close, with no logged lock errors. The user reused the TEST-SIMULTANEOUS label in the new isolated session; this is recorded in the evidence. MOBI and PDF subsequently passed; all test viewers are now closed. See the annotation investigation.

Sequential MOBI control: PASSED after the user completed bookmark creation. The bookmark matched local storage and the copied library before and after handled close, with no logged lock errors and unchanged source-library hashes. The earlier check found only a last-read position because bookmark creation had not yet been completed; it is not evidence of a save failure. Evidence: `test_data/free_ebooks_100/annotation_validation/sequential-mobi.json`. PDF subsequently passed; all test viewers are now closed.

Annotation comparison completed: sequential EPUB, MOBI, and PDF bookmarks matched local and copied-library storage before and after handled closure, with empty stderr for each. All test viewers closed and source-library hashes remained unchanged. With three viewers open, later staggered bookmarks also persisted without additional errors, but initial concurrent-launch BusyErrors (EPUB/PDF) remain unresolved. This supports sequential sample feasibility, not simultaneous-write safety or automatic recovery. See the [final comparison](test_data/free_ebooks_100/annotation_validation/README.md#final-comparison). G1 concurrency/failure handling and application acceptance remain open; no application code was written.

## Authorized foundation implementation

Implemented the sample-data shell and settings foundation in [source](mediainator/window.py); [run/test instructions](README.md). Six automated tests passed and an offscreen screenshot was inspected. No live-library adapter or viewer launcher is implemented. P2-B1/P2-C1, M1-02/M1-03 and relevant P4 work are ACTIVE, not DONE: remembered library selection, adapter, complete lifecycle and full acceptance remain outstanding. No application acceptance checkbox is marked complete. Step 3/G1 must precede the full 101-book application acceptance. Earlier no-code statements describe historical passes; the latest user authorization supersedes them.

Disposable integration pass: implemented an asynchronous Calibre listing adapter restricted to explicitly registered test copies, cover fallback, retained results on load failure, reload and timeout handling, and real format buttons. Single detached reader ownership (profile/module/PID/start-time) persists across restarts; missing files and second-reader requests are rejected. Reader close uses manual-close/explicit leave-open fallback, not automatic signaling. Twelve automated tests passed and a real one-book-copy Qt/Calibre adapter smoke check passed. Live-library selection, G1 production policy, detailed annotation-error handling and full 101-book application acceptance remain open. This supersedes earlier statements that all adapter/reader code was absent; those described the initial foundation pass.

M1 completion pass in progress: 19 automated tests now pass. Private snapshot creation, remembered-library UI, exclusive-access detection, bounded/cancellable loading and version-gated handled reader-close review have been implemented, with the normal live entry point still disabled pending integration validation. A real one-book snapshot adapter check passed without source changes. The user has approved private-snapshot browsing, original-file reading, and Calibre/other readers being closed during refresh/launch. Policy clarification is complete; integration validation remains. G1 is not yet closed and full 101-book acceptance has not started. See [acceptance preparation](test_data/m1_acceptance/README.md). Earlier test counts and manual-close-only descriptions are historical; M1 is not complete.

Latest decision: [M1 library access policy accepted](m1_library_access_decision.md). No access-policy clarification remains. G1 stays PARTIAL until integration verification passes; full 101-book acceptance still follows G1, not policy approval alone.

## Current acceptance checkpoint

G1 PASSED for the approved M1 policy; normal entry-point library selection now enabled. Full 101-book automated application acceptance ran afterwards and passed catalog/view/search/path/restart/error checks; source hashes unchanged during browsing. Twenty-one unit/workflow tests pass. Final desktop three-format launch and owned-reader Cancel/Close confirmation are pending. See [acceptance report](test_data/m1_acceptance/README.md). Do not repeat product clarification or mark M1 complete before the final evidence.

Latest desktop acceptance: EPUB/MOBI/PDF launch, readable display and navigation through the hub are user-confirmed for The Time Machine. M1-A04/A06 pass. Hub-close Cancel/Close reader confirmation (M1-A09 and final M1-A12 sign-off) remains pending; do not declare M1 complete yet.

Close-flow follow-up: user reported only the reader closes; initiating control is not yet confirmed. A real-Qt-dialog regression check with simulated asynchronous reader exit passes, and reader-only exit correctly leaves the hub open. Twenty-three automated tests pass; no application fix was made because the discrepancy is not yet reproduced. Desktop M1-A09/A12 remain open pending clarification and verification.

Final M1 sign-off: user-confirmed three-format reading/navigation and both hub close-dialog outcomes complete M1-01–M1-07 and M1-A01–M1-A12. Earlier reader-only close report was expected behaviour, not a reproduced defect. No additional code changes or release were needed for sign-off.

M2 decisions recorded: catalog viewing and single-book metadata editing only; seven editable fields; explicit Save/Discard; focus/30-second idle refresh with draft/access deferral; per-field/global conflict choices; retain partial successes and retry failed fields. Imports, exports, add/delete, format conversions and file-management operations are excluded. M3 contents remain uncommitted. See [M2 specification](milestone_02_metadata_editing.md) for the confirmed Calibre-managed side effects, clean-editor refresh and partial-save semantics; disposable write validation remains outstanding. No M2 write code or mutation tests performed in this planning pass.

M2 clarification decisions confirmed: metadata Save may perform Calibre-managed title/author path changes, cover writes and database updates, but M2 provides no direct filesystem commands. Dirty book selection, editor/module/app close and explicit Refresh use Save / Discard / Cancel. Automatic focus/idle refresh defers while dirty and updates clean editors. Save continues the requested action only once outstanding edits/results are resolved. Partial successes remain committed; Discard abandons only remaining unsaved changes. Every Save/Retry re-reads Calibre and checks remaining edits against their baseline for new conflicts. The three blocking questions are settled; initial disposable write validation is now complete; next is the guarded editor/write adapter, using the now-confirmed editor and recovery decisions. See [M2 specification](milestone_02_metadata_editing.md).

M2-01 capability validation completed on a fresh 101-book copy using one multi-format record. Seven-field round trip, path changes, real partial mutation and protocol conflict/retry checks are recorded in the [validation report](test_data/m2_validation/README.md). Original-library hashes were unchanged. Missing/invalid covers and ignored index changes require prevalidation, cover recovery protection and field read-back. M2 editor implementation, access/race handling and application acceptance remain open.

Confirmed M2 series rule: clearing Series hides its number and removes the series name on Save. Any internally retained Calibre index is ignored and is not a save failure. New series default explicitly to 1 unless edited; no retained index carries over. This supersedes literal stored-index removal. The future keep-number/start-at-1 prompt remains outside M2.

M2 editor/recovery decisions confirmed: actual failed series-name removal follows normal partial-save handling with Retry / Keep Editing / Discard and no rollback of successful writes. Covers support local selection, preview, replacement and complete removal; failed cover writes automatically restore the backed-up original, verify recovery and retain the proposed replacement for retry. Descriptions use basic rich text (paragraphs, bold, italic, bullet and numbered lists), preserving untouched HTML exactly. Series numbers accept non-negative decimals and default to 1 for a new series. Authors use ordered Add/Remove/Reorder entries; tags use unordered Add/Remove entries. Author names preserve commas; comma-containing tag names cannot be saved, with an explanation that Calibre treats commas as separators. These requirements are implemented and accepted; M2-A12–M2-A17 record acceptance in the M2 specification.

## M2 follow-up compatibility checkpoint

Disposable Calibre 9.2.1 API verification passed cover deletion, automatic backup-restoration protocol, ordered author round trips (including commas), exact untouched HTML preservation and numeric validation. UUID and format contents were preserved; original-library hashes were unchanged. These are capability/protocol results, not completed application acceptance.

The user resolved both compatibility blockers: when no series exists, hide and ignore Calibre's internally retained index; it is not a save failure. Assigning a new series explicitly defaults to 1 unless edited. Individual tag names may not contain commas; validation must prevent saving them and explain that Calibre treats commas as separators. Application implementation and acceptance remain open; these decisions do not mark tests complete.

## Current M2 implementation and gate status

M2-02–M2-06 are implemented and automated verification passed: 41 tests, 16 adapter checks and 17 real application checks on disposable 101-book copies. M2-07 is DONE following user desktop sign-off; M2 is COMPLETE for the agreed scope. G2 (M1 viewer lifecycle) is PASSED/CLOSED for Calibre 9.2.1 using recorded user confirmations and passing regressions. Earlier implementation-pending checkpoints are historical. See [M2 acceptance](test_data/m2_acceptance/README.md) and [M2 technical design](technical_design_m2.md). No release or schema migration was performed.

## Approved milestone sequence

M3 is [Safe Ebook Imports](milestone_03_safe_ebook_imports.md): copy-only, mandatory preview/confirmation for every batch, duplicate protection, failure recovery and source preservation. M3-G is the approved acceptance gate, not yet run. M4 is Bulk Metadata Editing; M5 is Hub Activity / Recovery. Their detailed scopes remain to be defined. Move, rename and delete-original commands remain deferred. M3 includes its own necessary import recovery; it does not wait for the broader M5 dashboard.

M3 import decisions confirmed: users may explicitly attach formats to existing books without automatic overwrite. Missing title/author use filename/Unknown fallbacks, with preview warnings and a persistent Needs metadata review marker. Interruption finishes verifying the current item if possible, preserves completed imports and records unfinished work. Restart offers Review / Retry / Discard Pending with completed/pending counts and no automatic resumption. Retry reconciles uncertain writes and requires the mandatory preview/confirmation; Discard Pending never removes completed imports or source files. See [M3 requirements and gate criteria](milestone_03_safe_ebook_imports.md). M3-01 planning is done; M3-02 technical validation is next. M3-G remains OPEN / NOT RUN.

M3-02 preparation: baseline/three working copies and ten fixtures prepared with hashes; source library unchanged. No application code changes or import execution in this pass. See [validation preparation](test_data/m3_validation/README.md). M3-G remains open.

M3-02 complete: 13 disposable capability/protocol checks passed; initial parser failure and required safeguards are retained in [validation results](test_data/m3_validation/RESULTS.md). No application code changed; M3-G remains open pending implementation and application acceptance.

Current M3 checkpoint: 50 tests, 23 import/recovery checks and five 101-book hub checks pass. M3-03–M3-06 are DONE; M3-07 remains ACTIVE pending two desktop confirmations. M3-G is OPEN. The user confirmed separate system-calculated completeness and explicitly controlled review status; editing does not clear review status. See [M3 acceptance](test_data/m3_acceptance/README.md).

Final M3 sign-off: the user confirmed mandatory preview/import, independent completeness/review controls, and all three imported/attached reader formats. M3-01–M3-07 and M3-G01–M3-G11 are complete. Fifty automated tests, 23 import/recovery checks and five hub/catalog checks passed. This supersedes prior desktop-pending checkpoints. Next is M4 scope definition.

Historical M4 planning checkpoint (superseded by the implementation checkpoint below): scope approved for add/remove tags, set/clear series and replace an author; stable multi-selection; keep/fixed/sequential numbers; mandatory preview; isolate conflicts while other books continue; durable pending recovery and reviewed field-scoped batch revert. [M4-G](milestone_04_bulk_metadata_editing.md) is OPEN / NOT RUN. M4-01 is DONE with all six clarification decisions recorded and acceptance fixtures planned; M4-02–M4-07 are TODO. Disposable validation is next. M5 remains Hub Activity / Recovery. Existing technical gate identifiers are unchanged.

Historical M4 implementation checkpoint (superseded by final sign-off below): M4-01–M4-06 DONE; M4-07 ACTIVE and M4-G OPEN only for final desktop acceptance. Bulk selection, five operations, mandatory preview, isolated conflicts, durable recovery/history and batch revert are implemented. Verification passed 64 unit/UI tests, 25 disposable application checks (including 101-book edit/revert) and 8 Calibre fault checks; original-library hashes unchanged. This supersedes earlier M4 planning-only/TODO checkpoints. At that checkpoint, the user needed a Calibre/reader window open; access guards were retained. See [acceptance instructions](test_data/m4_acceptance/README.md).

Final M4 sign-off (2026-09-21): the user confirmed every desktop checklist item and requested milestone/gate closure. M4-01–M4-07 and M4-G01–M4-G10 are complete; **M4 COMPLETE, M4-G PASSED/CLOSED**. Automated evidence remains 64 unit/UI tests, 25 application checks and 8 fault checks. [Desktop confirmation](test_data/m4_acceptance/desktop_confirmation.json). Next is M5 scope definition; no M5 implementation or release is claimed.

M5 planning checkpoint: the user approved Hub Activity & Recovery for Book-inator, one profile/device, including persistent history, explicit recovery actions, startup summary and emergency preservation of unsaved single-book edits. Dashboard customization, synchronization, backups, other modules and automatic resumption remain excluded. [M5 specification](milestone_05_hub_activity_recovery.md) records all decisions, tasks, gate criteria; its three initial clarifications are now resolved. No M5 code or validation is claimed.

M5 scope closure: all three clarification recommendations accepted. Successful emergency preservation automatically completes an already-requested close with truthful recovery notices; without a close request, the editor remains open. Delete History is unavailable for unresolved recovery until separate Review Recovery and explicit Discard Pending; resolved records may be deleted with confirmation. Successful routine preference saves are excluded from Activity, while actionable settings-save failures are included. M5-01 remains ACTIVE only for technical mapping; M5-02–M5-07 TODO, M5-G OPEN / NOT RUN. No M5 implementation or validation is claimed.

Latest M5 checkpoint: M5-01 DONE ([technical design](technical_design_m5.md)); M5-02 DONE ([31 passing disposable protocol checks](test_data/m5_validation/README.md)). Original-library hashes and ebook content were unchanged. M5-03–M5-07 remain TODO; M5-G OPEN / NOT RUN. No application code changed. Required next integrations include one startup summary and safe separation of book-review state from deletable import journals. Earlier technical-mapping/validation-pending checkpoints are historical.

Latest M5-03 checkpoint: production activity/recovery stores, operation hooks and independent book-review migration are implemented and verified. [85 unit/UI tests and 14 real disposable checks](test_data/m5_03_integration/README.md) passed; original-library hashes unchanged. M5-03 DONE; M5-04–M5-07 TODO; M5-G OPEN. The Activity UI, shared action coordinator, automatic emergency preservation/close continuation and final acceptance remain outstanding. Earlier no-application-code statements describe previous checkpoints.

Latest M5-04 checkpoint: default collapsible Hub Activity, grouped latest outcomes and distinct counts, read-only full history/details and one summary above module tabs are implemented. [93 passing unit/UI tests and offscreen evidence](test_data/m5_04_activity/README.md). M5-04 DONE; M5-05–M5-07 TODO; M5-G OPEN. Next: shared recovery actions. Automatic emergency preservation and close handling remain M5-06. Earlier checkpoints are historical.

Latest M5-05 checkpoint: shared review/retry routing, persistent dismissal, reviewed-revision discard, coordinated restart-safe history deletion and verified single-book recovery resolution are implemented. [119 unit/UI tests and 13 real disposable checks](test_data/m5_05_actions/README.md) passed. M5-05 DONE/CLOSED; M5-06–M5-07 TODO; M5-G OPEN. Next: automatic emergency preservation and close handling. Earlier checkpoints describe their historical implementation stages.

Latest M5-06 checkpoint: automatic emergency preservation after failed Save/Retry, alternate-location recovery, current-revision protection and requested editor/tab/Hub close continuation are implemented. [143 unit/UI tests and 14 real disposable checks](test_data/m5_06_emergency/README.md) passed. M5-06 DONE; M5-07 TODO; M5-G OPEN. Next: full application and desktop acceptance. Earlier checkpoints are historical.

Latest M5-07 checkpoint: [147 unit/UI tests, 21 application checks and two isolated KWin scenarios](test_data/m5_acceptance/README.md) passed. Fixed a duplicate editor Save prompt on native Wayland shutdown requests. The disposable desktop session is prepared; Activity/history, recovery Save and discard/delete checks are user-confirmed; the user accepts isolated KWin evidence as sufficient. Successful close and restart recovery without automatic editor opening or cover application are user-confirmed. M5-07 DONE; M5-G PASSED / CLOSED after final evidence review. No host logout/poweroff performed.
