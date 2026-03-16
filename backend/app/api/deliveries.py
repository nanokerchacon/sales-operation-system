from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.database.session import get_db
from app.models.delivery import DeliveryItem, DeliveryNote
from app.models.order import Order, OrderItem
from app.schemas.delivery import DeliveryDetailResponse, DeliveryListItem, DeliveryNoteCreate, DeliveryNoteRead
from app.services.access_control import CurrentUser, require_order_access, require_permission
from app.services.deliveries import get_delivery_detail, list_deliveries_overview


router = APIRouter()


@router.post("", response_model=DeliveryNoteRead)
def create_delivery(
    delivery: DeliveryNoteCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("deliveries.create")),
) -> DeliveryNote:
    order = db.get(Order, delivery.order_id)
    require_order_access(db, current_user.access_context, order)

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

    db.flush()

    total_ordered_quantity = (
        db.query(func.coalesce(func.sum(OrderItem.quantity), 0.0))
        .filter(OrderItem.order_id == delivery.order_id)
        .scalar()
    )
    total_delivered_quantity = (
        db.query(func.coalesce(func.sum(DeliveryItem.quantity), 0.0))
        .join(OrderItem, OrderItem.id == DeliveryItem.order_item_id)
        .filter(OrderItem.order_id == delivery.order_id)
        .scalar()
    )

    if total_delivered_quantity == total_ordered_quantity and order is not None:
        order.status = "completed"

    db.commit()

    return (
        db.query(DeliveryNote)
        .options(selectinload(DeliveryNote.items))
        .filter(DeliveryNote.id == db_delivery.id)
        .first()
    )


@router.get("", response_model=list[DeliveryListItem])
def list_deliveries(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("deliveries.view")),
) -> list[dict[str, object]]:
    return list_deliveries_overview(db, current_user.access_context)


@router.get("/{delivery_id}", response_model=DeliveryDetailResponse)
def delivery_detail(
    delivery_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("deliveries.view")),
) -> dict[str, object]:
    return get_delivery_detail(db, delivery_id, current_user.access_context)
