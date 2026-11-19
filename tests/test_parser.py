from decimal import Decimal

from app.scraper.parser import (
    ScrapedBook,
    next_page_url,
    parse_category_name,
    parse_category_urls,
    parse_listing,
)

BASE_URL = "https://books.toscrape.com/"
POETRY_URL = "https://books.toscrape.com/catalogue/category/books/poetry_23/index.html"
DEFAULT_URL = "https://books.toscrape.com/catalogue/category/books/default_15/index.html"
CATALOGUE_URL = "https://books.toscrape.com/catalogue/page-1.html"
LIGHT_IN_THE_ATTIC = "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"


def test_parse_category_urls_returns_50(load_fixture):
    urls = parse_category_urls(load_fixture("home.html"), BASE_URL)

    assert len(urls) == 50
    assert urls[0] == "https://books.toscrape.com/catalogue/category/books/travel_2/index.html"


def test_parse_category_name_reads_heading(load_fixture):
    assert parse_category_name(load_fixture("category_page.html")) == "Default"


def test_parse_listing_extracts_all_fields(load_fixture):
    html = load_fixture("category_last_page.html")

    books, skipped = parse_listing(html, POETRY_URL, "Poetry")

    assert skipped == 0
    assert len(books) == 19
    assert books[0] == ScrapedBook(
        source_url=LIGHT_IN_THE_ATTIC,
        title="A Light in the Attic",
        price=Decimal("51.77"),
        rating=3,
        category="Poetry",
        availability="In stock",
    )


def test_parse_listing_skips_cards_missing_fields_and_counts_them(load_fixture):
    html = load_fixture("cards_missing_fields.html")

    books, skipped = parse_listing(html, CATALOGUE_URL, "Test")

    assert [book.title for book in books] == ["Good Book"]
    assert books[0].price == Decimal("10.00")
    assert skipped == 4


def test_next_page_url_resolves_relative_link(load_fixture):
    html = load_fixture("category_page.html")

    assert next_page_url(html, DEFAULT_URL) == (
        "https://books.toscrape.com/catalogue/category/books/default_15/page-2.html"
    )


def test_next_page_url_none_on_last_page(load_fixture):
    assert next_page_url(load_fixture("category_last_page.html"), POETRY_URL) is None


def test_same_book_gives_identical_url_from_category_page_and_direct_link(load_fixture):
    from_category, _ = parse_listing(load_fixture("category_last_page.html"), POETRY_URL, "Poetry")
    from_catalogue, _ = parse_listing(load_fixture("catalogue_page.html"), CATALOGUE_URL, "Poetry")

    assert from_category[0].source_url == from_catalogue[0].source_url == LIGHT_IN_THE_ATTIC
