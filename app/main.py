"""Load local assessor CSVs and a small zoning sample."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.tools import describe_tables, load_arcgis, load_csv_table


DATA_DIR = Path(__file__).resolve().parent / "data" / "assessor"


def main():
    if DATA_DIR.exists():
        for csv_path in sorted(DATA_DIR.glob("*.csv")):
            table = "assessor_" + csv_path.stem.lower().replace("-", "_").replace(" ", "_")
            load_csv_table(table, csv_path)

    load_arcgis("arcgis_zoning", limit=100)
    print(describe_tables())


if __name__ == "__main__":
    main()
