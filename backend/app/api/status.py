from fastapi import APIRouter
from sqlalchemy import func

from app.database.session import SessionLocal
from app.models.delivery import DeliveryItem
from app.models.order import Order, OrderItem
from app.services.invoice_documents import (
    INVOICE_DOCUMENT_STATUS_ES,
    get_order_invoice_document_totals,
)


router = APIRouter()


STATUS_ES = {
    "ok": "Completo",
    "pending_delivery": "Pendiente de entrega",
    "pending_invoice": "Pendiente de facturar",
    "invoice_pending_acceptance": "Factura pendiente de aceptación",
    "invoice_over_delivery": "Error de facturación",
}

LEGACY_RISK_STATUS = {
    "ok": "no_risk",
    "pending_delivery": "delivered_not_invoiced",
    "pending_invoice": "partially_invoiced",
    "invoice_pending_acceptance": "partially_invoiced",
    "invoice_over_delivery": "invoiced_over_delivered",
}


def get_operational_status(
    ordered_quantity: float,
    delivered_quantity: float,
    invoiced_quantity: float,
    *,
    issued_quantity: float | None = None,
    pending_acceptance_quantity: float = 0.0,
) -> str:
    effective_issued_quantity = invoiced_quantity if issued_quantity is None else issued_quantity

    if effective_issued_quantity > delivered_quantity:
        return "invoice_over_delivery"
    if ordered_quantity > delivered_quantity:
        return "pending_delivery"
    if delivered_quantity > invoiced_quantity:
        if pending_acceptance_quantity > 0 and effective_issued_quantity >= delivered_quantity:
            return "invoice_pending_acceptance"
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
            invoice_totals = get_order_invoice_document_totals(db, order.id)
            accepted_quantity = float(invoice_totals["accepted_quantity"])
            issued_quantity = float(invoice_totals["issued_quantity"])
            pending_acceptance_quantity = float(invoice_totals["pending_acceptance_quantity"])

            pending_delivery_quantity = ordered_quantity - delivered_quantity
            pending_invoice_quantity = delivered_quantity - accepted_quantity
            operational_status = get_operational_status(
                ordered_quantity=ordered_quantity,
                delivered_quantity=delivered_quantity,
                invoiced_quantity=accepted_quantity,
                issued_quantity=issued_quantity,
                pending_acceptance_quantity=pending_acceptance_quantity,
            )
            legacy_risk_status = LEGACY_RISK_STATUS[operational_status]
            invoice_document_status = (
                "invoice_pending_acceptance"
                if pending_acceptance_quantity > 0
                else "invoice_accepted"
                if delivered_quantity > 0 and accepted_quantity >= delivered_quantity
                else "invoice_issued"
                if issued_quantity > 0
                else "not_invoiced"
            )

            response.append(
                {
                    "order_id": order.id,
                    "client_id": order.client_id,
                    "order_status": order.status,
                    "status": operational_status,
                    "status_es": STATUS_ES[operational_status],
                    "ordered_quantity": ordered_quantity,
                    "delivered_quantity": delivered_quantity,
                    "invoiced_quantity": accepted_quantity,
                    "issued_quantity": issued_quantity,
                    "pending_acceptance_quantity": pending_acceptance_quantity,
                    "pending_delivery_quantity": pending_delivery_quantity,
                    "pending_invoice_quantity": pending_invoice_quantity,
                    "has_issue": operational_status != "ok",
                    "risk_status": legacy_risk_status,
                    "risk_status_es": STATUS_ES[operational_status],
                    "has_risk": operational_status != "ok",
                    "invoice_document_status": invoice_document_status,
                    "invoice_document_status_es": INVOICE_DOCUMENT_STATUS_ES[invoice_document_status],
                }
            )

        return response
    finally:
        db.close()
