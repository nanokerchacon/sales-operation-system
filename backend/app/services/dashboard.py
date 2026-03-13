from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session, load_only

from app.api.status import LEGACY_RISK_STATUS, STATUS_ES, get_operational_status
from app.models.client import Client
from app.models.delivery import DeliveryItem, DeliveryNote
from app.models.invoice import Invoice, InvoiceItem
from app.models.order import Order, OrderItem
from app.services.invoice_documents import (
    INVOICE_DOCUMENT_STATUS_ES,
    get_order_invoice_document_totals,
    normalize_invoice_status,
    resolve_order_invoice_document_status,
)
from app.services.order_status import apply_order_status_quantity_fallback, normalize_order_status


OPERATIONS_LABELS_ES = {
    "total_orders": "Total de pedidos",
    "orders_with_issues": "Pedidos con incidencias",
    "orders_without_issues": "Pedidos correctos",
    "total_pending_delivery_quantity": "Cantidad pendiente de entregar",
    "total_pending_invoice_quantity": "Cantidad pendiente de cierre documental",
    "pending_delivery_orders": "Pedidos pendientes de entrega",
    "pending_invoice_orders": "Pedidos pendientes de facturar",
    "pending_acceptance_orders": "Pedidos con factura pendiente de aceptación",
    "invoice_over_delivery_orders": "Error de facturacion",
    "accepted_invoice_orders": "Pedidos con factura aceptada",
    "pending_acceptance_invoice_orders": "Pedidos con factura pendiente de aceptación",
    "total_accepted_invoice_quantity": "Cantidad facturada aceptada",
    "total_pending_acceptance_quantity": "Cantidad pendiente de aceptación",
}

ORDER_STATUS_SUMMARY_LABELS_ES = {
    "ok": "Completos",
    "pending_delivery": "Pendientes de entrega",
    "pending_invoice": "Pendientes de facturar",
    "invoice_pending_acceptance": "Pendientes de aceptación",
    "invoice_over_delivery": "Error de facturacion",
}

AGING_LABELS_ES = {
    "bucket_0_3_days": "0 a 3 dias",
    "bucket_4_7_days": "4 a 7 dias",
    "bucket_8_15_days": "8 a 15 dias",
    "bucket_over_15_days": "Mas de 15 dias",
    "total_pending_invoice_amount": "Total pendiente de cierre documental",
}

STATUS_PRIORITY = {
    "invoice_over_delivery": 0,
    "pending_invoice": 1,
    "invoice_pending_acceptance": 2,
    "pending_delivery": 3,
    "ok": 4,
}

PRIORITY_LABELS_ES = {
    "high": "Alta",
    "medium": "Media",
    "low": "Baja",
    "none": "Sin incidencias",
}

PRIORITY_ORDER = {
    "high": 0,
    "medium": 1,
    "low": 2,
    "none": 3,
}


def build_order_number(order_id: int) -> str:
    return f"PED-{order_id:06d}"


def _get_dashboard_orders(db: Session) -> list[Order]:
    return db.query(Order).options(load_only(Order.id, Order.client_id, Order.status)).all()


def get_priority_for_order(
    status: str,
    delivered_quantity: float,
    invoiced_quantity: float,
    pending_delivery_quantity: float,
    pending_acceptance_quantity: float = 0.0,
) -> str:
    if status == "invoice_over_delivery":
        return "high"
    if status == "pending_invoice":
        return "high"
    if status == "invoice_pending_acceptance":
        return "medium"
    if pending_delivery_quantity > 0:
        return "medium"
    if delivered_quantity > invoiced_quantity or pending_acceptance_quantity > 0:
        return "high"
    return "low"


def build_order_status_data(db: Session, order: Order) -> dict[str, int | float | str | bool]:
    ordered_quantity = (
        db.query(func.coalesce(func.sum(OrderItem.quantity), 0.0))
        .filter(OrderItem.order_id == order.id)
        .scalar()
    )
    delivered_quantity = (
        db.query(func.coalesce(func.sum(DeliveryItem.quantity), 0.0))
        .join(OrderItem, OrderItem.id == DeliveryItem.order_item_id)
        .filter(OrderItem.order_id == order.id)
        .scalar()
    )
    delivery_record_count = (
        db.query(func.count(DeliveryItem.id))
        .join(OrderItem, OrderItem.id == DeliveryItem.order_item_id)
        .filter(OrderItem.order_id == order.id)
        .scalar()
    )
    invoice_totals = get_order_invoice_document_totals(db, order.id)
    accepted_quantity = float(invoice_totals["accepted_quantity"] or 0.0)
    issued_quantity = float(invoice_totals["issued_quantity"] or 0.0)
    pending_acceptance_quantity = float(invoice_totals["pending_acceptance_quantity"] or 0.0)
    invoice_record_count = int(invoice_totals["invoice_count"] or 0)

    accepted_quantity_fallback = accepted_quantity
    delivered_quantity, accepted_quantity_fallback = apply_order_status_quantity_fallback(
        order_status=order.status,
        ordered_quantity=float(ordered_quantity or 0.0),
        delivered_quantity=float(delivered_quantity or 0.0),
        invoiced_quantity=accepted_quantity,
        has_delivery_records=bool(delivery_record_count),
        has_invoice_records=bool(invoice_record_count),
    )
    if accepted_quantity == 0 and accepted_quantity_fallback > 0:
        accepted_quantity = accepted_quantity_fallback
        issued_quantity = max(issued_quantity, accepted_quantity_fallback)

    client = db.query(Client).filter(Client.id == order.client_id).first()
    pending_delivery_quantity = ordered_quantity - delivered_quantity
    pending_invoice_quantity = delivered_quantity - accepted_quantity
    invoice_document_status = resolve_order_invoice_document_status(
        delivered_quantity=float(delivered_quantity or 0.0),
        issued_quantity=issued_quantity,
        accepted_quantity=accepted_quantity,
        pending_acceptance_quantity=pending_acceptance_quantity,
    )
    operational_status = get_operational_status(
        ordered_quantity=float(ordered_quantity or 0.0),
        delivered_quantity=float(delivered_quantity or 0.0),
        invoiced_quantity=accepted_quantity,
        issued_quantity=issued_quantity,
        pending_acceptance_quantity=pending_acceptance_quantity,
    )
    legacy_risk_status = LEGACY_RISK_STATUS[operational_status]

    return {
        "order_id": order.id,
        "order_number": build_order_number(order.id),
        "client_id": order.client_id,
        "client_name": client.name if client else "",
        "order_status": order.status,
        "status": operational_status,
        "status_es": STATUS_ES[operational_status],
        "ordered_quantity": float(ordered_quantity or 0.0),
        "delivered_quantity": float(delivered_quantity or 0.0),
        "invoiced_quantity": float(accepted_quantity or 0.0),
        "issued_quantity": float(issued_quantity or 0.0),
        "pending_acceptance_quantity": float(pending_acceptance_quantity or 0.0),
        "pending_delivery_quantity": float(pending_delivery_quantity or 0.0),
        "pending_invoice_quantity": float(pending_invoice_quantity or 0.0),
        "has_issue": operational_status != "ok",
        "risk_status": legacy_risk_status,
        "risk_status_es": STATUS_ES[operational_status],
        "has_risk": operational_status != "ok",
        "invoice_document_status": invoice_document_status,
        "invoice_document_status_es": INVOICE_DOCUMENT_STATUS_ES[invoice_document_status],
    }


def get_amount_pending_invoice(db: Session, order_id: int) -> float:
    order = db.query(Order).filter(Order.id == order_id).first()
    order_items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    amount_pending_invoice = 0.0
    delivery_item_count = 0
    invoice_item_count = 0

    for order_item in order_items:
        delivered_quantity = (
            db.query(func.coalesce(func.sum(DeliveryItem.quantity), 0.0))
            .filter(DeliveryItem.order_item_id == order_item.id)
            .scalar()
        )
        accepted_quantity = 0.0
        invoice_quantities = (
            db.query(Invoice.invoice_status, func.coalesce(func.sum(InvoiceItem.quantity), 0.0))
            .join(InvoiceItem, InvoiceItem.invoice_id == Invoice.id)
            .filter(InvoiceItem.order_item_id == order_item.id)
            .group_by(Invoice.invoice_status)
            .all()
        )
        for raw_status, quantity in invoice_quantities:
            if normalize_invoice_status(raw_status) == "accepted":
                accepted_quantity += float(quantity or 0.0)

        delivery_item_count += db.query(func.count(DeliveryItem.id)).filter(DeliveryItem.order_item_id == order_item.id).scalar()
        invoice_item_count += db.query(func.count(InvoiceItem.id)).filter(InvoiceItem.order_item_id == order_item.id).scalar()
        pending_invoice_quantity = delivered_quantity - accepted_quantity
        amount_pending_invoice += pending_invoice_quantity * (order_item.unit_price or 0.0)

    if amount_pending_invoice > 0:
        return float(amount_pending_invoice)

    normalized_status = normalize_order_status(order.status if order else None)
    if not order_items or delivery_item_count or invoice_item_count:
        return float(amount_pending_invoice)
    if normalized_status == "delivered":
        return float(sum((item.quantity or 0.0) * (item.unit_price or 0.0) for item in order_items))
    return float(amount_pending_invoice)


def get_days_since_last_delivery(db: Session, order_id: int) -> int:
    latest_delivery_date = (
        db.query(func.max(DeliveryNote.delivery_date))
        .filter(DeliveryNote.order_id == order_id)
        .scalar()
    )
    if latest_delivery_date is None:
        return 0

    return (date.today() - latest_delivery_date.date()).days


def get_aging_bucket(days_since_last_delivery: int) -> str:
    if days_since_last_delivery <= 3:
        return "bucket_0_3_days"
    if days_since_last_delivery <= 7:
        return "bucket_4_7_days"
    if days_since_last_delivery <= 15:
        return "bucket_8_15_days"
    return "bucket_over_15_days"


def get_operations_dashboard(db: Session) -> dict[str, int | float | dict[str, str]]:
    orders = _get_dashboard_orders(db)
    summary = {
        "total_orders": 0,
        "orders_with_issues": 0,
        "orders_without_issues": 0,
        "total_pending_delivery_quantity": 0.0,
        "total_pending_invoice_quantity": 0.0,
        "pending_delivery_orders": 0,
        "pending_invoice_orders": 0,
        "pending_acceptance_orders": 0,
        "invoice_over_delivery_orders": 0,
        "labels_es": OPERATIONS_LABELS_ES,
        "orders_with_risk": 0,
        "orders_without_risk": 0,
        "delivered_not_invoiced_orders": 0,
        "partially_invoiced_orders": 0,
        "invoiced_over_delivered_orders": 0,
        "accepted_invoice_orders": 0,
        "pending_acceptance_invoice_orders": 0,
        "total_accepted_invoice_quantity": 0.0,
        "total_pending_acceptance_quantity": 0.0,
    }

    for order in orders:
        order_status_data = build_order_status_data(db, order)
        summary["total_orders"] += 1
        summary["total_pending_delivery_quantity"] += order_status_data["pending_delivery_quantity"]
        summary["total_pending_invoice_quantity"] += order_status_data["pending_invoice_quantity"]
        summary["total_accepted_invoice_quantity"] += order_status_data["invoiced_quantity"]
        summary["total_pending_acceptance_quantity"] += order_status_data["pending_acceptance_quantity"]

        if order_status_data["has_issue"]:
            summary["orders_with_issues"] += 1
            summary["orders_with_risk"] += 1
        else:
            summary["orders_without_issues"] += 1
            summary["orders_without_risk"] += 1

        if order_status_data["status"] == "pending_delivery":
            summary["pending_delivery_orders"] += 1
            summary["delivered_not_invoiced_orders"] += 1
        elif order_status_data["status"] == "pending_invoice":
            summary["pending_invoice_orders"] += 1
            summary["partially_invoiced_orders"] += 1
        elif order_status_data["status"] == "invoice_pending_acceptance":
            summary["pending_acceptance_orders"] += 1
            summary["partially_invoiced_orders"] += 1
        elif order_status_data["status"] == "invoice_over_delivery":
            summary["invoice_over_delivery_orders"] += 1
            summary["invoiced_over_delivered_orders"] += 1

        if order_status_data["invoiced_quantity"] > 0:
            summary["accepted_invoice_orders"] += 1
        if order_status_data["pending_acceptance_quantity"] > 0:
            summary["pending_acceptance_invoice_orders"] += 1

    return summary


def get_order_status_summary(db: Session) -> dict[str, int | dict[str, str]]:
    summary = {
        "ok": 0,
        "pending_delivery": 0,
        "pending_invoice": 0,
        "invoice_pending_acceptance": 0,
        "invoice_over_delivery": 0,
        "labels_es": ORDER_STATUS_SUMMARY_LABELS_ES,
    }

    for order in _get_dashboard_orders(db):
        order_status_data = build_order_status_data(db, order)
        summary[order_status_data["status"]] += 1

    return summary


def get_orders_with_incidents(db: Session) -> list[dict[str, int | float | str | bool]]:
    orders_with_incidents: list[dict[str, int | float | str | bool]] = []

    for order in _get_dashboard_orders(db):
        order_status_data = build_order_status_data(db, order)
        if order_status_data["has_issue"]:
            orders_with_incidents.append(order_status_data)

    orders_with_incidents.sort(key=lambda order: STATUS_PRIORITY[order["status"]])
    return orders_with_incidents


def get_pending_invoices(db: Session) -> list[dict[str, int | float | str]]:
    pending_invoices: list[dict[str, int | float | str]] = []

    for order in _get_dashboard_orders(db):
        order_status_data = build_order_status_data(db, order)
        if order_status_data["pending_invoice_quantity"] <= 0:
            continue

        pending_invoices.append(
            {
                "order_id": order_status_data["order_id"],
                "order_number": order_status_data["order_number"],
                "client_id": order_status_data["client_id"],
                "client_name": order_status_data["client_name"],
                "order_status": order_status_data["order_status"],
                "status": order_status_data["status"],
                "status_es": order_status_data["status_es"],
                "ordered_quantity": order_status_data["ordered_quantity"],
                "delivered_quantity": order_status_data["delivered_quantity"],
                "invoiced_quantity": order_status_data["invoiced_quantity"],
                "issued_quantity": order_status_data["issued_quantity"],
                "pending_acceptance_quantity": order_status_data["pending_acceptance_quantity"],
                "pending_invoice_quantity": order_status_data["pending_invoice_quantity"],
                "amount_pending_invoice": get_amount_pending_invoice(db, order.id),
                "risk_status": order_status_data["risk_status"],
                "risk_status_es": order_status_data["risk_status_es"],
                "invoice_document_status": order_status_data["invoice_document_status"],
                "invoice_document_status_es": order_status_data["invoice_document_status_es"],
            }
        )

    pending_invoices.sort(
        key=lambda order: (-order["amount_pending_invoice"], -order["pending_invoice_quantity"])
    )
    return pending_invoices


def get_pending_revenue(db: Session) -> list[dict[str, int | float | str]]:
    pending_revenue: list[dict[str, int | float | str]] = []

    for order in _get_dashboard_orders(db):
        order_status_data = build_order_status_data(db, order)
        if order_status_data["pending_invoice_quantity"] <= 0:
            continue

        priority = get_priority_for_order(
            status=order_status_data["status"],
            delivered_quantity=order_status_data["delivered_quantity"],
            invoiced_quantity=order_status_data["invoiced_quantity"],
            pending_delivery_quantity=order_status_data["pending_delivery_quantity"],
            pending_acceptance_quantity=order_status_data["pending_acceptance_quantity"],
        )
        pending_revenue.append(
            {
                "order_id": order_status_data["order_id"],
                "order_number": order_status_data["order_number"],
                "client_id": order_status_data["client_id"],
                "client_name": order_status_data["client_name"],
                "order_status": order_status_data["order_status"],
                "status": order_status_data["status"],
                "status_es": order_status_data["status_es"],
                "delivered_quantity": order_status_data["delivered_quantity"],
                "invoiced_quantity": order_status_data["invoiced_quantity"],
                "issued_quantity": order_status_data["issued_quantity"],
                "pending_acceptance_quantity": order_status_data["pending_acceptance_quantity"],
                "pending_invoice_quantity": order_status_data["pending_invoice_quantity"],
                "amount_pending_invoice": get_amount_pending_invoice(db, order.id),
                "days_since_last_delivery": get_days_since_last_delivery(db, order.id),
                "priority_level": priority,
                "priority_level_es": PRIORITY_LABELS_ES[priority],
                "risk_level": priority,
                "risk_level_es": PRIORITY_LABELS_ES[priority],
                "risk_status": order_status_data["risk_status"],
                "risk_status_es": order_status_data["risk_status_es"],
                "invoice_document_status": order_status_data["invoice_document_status"],
                "invoice_document_status_es": order_status_data["invoice_document_status_es"],
            }
        )

    pending_revenue.sort(
        key=lambda order: (
            PRIORITY_ORDER[order["priority_level"]],
            -order["amount_pending_invoice"],
            -order["pending_invoice_quantity"],
        )
    )
    return pending_revenue


def get_work_queue(db: Session) -> list[dict[str, int | float | str]]:
    work_queue: list[dict[str, int | float | str]] = []

    for order in _get_dashboard_orders(db):
        order_status_data = build_order_status_data(db, order)
        priority = get_priority_for_order(
            status=order_status_data["status"],
            delivered_quantity=order_status_data["delivered_quantity"],
            invoiced_quantity=order_status_data["invoiced_quantity"],
            pending_delivery_quantity=order_status_data["pending_delivery_quantity"],
            pending_acceptance_quantity=order_status_data["pending_acceptance_quantity"],
        )
        work_queue.append(
            {
                "order_id": order_status_data["order_id"],
                "order_number": order_status_data["order_number"],
                "client_id": order_status_data["client_id"],
                "client_name": order_status_data["client_name"],
                "order_status": order_status_data["order_status"],
                "delivered_quantity": order_status_data["delivered_quantity"],
                "invoiced_quantity": order_status_data["invoiced_quantity"],
                "issued_quantity": order_status_data["issued_quantity"],
                "pending_acceptance_quantity": order_status_data["pending_acceptance_quantity"],
                "pending_delivery_quantity": order_status_data["pending_delivery_quantity"],
                "pending_invoice_quantity": order_status_data["pending_invoice_quantity"],
                "status": order_status_data["status"],
                "status_es": order_status_data["status_es"],
                "priority": priority,
                "priority_es": PRIORITY_LABELS_ES[priority],
                "amount_pending_invoice": get_amount_pending_invoice(db, order.id),
                "days_since_last_delivery": get_days_since_last_delivery(db, order.id),
                "priority_level": priority,
                "priority_level_es": PRIORITY_LABELS_ES[priority],
                "invoice_document_status": order_status_data["invoice_document_status"],
                "invoice_document_status_es": order_status_data["invoice_document_status_es"],
            }
        )

    work_queue.sort(
        key=lambda order: (
            PRIORITY_ORDER[order["priority"]],
            STATUS_PRIORITY[order["status"]],
            -order["pending_invoice_quantity"],
            -order["pending_delivery_quantity"],
        )
    )
    return work_queue


def get_clients_with_incidents(db: Session) -> list[dict[str, int | float | str]]:
    clients_summary: dict[int, dict[str, int | float | str]] = {}

    for order in _get_dashboard_orders(db):
        order_status_data = build_order_status_data(db, order)
        client_id = order_status_data["client_id"]

        if client_id not in clients_summary:
            clients_summary[client_id] = {
                "client_id": client_id,
                "client_name": order_status_data["client_name"],
                "total_orders": 0,
                "orders_with_issues": 0,
                "total_pending_invoice_quantity": 0.0,
                "total_pending_invoice_amount": 0.0,
                "highest_priority_level": "none",
                "highest_priority_level_es": PRIORITY_LABELS_ES["none"],
                "orders_with_risk": 0,
                "highest_risk_level": "none",
                "highest_risk_level_es": PRIORITY_LABELS_ES["none"],
            }

        client_summary = clients_summary[client_id]
        client_summary["total_orders"] += 1

        if not order_status_data["has_issue"]:
            continue

        priority = get_priority_for_order(
            status=order_status_data["status"],
            delivered_quantity=order_status_data["delivered_quantity"],
            invoiced_quantity=order_status_data["invoiced_quantity"],
            pending_delivery_quantity=order_status_data["pending_delivery_quantity"],
            pending_acceptance_quantity=order_status_data["pending_acceptance_quantity"],
        )
        client_summary["orders_with_issues"] += 1
        client_summary["orders_with_risk"] += 1
        client_summary["total_pending_invoice_quantity"] += order_status_data["pending_invoice_quantity"]
        client_summary["total_pending_invoice_amount"] += get_amount_pending_invoice(db, order.id)

        if PRIORITY_ORDER[priority] < PRIORITY_ORDER[client_summary["highest_priority_level"]]:
            client_summary["highest_priority_level"] = priority
            client_summary["highest_priority_level_es"] = PRIORITY_LABELS_ES[priority]
            client_summary["highest_risk_level"] = priority
            client_summary["highest_risk_level_es"] = PRIORITY_LABELS_ES[priority]

    clients_with_incidents = [
        client_summary
        for client_summary in clients_summary.values()
        if client_summary["orders_with_issues"] > 0
    ]
    clients_with_incidents.sort(
        key=lambda client: (
            PRIORITY_ORDER[client["highest_priority_level"]],
            -client["total_pending_invoice_amount"],
            -client["total_pending_invoice_quantity"],
        )
    )
    return clients_with_incidents


def get_aging_invoices(db: Session) -> dict[str, float | dict[str, str]]:
    summary = {
        "bucket_0_3_days": 0.0,
        "bucket_4_7_days": 0.0,
        "bucket_8_15_days": 0.0,
        "bucket_over_15_days": 0.0,
        "total_pending_invoice_amount": 0.0,
        "labels_es": AGING_LABELS_ES,
    }

    for order in _get_dashboard_orders(db):
        order_status_data = build_order_status_data(db, order)
        if order_status_data["pending_invoice_quantity"] <= 0:
            continue

        amount_pending_invoice = get_amount_pending_invoice(db, order.id)
        aging_bucket = get_aging_bucket(get_days_since_last_delivery(db, order.id))
        summary[aging_bucket] += amount_pending_invoice
        summary["total_pending_invoice_amount"] += amount_pending_invoice

    return summary

