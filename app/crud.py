from dataclasses import asdict

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import Book
from app.schemas import BookFilters
from app.scraper.parser import ScrapedBook

REFRESHED_COLUMNS = ("title", "price", "rating", "category", "availability")


def dedupe_by_url(books: list[ScrapedBook]) -> list[ScrapedBook]:
    return list({book.source_url: book for book in books}.values())


def list_books(db: Session, filters: BookFilters) -> tuple[list[Book], int]:
    query = select(Book)
    if filters.category is not None:
        query = query.where(func.lower(Book.category) == filters.category.lower())
    if filters.min_price is not None:
        query = query.where(Book.price >= filters.min_price)
    if filters.max_price is not None:
        query = query.where(Book.price <= filters.max_price)
    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()
    page = query.order_by(Book.id).limit(filters.limit).offset(filters.offset)
    return list(db.scalars(page)), total


def get_book(db: Session, book_id: int) -> Book | None:
    return db.get(Book, book_id)


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
