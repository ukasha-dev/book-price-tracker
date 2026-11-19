from fastapi import FastAPI

from app.logging_setup import configure_logging

configure_logging()

app = FastAPI(title="Book Price Tracker API")
