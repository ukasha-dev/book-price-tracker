from decimal import Decimal

from app.crud import dedupe_by_url
from app.scraper.parser import ScrapedBook


def make_book(url: str, title: str) -> ScrapedBook:
    return ScrapedBook(
        source_url=url,
        title=title,
        price=Decimal("1.00"),
        rating=1,
        category="Poetry",
        availability="In stock",
    )


def test_dedupe_by_url_keeps_one_row_per_url():
    books = [make_book("u1", "old"), make_book("u2", "other"), make_book("u1", "new")]

    result = dedupe_by_url(books)

    assert [book.title for book in result] == ["new", "other"]
