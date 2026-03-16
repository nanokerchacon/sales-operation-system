from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.order import Order, OrderItem
from app.services.access_control import AccessContext, apply_client_scope, apply_order_scope



def build_client_location(client: Client) -> str:
    return client.address or "-"



def build_order_display_number(order: Order) -> str:
    if order.order_number:
        return order.order_number
    return f"PED-{order.id:06d}"



def _order_amount_expression():
    return func.coalesce(Order.total_amount, Order.subtotal, func.coalesce(func.sum(OrderItem.line_amount), 0.0))



def list_clients_overview(db: Session, access_context: AccessContext, search: str | None = None) -> list[dict[str, object]]:
    query = (
        db.query(
            Client.id,
            Client.name,
            Client.legacy_code,
            Client.tax_id,
            Client.address,
            Client.phone,
            Client.email,
            Client.created_at,
            func.count(func.distinct(Order.id)).label("order_count"),
            func.coalesce(func.sum(func.coalesce(Order.total_amount, Order.subtotal, 0.0)), 0.0).label("total_order_amount"),
            func.max(Order.order_date).label("last_order_date"),
        )
        .outerjoin(Order, Order.client_id == Client.id)
        .group_by(
            Client.id,
            Client.name,
            Client.legacy_code,
            Client.tax_id,
            Client.address,
            Client.phone,
            Client.email,
            Client.created_at,
        )
        .order_by(Client.name.asc())
    )
    query = apply_client_scope(query, access_context)

    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            Client.name.ilike(pattern)
            | Client.tax_id.ilike(pattern)
            | Client.email.ilike(pattern)
        )

    rows = query.all()
    return [
        {
            "id": row.id,
            "name": row.name,
            "legacy_code": row.legacy_code,
            "tax_id": row.tax_id,
            "address": row.address,
            "phone": row.phone,
            "email": row.email,
            "location": row.address,
            "order_count": int(row.order_count or 0),
            "total_order_amount": float(row.total_order_amount or 0.0),
            "last_order_date": row.last_order_date,
            "created_at": row.created_at,
        }
        for row in rows
    ]



def get_client_detail(db: Session, access_context: AccessContext, client_id: int) -> dict[str, object]:
    query = db.query(Client)
    query = apply_client_scope(query, access_context)
    client = query.filter(Client.id == client_id).first()
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    summary_row = (
        db.query(
            func.count(func.distinct(Order.id)).label("order_count"),
            func.coalesce(func.sum(func.coalesce(Order.total_amount, Order.subtotal, 0.0)), 0.0).label("total_order_amount"),
            func.max(Order.order_date).label("last_order_date"),
        )
        .filter(Order.client_id == client.id)
        .first()
    )

    return {
        "id": client.id,
        "name": client.name,
        "legacy_code": client.legacy_code,
        "tax_id": client.tax_id,
        "address": client.address,
        "phone": client.phone,
        "email": client.email,
        "location": build_client_location(client),
        "summary": {
            "order_count": int(summary_row.order_count or 0),
            "total_order_amount": float(summary_row.total_order_amount or 0.0),
            "last_order_date": summary_row.last_order_date,
        },
        "created_at": client.created_at,
    }



def get_client_orders(db: Session, access_context: AccessContext, client_id: int) -> dict[str, object]:
    client_query = apply_client_scope(db.query(Client), access_context)
    client = client_query.filter(Client.id == client_id).first()
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    orders_query = apply_order_scope(db.query(Order), access_context)
    orders = (
        orders_query
        .filter(Order.client_id == client_id)
        .order_by(Order.order_date.desc(), Order.id.desc())
        .all()
    )

    order_ids = [order.id for order in orders]
    line_amounts = {}
    if order_ids:
        for order_id, total in (
            db.query(OrderItem.order_id, func.coalesce(func.sum(OrderItem.line_amount), 0.0))
            .filter(OrderItem.order_id.in_(order_ids))
            .group_by(OrderItem.order_id)
            .all()
        ):
            line_amounts[order_id] = float(total or 0.0)

    return {
        "client_id": client_id,
        "orders": [
            {
                "id": order.id,
                "order_number": build_order_display_number(order),
                "order_date": order.order_date,
                "status": order.status,
                "total_amount": float(order.total_amount or order.subtotal or line_amounts.get(order.id, 0.0)),
                "source": order.source,
            }
            for order in orders
        ],
    }
