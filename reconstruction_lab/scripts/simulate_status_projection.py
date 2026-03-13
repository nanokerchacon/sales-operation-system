from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LINKS_CSV = PROJECT_ROOT / "reconstruction_lab" / "notes" / "document_links.csv"
OUTPUT_CSV = PROJECT_ROOT / "reconstruction_lab" / "notes" / "status_projection.csv"

STATUS_ORDER = [
    "confirmed",
    "delivered",
    "invoice_pending_acceptance",
    "invoiced",
    "rectified_review",
]


def main() -> int:
    counter = Counter({status: 0 for status in STATUS_ORDER})

    with LINKS_CSV.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            operational_status = (row.get("operational_status", "") or "").strip()
            document_status = (row.get("document_status", "") or "").strip()

            if operational_status in counter:
                counter[operational_status] += 1
            if document_status == "rectified_review":
                counter["rectified_review"] += 1

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["projected_status", "count"])
        writer.writeheader()
        for status in STATUS_ORDER:
            writer.writerow({"projected_status": status, "count": counter[status]})

    print(f"CSV generado en: {OUTPUT_CSV}")
    for status in STATUS_ORDER:
        print(f"{status}: {counter[status]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
