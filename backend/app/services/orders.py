from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.status import get_operational_status
from app.models.client import Client
from app.models.delivery import DeliveryItem, DeliveryNote
from app.models.invoice import Invoice, InvoiceItem
from app.models.order import Order, OrderItem
from app.models.product import Product


STATUS_PRIORITY = {
    "invoice_over_delivery": 0,
    "pending_invoice": 1,
    "pending_delivery": 2,
    "ok": 3,
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
    invoiced_quantity = (
        db.query(func.coalesce(func.sum(InvoiceItem.quantity), 0.0))
        .filter(InvoiceItem.order_item_id == order_item_id)
        .scalar()
    )
    return float(delivered_quantity or 0.0), float(invoiced_quantity or 0.0)


def _resolve_summary_status(item_statuses: list[str]) -> str:
    if not item_statuses:
        return "ok"
    return min(item_statuses, key=lambda status: STATUS_PRIORITY[status])


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
        product = db.query(Product).filter(Product.id == order_item.product_id).first()
        delivered_quantity, invoiced_quantity = _get_order_item_quantities(db, order_item.id)
        ordered_quantity = float(order_item.quantity or 0.0)
        pending_delivery_quantity = ordered_quantity - delivered_quantity
        pending_invoice_quantity = delivered_quantity - invoiced_quantity
        item_status = get_operational_status(
            ordered_quantity=ordered_quantity,
            delivered_quantity=delivered_quantity,
            invoiced_quantity=invoiced_quantity,
        )

        item_rows.append(
            {
                "order_item_id": order_item.id,
                "product_code": product.sku if product else "",
                "description": (product.description or product.name) if product else "",
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
            }
        )

    return {
        "order": {
            "id": order.id,
            "order_number": build_order_number(order.id),
            "client_name": client.name if client else "",
            "order_date": _to_date_string(order.order_date),
            "status": summary_status,
        },
        "summary": {
            "total_ordered_quantity": total_ordered_quantity,
            "total_delivered_quantity": total_delivered_quantity,
            "total_invoiced_quantity": total_invoiced_quantity,
            "pending_delivery_quantity": total_ordered_quantity - total_delivered_quantity,
            "pending_invoice_quantity": total_delivered_quantity - total_invoiced_quantity,
            "status": summary_status,
        },
        "items": item_rows,
        "deliveries": delivery_rows,
        "invoices": invoice_rows,
    }
