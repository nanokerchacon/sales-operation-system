from __future__ import annotations

import re
import sys
from pathlib import Path

from sqlalchemy import or_


SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database.session import SessionLocal
from app.models.client import Client
from app.models.delivery import DeliveryItem, DeliveryNote
from app.models.invoice import Invoice, InvoiceItem
from app.models.order import Order, OrderItem


DEMO_NAME_PATTERNS = (
    "Tecnoceramic",
    "Demo",
    "Test",
    "Example",
)
DEMO_REGEX = re.compile("|".join(re.escape(pattern) for pattern in DEMO_NAME_PATTERNS), re.IGNORECASE)


def _build_name_filter():
    return or_(*(Client.name.ilike(f"%{pattern}%") for pattern in DEMO_NAME_PATTERNS))


def main() -> int:
    db = SessionLocal()
    try:
        matched_clients = (
            db.query(Client)
            .filter(_build_name_filter())
            .order_by(Client.name.asc(), Client.id.asc())
            .all()
        )

        if not matched_clients:
            print("No se encontraron clientes con coincidencias claras de datos ficticios.")
            return 0

        deletable_clients: list[Client] = []
        protected_clients: list[tuple[Client, int]] = []
        total_orders_to_delete = 0

        for client in matched_clients:
            client_orders = db.query(Order.id, Order.source).filter(Order.client_id == client.id).all()
            legacy_order_count = sum(1 for _, source in client_orders if source == "legacy_csv")
            if legacy_order_count > 0:
                protected_clients.append((client, legacy_order_count))
                continue

            if not DEMO_REGEX.search(client.name or ""):
                continue

            deletable_clients.append(client)
            total_orders_to_delete += len(client_orders)

        if protected_clients:
            print("Clientes protegidos por tener pedidos importados desde CSV:")
            for client, legacy_order_count in protected_clients:
                print(f"- {client.name} (id={client.id}, pedidos legacy_csv={legacy_order_count})")
            print("")

        if not deletable_clients:
            print("No hay clientes ficticios seguros para eliminar.")
            return 0

        print("Clientes detectados para eliminar:")
        for client in deletable_clients:
            print(f"- {client.name}")
        print("")
        print(f"Pedidos asociados encontrados: {total_orders_to_delete}")
        print("")

        confirmation = input("¿Confirmar eliminación? (y/n) ").strip().lower()
        if confirmation != "y":
            print("Operación cancelada.")
            return 0

        client_ids = [client.id for client in deletable_clients]
        order_ids = [order_id for (order_id,) in db.query(Order.id).filter(Order.client_id.in_(client_ids)).all()]

        deleted_invoice_items = 0
        deleted_delivery_items = 0
        deleted_invoices = 0
        deleted_delivery_notes = 0
        deleted_order_items = 0
        deleted_orders = 0

        if order_ids:
            order_item_ids = [
                order_item_id
                for (order_item_id,) in db.query(OrderItem.id).filter(OrderItem.order_id.in_(order_ids)).all()
            ]

            if order_item_ids:
                deleted_delivery_items = (
                    db.query(DeliveryItem)
                    .filter(DeliveryItem.order_item_id.in_(order_item_ids))
                    .delete(synchronize_session=False)
                )
                deleted_invoice_items = (
                    db.query(InvoiceItem)
                    .filter(InvoiceItem.order_item_id.in_(order_item_ids))
                    .delete(synchronize_session=False)
                )

            deleted_delivery_notes = (
                db.query(DeliveryNote)
                .filter(DeliveryNote.order_id.in_(order_ids))
                .delete(synchronize_session=False)
            )
            deleted_invoices = (
                db.query(Invoice)
                .filter(Invoice.order_id.in_(order_ids))
                .delete(synchronize_session=False)
            )
            deleted_order_items = (
                db.query(OrderItem)
                .filter(OrderItem.order_id.in_(order_ids))
                .delete(synchronize_session=False)
            )
            deleted_orders = (
                db.query(Order)
                .filter(Order.id.in_(order_ids))
                .delete(synchronize_session=False)
            )

        deleted_clients = (
            db.query(Client)
            .filter(Client.id.in_(client_ids))
            .delete(synchronize_session=False)
        )

        db.commit()

        print("")
        print("Eliminación completada.")
        print(f"Clientes eliminados: {deleted_clients}")
        print(f"Pedidos eliminados: {deleted_orders}")

        if deleted_order_items or deleted_delivery_notes or deleted_invoices:
            print(f"Lineas de pedido eliminadas: {deleted_order_items}")
            print(f"Albaranes eliminados: {deleted_delivery_notes}")
            print(f"Facturas eliminadas: {deleted_invoices}")
            print(f"Lineas de entrega eliminadas: {deleted_delivery_items}")
            print(f"Lineas de factura eliminadas: {deleted_invoice_items}")

        return 0
    except Exception as exc:
        db.rollback()
        print(f"Limpieza fallida: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
