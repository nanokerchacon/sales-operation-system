from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.database.session import get_db
from app.models.delivery import DeliveryItem
from app.models.invoice import Invoice, InvoiceItem
from app.models.order import Order, OrderItem
from app.schemas.invoice import InvoiceCreate, InvoiceDetailResponse, InvoiceListItem, InvoiceRead
from app.services.access_control import CurrentUser, require_order_access, require_permission
from app.services.invoice_documents import resolve_invoice_document_metadata
from app.services.invoices import get_invoice_detail, list_invoices_overview


router = APIRouter()


@router.post("", response_model=InvoiceRead)
def create_invoice(
    invoice: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("invoices.create")),
) -> Invoice:
    order = db.get(Order, invoice.order_id)
    require_order_access(db, current_user.access_context, order)

    document_metadata = resolve_invoice_document_metadata(
        source_folder=invoice.source_folder,
        invoice_type=invoice.invoice_type,
        invoice_status=invoice.invoice_status,
    )
    db_invoice = Invoice(order_id=invoice.order_id, **document_metadata)
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


@router.get("", response_model=list[InvoiceListItem])
def list_invoices(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("invoices.view")),
) -> list[dict[str, object]]:
    return list_invoices_overview(db, current_user.access_context)


@router.get("/{invoice_id}", response_model=InvoiceDetailResponse)
def invoice_detail(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("invoices.view")),
) -> dict[str, object]:
    invoice = get_invoice_detail(db, invoice_id, current_user.access_context)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice
