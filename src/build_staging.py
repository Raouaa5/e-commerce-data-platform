import logging
from pathlib import Path

from db import get_connection

SQL_DIR = Path("sql/staging")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s")
log = logging.getLogger("build_staging")


def main():
    files = sorted(SQL_DIR.glob("*.sql"))
    log.info("Building %d staging views from %s", len(files), SQL_DIR)

    with get_connection() as conn:  # one transaction: all views or none
        for path in files:
            sql = path.read_text(encoding="utf-8")
            if not sql.strip():
                raise ValueError(f"{path.name} is empty")
            conn.execute(sql)
            log.info("built %s", path.stem)

    log.info("Done")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log.exception("Build failed, nothing was committed")
        raise SystemExit(1)