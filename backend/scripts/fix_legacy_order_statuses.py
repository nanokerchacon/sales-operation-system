from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import func

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database.session import SessionLocal
from app.models.client import Client
from app.models.delivery import DeliveryItem
from app.models.invoice import InvoiceItem
from app.models.order import Order, OrderItem
from app.services.order_status import DEFAULT_LEGACY_ORDER_STATUS, infer_order_status


LEGACY_SOURCES = ("legacy_csv", "legacy")


def main() -> int:
    db = SessionLocal()
    try:
        legacy_orders = (
            db.query(Order)
            .filter(Order.source.in_(LEGACY_SOURCES), Order.status == "draft")
            .order_by(Order.id.asc())
            .all()
        )

        if not legacy_orders:
            print("No se encontraron pedidos legacy en draft para corregir.")
            return 0

        updates: list[tuple[Order, str]] = []
        for order in legacy_orders:
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
            new_status = infer_order_status(
                raw_status=None,
                ordered_quantity=ordered_quantity,
                delivered_quantity=delivered_quantity,
                invoiced_quantity=invoiced_quantity,
                pending_delivery_quantity=(ordered_quantity - delivered_quantity) if ordered_quantity else None,
                pending_invoice_quantity=(delivered_quantity - invoiced_quantity) if delivered_quantity else None,
                default_status=DEFAULT_LEGACY_ORDER_STATUS,
            )
            if new_status != order.status:
                updates.append((order, new_status))

        if not updates:
            print("No hay pedidos legacy en draft que requieran cambio de estado.")
            return 0

        print("Pedidos legacy detectados para actualizar:")
        for order, new_status in updates[:20]:
            print(
                f"- Pedido #{order.id} {order.series or ''}-{order.order_number or ''} "
                f"cliente={order.client_name_snapshot or order.client_id} draft -> {new_status}"
            )
        if len(updates) > 20:
            print(f"- ... {len(updates) - 20} pedidos mas")
        print("")
        print(f"Pedidos a cambiar: {len(updates)}")
        print("")

        confirmation = input("¿Confirmar actualizacion? (y/n) ").strip().lower()
        if confirmation != "y":
            print("Operacion cancelada.")
            return 0

        for order, new_status in updates:
            order.status = new_status

        db.commit()
        print("")
        print("Actualizacion completada.")
        print(f"Pedidos actualizados: {len(updates)}")
        return 0
    except Exception as exc:
        db.rollback()
        print(f"Correccion fallida: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
