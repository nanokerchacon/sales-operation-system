from __future__ import annotations

import csv
import re
import unicodedata
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.services.order_status import DEFAULT_LEGACY_ORDER_STATUS, infer_order_status


REQUIRED_COLUMNS = {
    "F_PEDIDO",
    "SERIE_PEDV",
    "PEDIDO",
    "CLIENTE",
    "NOMBRE_CLIENTE",
    "LIN_PED",
    "ARTICULO",
    "DESCRIPCION_ARTICULO",
    "CANTIDAD",
    "PRECIO_VTA",
    "IMPORTE_LIN",
}
STATUS_COLUMNS = {
    "ESTADO",
    "STATUS",
    "ORDER_STATUS",
    "ESTADO_PEDIDO",
    "SITUACION",
    "SITUACION_PEDIDO",
}
DELIVERED_COLUMNS = {
    "ENTREGADO",
    "SERVIDO",
    "DELIVERED",
    "CANTIDAD_ENTREGADA",
    "QTY_DELIVERED",
    "TOTAL_ENTREGADO",
}
INVOICED_COLUMNS = {
    "FACTURADO",
    "INVOICED",
    "CANTIDAD_FACTURADA",
    "QTY_INVOICED",
    "TOTAL_FACTURADO",
}
PENDING_DELIVERY_COLUMNS = {
    "PENDIENTE_ENTREGA",
    "PTE_ENTREGA",
    "PENDING_DELIVERY",
    "QTY_PENDING_DELIVERY",
    "CANTIDAD_PENDIENTE_ENTREGA",
}
PENDING_INVOICE_COLUMNS = {
    "PENDIENTE_FACTURA",
    "PTE_FACTURA",
    "PENDING_INVOICE",
    "QTY_PENDING_INVOICE",
    "CANTIDAD_PENDIENTE_FACTURA",
}
EMPTY_TEXT_TOKENS = {"", "-", "NULL", "NONE", "NULO", "(NULL)"}


@dataclass
class LegacyImportStats:
    orders_created: int = 0
    orders_skipped: int = 0
    order_items_created: int = 0
    clients_created: int = 0
    products_created: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "orders_created": self.orders_created,
            "orders_skipped": self.orders_skipped,
            "order_items_created": self.order_items_created,
            "clients_created": self.clients_created,
            "products_created": self.products_created,
        }


def import_legacy_orders_from_csv(db: Session, csv_path: str | Path) -> LegacyImportStats:
    normalized_rows = _load_rows(csv_path)
    grouped_orders = _group_rows_by_order(normalized_rows)
    stats = LegacyImportStats()
    existing_order_keys = {
        (order.series or "", order.order_number or "")
        for order in db.query(Order.series, Order.order_number).filter(Order.source == "legacy_csv").all()
    }
    client_cache_by_legacy: dict[str, Client] = {}
    client_cache_by_name: dict[str, Client] = {}
    product_cache_by_legacy: dict[str, Product] = {}
    product_cache_by_sku: dict[str, Product] = {}

    for (series, order_number), order_rows in grouped_orders.items():
        if (series, order_number) in existing_order_keys:
            stats.orders_skipped += 1
            continue

        first_row = order_rows[0]
        client = _resolve_client(
            db=db,
            legacy_code=first_row["CLIENTE"],
            client_name=first_row["NOMBRE_CLIENTE"],
            stats=stats,
            cache_by_legacy=client_cache_by_legacy,
            cache_by_name=client_cache_by_name,
        )

        order_date = first_row["F_PEDIDO"]
        order = Order(
            client_id=client.id,
            series=series,
            order_number=order_number,
            legacy_client_code=first_row["CLIENTE"] or None,
            client_name_snapshot=first_row["NOMBRE_CLIENTE"] or client.name,
            source="legacy_csv",
            subtotal=0.0,
            tax_amount=0.0,
            total_amount=0.0,
            status=map_legacy_order_status(order_rows),
        )
        if order_date is not None:
            order.order_date = order_date

        db.add(order)
        db.flush()

        occupied_line_numbers = {row["LIN_PED"] for row in order_rows if row["LIN_PED"] is not None}
        explicit_line_numbers: set[int] = set()
        next_line_number = 1
        order_subtotal = Decimal("0")
        sorted_rows = sorted(order_rows, key=lambda row: (row["LIN_PED"] is None, row["LIN_PED"] or 0))
        for row in sorted_rows:
            line_number = row["LIN_PED"]
            if line_number is None:
                while next_line_number in occupied_line_numbers:
                    next_line_number += 1
                line_number = next_line_number
                occupied_line_numbers.add(line_number)
                next_line_number += 1
            else:
                if line_number in explicit_line_numbers:
                    raise ValueError(
                        f"Duplicate line number {line_number} in legacy order {series}-{order_number}"
                    )
                explicit_line_numbers.add(line_number)

            article_code = row["ARTICULO"]
            product_id = None
            line_type = "text"
            if article_code:
                product = _resolve_product(
                    db=db,
                    legacy_code=article_code,
                    description=row["DESCRIPCION_ARTICULO"],
                    unit_price=row["PRECIO_VTA"],
                    stats=stats,
                    cache_by_legacy=product_cache_by_legacy,
                    cache_by_sku=product_cache_by_sku,
                )
                product_id = product.id
                line_type = "product"

            line_amount = row["IMPORTE_LIN"]
            order_subtotal += line_amount
            order_item = OrderItem(
                order_id=order.id,
                product_id=product_id,
                line_number=line_number,
                line_type=line_type,
                legacy_article_code=article_code or None,
                description=row["DESCRIPCION_ARTICULO"] or None,
                quantity=float(row["CANTIDAD"]),
                unit_price=float(row["PRECIO_VTA"]),
                line_amount=float(line_amount),
            )
            db.add(order_item)
            stats.order_items_created += 1

        order.subtotal = float(order_subtotal)
        order.total_amount = float(order_subtotal)
        stats.orders_created += 1
        existing_order_keys.add((series, order_number))

    db.commit()
    return stats


def map_legacy_order_status(order_rows: list[dict[str, object]]) -> str:
    explicit_status = next((str(row["LEGACY_STATUS_RAW"]) for row in order_rows if row["LEGACY_STATUS_RAW"]), None)
    ordered_quantity = _sum_decimal_field(order_rows, "CANTIDAD")
    delivered_quantity = _sum_optional_decimal_field(order_rows, "DELIVERED_QUANTITY")
    invoiced_quantity = _sum_optional_decimal_field(order_rows, "INVOICED_QUANTITY")
    pending_delivery_quantity = _sum_optional_decimal_field(order_rows, "PENDING_DELIVERY_QUANTITY")
    pending_invoice_quantity = _sum_optional_decimal_field(order_rows, "PENDING_INVOICE_QUANTITY")

    return infer_order_status(
        raw_status=explicit_status,
        ordered_quantity=ordered_quantity,
        delivered_quantity=delivered_quantity,
        invoiced_quantity=invoiced_quantity,
        pending_delivery_quantity=pending_delivery_quantity,
        pending_invoice_quantity=pending_invoice_quantity,
        default_status=DEFAULT_LEGACY_ORDER_STATUS,
    )


def _load_rows(csv_path: str | Path) -> list[dict[str, object]]:
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        sample = csv_file.read(4096)
        csv_file.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;") if sample else csv.excel
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(csv_file, dialect=dialect)
        if reader.fieldnames is None:
            raise ValueError("CSV file has no header row")

        normalized_fieldnames = [_normalize_header(name) for name in reader.fieldnames]
        missing_columns = REQUIRED_COLUMNS.difference(normalized_fieldnames)
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"CSV file is missing required columns: {missing}")

        rows: list[dict[str, object]] = []
        for row_number, raw_row in enumerate(reader, start=2):
            normalized_row = {
                _normalize_header(key): value
                for key, value in raw_row.items()
                if key is not None
            }
            if not any(_normalize_text(value) for value in normalized_row.values()):
                continue
            rows.append(_normalize_row(normalized_row, row_number))

    return rows


def _normalize_row(row: dict[str, str | None], row_number: int) -> dict[str, object]:
    series = _normalize_text(row.get("SERIE_PEDV"))
    order_number = _normalize_text(row.get("PEDIDO"))
    if not series or not order_number:
        raise ValueError(f"Row {row_number}: SERIE_PEDV and PEDIDO are required")

    article_code = _normalize_text(row.get("ARTICULO"))
    if article_code:
        quantity = _parse_decimal(row.get("CANTIDAD"), row_number, "CANTIDAD")
        unit_price = _parse_decimal(row.get("PRECIO_VTA"), row_number, "PRECIO_VTA")
        line_amount_raw = _normalize_text(row.get("IMPORTE_LIN"))
        line_amount = (
            _parse_decimal(row.get("IMPORTE_LIN"), row_number, "IMPORTE_LIN")
            if line_amount_raw
            else quantity * unit_price
        )
    else:
        quantity = _parse_decimal_optional(row.get("CANTIDAD"), default=Decimal("0"))
        unit_price = _parse_decimal_optional(row.get("PRECIO_VTA"), default=Decimal("0"))
        line_amount = _parse_decimal_optional(row.get("IMPORTE_LIN"), default=Decimal("0"))

    return {
        "F_PEDIDO": _parse_date(row.get("F_PEDIDO"), row_number),
        "SERIE_PEDV": series,
        "PEDIDO": order_number,
        "CLIENTE": _normalize_text(row.get("CLIENTE")),
        "NOMBRE_CLIENTE": _normalize_text(row.get("NOMBRE_CLIENTE")),
        "LIN_PED": _parse_int(row.get("LIN_PED"), row_number, "LIN_PED"),
        "ARTICULO": article_code,
        "DESCRIPCION_ARTICULO": _normalize_text(row.get("DESCRIPCION_ARTICULO")),
        "CANTIDAD": quantity,
        "PRECIO_VTA": unit_price,
        "IMPORTE_LIN": line_amount,
        "LEGACY_STATUS_RAW": _normalize_text(_get_first_value(row, STATUS_COLUMNS)),
        "DELIVERED_QUANTITY": _parse_decimal_nullable(_get_first_value(row, DELIVERED_COLUMNS), row_number, "ENTREGADO"),
        "INVOICED_QUANTITY": _parse_decimal_nullable(_get_first_value(row, INVOICED_COLUMNS), row_number, "FACTURADO"),
        "PENDING_DELIVERY_QUANTITY": _parse_decimal_nullable(
            _get_first_value(row, PENDING_DELIVERY_COLUMNS), row_number, "PENDIENTE_ENTREGA"
        ),
        "PENDING_INVOICE_QUANTITY": _parse_decimal_nullable(
            _get_first_value(row, PENDING_INVOICE_COLUMNS), row_number, "PENDIENTE_FACTURA"
        ),
    }


def _group_rows_by_order(rows: list[dict[str, object]]) -> OrderedDict[tuple[str, str], list[dict[str, object]]]:
    grouped: OrderedDict[tuple[str, str], list[dict[str, object]]] = OrderedDict()
    for row in rows:
        key = (str(row["SERIE_PEDV"]), str(row["PEDIDO"]))
        grouped.setdefault(key, []).append(row)
    return grouped


def _resolve_client(
    db: Session,
    legacy_code: str | None,
    client_name: str | None,
    stats: LegacyImportStats,
    cache_by_legacy: dict[str, Client],
    cache_by_name: dict[str, Client],
) -> Client:
    client = None
    if legacy_code:
        client = cache_by_legacy.get(legacy_code)
        if client is None:
            client = db.query(Client).filter(Client.legacy_code == legacy_code).first()
            if client is not None:
                cache_by_legacy[legacy_code] = client
                cache_by_name.setdefault(client.name, client)
    if client is None and client_name:
        client = cache_by_name.get(client_name)
        if client is None:
            client = db.query(Client).filter(Client.name == client_name).first()
            if client is not None:
                cache_by_name[client_name] = client
                if client.legacy_code:
                    cache_by_legacy.setdefault(client.legacy_code, client)
        if client is not None and legacy_code and not client.legacy_code:
            client.legacy_code = legacy_code
            db.flush()
            cache_by_legacy[legacy_code] = client
    if client is not None:
        return client

    fallback_name = client_name or legacy_code or "Legacy client"
    client = Client(name=fallback_name, legacy_code=legacy_code or None)
    db.add(client)
    db.flush()
    cache_by_name[fallback_name] = client
    if legacy_code:
        cache_by_legacy[legacy_code] = client
    stats.clients_created += 1
    return client


def _resolve_product(
    db: Session,
    legacy_code: str,
    description: str | None,
    unit_price: Decimal,
    stats: LegacyImportStats,
    cache_by_legacy: dict[str, Product],
    cache_by_sku: dict[str, Product],
) -> Product:
    product = cache_by_legacy.get(legacy_code)
    if product is None:
        product = db.query(Product).filter(Product.legacy_code == legacy_code).first()
        if product is not None:
            cache_by_legacy[legacy_code] = product
            cache_by_sku.setdefault(product.sku, product)
    if product is None:
        product = cache_by_sku.get(legacy_code)
        if product is None:
            product = db.query(Product).filter(Product.sku == legacy_code).first()
            if product is not None:
                cache_by_sku[legacy_code] = product
                if product.legacy_code:
                    cache_by_legacy.setdefault(product.legacy_code, product)
        if product is not None and not product.legacy_code:
            product.legacy_code = legacy_code
            if description and not product.description:
                product.description = description
            if product.unit_price is None:
                product.unit_price = float(unit_price)
            db.flush()
            cache_by_legacy[legacy_code] = product
    if product is not None:
        return product

    product = Product(
        name=description or legacy_code,
        sku=legacy_code,
        legacy_code=legacy_code,
        description=description or None,
        unit_price=float(unit_price),
    )
    db.add(product)
    db.flush()
    cache_by_legacy[legacy_code] = product
    cache_by_sku[legacy_code] = product
    stats.products_created += 1
    return product


def _normalize_header(value: str | None) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.strip().upper()
    text = re.sub(r"[^A-Z0-9]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_")


def _normalize_text(value: str | None) -> str:
    text = (value or "").replace("\xa0", " ").strip()
    if text.upper() in EMPTY_TEXT_TOKENS:
        return ""
    return text


def _get_first_value(row: dict[str, str | None], column_names: set[str]) -> str | None:
    for column_name in column_names:
        if column_name in row:
            return row[column_name]
    return None


def _parse_int(value: str | None, row_number: int, column_name: str) -> int | None:
    text = _normalize_text(value)
    if not text:
        return None
    try:
        return int(text)
    except ValueError as exc:
        raise ValueError(f"Row {row_number}: invalid integer in {column_name}: {text}") from exc


def _parse_decimal(value: str | None, row_number: int, column_name: str) -> Decimal:
    text = _normalize_text(value)
    if not text:
        raise ValueError(f"Row {row_number}: {column_name} is required")

    try:
        return _parse_decimal_optional(text, default=Decimal("0"))
    except InvalidOperation as exc:
        raise ValueError(f"Row {row_number}: invalid decimal in {column_name}: {text}") from exc


def _parse_decimal_nullable(value: str | None, row_number: int, column_name: str) -> Decimal | None:
    text = _normalize_text(value)
    if not text:
        return None
    try:
        return _parse_decimal_optional(text, default=Decimal("0"))
    except InvalidOperation as exc:
        raise ValueError(f"Row {row_number}: invalid decimal in {column_name}: {text}") from exc


def _parse_decimal_optional(value: str | None, default: Decimal) -> Decimal:
    text = _normalize_text(value)
    if not text:
        return default

    normalized = text.replace(" ", "").replace("'", "")
    if "," in normalized and "." in normalized:
        if normalized.rfind(",") > normalized.rfind("."):
            normalized = normalized.replace(".", "").replace(",", ".")
        else:
            normalized = normalized.replace(",", "")
    elif "," in normalized:
        normalized = normalized.replace(",", ".")

    return Decimal(normalized)


def _parse_date(value: str | None, row_number: int) -> datetime | None:
    text = _normalize_text(value)
    if not text:
        return None

    formats = ["%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%Y/%m/%d"]
    for date_format in formats:
        try:
            return datetime.strptime(text, date_format)
        except ValueError:
            continue

    raise ValueError(f"Row {row_number}: unsupported date format in F_PEDIDO: {text}")


def _sum_decimal_field(rows: list[dict[str, object]], key: str) -> Decimal:
    total = Decimal("0")
    for row in rows:
        value = row.get(key)
        if isinstance(value, Decimal):
            total += value
    return total


def _sum_optional_decimal_field(rows: list[dict[str, object]], key: str) -> Decimal | None:
    values = [row.get(key) for row in rows if isinstance(row.get(key), Decimal)]
    if not values:
        return None
    return sum(values, Decimal("0"))
