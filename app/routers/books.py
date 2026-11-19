from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app import crud
from app.database import DbSession
from app.schemas import BookFilters, BookList, BookRead

router = APIRouter(prefix="/books", tags=["Books"])


@router.get("", response_model=BookList, summary="List books")
def list_books(filters: Annotated[BookFilters, Query()], db: DbSession) -> BookList:
    """Return one page of books, optionally filtered by category and price range."""
    books, total = crud.list_books(db, filters)
    return BookList.model_validate(
        {"items": books, "total": total, "limit": filters.limit, "offset": filters.offset}
    )


@router.get(
    "/{book_id}",
    response_model=BookRead,
    summary="Get one book",
    responses={404: {"description": "Book not found"}},
)
def get_book(book_id: int, db: DbSession) -> BookRead:
    book = crud.get_book(db, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return BookRead.model_validate(book)
