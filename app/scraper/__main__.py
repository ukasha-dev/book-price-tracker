import logging

from app.database import SessionLocal
from app.logging_setup import configure_logging
from app.scraper.runner import run_scrape

logger = logging.getLogger(__name__)


def main() -> None:
    configure_logging()
    with SessionLocal() as db:
        result = run_scrape(db)
    logger.info("Scrape finished: %s", result.model_dump())


if __name__ == "__main__":
    main()
