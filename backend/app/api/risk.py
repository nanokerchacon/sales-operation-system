from fastapi import APIRouter
from sqlalchemy import func

from app.database.session import SessionLocal
from app.models.delivery import DeliveryItem
from app.models.invoice import InvoiceItem
from app.models.order import Order, OrderItem


router = APIRouter()


RISK_STATUS_ES = {
    "no_risk": "Sin riesgo",
    "delivered_not_invoiced": "Entregado no facturado",
    "partially_invoiced": "Facturación parcial",
    "invoiced_over_delivered": "Facturado por encima de lo entregado",
}


def get_risk_status(delivered_quantity: float, invoiced_quantity: float) -> str:
    if delivered_quantity == 0 and invoiced_quantity == 0:
        return "no_risk"
    if delivered_quantity > 0 and invoiced_quantity == 0:
        return "delivered_not_invoiced"
    if delivered_quantity > invoiced_quantity and invoiced_quantity > 0:
        return "partially_invoiced"
    if delivered_quantity == invoiced_quantity and delivered_quantity > 0:
        return "no_risk"
    if invoiced_quantity > delivered_quantity:
        return "invoiced_over_delivered"
    return "no_risk"


@router.get("/summary")
def get_risk_summary() -> list[dict[str, float | int | str | bool]]:
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
            risk_status = get_risk_status(
                delivered_quantity=delivered_quantity,
                invoiced_quantity=invoiced_quantity,
            )

            response.append(
                {
                    "order_id": order.id,
                    "client_id": order.client_id,
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
            )

        return response
    finally:
        db.close()
