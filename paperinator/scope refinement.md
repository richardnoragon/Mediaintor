Should Paper-inator primarily be a citation manager (EndNote replacement), a research workspace (ReadCube replacement), or a knowledge management system (something closer to Obsidian + Zotero)?

Personally, for your -inator ecosystem, I would aim for the third option. It is both more distinctive and integrates naturally with the Hub vision.

Geben Sie Ihr Feedback zu BizChat ab.
You said:
it should be more of a knowledge management system at first, primarly, but could be expanded later like the modules
Copilot said:

I think that's exactly the right direction for Paper-inator and, honestly, it makes it much more aligned with your existing ecosystem.

If you try to compete with EndNote on day one, you'll spend years chasing citation edge cases.

If instead you build:

Paper-inator = Research Knowledge Management

and

Citation Management = one capability among many

then you create something that fits naturally beside Book-inator.

Revised Positioning

Instead of:

Paper-inator
=
Reference Manager


I would define:

Paper-inator
=
Research Knowledge Operating System


for:

Researchers
Students
PhD candidates
Technical professionals
Lifelong learners
Anyone managing large amounts of knowledge
Relationship to Book-inator

I would make them siblings, not competitors.

Book-inator

Answers:

"What books do I own and read?"

Focus:

Books
Series
Authors
Libraries
Reading
Paper-inator

Answers:

"What knowledge have I collected, understood and connected?"

Focus:

Papers
Articles
Reports
Notes
Research Projects
Knowledge Networks
The Core Object Should NOT Be A Citation

This is the biggest architectural decision.

Most reference managers use:

Reference


as the central object.

Instead I would make:

Knowledge Item


the central object.

Examples:

Journal paper
PDF
Web article
Book chapter
Thesis
Dataset
YouTube lecture
Personal note
Website
Conference talk

All become first-class citizens.

This avoids the "it's only for academics" trap.

Proposed Core Entities
Knowledge Item

Contains:

Metadata
Content location
Tags
Notes
Relationships
Notes

Could be:

Summary
Key insights
Quotes
Questions
Action items

Exactly like researchers actually work.

Project

Examples:

PhD Thesis
Home Lab Research
Media-inator Design
AI Knowledge Base


Projects collect everything together.

Collections

User-defined groups.

Example:

Machine Learning
Knowledge Management
Information Retrieval
UI Design

Relationships

The future killer feature.

Examples:

Paper A supports Paper B

Paper C contradicts Paper D

Note E belongs to Project F

Dataset G used by Paper H


This becomes a personal knowledge graph.

Constitution Draft v2
Purpose

Paper-inator exists to help users collect, understand, organize, connect and preserve knowledge.

Principle 1

Knowledge First

Paper-inator prioritizes understanding information over storing citations.

Principle 2

Local First

All core functions operate without cloud services.

Principle 3

User Ownership

Users own their PDFs, notes, annotations, metadata and research history.

Principle 4

Connections Matter

Knowledge items should be linkable and contextualized rather than isolated.

Principle 5

References Are Important But Not Central

Citation management supports knowledge work but does not define it.

Principle 6

Incremental Complexity

A new user can start with:

Import PDF
Add Note
Done


Advanced workflows remain optional.

Module Roadmap

This also fits your modular philosophy perfectly.

M1 Foundation
Knowledge items
Collections
Tags
Local storage
M2 Reading
PDF viewer
Reading position
Highlights
M3 Notes
Linked notes
Rich text notes
Note search
M4 Projects
Research projects
Project dashboards
M5 Metadata
DOI lookup
PubMed
Crossref
M6 Citations
BibTeX
RIS
Bibliographies
M7 Knowledge Graph
Relationships
Visualization
Topic maps
M8 Discovery
Recommendations
Similar papers
Smart collections
How I Would Describe It In One Sentence

For your ecosystem, I'd use:

Paper-inator is a local-first research and knowledge management module that helps users collect, read, connect and preserve knowledge, with citation management as an integrated capability rather than its primary purpose.

That vision is distinct from EndNote, Mendeley, Zotero, and Papers while still allowing you to eventually absorb many of their strongest features as the module matures.