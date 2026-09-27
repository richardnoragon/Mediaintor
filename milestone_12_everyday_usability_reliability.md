# M12 — Everyday Usability and Reliability

Status: **COMPLETE; M12-G PASSED / CLOSED (2026-09-23).** Accepted build `0.1.0a1-f59e8af9b043f304`. [Final evidence review](test_data/m12_usability/gate_review.md). 223 source tests, 64 installed targeted tests, personal KDE acceptance and persisted-result verification passed. M11 unchanged; promotion remains separate.

## Goal and priorities

Eliminate workflow uncertainty through reliable preserved-draft recovery, precise save feedback, clear bulk-revert states and visible installation identification. Priority: recovery, save feedback, bulk revert, then installation identification. New Book-inator/Hub/NAS capabilities follow M12-G rather than being bundled into this work.

## Approved requirements

### Recovery reliability

Review / Retry must reconstruct the preserved draft when the record is valid and current metadata can be read. It must not silently present an empty editor instead of recoverable work. Explicit Save remains required before catalog changes. Missing draft, inaccessible draft, invalid/corrupt record, unavailable library and ongoing catalog refresh require specific explanations and safe retry behavior. Preserve ownership/library/book identity checks and conflict review; do not bypass them to satisfy an unconditional “always opens” promise.

Investigate and reproduce the M11 editor-close/catalog-refresh handoff before implementing a fix. Wait safely or explain why review is deferred; guard against stale callbacks and double-open operations. Use a recovery timestamp only if actually available—do not invent one for historical records.

### Precise save feedback

Identify the affected book and fields actually saved, for example “Saved tags for The Time Machine.” Distinguish complete success, no changes, conflicts and partial failures. A partial save must identify saved fields and remaining unsaved fields without claiming all work succeeded. Retain committed changes and existing explicit Save/Discard/Cancel policies. Keep personal metadata out of diagnostic export even when it is displayed in local feedback.

### Bulk revert clarity

Differentiate preview, confirmation, execution and verified completion. Preview states affected-book count and that confirmation is required. Completion reports verified outcomes, not just the number originally selected. Continue existing conflict, per-book exclusion, partial-success and recovery policies.

Approved rule: use “Cancelled — no books changed” only when no writes occurred. After any write, report the actual completed, failed and pending book counts, with an outcome such as “Revert completed”, “Revert interrupted” or “Revert failed”. Preserve verified successful writes and remaining recovery work. Do not claim no changes after partial success or an unverified write. Technical design must define consistent counting for partial-field saves, conflicts, exclusions and uncertain results without implying they completed successfully.

### Installation identification

Show the installation role/name in the main window title. Approved examples include “Media-inator — M12 Everyday” and “Media-inator — M12 Test”. Build information may accompany the label and must reflect the actual installed artifact. Keep launcher and window identification consistent. Define how deployment supplies the label and sensible defaults during technical design.

Do not rename or modify M11 to implement the illustrative “M11 Stable” title: accepted M11 remains unchanged. No promotion is inferred merely from an editable display label.

### Isolation

Create a separate M12 installation, copied library, copied configuration, independent data directories and backups. M11's accepted build/deployment is frozen as reference and must not be changed by M12 development; ordinary owner use can continue. Snapshot a quiet source at setup, keeping M11's later everyday data distinct. Never share writable mounts between M11 and M12.

## Regression scope — approved

Regression coverage includes book metadata editing, tag management, cover removal/replacement, workspace removal/actions, eligible history removal, imports, search/filter and review/retry workflows. Preserve existing confirmations and protections for unresolved recovery and history.

Book deletion, file deletion, library item destruction, recycle-bin functionality and related UI workflows are explicitly out of scope. “Removal” refers only to the existing actions listed above; it does not imply deleting books.

## Acceptance and promotion — approved

Acceptance of M12-G confirms that the build meets the M12 requirements. Promotion to the primary working installation is a separate owner decision. M11 remains retained as the stable reference installation regardless of that decision.

Do not switch the everyday launcher, replace M11, or merge newer M11 data as a side effect of acceptance. A later promotion plan must preserve newer user data rather than silently replacing it with the development snapshot.

## Work plan

| Task | Status | Deliverable |
| --- | --- | --- |
| M12-01 — technical design | COMPLETE — [design](technical_design_m12.md) and [reproduction](test_data/m12_usability/recovery_reproduction.json) | Use approved boundaries; reproduce recovery handoff; define draft loading states, feedback wording/counts, deployment labels and acceptance evidence. |
| M12-02 — isolated setup | COMPLETE — [verified baseline](test_data/m12_usability/setup.json) | Verify quiet source and backup; independent M12 library/configuration/runtime/launcher; record M11 protection and package identity. |
| M12-03 — recovery reliability | COMPLETE — [final evidence](test_data/m12_usability/gate_review.md) | Implement and test safe editor/refresh sequencing, preserved-draft reconstruction and actionable failure messages. |
| M12-04 — save feedback | COMPLETE — [final evidence](test_data/m12_usability/gate_review.md) | Book/field-specific outcomes, no-change and partial-failure feedback, with regression coverage. |
| M12-05 — revert clarity | COMPLETE — [final evidence](test_data/m12_usability/gate_review.md) | Explicit preview/confirmation/progress/final states and accurate result counts; retain journal/retry behavior. |
| M12-06 — installation identification | COMPLETE — [final evidence](test_data/m12_usability/gate_review.md) | Consistent deployment/window labels and verified build information, without modifying stable installations. |
| M12-07 — regression and package verification | COMPLETE — [final installed evidence](test_data/m12_usability/gate_review.md) | Targeted failures plus metadata editing, tag management, cover removal/replacement, workspace actions/removal, eligible history removal, import/search/filter/review/retry and recovery regression; isolated installed candidate verification. No book/file deletion. |
| M12-08 — personal KDE acceptance and final review | COMPLETE — [KDE acceptance and final review](test_data/m12_usability/gate_review.md) | Owner exercises exact candidate; corroborate persisted effects; document limitations and close M12-G only on evidence. Record acceptance only; leave promotion to a separate decision. |

## M12-G acceptance

- [x] Preserved drafts load correctly after editor/refresh transitions; missing/inaccessible/corrupt records give specific errors and preserve recoverable work.
- [x] Opening/retrying recovery never silently writes metadata or substitutes a blank editor for a valid preserved draft.
- [x] Save results identify the book, changed fields and verified outcome, including partial failures.
- [x] Revert preview and completion are visually/textually distinct; actual outcomes and pending work are accurately counted.
- [x] Window/launcher identify the running installation; displayed build identity is correct.
- [x] Existing metadata editing, tag management, cover removal/replacement, workspace actions/removal, eligible history removal, import/search/filter and review/retry/recovery workflows pass regression.
- [x] Isolated package and personal KDE acceptance pass with recorded build and persisted-result verification.
- [x] M11 reference installation remains unchanged by M12 work; backups and data boundaries verified.

No minimum runtime duration. Publication/distribution, NAS, additional modules and unrelated features are excluded. Working-installation promotion is a separate decision; M12-G does not authorize it.
