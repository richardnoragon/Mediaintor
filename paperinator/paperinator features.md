# Paper-inator Features

Status: planned feature specification, incorporating owner decisions through 26 September 2026. Features listed here are requirements and intentions, not claims of implementation or verification.

Paper-inator is a local-first knowledge management module centered on Knowledge Items. It helps users collect, read, annotate, connect, organize, preserve, and reuse knowledge. Research and citation workflows support that purpose.

## Scope and source precedence

The Paper-inator documents were reviewed in creation order, oldest first. Newer decisions take precedence over conflicting earlier proposals. The owner's subsequent clarifications take precedence over these documents.

| Creation date and time (Europe/Berlin) | Reference |
| --- | --- |
| 2026-09-26 19:34 | [Concept draft](paperinator%20concept%20draft.md) |
| 2026-09-26 19:35 | [Feature draft](paperinator%20feature%20draft.md) |
| 2026-09-26 19:38 | [Technical overview draft](paperinator%20technical%20overview%20draft.md) |
| 2026-09-26 19:51 | [Constitution draft](paperinator%20constittion%20draft.md) |
| 2026-09-26 19:53 | [Scope refinement](scope%20refinement.md) |
| 2026-09-26 20:33 | [Agreed overview](paperinator%20overview.md) |

Times above are filesystem creation timestamps observed during this review. Subsequent clarifications add document versions and a preferred version, preservation of original PDFs, saved searches, and the feature classifications below.

The [Book-inator](../bookinator/bookinator%20features.md), [Movie-inator](../movieinator/movieinator%20features.md), and [Music-inator](../musicinator/musicinator%20features.md) feature documents inform the organization of this list: acquisition, catalog management, search, content access, export, and preservation. Their product-specific features and external-product claims are not automatically Paper-inator requirements.

| Classification | Meaning |
| --- | --- |
| Foundation | Capabilities necessary to fulfill the agreed product purpose. They can be delivered across several milestones. |
| Advanced | Useful extensions beyond the foundation, without a commitment to the initial delivery. |
| Future | Deliberately deferred ideas requiring further scope decisions. |

These categories describe scope, not implementation status or a release schedule. Older milestone sequences do not override the newer decision to include notes, projects, highlights, and ordinary typed connections in the foundation.

## Foundation

### Knowledge library and metadata

- Maintain one personal library centered on Knowledge Items, with optional collections and projects.
- Support research papers, conference papers and proceedings, theses and dissertations, technical reports, white papers, datasets, academic book chapters, standards and specifications, and research-related web resources.
- Permit records without an attached PDF, including references to externally available resources.
- Record applicable metadata such as title, authors and contributors, publication details, year, abstract, keywords, DOI, and other relevant identifiers. Validation depends on item type; a missing DOI is not automatically an error for every item.
- Keep metadata, files, notes, highlights, and relationships accessible from the item.
- Allow manual creation and editing, with clear validation feedback that preserves unsaved input.
- Keep independent notes available without requiring a fabricated source record.

### Acquisition and file ownership

- Import individual PDFs and selected folders, create records manually, and request DOI lookup explicitly. DOI lookup belongs to the Research Services work planned for M21; the first Foundation milestone (M19) is fully offline and uses manual entry and local PDF metadata/text proposals.
- Preview proposed additions and metadata before confirming an import. Show duplicate candidates and proposed version grouping for review.
- Offer an explicit choice between **Managed Copy**, which copies a file into the library, and **Referenced File**, which leaves it in its existing location.
- Keep original source files untouched. Catalog organization must not silently rename, move, or overwrite them.
- Distinguish the Knowledge Item from its documents and supplementary attachments, such as images, spreadsheets, or code archives. Cataloguing an attachment does not imply an embedded editor for its format.
- Identify missing referenced files and provide a deliberate way to locate them again without losing their associated research information.
- Make file effects clear when removing a record or attachment. Removing catalog information must not silently delete an original file.

### Versions of a work

- Allow one Knowledge Item to contain several versions of the same work, including a preprint, accepted manuscript, and published version.
- Require user-reviewed grouping; similar titles or shared identifiers may suggest a match but must not silently merge works.
- Let the user designate a **Preferred Version** for default opening, citation selection, and metadata purposes.
- Preserve version-specific publication details and identifiers where they differ. Changing the preferred version must not silently overwrite existing metadata.
- Tie highlights, annotations, bookmarks, and reading positions to the exact document version from which they originated.
- Show which version is being opened or cited. A quotation or highlight must retain its actual source version and page reference even when another version is preferred.
- Keep version grouping distinct from duplicate removal: different versions can be intentional, useful parts of one item.

### Home and everyday organization

- Provide a default Home dashboard containing Inbox items, recently opened items, Continue Reading, items needing review, active projects, and recent notes.
- Offer startup choices of **Home Dashboard**, **Library**, **Projects**, and **Restore Last View**.
- Support tags, named collections, and optional projects. Collections group material; projects gather research material around a particular investigation.
- Allow membership in multiple collections or projects without duplicating the underlying library item.
- Keep the following dimensions independent:

| Dimension | Values |
| --- | --- |
| Reading progress | Unread, Reading, Read |
| Library handling | Inbox, Active, Archived |
| Flags | Needs Review, Key Reference, Favorite |

- Preserve reading progress when archiving or changing project membership. A flag must not force a reading or handling state.
- Provide bulk organization for selected items, including tags, membership, states, and flags, with a clear selection and operation scope.

### Search, filters, and saved searches

- Search descriptive metadata, notes, highlights, and searchable document text across the library.
- Filter by relevant properties, including item type, author, year, tags, collection, project, reading progress, handling state, and flags.
- Sort results by relevant fields and combine search text with filters.
- Save, name, update, and remove searches. Saved searches retain their criteria and reflect the current library rather than creating duplicate items.
- Navigate from a result to its item, note, highlight, or document location as applicable.
- Clearly distinguish an empty library from a search with no matches, and provide a way to clear narrowing criteria.
- Make the limits of text search visible. Image-only PDFs do not become searchable merely by being imported; OCR is not a foundation commitment.

### PDF reading and annotations

- Provide a built-in PDF reader as the default, with an option to open a document in an external reader.
- Support remembered reading positions, bookmarks, text highlights, sticky-note annotations, and search within searchable PDFs.
- Preserve original PDFs and store Paper-inator annotations separately.
- Allow users to edit or remove their annotations without modifying the original document.
- Offer explicit export of an **Annotated PDF Copy** for portable use. Export must not overwrite the original by default.
- Do not imply external annotation synchronization merely because a document can be opened in another reader.

### Reusable highlights

- Treat highlights as first-class research objects, retaining selected text, source document, exact version, and page or location reference.
- Search highlights globally and open their source context.
- Link highlights to notes and other Knowledge Items and include them in projects.
- Export highlights with their source references.
- Preserve the original source association when the item's preferred version changes; do not silently transfer highlights to different pagination.

### Notes and typed connections

- Create standalone notes and notes associated with sources, highlights, or projects.
- Support summaries, findings, methodology, limitations, questions, research ideas, meeting notes, and experiment results.
- Search and link notes as part of the knowledge library.
- Connect Knowledge Items, notes, highlights, and projects through ordinary views and links.
- Provide initial relationship types: **Supports**, **Contradicts**, **Extends**, **Uses**, **Derived From**, **References**, and **Related To**.
- Make the direction and meaning of a connection clear where applicable, and allow users to inspect, edit, and remove it.
- Make connections useful without requiring graph visualization.

### Metadata review and duplicate review

- Present extracted or retrieved metadata as proposals with their source and proposed changes visible.
- Require review before modifying existing metadata. Let the user retain existing values rather than accepting an entire proposal.
- Flag incomplete or questionable records for review without inventing missing information.
- Present likely duplicates for a user decision, distinguishing repeated imports, document versions, and genuinely separate works.
- Preserve notes, highlights, links, and version context when resolving duplicates; potentially conflicting information must not disappear silently.
- Keep source information and user-authored content distinguishable from any later automated suggestions.

### Citations and bibliographies

- Generate formatted citations and bibliographies with citation style support.
- Export bibliographic records as **BibTeX**, **RIS**, and **CSL JSON**.
- Use the preferred version as the default citation source while allowing source-specific references to retain the version actually used.
- Expose missing citation information so that users can correct it before export.
- Support citations for linked Book-inator books without transferring ownership of the book record.
- Keep citations an integrated research capability. Word-processor plugins are outside the foundation.

The initial style selection and detailed formatting coverage require a later specification; the older draft's examples are not a promise that every variation of those styles is supported.

### Explicit knowledge exports

- Export selected Knowledge Items, projects, notes, highlights, metadata, and relationships.
- Show an export preview listing the scope and whether document files are included.
- Make file inclusion an explicit choice, separate from exporting metadata or notes.
- Preserve source references and relevant connections in knowledge exports. Make omissions or references to material outside the export selection visible.
- Distinguish bibliographic exchange formats from a broader knowledge export: BibTeX or RIS alone cannot be assumed to preserve every note, highlight, and relationship.
- Define portable knowledge-export representations in the detailed specification, with user ownership and access outside Paper-inator as requirements.

### Preservation, backup, and restore

- Provide backup and restore for library records, notes, annotations, projects, connections, and relevant preferences.
- Clearly state whether a backup contains managed documents, referenced documents, or only their locations. A path alone is not a backup of the file.
- Preview restore effects and preserve recoverability before replacing existing library state.
- Keep imports, metadata changes, and bulk operations recoverable wherever practical, with clear outcomes and failures.
- Preserve document-version associations so restored highlights, bookmarks, and positions still identify the correct source.

### Hub integration and module boundaries

- Launch from the Media-inator Hub and follow shared navigation and appearance conventions.
- Keep Paper-inator's research workflows and library usable independently of unrelated modules.
- Respect **Book-inator ownership of books**. Link to books, search linked books, cite them, and include them in projects without building a duplicate book-management catalog.
- Allow academic chapters to be Knowledge Items with a parent-book link where available.
- Apply the research-purpose boundary with Document-inator: research knowledge belongs here; administrative and personal records belong in Document-inator. PDF format alone does not decide ownership.
- Preserve useful source information when a cross-module target is unavailable and make the unavailable link clear. Exact cross-module link behavior remains a technical specification task.

### Local operation and control

- Require no account for core import, reading, annotation, organization, search, and export.
- Keep core operations available offline. Explicit online lookups remain network-dependent.
- Perform DOI lookup, metadata retrieval, and online verification only when requested.
- Do not automatically upload documents, notes, annotations, or projects.
- Keep user data accessible through documented, open exchange formats.

## Advanced

These extend the foundation. They are not prerequisites for beginning to use the personal research library.

- **Existing-library migration:** import exchange files and supported data from tools such as Zotero, EndNote, and Mendeley, with a preview and a report of unsupported or omitted information. Exact formats and tool coverage require specification.
- **Change file ownership mode:** explicitly convert referenced files to managed copies, or managed files to referenced files where practical, while retaining research associations and explaining file effects.
- **Additional metadata providers:** extend explicitly requested lookup beyond the initial DOI workflow. Earlier drafts identify Crossref, PubMed, and arXiv as candidates; provider selection and coverage are not settled here.

## Future

The following are deliberately deferred and require their own scope and delivery decisions:

- Watch folders and browser capture.
- Custom fields and custom relationship types.
- Project tasks, writing goals, and specialized systematic-review or meta-analysis workflows.
- Recommendation engines and broader discovery services.
- Interactive knowledge graph visualization.
- Optional AI summaries, topic extraction, and suggested connections. AI output must be labelled and distinguishable from source material and user notes.
- Import of external annotations, annotation synchronization, and explicit PDF write-back.
- Word, LibreOffice, and Google Docs citation integration, including toolbars and plugins.
- Shared libraries, team permissions, real-time collaboration, and multi-user editing.
- Optional synchronization, explicitly configured and controlled by the user.
- Additional source types such as videos, recorded lectures, and presentations.

## Details still to specify

These do not reopen the agreed product direction. They identify the next level of design work:

- Exact metadata fields and validation rules by item type, including version metadata and preferred-version changes.
- Note editing format, attachment limits, and precise reader behavior.
- Duplicate-resolution rules and preservation of conflicting values.
- Citation style coverage and rendering of source-version references.
- Knowledge-export formats, included-link behavior, and backup/restore packaging.
- Cross-module identifiers, unavailable-book behavior, and search boundaries.
- Recovery guarantees and acceptance checks for each delivery milestone.

Foundation, Advanced, and Future must remain visibly distinct as these details are developed. None of the deferred features is required to make collecting, understanding, and connecting knowledge useful.


## Constitutional ownership and preservation clarification

The [Paper-inator constitution](paperinator%20constition.md) incorporates the owner's subsequent decisions and governs these requirements.

Personal research context belongs to the active profile: notes, highlights, annotations, reading positions and progress, flags, project membership, saved searches, and workspace preferences. It remains private unless explicitly exported or shared. The foundation includes no shared libraries, automatic sharing, or implicit synchronization between users.

Normal removal places the Knowledge Item and its associated research information in recoverable trash, including notes, highlights, connections, retained reading history or state, and project links. Managed files enter logical recoverable trash without changing their paths; referenced originals remain untouched. Independent objects and files still required by surviving associations must be preserved.

Permanent deletion is a separate explicit action. Its preview explains the affected research information and managed files and states that referenced originals remain on disk. Trash does not replace backup. Detailed retention and shared-association behavior must preserve these principles.

Changes to constitutional principles require explicit owner approval, a constitution update, an overview update, and review of feature and applicable technical documentation. Routine implementation choices within these boundaries do not require separate constitutional approval.


## Accepted technical behavior clarification

Each Hub profile has its own Paper-inator library directory and SQLite database. Profile separation is an organizational feature, not a security boundary against access through the same operating-system account.

Notes are authored in Markdown and stored within the Paper-inator library, which holds the authoritative copy. Notes can be exported as standard Markdown files; exported files are copies. Convenient editing tools and a rendered preview are provided. Export preserves readable content, links, and source references; additional output conversions remain detailed design choices.

The [technical overview](paperinator%20technical%20overview.md) separates source content from user knowledge while retaining the established version-specific annotations and original-PDF preservation rules.


## Delivery sequence (owner decision, 26 September 2026)

The Foundation is delivered across milestones; classifications above are unchanged.

| Milestone | Foundation capabilities |
| --- | --- |
| M19 Knowledge Foundation | Knowledge library and metadata, acquisition and file ownership (without DOI lookup), versions of a work, Home and everyday organization, search/filters/saved searches, Markdown notes and typed connections, trash and permanent deletion, Hub integration, local operation; documents open in an external reader |
| M20 Reading & Annotation | Built-in PDF reader, reading positions, bookmarks, reusable highlights, sticky-note annotations, annotated PDF copy |
| M21 Research & Preservation | Citations and bibliographies, BibTeX/RIS/CSL JSON, explicitly requested DOI lookup (Crossref) and metadata retrieval, explicit knowledge exports, backup and restore |
| M22 Import & Migration | Existing-library migration (Advanced), library-wide duplicate review and metadata merge workflows; watch folders only if still wanted (Future) |

Book-inator links, academic chapters linked to parent books and cross-module search follow once the cross-module link specification exists.



## Approved M19 trash clarification

Owner clarification for M19: recoverable trash is logical. Removed items and their associated research context are hidden from the active library and remain restorable. Managed files retain their existing library paths; normal removal and restoration do not move files. Referenced originals remain untouched. Only a separately previewed and explicitly confirmed permanent deletion may remove affected managed copies. Physical trash relocation is not required for M19 and has no assigned future milestone.
