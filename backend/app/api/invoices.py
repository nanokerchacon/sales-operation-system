from fastapi import APIRouter, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import selectinload

from app.database.session import SessionLocal
from app.models.delivery import DeliveryItem
from app.models.invoice import Invoice, InvoiceItem
from app.models.order import OrderItem
from app.schemas.invoice import InvoiceCreate, InvoiceRead


router = APIRouter()


@router.post("", response_model=InvoiceRead)
def create_invoice(invoice: InvoiceCreate) -> Invoice:
    db = SessionLocal()
    try:
        db_invoice = Invoice(order_id=invoice.order_id)
        db.add(db_invoice)
        db.flush()

        for item in invoice.items:
            order_item = db.query(OrderItem).filter(OrderItem.id == item.order_item_id).first()
            delivered_quantity = (
                db.query(func.coalesce(func.sum(DeliveryItem.quantity), 0.0))
                .filter(DeliveryItem.order_item_id == item.order_item_id)
                .scalar()
            )
            invoiced_quantity = (
                db.query(func.coalesce(func.sum(InvoiceItem.quantity), 0.0))
                .filter(InvoiceItem.order_item_id == item.order_item_id)
                .scalar()
            )
            remaining_invoiceable = delivered_quantity - invoiced_quantity

            if order_item is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"La línea de pedido {item.order_item_id} no existe.",
                )

            if item.quantity > remaining_invoiceable:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "No se puede facturar más cantidad de la entregada "
                        f"en la línea {item.order_item_id} del pedido. "
                        f"Cantidad entregada: {delivered_quantity}. "
                        f"Ya facturada: {invoiced_quantity}. "
                        f"Pendiente de facturar: {remaining_invoiceable}. "
                        f"Se intenta facturar ahora: {item.quantity}."
                    ),
                )

            db.add(InvoiceItem(invoice_id=db_invoice.id, **item.model_dump()))

        db.commit()

        return (
            db.query(Invoice)
            .options(selectinload(Invoice.items))
            .filter(Invoice.id == db_invoice.id)
            .first()
        )
    finally:
        db.close()


@router.get("", response_model=list[InvoiceRead])
def list_invoices() -> list[Invoice]:
    db = SessionLocal()
    try:
        return db.query(Invoice).options(selectinload(Invoice.items)).all()
    finally:
        db.close()
