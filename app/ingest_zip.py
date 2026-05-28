"""Load Skagit County assessor CSV ZIP files into DuckDB."""

from pathlib import Path
import os
import re
import tempfile
from urllib.parse import urlparse
from zipfile import ZipFile

import duckdb
import requests


DEFAULT_ASSESSOR_ZIP_URL = "https://www.skagitcounty.net/Assessor/Documents/DataDownloads/SkagitAssessmentData.zip"
ASSESSOR_DATA_DIR = Path(__file__).resolve().parent / "data" / "assessor"


def load_assessor_zip(zip_path_or_url=DEFAULT_ASSESSOR_ZIP_URL):
    """Extract assessor CSVs, load them into DuckDB, and return table summaries."""
    ASSESSOR_DATA_DIR.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as temp_dir:
        parsed = urlparse(str(zip_path_or_url))
        if parsed.scheme in {"http", "https"}:
            zip_path = Path(temp_dir) / "assessor.zip"
            response = requests.get(str(zip_path_or_url), timeout=60)
            response.raise_for_status()
            zip_path.write_bytes(response.content)
        else:
            zip_path = Path(zip_path_or_url)

        summaries = []
        db_path = os.getenv("OPENSKAGIT_DB_PATH", "openskagit.duckdb")
        conn = duckdb.connect(db_path)

        with ZipFile(zip_path) as archive:
            csv_members = [name for name in archive.namelist() if name.lower().endswith(".csv")]
            for member in sorted(csv_members):
                csv_path = ASSESSOR_DATA_DIR / Path(member).name
                with archive.open(member) as source, csv_path.open("wb") as target:
                    target.write(source.read())

                table_name = Path(csv_path.name).stem.lower()
                table_name = re.sub(r"[^a-z0-9]+", "_", table_name)
                table_name = re.sub(r"_+", "_", table_name).strip("_") or "table"

                conn.execute(
                    f'CREATE OR REPLACE TABLE "{table_name}" AS '
                    "SELECT * FROM read_csv_auto(?, ignore_errors=true)",
                    [str(csv_path)],
                )
                row_count = conn.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0]
                columns = [row[1] for row in conn.execute(f'PRAGMA table_info("{table_name}")').fetchall()]
                summaries.append(
                    {
                        "table": table_name,
                        "source_csv_path": str(csv_path),
                        "row_count": row_count,
                        "columns": columns,
                    }
                )

        conn.close()
        return summaries
