from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    scrape_base_url: str = "https://books.toscrape.com/"
    request_timeout: float = 10.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
