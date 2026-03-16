from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload

from app.database.session import get_db
from app.models.order import Order, OrderItem
from app.schemas.order import OrderCreate, OrderRead
from app.schemas.order_traceability import OrderTraceabilityResponse
from app.services.access_control import CurrentUser, apply_order_scope, require_permission
from app.services.orders import get_order_traceability


router = APIRouter()


@router.post("", response_model=OrderRead)
def create_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("orders.create")),
) -> Order:
    order_payload = order.model_dump(exclude={"items"}, exclude_none=True)
    order_payload.setdefault("status", "draft")
    order_payload.setdefault("source", "erp")

    db_order = Order(**order_payload)
    db.add(db_order)
    db.flush()

    for item in order.items:
        item_payload = item.model_dump(exclude_none=True)
        db.add(OrderItem(order_id=db_order.id, **item_payload))

    db.commit()

    return (
        db.query(Order)
        .options(selectinload(Order.items))
        .filter(Order.id == db_order.id)
        .first()
    )


@router.get("", response_model=list[OrderRead])
def list_orders(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("orders.view")),
) -> list[Order]:
    query = db.query(Order).options(selectinload(Order.items))
    query = apply_order_scope(query, current_user.access_context)
    return query.all()


@router.get("/{order_id}/traceability", response_model=OrderTraceabilityResponse)
def order_traceability(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("orders.view")),
) -> OrderTraceabilityResponse:
    return get_order_traceability(db, order_id, current_user.access_context)
