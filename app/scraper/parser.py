import logging
import re
from dataclasses import dataclass
from decimal import Decimal
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

RATINGS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


@dataclass(frozen=True, slots=True)
class ScrapedBook:
    source_url: str
    title: str
    price: Decimal
    rating: int
    category: str
    availability: str


def parse_price(text: str) -> Decimal:
    match = re.search(r"\d+(?:\.\d+)?", text)
    if match is None:
        raise ValueError(f"No price in {text!r}")
    return Decimal(match.group())


def parse_rating(css_classes: list[str]) -> int:
    for css_class in css_classes:
        if css_class in RATINGS:
            return RATINGS[css_class]
    raise ValueError(f"No rating in classes {css_classes!r}")


def parse_category_urls(html: bytes, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select("div.side_categories ul ul a")
    return [urljoin(base_url, str(link["href"])) for link in links]


def parse_category_name(html: bytes) -> str:
    heading = BeautifulSoup(html, "html.parser").select_one("h1")
    if heading is None:
        raise ValueError("Category page has no heading")
    return heading.get_text(strip=True)


def parse_listing(html: bytes, page_url: str, category: str) -> tuple[list[ScrapedBook], int]:
    soup = BeautifulSoup(html, "html.parser")
    books: list[ScrapedBook] = []
    skipped = 0
    for card in soup.select("article.product_pod"):
        book = _parse_card(card, page_url, category)
        if book is None:
            skipped += 1
        else:
            books.append(book)
    return books, skipped


def next_page_url(html: bytes, page_url: str) -> str | None:
    link = BeautifulSoup(html, "html.parser").select_one("li.next a")
    if link is None:
        return None
    return urljoin(page_url, str(link["href"]))


def _parse_card(card: Tag, page_url: str, category: str) -> ScrapedBook | None:
    link = card.select_one("h3 a")
    price = card.select_one("p.price_color")
    rating = card.select_one("p.star-rating")
    stock = card.select_one("p.availability")
    if link is None or price is None or rating is None or stock is None:
        logger.warning("Skipping card with missing fields on %s", page_url)
        return None
    title, href = link.get("title"), link.get("href")
    if not title or not href:
        logger.warning("Skipping card without title or link on %s", page_url)
        return None
    try:
        parsed_price = parse_price(price.get_text())
        parsed_rating = parse_rating(rating.get("class", []))
    except ValueError as error:
        logger.warning("Skipping %r on %s: %s", title, page_url, error)
        return None
    return ScrapedBook(
        source_url=urljoin(page_url, str(href)),
        title=str(title),
        price=parsed_price,
        rating=parsed_rating,
        category=category,
        availability=" ".join(stock.get_text().split()),
    )
