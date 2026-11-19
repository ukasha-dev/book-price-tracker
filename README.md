# Book Price Tracker API

A small backend service that scrapes book data from [books.toscrape.com](https://books.toscrape.com), stores it in PostgreSQL and serves it through a REST API built with FastAPI.

## Quick start

Requires Docker and Docker Compose.

```bash
docker-compose up
```

The API is then available at http://localhost:8000 and the interactive docs at http://localhost:8000/docs. Use `docker-compose up --build` after changing the code.

The database starts empty, so `GET /books` returns no items at first. Call `POST /scrape` (or run the scraper, below) to load the data.

## Running the scraper

Through the API:

```bash
curl -X POST http://localhost:8000/scrape
```

As a standalone script, with the stack running:

```bash
docker-compose exec app python -m app.scraper
```

Use `exec`, not `run`: `run` replaces the container's start command and skips the database migration, so on a fresh clone the table would not exist.

Both ways scrape about 1,000 books, which takes one to two minutes depending on your connection. Running them again refreshes the existing rows (title, price, rating, category, availability and `scraped_at`) and never creates duplicates.

## API endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/books` | List books with pagination and optional filters |
| GET | `/books/{id}` | Get one book |
| POST | `/scrape` | Run the scraper and update the database |

`GET /books` query parameters:

| Parameter | Default | Description |
|---|---|---|
| `limit` | 20 | Page size, 1 to 100 |
| `offset` | 0 | Number of books to skip |
| `category` | | Exact category name, case-insensitive |
| `min_price` | | Minimum price, inclusive |
| `max_price` | | Maximum price, inclusive |

### List books

```bash
curl "http://localhost:8000/books?limit=2"
```

```json
{
  "items": [
    {
      "id": 1,
      "source_url": "https://books.toscrape.com/catalogue/its-only-the-himalayas_981/index.html",
      "title": "It's Only the Himalayas",
      "price": 45.17,
      "rating": 2,
      "category": "Travel",
      "availability": "In stock",
      "scraped_at": "2026-11-19T18:07:39.727714Z"
    }
  ],
  "total": 1000,
  "limit": 2,
  "offset": 0
}
```

(The response lists `limit` items; one is shown here.)

### Filter by category

```bash
curl "http://localhost:8000/books?category=Poetry"
```

### Filter by price range

```bash
curl "http://localhost:8000/books?min_price=10&max_price=15&limit=5&offset=10"
```

### Get one book

```bash
curl http://localhost:8000/books/1
```

```json
{
  "id": 1,
  "source_url": "https://books.toscrape.com/catalogue/its-only-the-himalayas_981/index.html",
  "title": "It's Only the Himalayas",
  "price": 45.17,
  "rating": 2,
  "category": "Travel",
  "availability": "In stock",
  "scraped_at": "2026-11-19T18:07:39.727714Z"
}
```

An unknown id returns `404` with `{"detail": "Book not found"}`.

### Trigger a scrape

```bash
curl -X POST http://localhost:8000/scrape
```

```json
{
  "scraped": 1000,
  "skipped": 0,
  "failed_pages": 0,
  "duration_seconds": 66.14
}
```

The request blocks until the scrape finishes.

### Errors

| Status | When |
|---|---|
| 404 | `GET /books/{id}` for a book that does not exist |
| 409 | `POST /scrape` while another scrape is running |
| 422 | Invalid query parameters, for example `min_price` greater than `max_price` |
| 502 | `POST /scrape` when the source website cannot be reached |

## Configuration

Credentials are never hardcoded in the application: it only reads `DATABASE_URL` from the environment. `docker-compose.yml` fills each value from the environment or a `.env` file and falls back to a development default, so that `docker-compose up` also works on a fresh clone with no setup. To use your own values, copy `.env.example` to `.env` and edit it. Do not use the defaults outside local development.

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_USER` | `bookuser` | Database user |
| `POSTGRES_PASSWORD` | `bookpass` | Database password |
| `POSTGRES_DB` | `bookdb` | Database name |
| `APP_PORT` | `8000` | Host port for the API |

The app itself reads `DATABASE_URL`, which Compose builds from the values above.

## Design decisions

- **Scraping:** `requests` and BeautifulSoup. The site is static HTML, so no browser or framework is needed. The crawler walks the 50 category pages (about 65 requests) because every listing card already has title, price, rating and availability, and the page tells the category. Visiting all 1,000 detail pages would take about 16 times more requests.
- **No duplicates:** each book is keyed by its product URL, which is unique and stable, and written with `INSERT ... ON CONFLICT DO UPDATE`.
- **Error handling:** a page that fails to load after retries is logged and counted in `failed_pages`, and the run continues. A card with a missing field is skipped and counted in `skipped`. If the home page cannot be reached the scrape fails with a 502 and writes nothing.
- **Schema:** one `books` table with a unique `source_url`, a `NUMERIC(10,2)` price, a rating check from 1 to 5, and indexes on `category` and `price`. It is created by an Alembic migration that runs when the container starts. Category is a plain column because the task only needs it as a filter; a separate table would be the next step if categories needed their own data.
- **Pagination:** `limit` and `offset`, ordered by `id` so pages are stable.
- **Category filter:** matches the exact name in any case by comparing `lower(category)`. That comparison cannot use the plain index on `category`, which only serves exact-case matches. At about 1,000 rows this makes no difference; a functional index on `lower(category)` would be the fix for a much larger table.
- **Scraping from the API:** `POST /scrape` blocks until the run finishes. A lock returns 409 for a second concurrent run. The lock lives in the process, so the app runs with a single uvicorn worker. In production I would run the scrape as a background task in a queue such as Celery and return a task id.

## Project layout

```
app/
  main.py          FastAPI app
  config.py        settings from environment variables
  database.py      engine and session dependency
  models.py        SQLAlchemy model
  schemas.py       Pydantic models
  crud.py          queries and the upsert
  routers/         /books and /scrape endpoints
  scraper/         fetch client, HTML parser, crawl runner
alembic/           database migration
tests/             pytest suite with saved HTML fixtures
```

## Tests and linting

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pytest
ruff check .
```

The API tests use an in-memory SQLite database so they run without Docker; Postgres-specific behavior (upsert, migration, constraints) is verified against the real database in the Docker run.

## Troubleshooting

- **Changed database credentials have no effect:** the data volume keeps the credentials from its first start. Run `docker-compose down -v` to delete it, then start again.
- **Port 8000 is busy:** set `APP_PORT` to another port in `.env`.
