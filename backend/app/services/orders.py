from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.status import get_operational_status
from app.models.client import Client
from app.models.delivery import DeliveryItem, DeliveryNote
from app.models.invoice import Invoice, InvoiceItem
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.services.invoice_documents import (
    INVOICE_DOCUMENT_STATUS_ES,
    get_order_invoice_document_totals,
    resolve_order_invoice_document_status,
)


STATUS_PRIORITY = {
    "invoice_over_delivery": 0,
    "pending_invoice": 1,
    "invoice_pending_acceptance": 2,
    "pending_delivery": 3,
    "ok": 4,
}


def build_order_number(order_id: int) -> str:
    return f"PO{order_id:07d}"


def build_delivery_number(delivery_id: int) -> str:
    return str(delivery_id)


def get_invoice_number(invoice_id: int) -> str:
    return f"IC/{invoice_id:06d}"


def _to_date_string(value) -> str | None:
    if value is None:
        return None
    return value.date().isoformat()


def _get_order_item_quantities(db: Session, order_item_id: int) -> tuple[float, float]:
    delivered_quantity = (
        db.query(func.coalesce(func.sum(DeliveryItem.quantity), 0.0))
        .filter(DeliveryItem.order_item_id == order_item_id)
        .scalar()
    )
    accepted_invoiced_quantity = (
        db.query(func.coalesce(func.sum(InvoiceItem.quantity), 0.0))
        .join(Invoice, Invoice.id == InvoiceItem.invoice_id)
        .filter(InvoiceItem.order_item_id == order_item_id, Invoice.invoice_status == "accepted")
        .scalar()
    )
    return float(delivered_quantity or 0.0), float(accepted_invoiced_quantity or 0.0)


def _resolve_summary_status(item_statuses: list[str]) -> str:
    if not item_statuses:
        return "ok"
    return min(item_statuses, key=lambda status: STATUS_PRIORITY[status])


def _resolve_item_description(product: Product | None, order_item: OrderItem) -> str:
    if order_item.description:
        return order_item.description
    if product and product.description:
        return product.description
    if product and product.name:
        return product.name
    return ""


def get_order_traceability(db: Session, order_id: int) -> dict[str, object]:
    order = db.query(Order).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

    client = db.query(Client).filter(Client.id == order.client_id).first()
    order_items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()

    item_rows: list[dict[str, object]] = []
    status_candidates: list[str] = []
    total_ordered_quantity = 0.0
    total_delivered_quantity = 0.0
    total_invoiced_quantity = 0.0

    for order_item in order_items:
        product = None
        if order_item.product_id is not None:
            product = db.query(Product).filter(Product.id == order_item.product_id).first()
        delivered_quantity, invoiced_quantity = _get_order_item_quantities(db, order_item.id)
        ordered_quantity = float(order_item.quantity or 0.0)
        pending_delivery_quantity = ordered_quantity - delivered_quantity
        pending_invoice_quantity = delivered_quantity - invoiced_quantity
        item_status = get_operational_status(
            ordered_quantity=ordered_quantity,
            delivered_quantity=delivered_quantity,
            invoiced_quantity=invoiced_quantity,
            issued_quantity=invoiced_quantity,
        )

        item_rows.append(
            {
                "order_item_id": order_item.id,
                "product_code": product.sku if product else (order_item.legacy_article_code or ""),
                "description": _resolve_item_description(product, order_item),
                "ordered_quantity": ordered_quantity,
                "delivered_quantity": delivered_quantity,
                "invoiced_quantity": invoiced_quantity,
                "pending_delivery_quantity": pending_delivery_quantity,
                "pending_invoice_quantity": pending_invoice_quantity,
                "status": item_status,
            }
        )

        status_candidates.append(item_status)
        total_ordered_quantity += ordered_quantity
        total_delivered_quantity += delivered_quantity
        total_invoiced_quantity += invoiced_quantity

    invoice_totals = get_order_invoice_document_totals(db, order.id)
    total_issued_quantity = float(invoice_totals["issued_quantity"] or 0.0)
    total_pending_acceptance_quantity = float(invoice_totals["pending_acceptance_quantity"] or 0.0)
    invoice_document_status = resolve_order_invoice_document_status(
        delivered_quantity=total_delivered_quantity,
        issued_quantity=total_issued_quantity,
        accepted_quantity=total_invoiced_quantity,
        pending_acceptance_quantity=total_pending_acceptance_quantity,
    )
    summary_status = get_operational_status(
        ordered_quantity=total_ordered_quantity,
        delivered_quantity=total_delivered_quantity,
        invoiced_quantity=total_invoiced_quantity,
        issued_quantity=total_issued_quantity,
        pending_acceptance_quantity=total_pending_acceptance_quantity,
    )
    if not status_candidates:
        summary_status = _resolve_summary_status(status_candidates)

    deliveries = (
        db.query(DeliveryNote)
        .filter(DeliveryNote.order_id == order.id)
        .order_by(DeliveryNote.delivery_date.desc(), DeliveryNote.id.desc())
        .all()
    )
    delivery_rows = [
        {
            "id": delivery.id,
            "delivery_number": build_delivery_number(delivery.id),
            "delivery_date": _to_date_string(delivery.delivery_date),
        }
        for delivery in deliveries
    ]

    invoices = (
        db.query(Invoice)
        .filter(Invoice.order_id == order.id)
        .order_by(Invoice.invoice_date.desc(), Invoice.id.desc())
        .all()
    )
    invoice_rows: list[dict[str, object]] = []
    for invoice in invoices:
        total_amount = (
            db.query(func.coalesce(func.sum(InvoiceItem.quantity * InvoiceItem.unit_price), 0.0))
            .filter(InvoiceItem.invoice_id == invoice.id)
            .scalar()
        )
        invoice_rows.append(
            {
                "id": invoice.id,
                "invoice_number": get_invoice_number(invoice.id),
                "invoice_date": _to_date_string(invoice.invoice_date),
                "total_amount": float(total_amount or 0.0),
                "invoice_type": invoice.invoice_type,
                "invoice_status": invoice.invoice_status,
                "source_folder": invoice.source_folder,
            }
        )

    return {
        "order": {
            "id": order.id,
            "order_number": order.order_number or build_order_number(order.id),
            "client_name": order.client_name_snapshot or (client.name if client else ""),
            "order_date": _to_date_string(order.order_date),
            "status": summary_status,
            "invoice_document_status": invoice_document_status,
            "invoice_document_status_es": INVOICE_DOCUMENT_STATUS_ES[invoice_document_status],
        },
        "summary": {
            "total_ordered_quantity": total_ordered_quantity,
            "total_delivered_quantity": total_delivered_quantity,
            "total_invoiced_quantity": total_invoiced_quantity,
            "total_issued_quantity": total_issued_quantity,
            "total_pending_acceptance_quantity": total_pending_acceptance_quantity,
            "pending_delivery_quantity": total_ordered_quantity - total_delivered_quantity,
            "pending_invoice_quantity": total_delivered_quantity - total_invoiced_quantity,
            "status": summary_status,
            "invoice_document_status": invoice_document_status,
            "invoice_document_status_es": INVOICE_DOCUMENT_STATUS_ES[invoice_document_status],
        },
        "items": item_rows,
        "deliveries": delivery_rows,
        "invoices": invoice_rows,
    }
