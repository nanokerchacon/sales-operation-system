from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.models.client import Client
from app.models.delivery import DeliveryItem, DeliveryNote
from app.models.invoice import Invoice, InvoiceItem
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.services.access_control import AccessContext, apply_invoice_scope
from app.services.orders import (
    _resolve_client_name,
    _resolve_item_description,
    _resolve_product_code,
    _resolve_product_name,
    _to_date_string,
    build_delivery_number,
    build_order_number,
    get_invoice_number,
)


def _get_scoped_invoice(db: Session, invoice_id: int, access_context: AccessContext) -> Invoice | None:
    return (
        apply_invoice_scope(
            db.query(Invoice).options(selectinload(Invoice.items)),
            access_context,
        )
        .filter(Invoice.id == invoice_id)
        .first()
    )


def _get_invoice_total_amount(db: Session, invoice_id: int) -> float:
    total = (
        db.query(func.coalesce(func.sum(InvoiceItem.quantity * InvoiceItem.unit_price), 0.0))
        .filter(InvoiceItem.invoice_id == invoice_id)
        .scalar()
    )
    return float(total or 0.0)


def _get_invoice_delivery_rows(db: Session, invoice_id: int) -> list[dict[str, object]]:
    deliveries = (
        db.query(DeliveryNote.id, DeliveryNote.delivery_date)
        .join(DeliveryItem, DeliveryItem.delivery_note_id == DeliveryNote.id)
        .join(InvoiceItem, InvoiceItem.order_item_id == DeliveryItem.order_item_id)
        .filter(InvoiceItem.invoice_id == invoice_id)
        .distinct()
        .order_by(DeliveryNote.delivery_date.desc(), DeliveryNote.id.desc())
        .all()
    )
    return [
        {
            "id": delivery_id,
            "delivery_number": build_delivery_number(delivery_id),
            "delivery_date": _to_date_string(delivery_date),
        }
        for delivery_id, delivery_date in deliveries
    ]


def list_invoices_overview(db: Session, access_context: AccessContext) -> list[dict[str, object]]:
    invoices = (
        apply_invoice_scope(
            db.query(Invoice).options(selectinload(Invoice.items)),
            access_context,
        )
        .order_by(Invoice.invoice_date.desc(), Invoice.id.desc())
        .all()
    )

    order_ids = {invoice.order_id for invoice in invoices}
    orders = db.query(Order).filter(Order.id.in_(order_ids)).all() if order_ids else []
    order_map = {order.id: order for order in orders}

    client_ids = {order.client_id for order in orders}
    clients = db.query(Client).filter(Client.id.in_(client_ids)).all() if client_ids else []
    client_map = {client.id: client for client in clients}

    delivery_map = {invoice.id: _get_invoice_delivery_rows(db, invoice.id) for invoice in invoices}

    rows: list[dict[str, object]] = []
    for invoice in invoices:
        order = order_map.get(invoice.order_id)
        client = client_map.get(order.client_id) if order else None
        deliveries = delivery_map.get(invoice.id, [])
        primary_delivery = deliveries[0] if deliveries else None

        rows.append(
            {
                "id": invoice.id,
                "invoice_number": get_invoice_number(invoice.id),
                "client_id": order.client_id if order else None,
                "client_name": _resolve_client_name(order, client) if order else "",
                "order_id": invoice.order_id,
                "order_number": (order.order_number or build_order_number(order.id)) if order else None,
                "delivery_id": primary_delivery["id"] if primary_delivery else None,
                "delivery_number": primary_delivery["delivery_number"] if primary_delivery else None,
                "invoice_date": invoice.invoice_date,
                "status": invoice.invoice_status,
                "total_amount": _get_invoice_total_amount(db, invoice.id),
                "due_date": None,
                "payment_status": None,
                "invoice_type": invoice.invoice_type,
                "source_folder": invoice.source_folder,
            }
        )

    return rows


def get_invoice_detail(db: Session, invoice_id: int, access_context: AccessContext) -> dict[str, object] | None:
    invoice = _get_scoped_invoice(db, invoice_id, access_context)
    if invoice is None:
        return None

    order = db.query(Order).filter(Order.id == invoice.order_id).first()
    client = db.query(Client).filter(Client.id == order.client_id).first() if order else None

    order_item_ids = [item.order_item_id for item in invoice.items]
    order_items = db.query(OrderItem).filter(OrderItem.id.in_(order_item_ids)).all() if order_item_ids else []
    order_item_map = {order_item.id: order_item for order_item in order_items}

    product_ids = {order_item.product_id for order_item in order_items if order_item.product_id is not None}
    products = db.query(Product).filter(Product.id.in_(product_ids)).all() if product_ids else []
    product_map = {product.id: product for product in products}

    linked_deliveries = _get_invoice_delivery_rows(db, invoice.id)
    primary_delivery = linked_deliveries[0] if linked_deliveries else None
    total_amount = _get_invoice_total_amount(db, invoice.id)

    lines = []
    for item in invoice.items:
        order_item = order_item_map.get(item.order_item_id)
        product = product_map.get(order_item.product_id) if order_item and order_item.product_id is not None else None
        quantity = float(item.quantity or 0.0)
        unit_price = float(item.unit_price or 0.0)
        lines.append(
            {
                "id": item.id,
                "order_item_id": item.order_item_id,
                "product_id": order_item.product_id if order_item else None,
                "product_code": _resolve_product_code(product, order_item) if order_item else None,
                "product_name": _resolve_product_name(product, order_item) if order_item else None,
                "description": _resolve_item_description(product, order_item) if order_item else "",
                "quantity": quantity,
                "unit_price": unit_price,
                "total_amount": quantity * unit_price,
            }
        )

    return {
        "id": invoice.id,
        "invoice_number": get_invoice_number(invoice.id),
        "client_id": order.client_id if order else None,
        "client_name": _resolve_client_name(order, client) if order else "",
        "order_id": invoice.order_id,
        "order_number": (order.order_number or build_order_number(order.id)) if order else None,
        "delivery_id": primary_delivery["id"] if primary_delivery else None,
        "delivery_number": primary_delivery["delivery_number"] if primary_delivery else None,
        "invoice_date": invoice.invoice_date,
        "status": invoice.invoice_status,
        "due_date": None,
        "payment_status": None,
        "notes": None,
        "invoice_type": invoice.invoice_type,
        "source_folder": invoice.source_folder,
        "total_amount": total_amount,
        "lines": lines,
        "summary": {
            "taxable_base": total_amount,
            "tax_amount": None,
            "total_amount": total_amount,
            "payment_status": None,
            "due_date": None,
        },
        "relations": {
            "client_id": order.client_id if order else None,
            "client_name": _resolve_client_name(order, client) if order else "",
            "source_order_id": order.id if order else None,
            "source_order_number": (order.order_number or build_order_number(order.id)) if order else None,
            "primary_delivery_id": primary_delivery["id"] if primary_delivery else None,
            "primary_delivery_number": primary_delivery["delivery_number"] if primary_delivery else None,
            "linked_deliveries": linked_deliveries,
            "document_status": invoice.invoice_status,
            "payment_status": None,
            "payments_placeholder": "Base preparada para conectar cobros, vencimientos y conciliación en la siguiente fase.",
        },
    }
