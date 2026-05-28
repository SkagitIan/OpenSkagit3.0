"""Agent-facing helpers for inspecting and querying OpenSkagit data."""

from app.tools import conn, load_arcgis

AGENT_SYSTEM_INSTRUCTIONS = """Always call describe_database first.
Never invent columns.
Use sql_tool for analysis.
Use load_source only when a missing ArcGIS source is needed.
Answers must include direct answer, SQL used, row count, and key evidence fields."""


def describe_database():
    """Return DuckDB table names and columns."""
    tables = conn.execute("SHOW TABLES").fetchall()
    database = []

    for (table_name,) in tables:
        columns = conn.execute(f"PRAGMA table_info('{table_name}')").fetchall()
        database.append(
            {
                "table": table_name,
                "columns": [
                    {"name": column[1], "type": column[2]}
                    for column in columns
                ],
            }
        )

    return database


def load_source(source_id, where="1=1", limit=1000):
    """Load an ArcGIS source into DuckDB."""
    return load_arcgis(source_id, where=where, limit=limit)


def sql_tool(sql):
    """Run SQL through DuckDB and return a compact result summary."""
    result = conn.execute(sql)
    columns = [description[0] for description in result.description]
    rows = result.fetchall()

    return {
        "row_count": len(rows),
        "columns": columns,
        "rows": [dict(zip(columns, row)) for row in rows[:200]],
    }
