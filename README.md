# OpenSkagit

OpenSkagit is a small Python app for loading Skagit County public data into DuckDB and querying it from a browser.

## What is included

- A FastAPI backend with health, source, table, load, and read-only SQL endpoints.
- A simple static frontend at `/` for loading data and running queries.
- Railway deployment config that uses Railpack and starts Uvicorn with Railway's `PORT` variable.
- DuckDB helpers for local CSV, assessor ZIP, and ArcGIS ingestion.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.server:app --reload
```

Open <http://127.0.0.1:8000>.

## Deploy on Railway

1. Push this repository to GitHub.
2. Create a new Railway project from the GitHub repo.
3. Railway will use `railway.json` and run:

   ```bash
   uvicorn app.server:app --host 0.0.0.0 --port ${PORT:-8000}
   ```

4. Optional but recommended: add a Railway volume and set `OPENSKAGIT_DB_PATH` to a mounted path such as `/data/openskagit.duckdb` so loaded data survives redeploys.
5. Visit the deployed URL, load an ArcGIS source, refresh tables, and run a read-only SQL query.

## API endpoints

- `GET /health` - health check for Railway.
- `GET /api/sources` - configured ArcGIS sources.
- `GET /api/tables` - current DuckDB tables, row counts, and columns.
- `POST /api/load/arcgis` - load a configured ArcGIS source.
- `POST /api/load/assessor` - download and load the assessor ZIP.
- `POST /api/sql` - run one read-only SQL statement. Allowed prefixes are `SELECT`, `WITH`, `SHOW`, `DESCRIBE`, and `PRAGMA`.

## Notes

The app is intentionally simple. It does not include authentication, so do not expose private datasets through it without adding access controls first.
