# M3 — Safe Ebook Imports: implemented design

Status: M3 and M3-G complete following implementation, automated checks and final user desktop acceptance. No release is published.

## Preview and execution boundary

The hub's Import ebooks action opens a single import dialog. Choose files, choose a recursive folder, or drop local files. Preview runs in a background worker against a private library snapshot and makes no original-library mutation. It reports unsupported/invalid files, exact-content duplicates, missing metadata and similar titles. Similarity uses normalized title strings with a SequenceMatcher ratio of at least 0.85; it is a suggestion, never a merge decision. Similar-title rows require an explicit action.

The user confirms each preview. New records and explicit attachment to an existing record are separate actions. A destination already containing the format cannot be confirmed for attachment. The Calibre helper independently rechecks this with `replace=False`.

The helper runs under installed Calibre 9.2.1 with isolated configuration and Calibre's database lock. Process checks require Calibre/readers closed. Direct database SQL mutation and automatic format replacement are not used. Sources are opened read-only, hashed before/after extraction and staged privately before writing; staged bytes must match the confirmed fingerprint. Import hooks and automatic import tags are disabled for the validated copy path. EPUB structure/CRC, MOBI headers and PDF parser/page count provide format checks; this is not exhaustive content validation or malware scanning.

Content hashes implement duplicate identity across the library and batch. Title/author heuristics do not define duplicates. A preview fingerprint covers existing book identities, titles/authors, format lists and format content hashes. Changes relevant to the reviewed plan stop execution and require a refreshed preview. Each verified own mutation updates that fingerprint for subsequent items.

## Durable recovery

`import_store.py` writes version-1 JSON batches under an `imports/<library-path-hash>` folder beside hub settings. Each batch includes library UUID, item source/hash, effective metadata, action, destination identity, operation UUID, state and warnings. Writes use a temporary file, fsync and atomic replacement. Unsupported/corrupt journals are preserved and reported.

Operation UUID is persisted before creating a book. A metadata-only partial record is found by UUID and repaired rather than recreated. A committed format is reconciled by UUID and content hash before retry. Unverified outcomes remain distinguishable from success. Retry rebuilds a preview, requires confirmation and updates the existing journal; it does not strand a second copy of pending work.

Stop finishes the current item's verification if possible and prevents the next item from starting. Hub/module close requests stopping and keeps the window open until the active operation returns. Import workers are not force-killed in the middle of writes. Restart exposes previous unfinished work with completed/pending counts and Review / Retry / Discard Pending. Nothing resumes automatically. Discard changes work state only; completed imports and sources remain intact.

## Metadata completeness and review

Fallback title uses the filename stem; missing author uses Unknown. The batch records which fields used fallbacks. A completed fallback import appears in the Needs Metadata Review filter. Review markers are application-owned journal data, not hidden Calibre tags/custom columns.

The editor displays two independent states. Completeness is calculated from saved title/authors and known fallback provenance; unresolved filename/Unknown fallbacks count as incomplete. Review status remains Needs Metadata Review after metadata correction and changes only when the user chooses Mark Reviewed. Mark Reviewed requires a clean editor and never changes book metadata. Both states survive restart; editing fields does not silently mark them reviewed.

## Verification and limits

50 automated tests include all M1/M2 regressions. Real Qt/Calibre verification covers 23 import/recovery cases plus five 101-book hub/catalog checks. One bug found during these checks—missing destination identity after repairing a partial record—was fixed and the entire import run repeated successfully. Source/fixture hashes were unchanged during integration checks.

No claim is made for arbitrary third-party import plugins, tools bypassing Calibre's lock, arbitrary power-loss points, or every malformed ebook. Library-path relocation, richer shared activity history and multi-device recovery remain later work. Large-library hash scans and full snapshots favour correctness over speed and need later performance work.

Evidence and current desktop status: [M3 acceptance](test_data/m3_acceptance/README.md). Requirements: [M3](milestone_03_safe_ebook_imports.md). Earlier capability evidence: [M3-02](test_data/m3_validation/RESULTS.md).
