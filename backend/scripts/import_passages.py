"""
Import passages/questions from JSON seed files into SQLite.

Usage (from backend/):
  python scripts/import_passages.py
  python scripts/import_passages.py --file seeds/sample_passages.json
  python scripts/import_passages.py --file seeds/eps_template.json --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import func, select

from analyzer import analyze_text_complexity  # noqa: E402
from database.connection import SessionLocal  # noqa: E402
from database.init_db import init_database  # noqa: E402
from models.passage import Passage
from services.passage_service import create_passage_from_dict  # noqa: E402


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def merge_defaults(data: dict, defaults: dict) -> dict:
    merged = {**defaults, **data}
    for key in ("source_type", "source_name", "source_url", "license_type"):
        if key in defaults and key not in data:
            merged[key] = defaults[key]
    return merged


def passage_count(db) -> int:
    return db.scalar(select(func.count()).select_from(Passage).where(Passage.is_active.is_(True))) or 0


def import_file(path: Path, dry_run: bool = False, force: bool = False) -> int:
    payload = load_json(path)
    defaults = {
        k: payload[k]
        for k in (
            "source_type",
            "source_name",
            "source_url",
            "license_type",
            "commercial_ok",
            "derivative_ok",
        )
        if k in payload
    }

    passages = payload.get("passages", [])
    if not passages:
        print(f"No passages in {path}")
        return 0

    init_database()
    db = SessionLocal()
    if not dry_run and not force and passage_count(db) > 0:
        print(f"Skip import: {passage_count(db)} active passage(s) already in database. Use --force to re-import.")
        db.close()
        return 0

    count = 0
    try:
        for item in passages:
            record = merge_defaults(item, defaults)
            if dry_run:
                print(
                    f"[dry-run] {record['title']} "
                    f"(TOPIK {record['target_topik_level']}, "
                    f"{len(record.get('questions', []))} questions)"
                )
                count += 1
                continue
            create_passage_from_dict(db, record, analyzer_fn=analyze_text_complexity)
            count += 1
            print(f"Imported: {record['title']}")
        if not dry_run:
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Import passage JSON into database")
    parser.add_argument(
        "--file",
        type=Path,
        default=BACKEND_DIR / "seeds" / "sample_passages.json",
        help="JSON file path",
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate without writing")
    parser.add_argument("--force", action="store_true", help="Import even if passages already exist")
    args = parser.parse_args()

    path = args.file if args.file.is_absolute() else BACKEND_DIR / args.file
    if not path.exists():
        raise SystemExit(f"File not found: {path}")

    total = import_file(path, dry_run=args.dry_run, force=args.force)
    action = "Validated" if args.dry_run else "Imported"
    print(f"{action} {total} passage(s) from {path.name}")


if __name__ == "__main__":
    main()
