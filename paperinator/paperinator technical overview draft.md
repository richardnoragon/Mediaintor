2. Technical Overview

Given your ecosystem, I would keep this surprisingly simple initially.

Architecture
Media-inator Hub
    │
    ├── Book-inator
    ├── Music-inator
    ├── Paper-inator
    └── Future modules

Internal Layers
UI Layer

Qt / PySide

Consistent with Hub.

Service Layer

Modules:

library service
metadata service
PDF service
citation service
project service

Storage

SQLite.

Same philosophy as Book-inator.

Store:

References
Notes
Projects
Tags
Reading positions
File Storage
PaperLibrary/
    PDFs/
    Attachments/
    Notes/
    Exports/

Metadata Providers

Adapters:

Crossref Adapter
PubMed Adapter
arXiv Adapter


Exactly like your Calibre adapter concept.

Plugin Potential

Future:

Citation Style Adapter
Discovery Adapter
Import Adapter


But not in first release.