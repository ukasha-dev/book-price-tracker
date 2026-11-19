from fastapi import FastAPI

from app.logging_setup import configure_logging
from app.routers import books, scrape

configure_logging()

app = FastAPI(title="Book Price Tracker API")
app.include_router(books.router)
app.include_router(scrape.router)
