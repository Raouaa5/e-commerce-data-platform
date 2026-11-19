import os
import psycopg
from dotenv import load_dotenv

load_dotenv()  # reads .env and puts its values in environment variables


def get_connection():
    """Open a connection to the Olist database using settings from .env."""
    return psycopg.connect(
        host="localhost",
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )


if __name__ == "__main__":
    with get_connection() as conn:
        version = conn.execute("SELECT version()").fetchone()[0]
        print("Connected:", version)