import os
from collections.abc import Callable, Iterator
from decimal import Decimal
from pathlib import Path

import pytest

os.environ["DATABASE_URL"] = "sqlite://"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base, Book  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def load_fixture() -> Callable[[str], bytes]:
    def load(name: str) -> bytes:
        return (FIXTURES / name).read_bytes()

    return load


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with sessionmaker(engine, expire_on_commit=False)() as session:
        yield session


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def seeded_books(db_session: Session) -> None:
    db_session.add_all(
        Book(
            source_url=f"https://books.toscrape.com/catalogue/book-{n}_{n}/index.html",
            title=f"Book {n}",
            price=Decimal("2.50") * n,
            rating=n % 5 + 1,
            category="Poetry" if n <= 10 else "Travel",
            availability="In stock",
        )
        for n in range(1, 26)
    )
    db_session.commit()
