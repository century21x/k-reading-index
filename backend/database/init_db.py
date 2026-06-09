"""Initialize database schema and reference seeds."""

import sys
from pathlib import Path

from sqlalchemy import text

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database.connection import engine

DATABASE_DIR = Path(__file__).resolve().parent


def _run_sql_file(path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    with engine.begin() as conn:
        for statement in sql.split(";"):
            stmt = statement.strip()
            if stmt:
                conn.execute(text(stmt))


def init_database() -> None:
    _run_sql_file(DATABASE_DIR / "schema.sql")
    _run_sql_file(DATABASE_DIR / "seed_levels.sql")
    _run_sql_file(DATABASE_DIR / "seed_types.sql")


if __name__ == "__main__":
    init_database()
    print("Database initialized.")
