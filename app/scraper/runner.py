import logging
from dataclasses import dataclass, field

import requests

from app.scraper.client import get_html
from app.scraper.parser import (
    ScrapedBook,
    next_page_url,
    parse_category_name,
    parse_category_urls,
    parse_listing,
)

logger = logging.getLogger(__name__)


class ScrapeUnavailable(Exception):
    pass


@dataclass
class ScrapeOutcome:
    books: list[ScrapedBook] = field(default_factory=list)
    skipped: int = 0
    failed_pages: int = 0


def scrape_all(session: requests.Session, base_url: str, timeout: float) -> ScrapeOutcome:
    home_html = get_html(session, base_url, timeout)
    if home_html is None:
        raise ScrapeUnavailable(f"Could not load {base_url}")

    outcome = ScrapeOutcome()
    for category_url in parse_category_urls(home_html, base_url):
        _scrape_category(session, category_url, timeout, outcome)
    return outcome


def _scrape_category(
    session: requests.Session, category_url: str, timeout: float, outcome: ScrapeOutcome
) -> None:
    page_url: str | None = category_url
    while page_url is not None:
        html = get_html(session, page_url, timeout)
        if html is None:
            outcome.failed_pages += 1
            return
        try:
            category = parse_category_name(html)
        except ValueError as error:
            logger.warning("Skipping page %s: %s", page_url, error)
            outcome.failed_pages += 1
            return
        books, skipped = parse_listing(html, page_url, category)
        outcome.books.extend(books)
        outcome.skipped += skipped
        page_url = next_page_url(html, page_url)
