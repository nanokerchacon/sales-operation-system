from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.api.status import get_operational_status
from app.models.client import Client
from app.models.delivery import DeliveryItem, DeliveryNote
from app.models.invoice import Invoice, InvoiceItem
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.services.access_control import AccessContext, apply_delivery_scope
from app.services.invoice_documents import get_order_invoice_document_totals, resolve_order_invoice_document_status
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


def _resolve_delivery_status(invoice_status: str | None) -> str:
    if invoice_status == "invoice_accepted":
        return "completed"
    return "delivered"


def _get_scoped_delivery(db: Session, delivery_id: int, access_context: AccessContext) -> DeliveryNote:
    delivery = (
        apply_delivery_scope(
            db.query(DeliveryNote).options(selectinload(DeliveryNote.items)),
            access_context,
        )
        .filter(DeliveryNote.id == delivery_id)
        .first()
    )
    if delivery is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery not found")
    return delivery


def _get_order_invoice_status(db: Session, order_id: int) -> str:
    order_items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    total_delivered_quantity = (
        db.query(func.coalesce(func.sum(DeliveryItem.quantity), 0.0))
        .join(OrderItem, OrderItem.id == DeliveryItem.order_item_id)
        .filter(OrderItem.order_id == order_id)
        .scalar()
    )
    total_invoiced_quantity = (
        db.query(func.coalesce(func.sum(InvoiceItem.quantity), 0.0))
        .join(Invoice, Invoice.id == InvoiceItem.invoice_id)
        .join(OrderItem, OrderItem.id == InvoiceItem.order_item_id)
        .filter(OrderItem.order_id == order_id, Invoice.invoice_status == "accepted")
        .scalar()
    )
    total_ordered_quantity = sum(float(item.quantity or 0.0) for item in order_items)
    invoice_totals = get_order_invoice_document_totals(db, order_id)
    total_issued_quantity = float(invoice_totals["issued_quantity"] or 0.0)
    total_pending_acceptance_quantity = float(invoice_totals["pending_acceptance_quantity"] or 0.0)

    return resolve_order_invoice_document_status(
        delivered_quantity=float(total_delivered_quantity or 0.0),
        issued_quantity=total_issued_quantity,
        accepted_quantity=float(total_invoiced_quantity or 0.0),
        pending_acceptance_quantity=total_pending_acceptance_quantity,
    )


def _resolve_delivery_total_amount(db: Session, delivery: DeliveryNote) -> float:
    if not delivery.items:
        return 0.0

    order_item_ids = [item.order_item_id for item in delivery.items]
    order_items = db.query(OrderItem).filter(OrderItem.id.in_(order_item_ids)).all()
    order_item_map = {order_item.id: order_item for order_item in order_items}

    total = 0.0
    for item in delivery.items:
        order_item = order_item_map.get(item.order_item_id)
        unit_price = float(order_item.unit_price or 0.0) if order_item else 0.0
        total += float(item.quantity or 0.0) * unit_price
    return total


def list_deliveries_overview(db: Session, access_context: AccessContext) -> list[dict[str, object]]:
    deliveries = (
        apply_delivery_scope(
            db.query(DeliveryNote).options(selectinload(DeliveryNote.items)),
            access_context,
        )
        .order_by(DeliveryNote.delivery_date.desc(), DeliveryNote.id.desc())
        .all()
    )

    order_ids = {delivery.order_id for delivery in deliveries}
    orders = db.query(Order).filter(Order.id.in_(order_ids)).all() if order_ids else []
    order_map = {order.id: order for order in orders}

    client_ids = {order.client_id for order in orders}
    clients = db.query(Client).filter(Client.id.in_(client_ids)).all() if client_ids else []
    client_map = {client.id: client for client in clients}

    rows: list[dict[str, object]] = []
    for delivery in deliveries:
        order = order_map.get(delivery.order_id)
        client = client_map.get(order.client_id) if order else None
        invoice_status = _get_order_invoice_status(db, delivery.order_id) if order else None

        rows.append(
            {
                "id": delivery.id,
                "order_id": delivery.order_id,
                "delivery_number": build_delivery_number(delivery.id),
                "client_id": order.client_id if order else None,
                "client_name": _resolve_client_name(order, client) if order else "",
                "order_number": (order.order_number or build_order_number(order.id)) if order else None,
                "delivery_date": delivery.delivery_date,
                "created_at": delivery.created_at,
                "status": _resolve_delivery_status(invoice_status),
                "total_amount": _resolve_delivery_total_amount(db, delivery),
                "invoice_status": invoice_status,
                "items": delivery.items,
            }
        )

    return rows


def get_delivery_detail(db: Session, delivery_id: int, access_context: AccessContext) -> dict[str, object]:
    delivery = _get_scoped_delivery(db, delivery_id, access_context)
    order = db.query(Order).filter(Order.id == delivery.order_id).first()
    client = db.query(Client).filter(Client.id == order.client_id).first() if order else None

    order_item_ids = [item.order_item_id for item in delivery.items]
    order_items = db.query(OrderItem).filter(OrderItem.id.in_(order_item_ids)).all() if order_item_ids else []
    order_item_map = {order_item.id: order_item for order_item in order_items}

    product_ids = {order_item.product_id for order_item in order_items if order_item.product_id is not None}
    products = db.query(Product).filter(Product.id.in_(product_ids)).all() if product_ids else []
    product_map = {product.id: product for product in products}

    invoice_status = _get_order_invoice_status(db, delivery.order_id) if order else None
    delivery_total_amount = _resolve_delivery_total_amount(db, delivery)

    invoice_rows: list[dict[str, object]] = []
    if order_item_ids:
        invoices = (
            apply_delivery_scope(
                db.query(Invoice)
                .join(InvoiceItem, Invoice.id == InvoiceItem.invoice_id)
                .filter(Invoice.order_id == delivery.order_id, InvoiceItem.order_item_id.in_(order_item_ids))
                .distinct(),
                access_context,
            )
            .order_by(Invoice.invoice_date.desc(), Invoice.id.desc())
            .all()
        )
        invoice_ids = [invoice.id for invoice in invoices]
        invoice_amounts: dict[int, float] = {}
        if invoice_ids:
            for invoice_id, total in (
                db.query(InvoiceItem.invoice_id, func.coalesce(func.sum(InvoiceItem.quantity * InvoiceItem.unit_price), 0.0))
                .filter(InvoiceItem.invoice_id.in_(invoice_ids))
                .group_by(InvoiceItem.invoice_id)
                .all()
            ):
                invoice_amounts[invoice_id] = float(total or 0.0)

        invoice_rows = [
            {
                "id": invoice.id,
                "invoice_number": get_invoice_number(invoice.id),
                "invoice_date": _to_date_string(invoice.invoice_date),
                "invoice_status": invoice.invoice_status,
                "total_amount": invoice_amounts.get(invoice.id, 0.0),
            }
            for invoice in invoices
        ]

    lines = []
    total_delivery_quantity = 0.0
    for item in delivery.items:
        order_item = order_item_map.get(item.order_item_id)
        product = product_map.get(order_item.product_id) if order_item and order_item.product_id is not None else None
        quantity = float(item.quantity or 0.0)
        unit_price = float(order_item.unit_price or 0.0) if order_item else None
        total_amount = quantity * unit_price if unit_price is not None else None
        total_delivery_quantity += quantity
        lines.append(
            {
                "id": item.id,
                "order_item_id": item.order_item_id,
                "product_id": order_item.product_id if order_item else None,
                "product_code": _resolve_product_code(product, order_item) if order_item else None,
                "product_name": _resolve_product_name(product, order_item) if order_item else None,
                "description": _resolve_item_description(product, order_item) if order_item else "",
                "quantity": quantity,
                "unit_label": None,
                "unit_price": unit_price,
                "total_amount": total_amount,
            }
        )

    accepted_quantity = (
        db.query(func.coalesce(func.sum(InvoiceItem.quantity), 0.0))
        .join(Invoice, Invoice.id == InvoiceItem.invoice_id)
        .filter(Invoice.order_id == delivery.order_id, Invoice.invoice_status == "accepted")
        .scalar()
    )
    issued_quantity = (
        db.query(func.coalesce(func.sum(InvoiceItem.quantity), 0.0))
        .join(Invoice, Invoice.id == InvoiceItem.invoice_id)
        .filter(Invoice.order_id == delivery.order_id)
        .scalar()
    )
    logistics_status = get_operational_status(
        ordered_quantity=total_delivery_quantity,
        delivered_quantity=total_delivery_quantity,
        invoiced_quantity=float(accepted_quantity or 0.0),
        issued_quantity=float(issued_quantity or 0.0),
    )

    return {
        "id": delivery.id,
        "delivery_number": build_delivery_number(delivery.id),
        "client_id": order.client_id if order else None,
        "client_name": _resolve_client_name(order, client) if order else "",
        "order_id": delivery.order_id,
        "order_number": (order.order_number or build_order_number(order.id)) if order else None,
        "delivery_date": delivery.delivery_date,
        "created_at": delivery.created_at,
        "status": _resolve_delivery_status(invoice_status),
        "notes": None,
        "total_amount": delivery_total_amount,
        "invoice_status": invoice_status,
        "lines": lines,
        "relations": {
            "source_order_id": order.id if order else None,
            "source_order_number": (order.order_number or build_order_number(order.id)) if order else None,
            "source_order_status": (order.status or logistics_status) if order else None,
            "document_status": invoice_status,
            "linked_invoices": invoice_rows,
        },
    }
