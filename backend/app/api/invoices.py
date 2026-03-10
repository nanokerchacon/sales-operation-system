from fastapi import APIRouter
from sqlalchemy.orm import selectinload

from app.database.session import SessionLocal
from app.models.invoice import Invoice, InvoiceItem
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
