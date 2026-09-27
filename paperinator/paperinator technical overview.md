# Paper-inator Technical Overview

Status: agreed architectural direction with proposed implementation details. This is a design overview, not an implemented system, final schema, dependency selection, or release authorization.

## 1. Authority and references

Explicit owner decisions and the [constitution](paperinator%20constition.md) govern this design. Paper-inator documents were reviewed in creation order, with newer decisions taking precedence over conflicting older proposals:

| Created, Europe/Berlin, 26 September 2026 | Reference |
| --- | --- |
| 19:34 | [Concept draft](paperinator%20concept%20draft.md) |
| 19:35 | [Feature draft](paperinator%20feature%20draft.md) |
| 19:38 | [Technical overview draft](paperinator%20technical%20overview%20draft.md) |
| 19:51 | [Constitution draft](paperinator%20constittion%20draft.md) |
| 19:53 | [Scope refinement](scope%20refinement.md) |
| 20:33 | [Overview](paperinator%20overview.md) |
| 20:59 | [Features](paperinator%20features.md) |
| 21:10 | [Constitution](paperinator%20constition.md) |

These are observed filesystem creation times, not evidence of feature implementation. Subsequent owner clarification approves Python/PyQt6 services, separate profile libraries, Markdown notes, replaceable third-party components, and the separation of source content from user knowledge. File creation order does not bypass constitutional amendment requirements.

Reference designs are [Hub and Book-inator M1](../technical_design_m1.md), [Movie-inator M17](../technical_design_m17.md), and [Music-inator M18](../technical_design_m18.md). They inform desktop integration, domain/service separation, transactional catalog changes, reviewed imports, activity reporting, and testing. Paper-inator does not inherit their domain-specific storage or external-player limitations.

## 2. Accepted architectural decisions

| Area | Direction |
| --- | --- |
| Application | Python and PyQt6 within the existing Media-inator Hub |
| Deployment | Desktop module; no web frontend, REST server, or client/server split |
| Storage | Separate library directory and SQLite database for each Hub profile |
| Notes | Authoritative storage in the profile's SQLite library; Markdown content format; convenient editing tools and rendered preview; explicit export as `.md` files |
| Documents | Preserved source files; separate user annotations and version-specific reading state |
| Components | Replaceable PDF, text-extraction, citation, and provider adapters; the PDF engine is chosen in the reader milestone |
| Dependencies | Additional libraries allowed after compatibility, maintenance, licensing, and platform evaluation |

Profile separation is an organizational feature, not a security boundary. It prevents unintended mixing through application workflows; it does not protect files from someone with access through the same operating-system account. Encryption and a separate authentication system are not selected here.

## 3. Application structure

Paper-inator uses the Hub's application lifecycle, module navigation, profiles, shared appearance, workspaces, and activity reporting. The UI coordinates services rather than directly implementing database or file operations.

| Component | Responsibility |
| --- | --- |
| Paper-inator UI | Home, library, projects, editors, reading views, previews, and recovery interactions |
| Library service | Knowledge Items, versions, collections, projects, states, relationships, and validation |
| Document service | Managed and referenced files, identity checks, locating missing files, document access |
| Annotation service | Highlights, annotations, bookmarks, source anchors, and reading positions |
| Search service | Metadata, note, highlight, and document-text search; filters and saved searches |
| Citation service | Version-aware citation data, style application, bibliographies, bibliographic export |
| Import service | Discovery, extraction, duplicate/version proposals, preview, and confirmed application |
| Export service | Reviewed knowledge exports, file inclusion, Markdown output, annotated PDF copies |
| Metadata service | Explicit provider requests, provenance, and proposed changes |

Storage, file-operation recovery, backup, and restore support these services through shared internal interfaces. Exact Python filenames and class boundaries remain implementation details. Domain logic should be testable without constructing Qt widgets.

Long-running extraction, indexing, copying, and network requests run away from the UI thread. Workers report progress, cancellation, and errors through controlled interfaces. Worker tasks remain bound to the originating profile and library even if the active UI profile changes; results must not be applied to a different profile.

## 4. Source content and user knowledge

The experience combines two logically distinct layers:

| Layer | Contents |
| --- | --- |
| Source content | PDFs and other attachments, imported references, bibliographic metadata, document versions, provenance |
| User knowledge | Markdown notes, highlights, annotations, connections, reading positions and progress, flags, projects, memberships, saved searches |

Separation does not require two databases. Both layers can reside in one profile's SQLite library with distinct entities and relationships. Binary source files remain outside the database. Source metadata can be edited through reviewed operations; source-file preservation does not make metadata uneditable.

Metadata proposals should remain distinguishable from accepted values. A later AI adapter must also retain the distinction between source material, user content, and generated suggestions.

## 5. Profile library layout

An illustrative layout is:

```text
Paper-inator/
  profiles/
    <stable-profile-id>/
      library.sqlite
      files/
      cache/
      exports/
      backups/
```

Use stable Hub profile identifiers rather than display names for identity. Renaming a profile must not create a different library. Final platform paths and folder names remain configurable implementation decisions.

The SQLite library holds structured records and relationships. Managed files belong to the profile library; referenced files retain their external locations. Cache data, such as extracted text and thumbnails, is rebuildable and distinguishable from authoritative research content.

Markdown is the authoritative note content format. **Owner decision (26 September 2026): the authoritative copy of every note is stored within the Paper-inator database.** Users may explicitly export notes as standard `.md` files; exported files are not authoritative copies. No `notes/` folder is needed, and derived previews and exports stay clearly identified.

| Aspect | Decision |
| --- | --- |
| Authoritative note storage | SQLite (profile library database) |
| Note format | Markdown |
| Export format | Markdown (`.md`) |

Exports and backups may use user-selected destinations. A backup directory beside the library is convenient but is not independent protection against losing the device.

## 6. Conceptual data model

| Entity | Purpose |
| --- | --- |
| Library | Stable identity, owning profile, schema version, creation information |
| Knowledge Item | Type, accepted descriptive metadata, item-level reading progress and handling state |
| Document Version | Preprint, accepted manuscript, published version, or other reviewed version; version metadata |
| File/Attachment | Managed/reference mode, location, content identity, document association, availability |
| Note | Markdown content and optional source associations; can exist independently |
| Highlight/Annotation | Content, exact source version, location anchor, and user context |
| Bookmark/Reading Position | Location within a particular document version |
| Collection/Project | Organization and many-to-many membership without item duplication |
| Connection | Typed links between supported objects, with direction where meaningful |
| Saved Search | Named search and filter criteria rather than copied results |
| Trash/Operation Record | Recoverable removal state and progress of multi-step operations |

Use stable identifiers for items, versions, notes, and links; titles and file paths are mutable labels, not identities. Cross-module references include the target module and stable catalog/item identity and must tolerate unavailable targets.

A preferred-version reference supplies defaults for opening and citations. It must not reassign existing highlights or replace their page references. Item-level progress remains distinct from exact per-version positions.

The final schema must specify foreign-key behavior carefully: an unconditional cascading delete is inappropriate for recoverable removal or independently linked notes. Connections and memberships must survive trash/restore as required without deleting unrelated objects.

## 7. File identity, versions, and imports

Import follows discovery, local inspection, proposal, preview, confirmation, application, and outcome reporting. No online lookup is implied by a folder scan.

Content fingerprints can identify identical files; title or identifier similarities can suggest related records. These answer different questions. A duplicate file, another version of one work, and a separate work must not be treated as equivalent. User-reviewed grouping remains required.

Before applying an import, revalidate the chosen source and destination so an outdated preview cannot silently act on changed files. Managed copies should be staged and verified before becoming available as completed imports. Referenced mode records the location without modifying the source.

Database transactions cannot atomically commit arbitrary filesystem changes. Operations involving both need a recorded plan, temporary staging, explicit completion states, and restart recovery. The UI must not report completion solely because the database write succeeded while the file copy failed.

As in Movie- and Music-inator, confirmed groups may be handled in bounded units with visible partial outcomes. Exact commit and cancellation boundaries must be specified and tested before implementation. Completed units must remain distinguishable from interrupted work.

## 8. PDF and annotation adapters

Define component interfaces for rendering, text extraction and selection, navigation, and annotated-copy export. These capabilities may require different libraries. Do not assume a component that displays a PDF also supports reliable text anchors or portable annotation export.

The built-in reader will use a PDF adapter abstraction. The concrete PDF engine will be selected during the reader milestone after compatibility, licensing, annotation, search, and packaging evaluation. M19 defines and tests the reader and annotation adapter interfaces only; QtPdf is the first evaluation candidate, and a different library may later serve extraction or export behind its own adapter.

Annotations should identify the source version and file content, with page/location information and suitable text or geometric anchors. The detailed anchor format is pending. A changed file must not silently receive old annotations as though it were identical; show a mismatch and require reviewed resolution.

Original PDFs remain untouched. Annotated export creates a separate output and reports unsupported annotation types rather than silently dropping them. External-reader opening does not promise position capture or annotation synchronization.

Image-only PDFs may render without searchable text. OCR remains outside the agreed foundation commitment; report search limitations accurately.

## 9. Markdown notes and links

Provide Markdown editing, a formatted preview, and convenient commands for common formatting and inserting links. Store readable Markdown and preserve source references in exports.

Internal links should target stable object identifiers with readable labels. The owner's wiki-link examples express convenient linking, not a finalized syntax; exact Markdown extensions remain to be chosen. Renaming an item must not break its links.

Rendered previews must not execute embedded scripts or fetch remote resources automatically. This preserves the explicit-online-action policy. Export must explain how internal links are represented when targets are absent from the selected export.

HTML, PDF, and other note-output formats are possible extensions; choosing Markdown does not automatically commit to every conversion mentioned as an example.

## 10. Search and indexing

Search covers accepted metadata, Markdown notes, highlights, and available extracted document text within the active profile. Indexes are derived, rebuildable data. A local SQLite full-text index is a candidate, subject to runtime capability checks and relevance testing, not a fixed engine selection.

Saved searches store criteria. Collection and project filters operate over memberships without duplicating records. Reading progress, handling state, and flags remain independent filters.

Indexing is incremental background work with visible failures and cancellation. Search results retain source/version identity. Profile switching must not expose another profile's cached results. Normal search should distinguish active material from trash; exact trash-search controls remain a UI design detail.

## 11. Metadata and citations

Provider adapters return proposed metadata with provenance. Network requests occur only on explicit action, with bounded execution and understandable failure states. Crossref, PubMed, and arXiv are earlier candidates, not selected providers or verified integrations. Metadata provider adapters exist architecturally, but none is implemented in M19; DOI lookup (Crossref) and metadata retrieval are planned for M21.

Citation formatting uses a replaceable component consuming normalized bibliographic data. The design must support the agreed formatted citations, bibliographies, BibTeX, RIS, and CSL JSON exports. Exact style coverage and component choice remain pending.

Preferred versions supply defaults, but citations to a specific highlight retain its actual version and location. Missing metadata must remain visible rather than fabricated. Linked Book-inator records are accessed through a defined integration boundary, without Paper-inator taking ownership of their catalog.

## 12. Trash, deletion, and recovery

Normal removal records a recoverable state for the item and its associations. Affected managed files remain at their existing paths in logical recoverable trash; referenced originals remain untouched. Shared files and independent notes still used elsewhere must remain available to surviving associations.

For M19, normal removal and restoration update logical trash state transactionally without relocating managed files. No physical trash directory is required. Operation records coordinate explicitly confirmed permanent deletion and its filesystem effects. Recovery must respect library ownership and active operations. Logical trash identifiers must not depend solely on a mutable display path.

Permanent deletion is a separate confirmed operation with a preview of the exact scope. Revalidate dependencies before deleting managed files. Never follow a referenced-file path into deletion, and do not introduce automatic permanent purging. Partial failures must be reported and recoverable or retryable without pretending deleted content can be restored.

Detailed reference-counting, shared-association rules, and filesystem containment checks belong in the implementation design and tests.

## 13. Persistence, migrations, and backups

Use transactional SQLite writes, validation, and revision/conflict checks informed by the other modules. Editors should submit changed fields and preserve unsaved input on failure. Reject foreign or unsupported newer catalogs without modifying them.

Version schemas and migrations explicitly. Back up before destructive migration, validate the result, and keep a recovery route. File-operation recovery remains necessary even when database transactions are correct.

Backups must capture a consistent database and the required authoritative content, including Markdown notes, annotations, and managed documents according to the selected scope. Do not assume copying an open database file alone creates a consistent backup.

Backup manifests distinguish included file contents from external references. Restore previews explain replacement effects and verify identifiers and version associations. Rebuildable caches need not be authoritative backup content. Exact backup packaging and restore transaction boundaries remain open.

## 14. Hub integration

Register the module through the existing Hub mechanisms. Repeated launch should focus the existing module; workspace selection must be bound to the correct profile and library identity. Follow the Hub's shared appearance and settings rules while keeping document presentation distinct.

Integrate unsaved edits, active tasks, failures, and recovery with Hub review and activity flows. Keep task ownership stable across profile changes. Search and cross-module links must respect profile boundaries.

The separate profile database deliberately differs from Movie/Music catalogs with per-profile personal tables. Paper-inator's constitution rules out shared libraries in the foundation. Likewise, its managed files and recoverable trash require more file coordination than the other modules' catalog-only deletion.

## 15. Dependency evaluation and verification

Additional third-party libraries may be used where required, subject to compatibility, maintenance, licensing, and platform-support evaluation. Keep PDF and citation implementations behind interfaces so replacement does not require a constitutional change.

Before choosing dependencies, validate representative PDF rendering, text selection, anchors, annotated-copy output, and citation examples on the target environment. This overview does not assert that any candidate package meets those requirements.

Verification should cover:

- Profile isolation, stable ownership of background work, and no unrequested network activity.
- Import review, exact-file duplicates versus versions, changed-source detection, and preserved originals.
- Version-specific annotations and positions across preferred-version changes.
- Markdown persistence, readable export, stable links, and preview behavior.
- Trash/restore and permanent-deletion scope, shared associations, and interruption recovery.
- Metadata conflicts, schema rejection, migrations, and complete backup restoration.
- Search isolation and rebuilds; citations retaining the actual source version.
- Real Qt desktop checks for Hub lifecycle, accessibility, reading, and failure feedback, alongside domain tests.

## 16. Remaining detailed decisions

The next technical specification must settle exact schemas and paths, reader and citation components, supported citation styles, link and annotation formats, export/backup representations, recovery boundaries, and implementation milestones.

These choices remain within the agreed architecture. No new constitutional amendment is required for routine implementation decisions that preserve its principles. Foundation, Advanced, and Future classifications remain as recorded in the feature document.


## 17. Milestone plan and M19 implementation

Owner decisions of 26 September 2026 sequence the Foundation:

| Milestone | Goal | Content |
| --- | --- | --- |
| M19 Knowledge Foundation | Can I build and manage a research knowledge base? | Hub integration, profile library, Knowledge Items, version grouping, managed/referenced files, states, flags, tags, collections, projects, Markdown notes, typed connections, search, saved searches, trash; external PDF opening only; fully offline |
| M20 Reading & Annotation | Can I actively study and annotate knowledge? | Built-in PDF reader, reading positions, bookmarks, highlights, sticky notes, highlight-to-note linking, highlight search |
| M21 Research & Preservation | Can I use this knowledge in research workflows and protect my work? | Citations, bibliographies, BibTeX, RIS, CSL JSON, DOI lookup (Crossref), metadata retrieval, backup, restore |
| M22 Import & Migration | Can I migrate from other systems? | Existing-library import, duplicate review, metadata merge workflows, watch folders if still desired |

The M19 schema, file handling, trash operation records and adapters are specified in [technical_design_m19.md](../technical_design_m19.md). Within this overview's principles it chooses: one directory per stable profile id with the owning profile recorded in the database; logical trash with managed copies deleted only by previewed permanent deletion (completed on restart if interrupted); content fingerprints for identical-file detection and changed-file checks; stable `paper:<type>/<id>` Markdown links; SQLite FTS5 for derived document text.



## Approved M19 trash clarification

Owner clarification for M19: recoverable trash is logical. Removed items and their associated research context are hidden from the active library and remain restorable. Managed files retain their existing library paths; normal removal and restoration do not move files. Referenced originals remain untouched. Only a separately previewed and explicitly confirmed permanent deletion may remove affected managed copies. Physical trash relocation is not required for M19 and has no assigned future milestone.
