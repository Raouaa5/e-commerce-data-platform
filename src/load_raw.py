import csv
from pathlib import Path

from db import get_connection

DATA_DIR = Path("data/raw")


def read_header(csv_path):
    """Return the column names from the first line of a CSV file."""
    with open(csv_path, encoding="utf-8", newline="") as f:
        return next(csv.reader(f))


def load_table(conn, table, csv_path):
    """Empty raw.<table>, then bulk-load the CSV into it. Returns rows loaded."""
    columns = ", ".join(read_header(csv_path))

    with conn.cursor() as cur:
        cur.execute(f"TRUNCATE raw.{table}")

        copy_sql = f"COPY raw.{table} ({columns}) FROM STDIN WITH (FORMAT csv, HEADER true)"
        with cur.copy(copy_sql) as copy:
            with open(csv_path, "rb") as f:
                while chunk := f.read(1024 * 1024):  # 1 MB at a time
                    copy.write(chunk)

        cur.execute(
            f"UPDATE raw.{table} SET _source_file = %s WHERE _source_file IS NULL",
            (csv_path.name,),
        )
        cur.execute(f"SELECT count(*) FROM raw.{table}")
        return cur.fetchone()[0]


if __name__ == "__main__":
    with get_connection() as conn:
        n = load_table(conn, "orders", DATA_DIR / "olist_orders_dataset.csv")
        print(f"raw.orders: {n} rows")