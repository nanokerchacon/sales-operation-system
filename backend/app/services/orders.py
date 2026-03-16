from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.status import get_operational_status
from app.models.client import Client
from app.models.delivery import DeliveryItem, DeliveryNote
from app.models.invoice import Invoice, InvoiceItem
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.services.access_control import AccessContext, apply_order_scope, require_order_access
from app.services.invoice_documents import (
    INVOICE_DOCUMENT_STATUS_ES,
    get_order_invoice_document_totals,
    resolve_order_invoice_document_status,
)


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


def _line_total(order_item: OrderItem) -> float:
    if order_item.line_amount is not None:
        return float(order_item.line_amount)
    return float(order_item.quantity or 0.0) * float(order_item.unit_price or 0.0)


def _resolve_order_total_amount(order: Order, order_items: list[OrderItem] | None = None) -> float:
    if order.total_amount is not None:
        return float(order.total_amount)
    if order.subtotal is not None:
        return float(order.subtotal)
    if not order_items:
        return 0.0
    return sum(_line_total(item) for item in order_items)


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


def _resolve_item_description(product: Product | None, order_item: OrderItem) -> str:
    if order_item.description:
        return order_item.description
    if product and product.description:
        return product.description
    if product and product.name:
        return product.name
    return ""


def _resolve_product_code(product: Product | None, order_item: OrderItem) -> str | None:
    if product and product.sku:
        return product.sku
    return order_item.legacy_article_code


def _resolve_product_name(product: Product | None, order_item: OrderItem) -> str | None:
    if product and product.name:
        return product.name
    if order_item.description:
        return order_item.description
    return None


def _resolve_client_name(order: Order, client: Client | None) -> str:
    return order.client_name_snapshot or (client.name if client else "")


def _resolve_order_status(order: Order, operational_status: str) -> str:
    return order.status or operational_status or "draft"


def _resolve_delivery_status(total_ordered_quantity: float, total_delivered_quantity: float) -> str:
    if total_ordered_quantity <= 0:
        return "pending_delivery"
    if total_delivered_quantity >= total_ordered_quantity:
        return "delivered"
    return "pending_delivery"


def _build_order_metrics(db: Session, order: Order, order_items: list[OrderItem]) -> dict[str, float | str]:
    total_ordered_quantity = 0.0
    total_delivered_quantity = 0.0
    total_invoiced_quantity = 0.0

    for order_item in order_items:
        delivered_quantity, invoiced_quantity = _get_order_item_quantities(db, order_item.id)
        total_ordered_quantity += float(order_item.quantity or 0.0)
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
    logistics_status = get_operational_status(
        ordered_quantity=total_ordered_quantity,
        delivered_quantity=total_delivered_quantity,
        invoiced_quantity=total_invoiced_quantity,
        issued_quantity=total_issued_quantity,
        pending_acceptance_quantity=total_pending_acceptance_quantity,
    )

    return {
        "total_ordered_quantity": total_ordered_quantity,
        "total_delivered_quantity": total_delivered_quantity,
        "total_invoiced_quantity": total_invoiced_quantity,
        "total_issued_quantity": total_issued_quantity,
        "total_pending_acceptance_quantity": total_pending_acceptance_quantity,
        "logistics_status": logistics_status,
        "delivery_status": _resolve_delivery_status(total_ordered_quantity, total_delivered_quantity),
        "invoice_status": invoice_document_status,
    }


def _get_scoped_order(db: Session, order_id: int, access_context: AccessContext) -> Order:
    order = db.query(Order).filter(Order.id == order_id).first()
    require_order_access(db, access_context, order)
    return order


def build_order_list_item(db: Session, order: Order, client: Client | None = None) -> dict[str, object]:
    order_items = (
        db.query(OrderItem)
        .filter(OrderItem.order_id == order.id)
        .order_by(OrderItem.line_number.asc(), OrderItem.id.asc())
        .all()
    )
    metrics = _build_order_metrics(db, order, order_items)
    return {
        "id": order.id,
        "order_number": order.order_number or build_order_number(order.id),
        "client_id": order.client_id,
        "client_name": _resolve_client_name(order, client),
        "order_date": order.order_date,
        "status": _resolve_order_status(order, str(metrics["logistics_status"])),
        "total_amount": _resolve_order_total_amount(order, order_items),
        "delivery_status": metrics["delivery_status"],
        "invoice_status": metrics["invoice_status"],
    }


def list_orders_overview(db: Session, access_context: AccessContext) -> list[dict[str, object]]:
    orders = (
        apply_order_scope(db.query(Order), access_context)
        .order_by(Order.order_date.desc(), Order.id.desc())
        .all()
    )
    client_ids = {order.client_id for order in orders}
    clients = db.query(Client).filter(Client.id.in_(client_ids)).all() if client_ids else []
    client_map = {client.id: client for client in clients}
    return [build_order_list_item(db, order, client_map.get(order.client_id)) for order in orders]


def get_order_detail(db: Session, order_id: int, access_context: AccessContext) -> dict[str, object]:
    order = _get_scoped_order(db, order_id, access_context)
    client = db.query(Client).filter(Client.id == order.client_id).first()
    order_items = (
        db.query(OrderItem)
        .filter(OrderItem.order_id == order.id)
        .order_by(OrderItem.line_number.asc(), OrderItem.id.asc())
        .all()
    )
    product_ids = {item.product_id for item in order_items if item.product_id is not None}
    products = db.query(Product).filter(Product.id.in_(product_ids)).all() if product_ids else []
    product_map = {product.id: product for product in products}
    metrics = _build_order_metrics(db, order, order_items)

    deliveries = (
        db.query(DeliveryNote)
        .filter(DeliveryNote.order_id == order.id)
        .order_by(DeliveryNote.delivery_date.desc(), DeliveryNote.id.desc())
        .all()
    )
    invoices = (
        db.query(Invoice)
        .filter(Invoice.order_id == order.id)
        .order_by(Invoice.invoice_date.desc(), Invoice.id.desc())
        .all()
    )

    invoice_amounts = {}
    if invoices:
        invoice_ids = [invoice.id for invoice in invoices]
        for invoice_id, total in (
            db.query(InvoiceItem.invoice_id, func.coalesce(func.sum(InvoiceItem.quantity * InvoiceItem.unit_price), 0.0))
            .filter(InvoiceItem.invoice_id.in_(invoice_ids))
            .group_by(InvoiceItem.invoice_id)
            .all()
        ):
            invoice_amounts[invoice_id] = float(total or 0.0)

    return {
        "id": order.id,
        "order_number": order.order_number or build_order_number(order.id),
        "client_id": order.client_id,
        "client_name": _resolve_client_name(order, client),
        "order_date": order.order_date,
        "status": _resolve_order_status(order, str(metrics["logistics_status"])),
        "client_reference": order.legacy_client_code,
        "notes": order.notes,
        "subtotal": float(order.subtotal) if order.subtotal is not None else None,
        "tax_amount": float(order.tax_amount) if order.tax_amount is not None else None,
        "total_amount": _resolve_order_total_amount(order, order_items),
        "lines": [
            {
                "id": item.id,
                "line_number": item.line_number,
                "product_id": item.product_id,
                "product_code": _resolve_product_code(product_map.get(item.product_id), item),
                "product_name": _resolve_product_name(product_map.get(item.product_id), item),
                "description": _resolve_item_description(product_map.get(item.product_id), item),
                "quantity": float(item.quantity or 0.0),
                "unit_price": float(item.unit_price or 0.0),
                "total_amount": _line_total(item),
            }
            for item in order_items
        ],
        "traceability": {
            "logistics_status": metrics["logistics_status"],
            "delivery_status": metrics["delivery_status"],
            "invoice_status": metrics["invoice_status"],
            "deliveries": [
                {
                    "id": delivery.id,
                    "document_number": build_delivery_number(delivery.id),
                    "document_date": _to_date_string(delivery.delivery_date),
                    "status": metrics["delivery_status"],
                    "total_amount": None,
                }
                for delivery in deliveries
            ],
            "invoices": [
                {
                    "id": invoice.id,
                    "document_number": get_invoice_number(invoice.id),
                    "document_date": _to_date_string(invoice.invoice_date),
                    "status": invoice.invoice_status,
                    "total_amount": invoice_amounts.get(invoice.id, 0.0),
                }
                for invoice in invoices
            ],
        },
    }


def get_order_traceability(db: Session, order_id: int, access_context: AccessContext) -> dict[str, object]:
    order = _get_scoped_order(db, order_id, access_context)

    client = db.query(Client).filter(Client.id == order.client_id).first()
    order_items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()

    item_rows: list[dict[str, object]] = []
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
            "client_name": _resolve_client_name(order, client),
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
