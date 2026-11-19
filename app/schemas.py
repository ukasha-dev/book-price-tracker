from datetime import datetime
from decimal import Decimal
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, model_validator

Price = Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]


class BookRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_url: str
    title: str
    price: Price
    rating: int
    category: str
    availability: str
    scraped_at: datetime


class BookList(BaseModel):
    items: list[BookRead]
    total: int
    limit: int
    offset: int


class BookFilters(BaseModel):
    category: str | None = Field(default=None, description="Exact category name, any case")
    min_price: Decimal | None = Field(default=None, ge=0)
    max_price: Decimal | None = Field(default=None, ge=0)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def check_price_range(self) -> Self:
        has_range = self.min_price is not None and self.max_price is not None
        if has_range and self.min_price > self.max_price:
            raise ValueError("min_price must not exceed max_price")
        return self


class ScrapeResult(BaseModel):
    scraped: int
    skipped: int
    failed_pages: int
    duration_seconds: float
