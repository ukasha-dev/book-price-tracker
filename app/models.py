from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Book(Base):
    __tablename__ = "books"
    __table_args__ = (
        UniqueConstraint("source_url", name="uq_books_source_url"),
        CheckConstraint("price >= 0", name="ck_books_price_non_negative"),
        CheckConstraint("rating BETWEEN 1 AND 5", name="ck_books_rating_range"),
        Index("ix_books_category", "category"),
        Index("ix_books_price", "price"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_url: Mapped[str] = mapped_column(String(500))
    title: Mapped[str] = mapped_column(String(500))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    rating: Mapped[int] = mapped_column(SmallInteger)
    category: Mapped[str] = mapped_column(String(100))
    availability: Mapped[str] = mapped_column(String(100))
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
