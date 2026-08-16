import csv
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "instance" / "cartrust.sqlite3"
COLS = ["source", "title", "make", "model", "year", "min_price", "avg_price", "max_price", "sample_size", "source_url", "license_note"]


def integer(value):
    return int("".join(ch for ch in str(value or "") if ch.isdigit()) or 0)


def main(csv_path):
    DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vehicle_reference (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL, title TEXT NOT NULL, make TEXT, model TEXT, year INTEGER,
            min_price INTEGER, avg_price INTEGER, max_price INTEGER, sample_size INTEGER,
            source_url TEXT, license_note TEXT, updated_at TEXT NOT NULL
        )
    """)
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        missing = set(COLS) - set(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"Faltan columnas: {', '.join(sorted(missing))}")
        count = 0
        for row in reader:
            conn.execute(
                """
                INSERT INTO vehicle_reference
                (source,title,make,model,year,min_price,avg_price,max_price,sample_size,source_url,license_note,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (row["source"], row["title"], row["make"], row["model"], integer(row["year"]), integer(row["min_price"]), integer(row["avg_price"]), integer(row["max_price"]), integer(row["sample_size"]), row["source_url"], row["license_note"], datetime.now(timezone.utc).isoformat(timespec="seconds")),
            )
            count += 1
    conn.commit()
    print(f"Importadas {count} referencias autorizadas.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Uso: python scripts/import_reference_csv.py data/reference_authorized_template.csv")
    main(sys.argv[1])
