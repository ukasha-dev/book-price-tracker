# Book Price Tracker API

Scrapes book data from [books.toscrape.com](https://books.toscrape.com), saves it to Postgres, and serves it over a FastAPI REST API.

Demo video: [watch the walkthrough](https://www.loom.com/share/f513eebd1aff41cc9cb3b3e6aa2c1a48)

## Run it

You need Docker and Docker Compose.

```bash
docker-compose up
```

The API runs at http://localhost:8000 and the docs are at http://localhost:8000/docs. If you change the code, rebuild with `docker-compose up --build`.

The database starts empty, so `GET /books` returns nothing until you run a scrape (see below).

## Scraping

Trigger it through the API:

```bash
curl -X POST http://localhost:8000/scrape
```

Or run it as a script while the stack is running:

```bash
docker-compose exec app python -m app.scraper
```

Use `exec`, not `run`. `run` overrides the container's start command and skips the migration, so the table won't exist on a fresh clone.

A full scrape pulls about 1,000 books and takes one to two minutes. Running it again updates existing rows instead of creating duplicates.

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/books` | List books, with pagination and filters |
| GET | `/books/{id}` | Get one book |
| POST | `/scrape` | Run the scraper and update the database |

Query parameters for `GET /books`:

| Parameter | Default | Description |
|---|---|---|
| `limit` | 20 | Page size, 1 to 100 |
| `offset` | 0 | Number of books to skip |
| `category` | | Category name, not case sensitive |
| `min_price` | | Minimum price, inclusive |
| `max_price` | | Maximum price, inclusive |

### List books

```bash
curl "http://localhost:8000/books?limit=1"
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
  "limit": 1,
  "offset": 0
}
```

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

### Run a scrape

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

### Error responses

| Status | When |
|---|---|
| 404 | `GET /books/{id}` for a book that does not exist |
| 409 | `POST /scrape` while another scrape is running |
| 422 | Invalid query parameters, for example `min_price` greater than `max_price` |
| 502 | `POST /scrape` when the source website cannot be reached |

## Configuration

Docker Compose reads these variables from your environment or a `.env` file. If they aren't set, it uses default dev values so `docker-compose up` works on a fresh clone. To set your own, copy `.env.example` to `.env` and edit it. The defaults are for local use only.

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_USER` | `bookuser` | Database user |
| `POSTGRES_PASSWORD` | `bookpass` | Database password |
| `POSTGRES_DB` | `bookdb` | Database name |
| `APP_PORT` | `8000` | Port the API is published on |

The app itself only reads `DATABASE_URL`, which Compose builds from these values.

## How it works

I used `requests` and BeautifulSoup since the site is just static HTML. Instead of opening every single book page, the scraper crawls the category pages, which already list all the fields and give you the category. That cuts down the number of requests a lot.

To avoid duplicates, each book is matched by its product URL and saved with `INSERT ... ON CONFLICT DO UPDATE`. If a page still fails after retries, I log it, bump `failed_pages`, and keep going. Any book missing a field gets skipped and counted in `skipped`. If the home page can't be reached at all, nothing gets written and the API returns 502.

There's a single `books` table with a unique `source_url`, a `NUMERIC(10,2)` price, a 1 to 5 rating check, and indexes on `category` and `price`. An Alembic migration creates it when the container starts.

Category is just a plain column because I only use it for filtering. The filter compares `lower(category)`, which won't hit the plain index on `category`, though with about 1,000 rows that doesn't really matter.

`POST /scrape` blocks until the scrape finishes, and an in-process lock returns 409 if another run is already going. Since that lock only works within one process, the app runs a single uvicorn worker. In production I'd move this to a background job like Celery and return a task id instead.

## Project layout

```
app/
  main.py          FastAPI app
  config.py        settings from environment variables
  database.py      engine and session
  models.py        SQLAlchemy model
  schemas.py       Pydantic models
  crud.py          queries and the upsert
  routers/         /books and /scrape endpoints
  scraper/         fetch client, HTML parser, crawler
alembic/           database migration
tests/             pytest tests with saved HTML fixtures
```

## Tests and linting

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
ruff check .
```

On Windows, activate the venv with `.venv\Scripts\activate`.

The API tests run against an in-memory SQLite database so you don't need Docker. Postgres-specific stuff (the upsert, the migration, and the constraints) gets tested against the real database when running in Docker.

## Troubleshooting

- Changed database credentials have no effect: the data volume keeps the credentials from its first start. Run `docker-compose down -v` to wipe it, then start again.
- Port 8000 is busy: set `APP_PORT` to another port in `.env`.