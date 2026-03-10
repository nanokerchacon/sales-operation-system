from fastapi import APIRouter, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import selectinload

from app.database.session import SessionLocal
from app.models.delivery import DeliveryItem, DeliveryNote
from app.models.order import OrderItem
from app.schemas.delivery import DeliveryNoteCreate, DeliveryNoteRead


router = APIRouter()


@router.post("", response_model=DeliveryNoteRead)
def create_delivery(delivery: DeliveryNoteCreate) -> DeliveryNote:
    db = SessionLocal()
    try:
        db_delivery = DeliveryNote(order_id=delivery.order_id)
        db.add(db_delivery)
        db.flush()

        requested_quantities: dict[int, float] = {}

        for item in delivery.items:
            order_item = db.get(OrderItem, item.order_item_id)
            if order_item is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"La línea de pedido {item.order_item_id} no existe.",
                )

            ordered_quantity = order_item.quantity

            delivered_quantity = (
                db.query(func.coalesce(func.sum(DeliveryItem.quantity), 0.0))
                .filter(DeliveryItem.order_item_id == item.order_item_id)
                .scalar()
            )
            delivered_quantity += requested_quantities.get(item.order_item_id, 0.0)

            remaining = ordered_quantity - delivered_quantity
            requested_quantity = item.quantity

            if requested_quantity > remaining:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"No se puede entregar más cantidad de la pedida en la línea "
                        f"{item.order_item_id} del pedido. Cantidad pedida: "
                        f"{ordered_quantity}. Ya entregada: {delivered_quantity}. "
                        f"Pendiente: {remaining}. Se intenta entregar ahora: "
                        f"{requested_quantity}."
                    ),
                )

            db.add(DeliveryItem(delivery_note_id=db_delivery.id, **item.model_dump()))
            requested_quantities[item.order_item_id] = (
                requested_quantities.get(item.order_item_id, 0.0) + requested_quantity
            )

        db.commit()

        return (
            db.query(DeliveryNote)
            .options(selectinload(DeliveryNote.items))
            .filter(DeliveryNote.id == db_delivery.id)
            .first()
        )
    finally:
        db.close()


@router.get("", response_model=list[DeliveryNoteRead])
def list_deliveries() -> list[DeliveryNote]:
    db = SessionLocal()
    try:
        return db.query(DeliveryNote).options(selectinload(DeliveryNote.items)).all()
    finally:
        db.close()
