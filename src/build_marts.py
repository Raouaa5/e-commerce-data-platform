import logging
from pathlib import Path

from db import get_connection

SQL_DIR = Path("sql/marts")

# Order matters: dimensions first, then facts.
MODELS = [
    "dim_date",
    "dim_products",
    "dim_sellers",
    "dim_customers",
    "fct_order_items",
    "fct_orders",
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s")
log = logging.getLogger("build_marts")


def main():
    log.info("Building %d mart tables", len(MODELS))
    with get_connection() as conn:  # one transaction: all tables or none
        for name in MODELS:
            path = SQL_DIR / f"{name}.sql"
            sql = path.read_text(encoding="utf-8")
            if not sql.strip():
                raise ValueError(f"{path.name} is empty")
            conn.execute(sql)
            rows = conn.execute(f"SELECT count(*) FROM marts.{name}").fetchone()[0]
            log.info("built marts.%-16s %9d rows", name, rows)
    log.info("Done")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log.exception("Build failed, nothing was committed")
        raise SystemExit(1)