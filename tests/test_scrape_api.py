from app.routers import scrape as scrape_router
from app.scraper.runner import ScrapeUnavailable


def test_second_concurrent_scrape_returns_409(client):
    assert scrape_router.scrape_lock.acquire(blocking=False)
    try:
        response = client.post("/scrape")
    finally:
        scrape_router.scrape_lock.release()

    assert response.status_code == 409
    assert response.json() == {"detail": "Scrape already in progress"}


def test_scrape_unavailable_returns_502(client, monkeypatch):
    def unavailable(db):
        raise ScrapeUnavailable("site is down")

    monkeypatch.setattr(scrape_router, "run_scrape", unavailable)

    response = client.post("/scrape")

    assert response.status_code == 502
