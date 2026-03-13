from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database.session import SessionLocal
from app.services.legacy_order_import import import_legacy_orders_from_csv


def main() -> int:
    parser = argparse.ArgumentParser(description="Import legacy orders from a CSV file")
    parser.add_argument("csv_path", help="Path to the legacy CSV file")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        stats = import_legacy_orders_from_csv(db, args.csv_path)
    except Exception as exc:
        db.rollback()
        print(f"Import failed: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()

    print("Legacy orders import completed")
    for key, value in stats.as_dict().items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
