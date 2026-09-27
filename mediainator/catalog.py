"""In-memory catalog shared by both Book-inator presentations."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Book:
    id: str
    title: str
    author: str
    formats: tuple[str, ...]
    tags: tuple[str, ...]
    reading_status: str = "Unknown"
    paths: tuple[tuple[str, str], ...] = ()
    cover: str = ""
    uuid: str = ""
    series: str = ""
    missing_fields: tuple[str, ...] = ()


SAMPLE_BOOKS = (
    Book("sample-alice", "Alice's Adventures in Wonderland", "Lewis Carroll",
         ("EPUB", "MOBI", "PDF"), ("Fantasy", "Children's fiction")),
    Book("sample-time", "The Time Machine", "H. G. Wells",
         ("EPUB", "MOBI"), ("Science fiction",)),
    Book("sample-raven", "The Raven", "Edgar Allan Poe",
         ("EPUB", "PDF"), ("Poetry",)),
)


def find_books(books: tuple[Book, ...], query: str, tags=(), formats=(), statuses=()) -> list[Book]:
    """Literal text matching; AND categories, OR values within each category."""
    query = query.strip().casefold()
    return sorted(
        (book for book in books
         if any(query in value.casefold() for value in (book.title, book.author, book.series))
         and (not tags or set(tags).intersection(book.tags))
         and (not formats or set(formats).intersection(book.formats))
         and (not statuses or book.reading_status in statuses)),
        key=lambda book: (book.title.casefold(), book.id),
    )
