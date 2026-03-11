from fastapi import APIRouter
from sqlalchemy import func

from app.database.session import SessionLocal
from app.models.delivery import DeliveryItem
from app.models.invoice import InvoiceItem
from app.models.order import Order, OrderItem


router = APIRouter()


STATUS_ES = {
    "ok": "Completo",
    "pending_delivery": "Pendiente de entrega",
    "pending_invoice": "Pendiente de facturar",
    "invoice_over_delivery": "Error de facturación",
}

LEGACY_RISK_STATUS = {
    "ok": "no_risk",
    "pending_delivery": "delivered_not_invoiced",
    "pending_invoice": "partially_invoiced",
    "invoice_over_delivery": "invoiced_over_delivered",
}


def get_operational_status(
    ordered_quantity: float,
    delivered_quantity: float,
    invoiced_quantity: float,
) -> str:
    if invoiced_quantity > delivered_quantity:
        return "invoice_over_delivery"
    if ordered_quantity > delivered_quantity:
        return "pending_delivery"
    if delivered_quantity > invoiced_quantity:
        return "pending_invoice"
    return "ok"


@router.get("/summary")
def get_status_summary() -> list[dict[str, float | int | str | bool]]:
    db = SessionLocal()
    try:
        orders = db.query(Order).all()
        response: list[dict[str, float | int | str | bool]] = []

        for order in orders:
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

            pending_delivery_quantity = ordered_quantity - delivered_quantity
            pending_invoice_quantity = delivered_quantity - invoiced_quantity
            operational_status = get_operational_status(
                ordered_quantity=ordered_quantity,
                delivered_quantity=delivered_quantity,
                invoiced_quantity=invoiced_quantity,
            )
            legacy_risk_status = LEGACY_RISK_STATUS[operational_status]

            response.append(
                {
                    "order_id": order.id,
                    "client_id": order.client_id,
                    "order_status": order.status,
                    "status": operational_status,
                    "status_es": STATUS_ES[operational_status],
                    "ordered_quantity": ordered_quantity,
                    "delivered_quantity": delivered_quantity,
                    "invoiced_quantity": invoiced_quantity,
                    "pending_delivery_quantity": pending_delivery_quantity,
                    "pending_invoice_quantity": pending_invoice_quantity,
                    "has_issue": operational_status != "ok",
                    "risk_status": legacy_risk_status,
                    "risk_status_es": STATUS_ES[operational_status],
                    "has_risk": operational_status != "ok",
                }
            )

        return response
    finally:
        db.close()
