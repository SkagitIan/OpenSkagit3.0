"""Small FastAPI web app for OpenSkagit."""

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.agent_tools import describe_database
from app.ingest_zip import DEFAULT_ASSESSOR_ZIP_URL, load_assessor_zip
from app.sources import SOURCES
from app.tools import describe_tables, load_arcgis, run_sql

app = FastAPI(title="OpenSkagit", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


class SqlRequest(BaseModel):
    """Request body for read-only SQL queries."""

    sql: str


class ArcgisLoadRequest(BaseModel):
    """Request body for loading an ArcGIS source."""

    source_id: str
    where: str = "1=1"
    limit: int = 1000


class AssessorLoadRequest(BaseModel):
    """Request body for loading assessor CSVs from a ZIP file or URL."""

    zip_path_or_url: str = DEFAULT_ASSESSOR_ZIP_URL


READ_ONLY_PREFIXES = ("select", "show", "describe", "pragma", "with")


def _records_from_frame(frame) -> list[dict[str, Any]]:
    return frame.where(frame.notna(), None).to_dict(orient="records")


def _validate_read_only_sql(sql: str) -> str:
    cleaned = sql.strip().rstrip(";")
    if not cleaned:
        raise HTTPException(status_code=400, detail="SQL is required.")
    if ";" in cleaned:
        raise HTTPException(status_code=400, detail="Only one SQL statement is allowed.")
    if not cleaned.lower().startswith(READ_ONLY_PREFIXES):
        raise HTTPException(status_code=400, detail="Only read-only SQL is allowed.")
    return cleaned


@app.get("/")
def index():
    """Serve the simple browser UI."""
    return FileResponse("app/static/index.html")


@app.get("/health")
def health():
    """Railway health check endpoint."""
    return {"ok": True}


@app.get("/api/sources")
def sources():
    """List configured ArcGIS sources."""
    return {"sources": SOURCES}


@app.get("/api/tables")
def tables():
    """List DuckDB tables and columns."""
    summary = _records_from_frame(describe_tables())
    return {"tables": summary, "database": describe_database()}


@app.post("/api/sql")
def sql_query(request: SqlRequest):
    """Run one read-only SQL statement against DuckDB."""
    sql = _validate_read_only_sql(request.sql)
    try:
        frame = run_sql(sql)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {
        "columns": list(frame.columns),
        "row_count": len(frame),
        "rows": _records_from_frame(frame.head(200)),
    }


@app.post("/api/load/arcgis")
def load_arcgis_source(request: ArcgisLoadRequest):
    """Load a configured ArcGIS source into DuckDB."""
    if request.source_id not in SOURCES:
        raise HTTPException(status_code=404, detail="Unknown source_id.")
    if request.limit < 1 or request.limit > 10000:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 10000.")
    try:
        row_count = load_arcgis(request.source_id, where=request.where, limit=request.limit)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {"source_id": request.source_id, "row_count": row_count}


@app.post("/api/load/assessor")
def load_assessor(request: AssessorLoadRequest):
    """Load assessor CSVs from a ZIP file or URL into DuckDB."""
    try:
        summaries = load_assessor_zip(request.zip_path_or_url)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {"tables": summaries}
