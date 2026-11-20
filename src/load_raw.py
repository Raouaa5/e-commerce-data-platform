import csv
import logging
import time
from pathlib import Path

from db import get_connection

DATA_DIR = Path("data/raw")

# table in the raw schema -> source CSV file
TABLES = {
    "customers": "olist_customers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "product_category_name_translation": "product_category_name_translation.csv",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(message)s",
)
log = logging.getLogger("load_raw")


class LoadError(Exception):
    """Raised when a load does not match its source file."""


def read_header(csv_path):
    """Return the column names from the first line of a CSV file."""
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        return next(csv.reader(f))


def count_csv_rows(csv_path):
    """Count data rows (not lines) in a CSV, excluding the header."""
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        return sum(1 for _ in csv.reader(f)) - 1


def load_table(conn, table, csv_path):
    """Empty raw.<table>, bulk-load the CSV, check row counts. Returns rows loaded."""
    if not csv_path.exists():
        raise LoadError(f"missing source file: {csv_path}")

    columns = ", ".join(read_header(csv_path))
    expected = count_csv_rows(csv_path)

    with conn.cursor() as cur:
        cur.execute(f"TRUNCATE raw.{table}")

        copy_sql = f"COPY raw.{table} ({columns}) FROM STDIN WITH (FORMAT csv, HEADER true)"
        with cur.copy(copy_sql) as copy:
            with open(csv_path, "rb") as f:
                while chunk := f.read(1024 * 1024):
                    copy.write(chunk)

        cur.execute(
            f"UPDATE raw.{table} SET _source_file = %s WHERE _source_file IS NULL",
            (csv_path.name,),
        )
        cur.execute(f"SELECT count(*) FROM raw.{table}")
        loaded = cur.fetchone()[0]

    if loaded != expected:
        raise LoadError(f"raw.{table}: {loaded} rows loaded, {expected} in {csv_path.name}")
    return loaded


def main():
    start = time.perf_counter()
    log.info("Loading %d tables from %s", len(TABLES), DATA_DIR)

    with get_connection() as conn:  # one transaction: all tables or none
        for table, filename in TABLES.items():
            t0 = time.perf_counter()
            n = load_table(conn, table, DATA_DIR / filename)
            log.info("raw.%-35s %9d rows  %5.1fs", table, n, time.perf_counter() - t0)

    log.info("Done in %.1fs", time.perf_counter() - start)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log.exception("Load failed, nothing was committed")
        raise SystemExit(1)