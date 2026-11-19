import threading

from fastapi import APIRouter, HTTPException

from app.database import DbSession
from app.schemas import ScrapeResult
from app.scraper.runner import ScrapeUnavailable, run_scrape

router = APIRouter(tags=["Scraper"])

scrape_lock = threading.Lock()


@router.post(
    "/scrape",
    response_model=ScrapeResult,
    summary="Run the scraper",
    responses={
        409: {"description": "A scrape is already running"},
        502: {"description": "The source website could not be reached"},
    },
)
def scrape(db: DbSession) -> ScrapeResult:
    """Scrape books.toscrape.com and update the database. Blocks until the run finishes."""
    if not scrape_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="Scrape already in progress")
    try:
        return run_scrape(db)
    except ScrapeUnavailable as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    finally:
        scrape_lock.release()
