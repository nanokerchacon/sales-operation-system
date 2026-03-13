from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.invoice import Invoice, InvoiceItem
from app.models.order import OrderItem


FOLDER_RULES: tuple[tuple[str, str, str], ...] = (
    ("N 2026", "national", "accepted"),
    ("IC 2026", "intracommunity", "accepted"),
    ("EX 2026", "export", "accepted"),
    ("CI 2026", "commercial_invoice", "accepted"),
    ("FACE", "electronic", "pending_acceptance"),
    ("FACEEMIT", "electronic", "pending_acceptance"),
    ("FR 2026", "rectificative", "rectified_review"),
)

INVOICE_DOCUMENT_STATUS_ES = {
    "not_invoiced": "Sin factura emitida",
    "invoice_issued": "Factura emitida",
    "invoice_pending_acceptance": "Pendiente de aceptación",
    "invoice_accepted": "Factura aceptada",
}


def normalize_source_folder(source_folder: str | None) -> str | None:
    if source_folder is None:
        return None
    normalized = " ".join(source_folder.strip().upper().split())
    return normalized or None


def normalize_invoice_status(invoice_status: str | None) -> str:
    if not invoice_status:
        return "accepted"
    return invoice_status.strip().lower() or "accepted"


def infer_invoice_document_metadata(source_folder: str | None) -> tuple[str, str]:
    normalized_folder = normalize_source_folder(source_folder)
    if normalized_folder is None:
        return "standard", "accepted"

    for folder_name, invoice_type, invoice_status in FOLDER_RULES:
        if normalized_folder == folder_name:
            return invoice_type, invoice_status

    return "standard", "accepted"


def resolve_invoice_document_metadata(
    source_folder: str | None,
    invoice_type: str | None = None,
    invoice_status: str | None = None,
) -> dict[str, str | None]:
    inferred_type, inferred_status = infer_invoice_document_metadata(source_folder)
    return {
        "source_folder": source_folder.strip() if source_folder else None,
        "invoice_type": (invoice_type or inferred_type).strip().lower(),
        "invoice_status": normalize_invoice_status(invoice_status or inferred_status),
    }


def get_order_invoice_document_totals(db: Session, order_id: int) -> dict[str, float | int | bool]:
    invoice_rows = db.query(Invoice.id, Invoice.invoice_status).filter(Invoice.order_id == order_id).all()
    quantity_rows = (
        db.query(
            Invoice.id,
            Invoice.invoice_status,
            func.coalesce(func.sum(InvoiceItem.quantity), 0.0),
        )
        .join(InvoiceItem, InvoiceItem.invoice_id == Invoice.id)
        .join(OrderItem, OrderItem.id == InvoiceItem.order_item_id)
        .filter(OrderItem.order_id == order_id)
        .group_by(Invoice.id, Invoice.invoice_status)
        .all()
    )

    accepted_quantity = 0.0
    issued_quantity = 0.0
    pending_acceptance_quantity = 0.0
    rectified_review_quantity = 0.0

    for _, raw_status, quantity in quantity_rows:
        normalized_status = normalize_invoice_status(raw_status)
        current_quantity = float(quantity or 0.0)
        issued_quantity += current_quantity

        if normalized_status == "accepted":
            accepted_quantity += current_quantity
        elif normalized_status == "pending_acceptance":
            pending_acceptance_quantity += current_quantity
        elif normalized_status == "rectified_review":
            rectified_review_quantity += current_quantity

    invoice_count = len(invoice_rows)
    pending_acceptance_invoice_count = sum(
        1 for _, invoice_status in invoice_rows if normalize_invoice_status(invoice_status) == "pending_acceptance"
    )
    accepted_invoice_count = sum(
        1 for _, invoice_status in invoice_rows if normalize_invoice_status(invoice_status) == "accepted"
    )

    return {
        "issued_quantity": issued_quantity,
        "accepted_quantity": accepted_quantity,
        "pending_acceptance_quantity": pending_acceptance_quantity,
        "rectified_review_quantity": rectified_review_quantity,
        "invoice_count": invoice_count,
        "accepted_invoice_count": accepted_invoice_count,
        "pending_acceptance_invoice_count": pending_acceptance_invoice_count,
        "has_issued_invoice": issued_quantity > 0 or invoice_count > 0,
        "has_pending_acceptance": pending_acceptance_quantity > 0 or pending_acceptance_invoice_count > 0,
    }


def resolve_order_invoice_document_status(
    delivered_quantity: float,
    issued_quantity: float,
    accepted_quantity: float,
    pending_acceptance_quantity: float,
) -> str:
    if pending_acceptance_quantity > 0:
        return "invoice_pending_acceptance"
    if delivered_quantity > 0 and accepted_quantity >= delivered_quantity:
        return "invoice_accepted"
    if issued_quantity > 0:
        return "invoice_issued"
    return "not_invoiced"
