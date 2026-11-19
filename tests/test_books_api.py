def test_list_books_returns_first_page_with_total(client, seeded_books):
    response = client.get("/books")

    body = response.json()
    assert response.status_code == 200
    assert body["total"] == 25
    assert len(body["items"]) == 20
    assert body["limit"] == 20
    assert body["offset"] == 0
    assert body["items"][0]["price"] == 2.5
    assert isinstance(body["items"][0]["price"], float)


def test_filter_by_category_case_insensitive(client, seeded_books):
    body = client.get("/books", params={"category": "poetry"}).json()

    assert body["total"] == 10
    assert {item["category"] for item in body["items"]} == {"Poetry"}


def test_price_range_filter_inclusive(client, seeded_books):
    body = client.get("/books", params={"min_price": 10, "max_price": 20}).json()

    assert [item["price"] for item in body["items"]] == [10.0, 12.5, 15.0, 17.5, 20.0]


def test_get_unknown_book_returns_404(client):
    response = client.get("/books/9999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Book not found"}


def test_min_greater_than_max_returns_422(client):
    response = client.get("/books", params={"min_price": 20, "max_price": 10})

    assert response.status_code == 422
