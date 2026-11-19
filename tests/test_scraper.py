import pytest
import requests

from app.scraper import __main__ as entrypoint
from app.scraper import runner
from app.scraper.client import get_html
from app.scraper.parser import parse_category_urls
from app.scraper.runner import ScrapeUnavailable, scrape_all

BASE_URL = "https://books.toscrape.com/"


class DownSession:
    def get(self, url: str, timeout: float) -> requests.Response:
        raise requests.ConnectionError("site is down")


def serve(monkeypatch, pages: dict[str, bytes]) -> None:
    monkeypatch.setattr(runner, "get_html", lambda session, url, timeout: pages.get(url))


def test_get_html_returns_none_when_request_fails():
    assert get_html(DownSession(), BASE_URL, timeout=1) is None


def test_failed_category_page_counted_not_fatal(monkeypatch, load_fixture):
    home = load_fixture("home.html")
    first_category = parse_category_urls(home, BASE_URL)[0]
    serve(monkeypatch, {BASE_URL: home, first_category: load_fixture("category_last_page.html")})

    outcome = scrape_all(object(), BASE_URL, timeout=1)

    assert len(outcome.books) == 19
    assert outcome.failed_pages == 49


def test_script_exits_with_error_when_site_unreachable(monkeypatch):
    def unavailable(db):
        raise ScrapeUnavailable("site is down")

    monkeypatch.setattr(entrypoint, "run_scrape", unavailable)

    with pytest.raises(SystemExit) as exit_info:
        entrypoint.main()

    assert exit_info.value.code == 1


def test_home_page_failure_raises_scrape_unavailable(monkeypatch):
    serve(monkeypatch, {})

    with pytest.raises(ScrapeUnavailable):
        scrape_all(object(), BASE_URL, timeout=1)
