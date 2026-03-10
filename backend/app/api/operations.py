from fastapi import APIRouter
from sqlalchemy import func

from app.database.session import SessionLocal
from app.models.delivery import DeliveryItem
from app.models.invoice import InvoiceItem
from app.models.order import Order, OrderItem


router = APIRouter()


OPERATION_STATUS_ES = {
    "pending_delivery": "Pendiente de envío",
    "partial_delivery": "Envío parcial",
    "pending_invoice": "Pendiente de facturar",
    "partial_invoice": "Facturación parcial",
    "fully_invoiced": "Completamente facturado",
}


def get_operation_status(
    ordered_quantity: float,
    delivered_quantity: float,
    invoiced_quantity: float,
) -> str:
    if delivered_quantity == 0 and invoiced_quantity == 0:
        return "pending_delivery"
    if delivered_quantity < ordered_quantity:
        return "partial_delivery"
    if delivered_quantity == ordered_quantity and invoiced_quantity == 0:
        return "pending_invoice"
    if invoiced_quantity > 0 and invoiced_quantity < ordered_quantity:
        return "partial_invoice"
    if invoiced_quantity == ordered_quantity:
        return "fully_invoiced"
    return "pending_delivery"


@router.get("/status")
def list_operations_status() -> list[dict[str, float | int | str]]:
    db = SessionLocal()
    try:
        orders = db.query(Order).all()
        response: list[dict[str, float | int | str]] = []

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
            pending_invoice_quantity = ordered_quantity - invoiced_quantity
            operation_status = get_operation_status(
                ordered_quantity=ordered_quantity,
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
                    "operation_status": operation_status,
                    "operation_status_es": OPERATION_STATUS_ES[operation_status],
                }
            )

        return response
    finally:
        db.close()
