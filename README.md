# OpenSkagit

OpenSkagit is a small Python app for loading Skagit County public data into DuckDB and querying it from a browser.

## What is included

- A FastAPI backend with health, source, table, load, and read-only SQL endpoints.
- A simple static frontend at `/` for loading data and running queries.
- Railway deployment config that uses Railpack and starts Uvicorn with Railway's `PORT` variable.
- DuckDB helpers for local CSV, assessor ZIP, and ArcGIS ingestion.
- Agent-facing helper functions that make the loaded DuckDB data easier to inspect and query with AI.

## Data resources

OpenSkagit can work with these public Skagit County data resources:

- **ArcGIS parcels**: `arcgis_parcels` loads layer `0` from Skagit County's `OpenData/AssessorDataParcels` ArcGIS FeatureServer.
- **ArcGIS zoning**: `arcgis_zoning` loads layer `14` from Skagit County's `Planning/ComprehensivePlanWebMap` ArcGIS MapServer.
- **Assessor ZIP**: the assessor loader downloads `SkagitAssessmentData.zip` from Skagit County, extracts each CSV, and creates one DuckDB table per CSV.
- **Local assessor CSVs**: `app/main.py` can load CSV files from `app/data/assessor` into DuckDB for local experiments.

Loaded data is stored in DuckDB. By default the database file is `openskagit.duckdb`; set `OPENSKAGIT_DB_PATH` to use another path, such as a Railway volume mount.

## How OpenSkagit uses AI

OpenSkagit does not call an AI model by itself. Instead, it provides a simple, safe workflow that an AI assistant or agent can follow when answering questions about the loaded data:

1. **Inspect the database first** with `describe_database()` or `GET /api/tables`. This returns the available tables and columns so the AI does not invent table names or fields.
2. **Load missing public data only when needed** with `load_source(source_id, where="1=1", limit=1000)` or `POST /api/load/arcgis`. This keeps the workflow small and repeatable.
3. **Query with SQL** using `sql_tool(sql)` or `POST /api/sql`. SQL through the web API is limited to one read-only statement with `SELECT`, `WITH`, `SHOW`, `DESCRIBE`, or `PRAGMA`.
4. **Answer from evidence**. Agent answers should include the direct answer, the SQL used, the row count, and key evidence fields from the query result.

The intended agent instructions are:

```text
Always call describe_database first.
Never invent columns.
Use sql_tool for analysis.
Use load_source only when a missing ArcGIS source is needed.
Answers must include direct answer, SQL used, row count, and key evidence fields.
```

This design keeps the AI layer separate from data loading and querying. The app owns the public data connections, DuckDB storage, and read-only SQL guardrails; an AI assistant only inspects schema, runs evidence-based queries, and summarizes results.

## Basic workflow

1. Start the app locally or deploy it to Railway.
2. Open the browser UI.
3. Load a public data source:
   - choose an ArcGIS source and row limit, then click **Load ArcGIS source**; or
   - click **Load assessor ZIP** to download and load assessor CSV tables.
4. Click **Refresh tables** to review available tables, row counts, and columns.
5. Run read-only SQL in the query box.
6. If using an AI assistant, have it inspect the database schema first, run SQL for analysis, and cite the evidence fields it used.

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
