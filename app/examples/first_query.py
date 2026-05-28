"""FIRST_SUCCESS_TARGET example query for OpenSkagit.

This script is intentionally small and exploratory. Assessor CSV column names can
change, so it prints likely columns before showing the final query shape.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.tools import describe_tables, load_arcgis, run_sql


ZONING_TABLE = "arcgis_zoning"

COLUMN_SEARCHES = {
    "parcel id (PARCELID)": ["PARCELID", "parcel_id", "parcel", "pid"],
    "acreage (Acres)": ["Acres", "acre", "land_acres", "landacres", "area"],
    "year built (YearBuilt)": ["YearBuilt", "year_built", "yrbuilt", "built"],
    "zoning column for Rural Reserve": ["Rural Reserve", "zoning", "zone", "comp", "designation"],
}


def quote_name(name):
    """Quote a DuckDB identifier."""
    return '"' + name.replace('"', '""') + '"'


def table_names():
    """Return current DuckDB table names."""
    tables = describe_tables()
    if tables.empty:
        return []
    return tables["table"].tolist()


def columns_for(table):
    """Return column names for a table."""
    info = run_sql(f"PRAGMA table_info({quote_name(table)})")
    return info["name"].tolist()


def print_tables_and_columns():
    """Print available tables and their columns."""
    tables = describe_tables()
    if tables.empty:
        print("No DuckDB tables found yet.")
        return

    print("Available tables and columns:")
    for _, row in tables.iterrows():
        columns = columns_for(row["table"])
        print(f"- {row['table']} ({row['rows']} rows): {', '.join(columns)}")


def find_column_candidates():
    """Print likely columns for the first success target."""
    print("\nLikely column candidates before FIRST_SUCCESS_TARGET query:")
    found = {}
    for label, searches in COLUMN_SEARCHES.items():
        matches = []
        for table in table_names():
            for column in columns_for(table):
                column_lower = column.lower()
                if any(search.lower() in column_lower for search in searches):
                    matches.append((table, column))
        found[label] = matches
        if matches:
            match_text = ", ".join(f"{table}.{column}" for table, column in matches)
        else:
            match_text = "no likely columns found"
        print(f"- {label}: {match_text}")
    return found


def first_match(matches):
    """Return the first (table, column) pair from a candidate list."""
    return matches[0] if matches else (None, None)


def print_first_success_target_sql(candidates):
    """Show a clearly labeled placeholder SQL query for the target."""
    parcel_table, parcel_col = first_match(candidates["parcel id (PARCELID)"])
    acres_table, acres_col = first_match(candidates["acreage (Acres)"])
    year_table, year_col = first_match(candidates["year built (YearBuilt)"])
    zoning_table, zoning_col = first_match(candidates["zoning column for Rural Reserve"])

    assessor_table = parcel_table or acres_table or year_table or "YOUR_ASSESSOR_TABLE"
    parcel_expr = f"a.{quote_name(parcel_col)}" if parcel_col else "a.PARCELID"
    acres_expr = f"a.{quote_name(acres_col)}" if acres_col else "a.Acres"
    year_expr = f"a.{quote_name(year_col)}" if year_col else "a.YearBuilt"
    zoning_expr = f"z.{quote_name(zoning_col)}" if zoning_col else "z.YOUR_ZONING_COLUMN"

    print("\nFIRST_SUCCESS_TARGET placeholder SQL")
    print("Target: parcels over 5 acres, Rural Reserve zoning, homes built before 1970")
    print(
        f"""
-- FIRST_SUCCESS_TARGET
-- Review the candidate columns above, then replace any placeholder names.
-- This assumes your assessor parcel table can be joined to zoning by PARCELID.
SELECT
    {parcel_expr} AS PARCELID,
    {acres_expr} AS Acres,
    {year_expr} AS YearBuilt,
    {zoning_expr} AS zoning
FROM {quote_name(assessor_table)} AS a
JOIN {quote_name(zoning_table or ZONING_TABLE)} AS z
    ON {parcel_expr} = z.PARCELID
WHERE TRY_CAST({acres_expr} AS DOUBLE) > 5
  AND {zoning_expr} ILIKE '%Rural Reserve%'
  AND TRY_CAST({year_expr} AS INTEGER) < 1970
LIMIT 25;
""".strip()
    )

    if not all([parcel_table, acres_table, year_table, zoning_table]):
        print("\nSkipping execution: choose real table/column names for the placeholders above first.")
        return

    print("\nNot executing automatically; verify the join key and column choices first.")


def main():
    print_tables_and_columns()

    if ZONING_TABLE not in table_names():
        print(f"\nLoading {ZONING_TABLE} from ArcGIS because it is not in DuckDB yet...")
        try:
            row_count = load_arcgis(ZONING_TABLE, limit=1000)
        except Exception as error:  # Keep the example useful when ArcGIS is unreachable.
            print(f"Could not load {ZONING_TABLE}: {error}")
            print("Continuing so you can still review the FIRST_SUCCESS_TARGET query shape.")
        else:
            print(f"Loaded {row_count} rows into {ZONING_TABLE}.")
            print_tables_and_columns()

    candidates = find_column_candidates()
    print_first_success_target_sql(candidates)


if __name__ == "__main__":
    main()
