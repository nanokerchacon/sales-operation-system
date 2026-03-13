from fastapi import APIRouter
from sqlalchemy.orm import selectinload

from app.database.session import SessionLocal
from app.models.order import Order, OrderItem
from app.schemas.order import OrderCreate, OrderRead
from app.schemas.order_traceability import OrderTraceabilityResponse
from app.services.orders import get_order_traceability


router = APIRouter()


@router.post("", response_model=OrderRead)
def create_order(order: OrderCreate) -> Order:
    db = SessionLocal()
    try:
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
    finally:
        db.close()


@router.get("", response_model=list[OrderRead])
def list_orders() -> list[Order]:
    db = SessionLocal()
    try:
        return db.query(Order).options(selectinload(Order.items)).all()
    finally:
        db.close()


@router.get("/{order_id}/traceability", response_model=OrderTraceabilityResponse)
def order_traceability(order_id: int) -> OrderTraceabilityResponse:
    db = SessionLocal()
    try:
        return get_order_traceability(db, order_id)
    finally:
        db.close()
