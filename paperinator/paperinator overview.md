# Paper-inator — Research and Knowledge Management

Status: agreed product overview, based on owner scope decisions. This document describes intended behavior, not implemented or verified functionality. Delivery milestones and technical specifications will be defined separately.

## Collect, understand, connect, and preserve knowledge

Paper-inator is a local-first personal research and knowledge management module launched from the Media-inator Hub. It helps researchers, students, technical professionals, and lifelong learners collect sources, read them, capture understanding, connect ideas, and use that knowledge in projects.

Knowledge management comes first. Citation management is a supported workflow, but Paper-inator is not primarily a writing tool. A user can begin by importing a paper and making a note; projects and more advanced workflows remain optional.

The everyday journey is: collect a Knowledge Item, read it, annotate it, connect it to other knowledge, use it in projects, and cite it when needed.

## A library centered on Knowledge Items

The primary object is a **Knowledge Item**. The planned scope includes research papers, conference papers and proceedings, theses and dissertations, technical reports, white papers, datasets, academic book chapters, standards and specifications, and research-related web resources. Research notes can also exist independently of a source.

An item brings together its descriptive metadata, content location or attachments, tags, reading progress, notes, highlights, and connections. Bibliographic information can include title, authors, publication details, year, abstract, keywords, and identifiers such as DOI where applicable. Not every type of item requires the same fields or a local PDF.

One library holds the items. Optional projects gather relevant items, notes, and highlights for a particular investigation. An item can participate in several projects without duplicating its library record.

## Start with what needs attention

The default Paper-inator Home dashboard presents Inbox items, recently opened items, Continue Reading, items needing review, active projects, and recent notes.

Users can choose Home Dashboard, Library, Projects, or Restore Last View as their startup behavior. The default is Home Dashboard, with Inbox and recent activity.

Organization uses independent dimensions rather than one compulsory sequence:

| Dimension | Values |
| --- | --- |
| Reading progress | Unread, Reading, Read |
| Library handling | Inbox, Active, Archived |
| Independent flags | Needs Review, Key Reference, Favorite |

A paper can be Read, Active, and a Key Reference at the same time. Archiving an item does not reset its reading progress. Tags, searches, and project membership provide additional ways to organize the library.

## Read and keep the useful passages

The built-in PDF reader is the default reading experience, with an external-reader option. It supports remembered reading positions, bookmarks, highlights, sticky-note annotations, and full-text search. Users remain free to open their documents outside Paper-inator.

Highlights are reusable knowledge objects. Each retains its source document and page or location reference. Users can search highlights across the library, link them to notes and other Knowledge Items, include them in projects, and export them with source references.

Reader details, including interoperability with annotations made in external readers, will be specified separately; offering an external reader does not itself promise annotation synchronization.

## Capture your own understanding

Notes can accompany a source or stand independently. They can record summaries, findings, methods, limitations, questions, research ideas, meeting notes, and experiment results. Users do not need to create a dummy paper to save an idea.

Knowledge Items, notes, highlights, and projects can be connected. Initial relationship types include **Supports, Contradicts, Extends, Uses, Derived From, References, and Related To**. Ordinary views, searches, and links make these connections usable from the beginning.

An interactive knowledge graph and custom relationship types are later capabilities. The underlying connections remain useful without graph visualization.

## Bring sources into the library deliberately

The initial acquisition scope includes PDF import, folder import, manual entry, and explicitly requested DOI lookup. Import presents an explicit file-handling choice:

| Choice | Behavior |
| --- | --- |
| Managed copy | Copy the selected file into the Paper-inator library. |
| Referenced file | Leave the file in its original location and record a reference to it. |

Users should be able to change between these models later where practical, through an explicit operation. Import and file-management details must make their effects clear and preserve the user's control of originals.

Importing existing reference libraries, including exchange formats and migrations from tools such as Zotero, EndNote, and Mendeley, follows the initial acquisition work. Browser capture is a later stage. Specific migration coverage will be defined and tested separately.

## Review metadata and automation

Metadata extraction and online retrieval may propose information. Changes to existing metadata require review before application. Users should be able to see what would change and where the proposed information came from.

Source material, user-authored notes, and any future AI-generated suggestions remain distinguishable. AI summaries, topic extraction, and suggested connections are optional later features and must be clearly labelled. They must not silently become user notes or authoritative source metadata.

## Cite and export your research

The planned initial product scope includes formatted citations, bibliographies, citation style support, and BibTeX, RIS, and CSL JSON export. These capabilities support knowledge work alongside reading and organization; their implementation may be staged within the foundation work.

Users can explicitly export selected Knowledge Items, projects, notes, highlights, metadata, and relationships. An export preview shows what is included, with a separate choice about including files. Highlight exports retain their source references. Citation formats and broader knowledge exports serve different purposes; the detailed export specification will define how each object is represented.

Word, LibreOffice, and Google Docs integration, including citation toolbars and plugins, is deferred. The initial library is personal; shared libraries, team permissions, real-time collaboration, and multi-user editing are also deferred.

## Work alongside the other Hub modules

Paper-inator follows the Hub's module navigation and shared appearance conventions while retaining its own research workflows.

Books remain owned and managed by Book-inator. Paper-inator's planned integration can link to those books, cite them, include them in research projects, and search linked books without creating a second book-management system. Academic chapters can be Knowledge Items with a connection to their parent book where available.

Purpose determines the boundary with Document-inator. Research papers, research reports, standards, and research-related web resources belong in Paper-inator. Administrative and personal documents, such as tax records, insurance contracts, and utility bills, belong in Document-inator. File format alone does not determine ownership.

Cross-module linking details will be specified separately. Paper-inator's core research library must remain usable without depending on unrelated modules.

## Local first, with user-owned data

Core collecting, reading, annotation, organization, search, and export work offline and require no account. Users own their documents, metadata, notes, annotations, projects, and research history. Open exchange formats support access to that information outside Paper-inator.

Online operations, such as DOI lookup, metadata retrieval, or reference verification, occur only when requested. Documents, notes, annotations, and projects are not automatically uploaded to external services. Network-dependent lookups require connectivity; the rest of the library remains usable without them.

Imports, metadata updates, and bulk changes should be recoverable wherever practical. Automation must make changes understandable and reviewable.

Future synchronization must be optional, explicitly configured, and user controlled.

## Foundation and later growth

The agreed foundation covers Knowledge Items, notes, reusable highlights, projects, typed connections, a personal local library, PDF reading, tags and independent states, explicit file handling, metadata review, citations, and explicit exports. This is the initial product scope, not a promise to deliver every capability in one milestone.

Later work can add existing-library migration, browser capture, interactive graph visualization, custom relationships, discovery and recommendations, optional AI assistance, word-processor integration, collaboration, and optional synchronization. Videos, recorded lectures, and presentations are potential later source types.

Detailed feature, technical, and constitutional documents should elaborate this agreed scope. Earlier Paper-inator drafts provide background; where they differ, the decisions recorded here guide the next specification.


## Constitutional ownership and preservation clarification

The [Paper-inator constitution](paperinator%20constition.md) incorporates the owner's subsequent decisions and governs these requirements.

Personal research context belongs to the active profile: notes, highlights, annotations, reading positions and progress, flags, project membership, saved searches, and workspace preferences. It remains private unless explicitly exported or shared. The foundation includes no shared libraries, automatic sharing, or implicit synchronization between users.

Normal removal places the Knowledge Item and its associated research information in recoverable trash, including notes, highlights, connections, retained reading history or state, and project links. Managed files enter logical recoverable trash without changing their paths; referenced originals remain untouched. Independent objects and files still required by surviving associations must be preserved.

Permanent deletion is a separate explicit action. Its preview explains the affected research information and managed files and states that referenced originals remain on disk. Trash does not replace backup. Detailed retention and shared-association behavior must preserve these principles.

Changes to constitutional principles require explicit owner approval, a constitution update, an overview update, and review of feature and applicable technical documentation. Routine implementation choices within these boundaries do not require separate constitutional approval.


## Approved M19 trash clarification

Owner clarification for M19: recoverable trash is logical. Removed items and their associated research context are hidden from the active library and remain restorable. Managed files retain their existing library paths; normal removal and restoration do not move files. Referenced originals remain untouched. Only a separately previewed and explicitly confirmed permanent deletion may remove affected managed copies. Physical trash relocation is not required for M19 and has no assigned future milestone.
