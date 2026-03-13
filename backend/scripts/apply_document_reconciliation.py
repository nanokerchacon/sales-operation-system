from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database.session import SessionLocal
from app.models.client import Client
from app.models.invoice import Invoice
from app.models.order import Order


DOCUMENT_LINKS_CSV = PROJECT_ROOT / "reconstruction_lab" / "notes" / "document_links.csv"
REVIEW_CSV = PROJECT_ROOT / "reconstruction_lab" / "notes" / "document_links_review.csv"
ALLOWED_OPERATIONAL_STATUSES = {
    "confirmed",
    "delivered",
    "invoice_pending_acceptance",
    "invoiced",
}
INVOICE_STATUS_BY_DOCUMENT_STATUS = {
    "accepted": "accepted",
    "pending_acceptance": "pending_acceptance",
    "rectified_review": "rectified_review",
}


@dataclass
class ReconciliationRow:
    order_reference: str
    operational_status: str
    document_status: str
    confidence: str
    matching_rule: str
    notes: str


@dataclass
class Summary:
    found_orders: int = 0
    not_found_orders: int = 0
    changed_order_statuses: int = 0
    linked_invoice_documents: int = 0
    skipped_low_confidence: int = 0
    skipped_unresolved_review: int = 0
    skipped_ambiguous: int = 0
    skipped_invalid_reference: int = 0
    skipped_no_change: int = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply validated document reconciliation to the database")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Print proposed changes without committing them")
    mode.add_argument("--apply", action="store_true", help="Apply the reconciliation changes to the database")
    return parser.parse_args()


def load_unresolved_review_references(path: Path) -> set[str]:
    if not path.exists():
        return set()

    unresolved: set[str] = set()
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            order_reference = (row.get("order_reference", "") or "").strip()
            manual_resolution = (row.get("manual_resolution", "") or "").strip()
            if order_reference and not manual_resolution:
                unresolved.add(order_reference)
    return unresolved


def load_reconciliation_rows(path: Path) -> list[ReconciliationRow]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [
            ReconciliationRow(
                order_reference=(row.get("order_reference", "") or "").strip(),
                operational_status=(row.get("operational_status", "") or "").strip(),
                document_status=(row.get("document_status", "") or "").strip(),
                confidence=(row.get("confidence", "") or "").strip().lower(),
                matching_rule=(row.get("matching_rule", "") or "").strip(),
                notes=(row.get("notes", "") or "").strip(),
            )
            for row in reader
        ]


def parse_order_reference(order_reference: str) -> tuple[str, str] | None:
    value = (order_reference or "").strip().upper()
    if "_" not in value:
        return None
    series, order_number = value.split("_", 1)
    if not series or not order_number:
        return None
    return series, str(int(order_number)) if order_number.isdigit() else order_number


def is_ambiguous(row: ReconciliationRow) -> bool:
    lowered_notes = row.notes.lower()
    lowered_rule = row.matching_rule.lower()
    return "ambiguous_" in lowered_notes or "ambiguous_plan=" in lowered_notes or "ambiguous" in lowered_rule


def find_matching_orders(db, series: str, order_number: str) -> list[Order]:
    candidates = db.query(Order).filter(Order.series == series).all()
    matches: list[Order] = []
    for order in candidates:
        current_number = (order.order_number or "").strip()
        normalized_current = str(int(current_number)) if current_number.isdigit() else current_number
        if normalized_current == order_number:
            matches.append(order)
    return matches


def process_rows(rows: list[ReconciliationRow], unresolved_review: set[str], apply_changes: bool) -> int:
    summary = Summary()
    db = SessionLocal()
    try:
        for row in rows:
            if row.confidence == "low":
                summary.skipped_low_confidence += 1
                continue
            if row.order_reference in unresolved_review:
                summary.skipped_unresolved_review += 1
                continue
            if is_ambiguous(row):
                summary.skipped_ambiguous += 1
                continue
            if row.operational_status not in ALLOWED_OPERATIONAL_STATUSES:
                summary.skipped_invalid_reference += 1
                continue

            parsed_reference = parse_order_reference(row.order_reference)
            if parsed_reference is None:
                summary.skipped_invalid_reference += 1
                continue

            series, order_number = parsed_reference
            matches = find_matching_orders(db, series, order_number)
            if len(matches) != 1:
                summary.not_found_orders += 1
                print(
                    f"SKIP order_reference={row.order_reference} matches={len(matches)} "
                    f"reason=order_not_found_or_not_unique"
                )
                continue

            order = matches[0]
            summary.found_orders += 1

            order_changed = False
            invoice_updates = 0

            if order.status != row.operational_status:
                print(
                    f"ORDER #{order.id} {order.series}-{order.order_number}: "
                    f"{order.status or '-'} -> {row.operational_status} "
                    f"[rule={row.matching_rule}]"
                )
                if apply_changes:
                    order.status = row.operational_status
                summary.changed_order_statuses += 1
                order_changed = True

            target_invoice_status = INVOICE_STATUS_BY_DOCUMENT_STATUS.get(row.document_status)
            if target_invoice_status:
                invoices = list(order.invoices)
                if len(invoices) == 1:
                    invoice = invoices[0]
                    if invoice.invoice_status != target_invoice_status:
                        print(
                            f"INVOICE #{invoice.id} order={order.id}: "
                            f"{invoice.invoice_status} -> {target_invoice_status}"
                        )
                        if apply_changes:
                            invoice.invoice_status = target_invoice_status
                        invoice_updates += 1
                elif len(invoices) > 1:
                    print(
                        f"SKIP_INVOICES order_reference={row.order_reference} "
                        f"reason=multiple_invoice_rows count={len(invoices)}"
                    )

            if invoice_updates:
                summary.linked_invoice_documents += invoice_updates
            elif not order_changed:
                summary.skipped_no_change += 1

        if apply_changes:
            db.commit()
        else:
            db.rollback()

        print("")
        print("Resumen:")
        print(f"pedidos encontrados: {summary.found_orders}")
        print(f"pedidos no encontrados: {summary.not_found_orders}")
        print(f"cambios de estado: {summary.changed_order_statuses}")
        print(f"facturas/documentos vinculados: {summary.linked_invoice_documents}")
        print(f"registros omitidos por baja confianza: {summary.skipped_low_confidence}")
        print(f"registros omitidos por revision no resuelta: {summary.skipped_unresolved_review}")
        print(f"registros omitidos por ambiguedad: {summary.skipped_ambiguous}")
        print(f"registros omitidos por referencia invalida: {summary.skipped_invalid_reference}")
        print(f"registros omitidos sin cambios: {summary.skipped_no_change}")
        return 0
    except Exception as exc:
        db.rollback()
        print(f"Apply failed: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()


def main() -> int:
    args = parse_args()
    if not DOCUMENT_LINKS_CSV.exists():
        print(f"No existe el archivo: {DOCUMENT_LINKS_CSV}", file=sys.stderr)
        return 1

    unresolved_review = load_unresolved_review_references(REVIEW_CSV)
    rows = load_reconciliation_rows(DOCUMENT_LINKS_CSV)
    return process_rows(rows, unresolved_review, apply_changes=args.apply)


if __name__ == "__main__":
    raise SystemExit(main())
