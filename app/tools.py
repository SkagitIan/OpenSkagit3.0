"""Small DuckDB and ArcGIS helpers."""

import json
import re

import duckdb
import pandas as pd
import requests

from app.sources import SOURCES

conn = duckdb.connect("openskagit.duckdb")

_SAFE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _table_name(name):
    if not _SAFE_NAME.match(name):
        raise ValueError(f"Unsafe table name: {name}")
    return name


def load_csv_table(table, path):
    """Load a CSV file into a DuckDB table."""
    table = _table_name(table)
    conn.execute(
        f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM read_csv_auto(?)",
        [str(path)],
    )
    return conn.execute(f"SELECT COUNT(*) AS rows FROM {table}").fetchone()[0]


def arcgis_query(source, where="1=1", limit=1000, geometry=None):
    """Query an ArcGIS layer and return its features."""
    url = source["url"].rstrip("/")
    layer = source["layer"]
    query_url = f"{url}/{layer}/query"
    params = {
        "f": "json",
        "where": where,
        "outFields": "*",
        "returnGeometry": "true",
        "resultRecordCount": limit,
    }
    if geometry is not None:
        params["geometry"] = json.dumps(geometry) if isinstance(geometry, dict) else geometry
        params["geometryType"] = "esriGeometryEnvelope"
        params["spatialRel"] = "esriSpatialRelIntersects"

    response = requests.get(query_url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise RuntimeError(data["error"])
    return data.get("features", [])


def features_to_df(features):
    """Convert ArcGIS features into a pandas DataFrame."""
    rows = []
    for feature in features:
        row = dict(feature.get("attributes", {}))
        if "geometry" in feature:
            row["geometry"] = json.dumps(feature["geometry"])
        rows.append(row)
    return pd.DataFrame(rows)


def load_arcgis(source_id, where="1=1", limit=1000):
    """Load an ArcGIS source into DuckDB."""
    source = SOURCES[source_id]
    table = _table_name(source["table"])
    features = arcgis_query(source, where=where, limit=limit)
    df = features_to_df(features)
    conn.register("arcgis_df", df)
    conn.execute(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM arcgis_df")
    conn.unregister("arcgis_df")
    return len(df)


def run_sql(sql):
    """Run SQL against the shared DuckDB connection."""
    return conn.execute(sql).df()


def describe_tables():
    """Return table names and row counts in the DuckDB database."""
    tables = conn.execute("SHOW TABLES").fetchall()
    rows = []
    for (table,) in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {_table_name(table)}").fetchone()[0]
        rows.append({"table": table, "rows": count})
    return pd.DataFrame(rows)
