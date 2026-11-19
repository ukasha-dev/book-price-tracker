from pydantic import BaseModel


class ScrapeResult(BaseModel):
    scraped: int
    skipped: int
    failed_pages: int
    duration_seconds: float
