# Paper-inator Constitution

Status: agreed planning constitution, incorporating owner decisions through 26 September 2026. Requirements below govern design and future delivery; they do not claim implemented functionality or authorize implementation or release.

## 1. Authority and reference order

Explicit owner decisions take precedence. The [Hub constitution](../mediaintor%20hub/constitution_hub.md) governs shared behavior; this document defines Paper-inator's domain principles. Conflicts must be reconciled against recorded decisions rather than resolved through undocumented assumptions.

The Paper-inator sources were reviewed in filesystem creation-date order, oldest first. Newer decisions supersede conflicting older proposals:

| Created, Europe/Berlin | Document |
| --- | --- |
| 2026-09-26 19:34 | [Concept draft](paperinator%20concept%20draft.md) |
| 2026-09-26 19:35 | [Feature draft](paperinator%20feature%20draft.md) |
| 2026-09-26 19:38 | [Technical overview draft](paperinator%20technical%20overview%20draft.md) |
| 2026-09-26 19:51 | [Constitution draft](paperinator%20constittion%20draft.md) |
| 2026-09-26 19:53 | [Scope refinement](scope%20refinement.md) |
| 2026-09-26 20:33 | [Overview](paperinator%20overview.md) |
| 2026-09-26 20:59 | [Features](paperinator%20features.md) |

Subsequent owner decisions explicitly establish personal research ownership, recoverable removal, managed-file trash, and approval for constitutional amendments. They govern the corresponding sections below. Future file timestamps alone do not authorize constitutional amendments.

The [Book-inator constitution](../bookinator/bookinator_constituion.md), [Movie-inator constitution](../movieinator/movieinator_constitution.md), and [Music-inator constitution](../musicinator/musicinator_constitution.md) provide references for shared integration, recovery, and documentation discipline. Their domain-specific implementation choices and third-party reference features are not automatically Paper-inator commitments.

## 2. Purpose and primary objects

Paper-inator exists to help users collect, understand, organize, connect, preserve, and reuse research knowledge. Knowledge management comes first. Citations and bibliographies support that work without making Paper-inator primarily a writing application.

The **Knowledge Item** is the primary object. Notes, highlights, projects, and connections are first-class supporting objects. A user must be able to begin with an item or an independent research note without first creating a project.

One personal library can contain many optional projects. An item can belong to several projects without duplication. Connections and reusable highlights must remain useful through ordinary views and links, independently of any future graph visualization.

Reading progress, library handling, and personal flags remain separate dimensions. Archiving must not silently reset reading progress or destroy research associations.

## 3. Local operation and explicit online actions

Core library use must work offline and require no account: local import, reading, annotation, organization, search, and export. Network-dependent operations such as DOI lookup must be clearly identified and occur only when requested.

Documents, notes, annotations, projects, and other user content must not be automatically uploaded. Online metadata retrieval is not blanket permission to send local documents or research context to a provider.

Future synchronization must remain optional, explicitly configured, and user controlled. It must not introduce implicit synchronization between users. Optional future AI assistance must be clearly labelled and distinguishable from source material and user-authored content.

## 4. Personal research ownership

Personal research activity belongs to the active user profile and remains private unless explicitly exported or shared.

This includes notes, highlights, annotations, reading positions, reading progress, flags, project membership, saved searches, and workspace preferences. Profile switching must preserve ownership rather than transfer personal activity to the newly active profile.

The foundation contains no shared libraries, automatic sharing, or implicit cross-user synchronization. Future collaboration must preserve explicit user control and must not silently make existing private material shared.

Exports must show their scope, including personal research content and whether files are included. Privacy is a product requirement; this constitution does not select encryption, authentication, or an operating-system security mechanism.

## 5. Documents, versions, and source fidelity

Original source documents must be preserved. Import explicitly distinguishes managed copies from files referenced in their existing locations. Referenced originals must not be silently moved, renamed, overwritten, or deleted.

A Knowledge Item may group versions of the same work after user review. The user can choose a preferred version for opening, citation defaults, and metadata purposes. Choosing a preferred version must not silently overwrite conflicting information.

Highlights, annotations, bookmarks, and reading positions belong to the exact document version where they originated. They must retain that association when a preferred version changes. A quotation must retain its actual source and page or location reference; a different preferred version must not silently replace that evidence.

Paper-inator annotations are stored separately from original PDFs. An annotated PDF copy may be exported explicitly. External annotation import, synchronization, and PDF write-back are deferred capabilities, not implied by external-reader support. Any future write-back must preserve originals and comply with the amendment process if it would change that principle.

## 6. Recoverable removal and permanent deletion

Normal removal places a Knowledge Item in recoverable trash. Its associated research information remains recoverable, including notes, highlights, connections, retained reading history or state, and project links. This preservation requirement does not itself add a new comprehensive reading-history feature.

Referenced files remain untouched. Managed files associated with the removal enter logical recoverable trash, retaining their existing paths rather than being moved or destroyed. The original file from which a managed copy was made remains an original source, not a deletion target.

Restoration must recover the item and its surviving research associations. Removing one item must not destroy an independent note, another item's data, or a file still required by another surviving association. Detailed shared-association rules must be specified before implementation.

Permanent deletion is a separate explicit action. Before confirmation, show the affected item, research information, connections, history or state, project associations, and managed files. Explain that affected managed files will be removed and referenced originals will remain on disk. Do not silently expand deletion beyond the displayed scope.

Trash is not a backup. Retention, storage representation, and shared-file handling require detailed specification; they must not introduce silent permanent purging contrary to the explicit-deletion principle.

## 7. Reviewable changes and recovery

Metadata discovery may propose changes. Existing metadata must not be silently overwritten; users must be able to inspect proposed values and their sources and retain existing information.

Duplicate detection must distinguish identical files, versions of one work, and separate works. Grouping and resolution require review and must preserve research context rather than discard conflicting values silently.

Imports and bulk changes must expose their scope and results. Operations should be recoverable wherever practical. Failures must be reported accurately, with retained edits or recovery paths rather than false success messages.

Backup and restore must state what they cover: library data, personal research context, settings, managed files, and referenced files or paths. A stored path is not a backup of the referenced document. Restore must explain replacement effects and preserve recoverability.

## 8. Module ownership and Hub integration

Book-inator owns books. Paper-inator may link to and cite books, search linked books, and include them in research projects without taking over their management. Academic chapters can be Knowledge Items linked to their parent book.

Paper-inator owns research knowledge items. Document-inator owns general administrative and personal documents. Purpose, not file format alone, determines this boundary. These later owner decisions refine the earlier Hub description of Paper-inator as scientific papers only.

Paper-inator launches through the Hub and follows shared navigation, profile, appearance, workspace, activity, and recovery policies. It must not invent a competing suite-wide permission or workspace system. Its core research library remains usable without unrelated modules.

Shared appearance applies to ordinary application controls under the Hub's appearance boundary; document presentation and external-reader behavior are not silently replaced by application-theme changes.

Module closure, Hub exit, and profile switching must respect applicable shared unsaved-edit and task-review rules. External-reader capabilities and position-restoration limitations must be described accurately. Unrelated external applications must not be closed as though Paper-inator owns them.

Inherited suite requirements are not claims that every future Hub feature is available in the initial Paper-inator delivery.

## 9. Scope discipline

The feature document distinguishes **Foundation**, **Advanced**, and **Future**. Foundation describes the capabilities required to fulfill the product purpose; delivery may span several milestones. Advanced and Future entries are not automatic commitments for the initial release.

Projects remain optional. Citation management remains a capability. Graph visualization, recommendations, AI assistance, collaboration, cloud synchronization, browser capture, and word-processor plugins must not become prerequisites for core knowledge work.

No framework, database schema, provider, citation engine, annotation format, or sync protocol is selected by this constitution. Technical choices may evolve within these requirements.

## 10. Amendments and documentation

Changes affecting any constitutional principle require explicit owner approval. The principles include knowledge management first, Knowledge Items as the primary object, optional projects, first-class highlights and connections, local operation, no account requirement, no automatic uploads, personal ownership, original preservation, recoverable removal, explicit permanent deletion, and module ownership boundaries.

An approved amendment requires a constitution update, an overview update, a feature-document review, and a technical-document review where applicable. Review outcomes must be recorded; affected documents must be reconciled rather than left with competing requirements.

Routine implementation choices within these boundaries do not require separate constitutional approval. This rule must not create approval requests for ordinary reversible work already authorized by the owner.

Documentation must distinguish agreed requirements, unresolved details, implemented behavior, and verified acceptance. A feature's appearance in this constitution is not evidence that it has shipped.

## 11. Review of existing documents

For this constitution, the overview and features receive matching personal-ownership and removal rules. The earlier technical overview was reviewed: its storage and adapter suggestions remain exploratory. It does not yet specify profile isolation, recoverable trash, version-bound annotations, or restore semantics. Those details require a later technical specification, with this constitution governing them.

Earlier drafts remain historical references. Their broader feature ideas and proposed milestone ordering do not override the agreed overview, features, or subsequent owner decisions.


## Approved M19 trash clarification

Owner clarification for M19: recoverable trash is logical. Removed items and their associated research context are hidden from the active library and remain restorable. Managed files retain their existing library paths; normal removal and restoration do not move files. Referenced originals remain untouched. Only a separately previewed and explicitly confirmed permanent deletion may remove affected managed copies. Physical trash relocation is not required for M19 and has no assigned future milestone.
