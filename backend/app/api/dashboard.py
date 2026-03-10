from datetime import date

from fastapi import APIRouter
from sqlalchemy import func

from app.api.risk import RISK_STATUS_ES, get_risk_status
from app.database.session import SessionLocal
from app.models.client import Client
from app.models.delivery import DeliveryItem, DeliveryNote
from app.models.invoice import InvoiceItem
from app.models.order import Order, OrderItem


router = APIRouter()


LABELS_ES = {
    "total_orders": "Total de pedidos",
    "orders_with_risk": "Pedidos con riesgo",
    "orders_without_risk": "Pedidos sin riesgo",
    "total_pending_delivery_quantity": "Cantidad pendiente de entregar",
    "total_pending_invoice_quantity": "Cantidad pendiente de facturar",
    "delivered_not_invoiced_orders": "Pedidos entregados no facturados",
    "partially_invoiced_orders": "Pedidos con facturación parcial",
    "invoiced_over_delivered_orders": "Pedidos facturados por encima de lo entregado",
}

AGING_LABELS_ES = {
    "bucket_0_3_days": "0 a 3 días",
    "bucket_4_7_days": "4 a 7 días",
    "bucket_8_15_days": "8 a 15 días",
    "bucket_over_15_days": "Más de 15 días",
    "total_pending_invoice_amount": "Total pendiente de facturar",
}

RISK_PRIORITY = {
    "delivered_not_invoiced": 0,
    "partially_invoiced": 1,
    "invoiced_over_delivered": 2,
}

RISK_LEVEL_ES = {
    "low": "Riesgo bajo",
    "medium": "Riesgo medio",
    "high": "Riesgo alto",
    "none": "Sin riesgo",
}

RISK_LEVEL_PRIORITY = {
    "high": 0,
    "medium": 1,
    "low": 2,
    "none": 3,
}


def build_order_risk_data(db: SessionLocal, order: Order) -> dict[str, int | float | str | bool]:
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
    invoiced_quantity = (
        db.query(func.coalesce(func.sum(InvoiceItem.quantity), 0.0))
        .join(OrderItem, OrderItem.id == InvoiceItem.order_item_id)
        .filter(OrderItem.order_id == order.id)
        .scalar()
    )
    client = db.query(Client).filter(Client.id == order.client_id).first()
    pending_delivery_quantity = ordered_quantity - delivered_quantity
    pending_invoice_quantity = delivered_quantity - invoiced_quantity
    risk_status = get_risk_status(
        delivered_quantity=delivered_quantity,
        invoiced_quantity=invoiced_quantity,
    )

    return {
        "order_id": order.id,
        "client_id": order.client_id,
        "client_name": client.name if client else "",
        "status": order.status,
        "ordered_quantity": ordered_quantity,
        "delivered_quantity": delivered_quantity,
        "invoiced_quantity": invoiced_quantity,
        "pending_delivery_quantity": pending_delivery_quantity,
        "pending_invoice_quantity": pending_invoice_quantity,
        "risk_status": risk_status,
        "risk_status_es": RISK_STATUS_ES[risk_status],
        "has_risk": risk_status != "no_risk",
    }


def get_amount_pending_invoice(db: SessionLocal, order_id: int) -> float:
    order_items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    amount_pending_invoice = 0.0

    for order_item in order_items:
        delivered_quantity = (
            db.query(func.coalesce(func.sum(DeliveryItem.quantity), 0.0))
            .filter(DeliveryItem.order_item_id == order_item.id)
            .scalar()
        )
        invoiced_quantity = (
            db.query(func.coalesce(func.sum(InvoiceItem.quantity), 0.0))
            .filter(InvoiceItem.order_item_id == order_item.id)
            .scalar()
        )
        pending_invoice_quantity = delivered_quantity - invoiced_quantity
        amount_pending_invoice += pending_invoice_quantity * order_item.unit_price

    return amount_pending_invoice


def get_days_since_last_delivery(db: SessionLocal, order_id: int) -> int:
    latest_delivery_date = (
        db.query(func.max(DeliveryNote.delivery_date))
        .filter(DeliveryNote.order_id == order_id)
        .scalar()
    )
    if latest_delivery_date is None:
        return 0

    return (date.today() - latest_delivery_date.date()).days


def get_risk_level(days_since_last_delivery: int) -> str:
    if days_since_last_delivery <= 3:
        return "low"
    if days_since_last_delivery <= 7:
        return "medium"
    return "high"


def get_aging_bucket(days_since_last_delivery: int) -> str:
    if days_since_last_delivery <= 3:
        return "bucket_0_3_days"
    if days_since_last_delivery <= 7:
        return "bucket_4_7_days"
    if days_since_last_delivery <= 15:
        return "bucket_8_15_days"
    return "bucket_over_15_days"


@router.get("/operations")
def get_operations_dashboard() -> dict[str, int | float | dict[str, str]]:
    db = SessionLocal()
    try:
        orders = db.query(Order).all()
        summary = {
            "total_orders": 0,
            "orders_with_risk": 0,
            "orders_without_risk": 0,
            "total_pending_delivery_quantity": 0.0,
            "total_pending_invoice_quantity": 0.0,
            "delivered_not_invoiced_orders": 0,
            "partially_invoiced_orders": 0,
            "invoiced_over_delivered_orders": 0,
            "labels_es": LABELS_ES,
        }

        for order in orders:
            order_risk_data = build_order_risk_data(db, order)

            summary["total_orders"] += 1
            summary["total_pending_delivery_quantity"] += order_risk_data["pending_delivery_quantity"]
            summary["total_pending_invoice_quantity"] += order_risk_data["pending_invoice_quantity"]

            if order_risk_data["has_risk"]:
                summary["orders_with_risk"] += 1
            else:
                summary["orders_without_risk"] += 1

            if order_risk_data["risk_status"] == "delivered_not_invoiced":
                summary["delivered_not_invoiced_orders"] += 1
            elif order_risk_data["risk_status"] == "partially_invoiced":
                summary["partially_invoiced_orders"] += 1
            elif order_risk_data["risk_status"] == "invoiced_over_delivered":
                summary["invoiced_over_delivered_orders"] += 1

        return summary
    finally:
        db.close()


@router.get("/risk-orders")
def get_risk_orders() -> list[dict[str, int | float | str | bool]]:
    db = SessionLocal()
    try:
        orders = db.query(Order).all()
        risk_orders: list[dict[str, int | float | str | bool]] = []

        for order in orders:
            order_risk_data = build_order_risk_data(db, order)
            if order_risk_data["has_risk"]:
                risk_orders.append(order_risk_data)

        risk_orders.sort(key=lambda order: RISK_PRIORITY[order["risk_status"]])

        return risk_orders
    finally:
        db.close()


@router.get("/pending-invoices")
def get_pending_invoices() -> list[dict[str, int | float | str]]:
    db = SessionLocal()
    try:
        orders = db.query(Order).all()
        pending_invoices: list[dict[str, int | float | str]] = []

        for order in orders:
            order_risk_data = build_order_risk_data(db, order)
            if order_risk_data["delivered_quantity"] <= order_risk_data["invoiced_quantity"]:
                continue

            pending_invoices.append(
                {
                    "order_id": order_risk_data["order_id"],
                    "client_id": order_risk_data["client_id"],
                    "client_name": order_risk_data["client_name"],
                    "status": order_risk_data["status"],
                    "ordered_quantity": order_risk_data["ordered_quantity"],
                    "delivered_quantity": order_risk_data["delivered_quantity"],
                    "invoiced_quantity": order_risk_data["invoiced_quantity"],
                    "pending_invoice_quantity": order_risk_data["pending_invoice_quantity"],
                    "amount_pending_invoice": get_amount_pending_invoice(db, order.id),
                    "risk_status": order_risk_data["risk_status"],
                    "risk_status_es": order_risk_data["risk_status_es"],
                }
            )

        pending_invoices.sort(
            key=lambda order: (
                -order["amount_pending_invoice"],
                -order["pending_invoice_quantity"],
            )
        )

        return pending_invoices
    finally:
        db.close()


@router.get("/revenue-at-risk")
def get_revenue_at_risk() -> list[dict[str, int | float | str]]:
    db = SessionLocal()
    try:
        orders = db.query(Order).all()
        revenue_at_risk: list[dict[str, int | float | str]] = []

        for order in orders:
            order_risk_data = build_order_risk_data(db, order)
            if order_risk_data["delivered_quantity"] <= order_risk_data["invoiced_quantity"]:
                continue

            days_since_last_delivery = get_days_since_last_delivery(db, order.id)
            risk_level = get_risk_level(days_since_last_delivery)

            revenue_at_risk.append(
                {
                    "order_id": order_risk_data["order_id"],
                    "client_id": order_risk_data["client_id"],
                    "client_name": order_risk_data["client_name"],
                    "status": order_risk_data["status"],
                    "delivered_quantity": order_risk_data["delivered_quantity"],
                    "invoiced_quantity": order_risk_data["invoiced_quantity"],
                    "pending_invoice_quantity": order_risk_data["pending_invoice_quantity"],
                    "amount_pending_invoice": get_amount_pending_invoice(db, order.id),
                    "days_since_last_delivery": days_since_last_delivery,
                    "risk_level": risk_level,
                    "risk_level_es": RISK_LEVEL_ES[risk_level],
                    "risk_status": order_risk_data["risk_status"],
                    "risk_status_es": order_risk_data["risk_status_es"],
                }
            )

        revenue_at_risk.sort(
            key=lambda order: (
                RISK_LEVEL_PRIORITY[order["risk_level"]],
                -order["amount_pending_invoice"],
                -order["pending_invoice_quantity"],
            )
        )

        return revenue_at_risk
    finally:
        db.close()


@router.get("/work-queue")
def get_work_queue() -> list[dict[str, int | float | str]]:
    db = SessionLocal()
    try:
        orders = db.query(Order).all()
        work_queue: list[dict[str, int | float | str]] = []

        for order in orders:
            order_risk_data = build_order_risk_data(db, order)
            if order_risk_data["delivered_quantity"] <= order_risk_data["invoiced_quantity"]:
                continue

            days_since_last_delivery = get_days_since_last_delivery(db, order.id)
            risk_level = get_risk_level(days_since_last_delivery)

            work_queue.append(
                {
                    "order_id": order_risk_data["order_id"],
                    "client_id": order_risk_data["client_id"],
                    "client_name": order_risk_data["client_name"],
                    "status": order_risk_data["status"],
                    "delivered_quantity": order_risk_data["delivered_quantity"],
                    "invoiced_quantity": order_risk_data["invoiced_quantity"],
                    "pending_invoice_quantity": order_risk_data["pending_invoice_quantity"],
                    "amount_pending_invoice": get_amount_pending_invoice(db, order.id),
                    "days_since_last_delivery": days_since_last_delivery,
                    "risk_status": order_risk_data["risk_status"],
                    "risk_status_es": order_risk_data["risk_status_es"],
                    "risk_level": risk_level,
                    "risk_level_es": RISK_LEVEL_ES[risk_level],
                }
            )

        work_queue.sort(
            key=lambda order: (
                RISK_LEVEL_PRIORITY[order["risk_level"]],
                -order["amount_pending_invoice"],
                -order["pending_invoice_quantity"],
            )
        )

        return work_queue
    finally:
        db.close()


@router.get("/client-risk")
def get_client_risk() -> list[dict[str, int | float | str]]:
    db = SessionLocal()
    try:
        orders = db.query(Order).all()
        clients_summary: dict[int, dict[str, int | float | str]] = {}

        for order in orders:
            order_risk_data = build_order_risk_data(db, order)
            client_id = order_risk_data["client_id"]

            if client_id not in clients_summary:
                clients_summary[client_id] = {
                    "client_id": client_id,
                    "client_name": order_risk_data["client_name"],
                    "total_orders": 0,
                    "orders_with_risk": 0,
                    "total_pending_invoice_quantity": 0.0,
                    "total_pending_invoice_amount": 0.0,
                    "highest_risk_level": "none",
                    "highest_risk_level_es": RISK_LEVEL_ES["none"],
                }

            client_summary = clients_summary[client_id]
            client_summary["total_orders"] += 1

            if order_risk_data["delivered_quantity"] <= order_risk_data["invoiced_quantity"]:
                continue

            client_summary["orders_with_risk"] += 1
            client_summary["total_pending_invoice_quantity"] += order_risk_data["pending_invoice_quantity"]
            client_summary["total_pending_invoice_amount"] += get_amount_pending_invoice(db, order.id)

            days_since_last_delivery = get_days_since_last_delivery(db, order.id)
            risk_level = get_risk_level(days_since_last_delivery)
            current_highest_risk_level = client_summary["highest_risk_level"]

            if RISK_LEVEL_PRIORITY[risk_level] < RISK_LEVEL_PRIORITY[current_highest_risk_level]:
                client_summary["highest_risk_level"] = risk_level
                client_summary["highest_risk_level_es"] = RISK_LEVEL_ES[risk_level]

        risky_clients = [
            client_summary
            for client_summary in clients_summary.values()
            if client_summary["orders_with_risk"] > 0
        ]

        risky_clients.sort(
            key=lambda client: (
                RISK_LEVEL_PRIORITY[client["highest_risk_level"]],
                -client["total_pending_invoice_amount"],
                -client["total_pending_invoice_quantity"],
            )
        )

        return risky_clients
    finally:
        db.close()


@router.get("/aging-invoices")
def get_aging_invoices() -> dict[str, float | dict[str, str]]:
    db = SessionLocal()
    try:
        orders = db.query(Order).all()
        summary = {
            "bucket_0_3_days": 0.0,
            "bucket_4_7_days": 0.0,
            "bucket_8_15_days": 0.0,
            "bucket_over_15_days": 0.0,
            "total_pending_invoice_amount": 0.0,
            "labels_es": AGING_LABELS_ES,
        }

        for order in orders:
            order_risk_data = build_order_risk_data(db, order)
            if order_risk_data["delivered_quantity"] <= order_risk_data["invoiced_quantity"]:
                continue

            amount_pending_invoice = get_amount_pending_invoice(db, order.id)
            days_since_last_delivery = get_days_since_last_delivery(db, order.id)
            aging_bucket = get_aging_bucket(days_since_last_delivery)

            summary[aging_bucket] += amount_pending_invoice
            summary["total_pending_invoice_amount"] += amount_pending_invoice

        return summary
    finally:
        db.close()
