from dataclasses import asdict

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import Book
from app.scraper.parser import ScrapedBook

REFRESHED_COLUMNS = ("title", "price", "rating", "category", "availability")


def dedupe_by_url(books: list[ScrapedBook]) -> list[ScrapedBook]:
    return list({book.source_url: book for book in books}.values())


def upsert_books(db: Session, books: list[ScrapedBook]) -> None:
    rows = [asdict(book) for book in dedupe_by_url(books)]
    if not rows:
        return
    statement = insert(Book)
    statement = statement.on_conflict_do_update(
        index_elements=[Book.source_url],
        set_={
            **{column: statement.excluded[column] for column in REFRESHED_COLUMNS},
            "scraped_at": func.now(),
        },
    )
    db.execute(statement, rows)
    db.commit()
