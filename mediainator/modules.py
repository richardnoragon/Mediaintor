"""Explicit ecosystem registry; unavailable modules never execute launch code."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Module:
    id: str
    name: str
    description: str
    available: bool = False

MODULES = (
    Module("bookinator", "Book-inator", "Browse, read and manage books", True),
    Module("musicinator", "Music-inator", "Catalog albums, editions, tracks and owned copies", True),
    Module("movieinator", "Movie-inator", "Catalog movies, editions and owned copies", True),
    Module("gameinator", "Game-inator", "Games"),
    Module("paperinator", "Paper-inator", "Collect, read, connect and preserve research knowledge", True),
    Module("documentinator", "Document-inator", "Other documents"),
    Module("stampinator", "Stamp-inator", "Stamps"),
    Module("pictureinator", "Picture-inator", "Pictures"),
    Module("currencyinator", "Currency-inator", "Currency"),
)


def launch_module(module_id, hub):
    module = next((m for m in MODULES if m.id == module_id), None)
    if module is None or not module.available:
        return False
    if module.id == "bookinator":
        hub.open_books()
        return True
    if module.id == "musicinator":
        hub.open_music()
        return True
    if module.id == "movieinator":
        hub.open_movies()
        return True
    if module.id == "paperinator":
        hub.open_papers()
        return True
    return False
