from __future__ import annotations

import re
import unicodedata
from decimal import Decimal


DEFAULT_LEGACY_ORDER_STATUS = "confirmed"


def normalize_order_status(raw_status: str | None) -> str | None:
    normalized = _normalize_status_text(raw_status)
    if not normalized:
        return None

    if "draft" in normalized or "borrador" in normalized or "proforma" in normalized or "presupuesto" in normalized:
        return "draft"
    if any(token in normalized for token in ("completed", "completado", "cerrado", "closed", "finalizado", "finalised", "finalized")):
        return "completed"
    if (
        ("pending" in normalized or "pendiente" in normalized)
        and any(token in normalized for token in ("invoice", "factur"))
    ):
        return "delivered"
    if any(token in normalized for token in ("invoiced", "facturado", "facturada", "billed")):
        return "invoiced"
    if any(token in normalized for token in ("delivered", "entregado", "entregada", "servido", "expedido", "shipped")):
        return "delivered"
    if any(token in normalized for token in ("confirmed", "confirmado", "confirmada", "en curso", "in progress", "activo", "active", "abierto", "open")):
        return "confirmed"
    if "pending" in normalized or "pendiente" in normalized:
        return "pending"

    return None


def infer_order_status(
    raw_status: str | None,
    ordered_quantity: Decimal | float | int,
    delivered_quantity: Decimal | float | int | None = None,
    invoiced_quantity: Decimal | float | int | None = None,
    pending_delivery_quantity: Decimal | float | int | None = None,
    pending_invoice_quantity: Decimal | float | int | None = None,
    default_status: str = DEFAULT_LEGACY_ORDER_STATUS,
) -> str:
    explicit_status = normalize_order_status(raw_status)
    quantity_status = _infer_status_from_quantities(
        ordered_quantity=_to_decimal(ordered_quantity),
        delivered_quantity=_to_decimal(delivered_quantity),
        invoiced_quantity=_to_decimal(invoiced_quantity),
        pending_delivery_quantity=_to_decimal(pending_delivery_quantity),
        pending_invoice_quantity=_to_decimal(pending_invoice_quantity),
    )

    if explicit_status in {"completed", "invoiced", "delivered"}:
        return explicit_status
    if explicit_status == "draft" and quantity_status in {"completed", "invoiced", "delivered"}:
        return quantity_status
    if explicit_status in {"confirmed", "pending"} and quantity_status not in {None, "confirmed"}:
        return quantity_status
    if explicit_status is not None:
        return explicit_status
    if quantity_status is not None:
        return quantity_status
    return default_status


def apply_order_status_quantity_fallback(
    order_status: str | None,
    ordered_quantity: float,
    delivered_quantity: float,
    invoiced_quantity: float,
    has_delivery_records: bool,
    has_invoice_records: bool,
) -> tuple[float, float]:
    if ordered_quantity <= 0:
        return delivered_quantity, invoiced_quantity
    if has_delivery_records or has_invoice_records:
        return delivered_quantity, invoiced_quantity
    if delivered_quantity > 0 or invoiced_quantity > 0:
        return delivered_quantity, invoiced_quantity

    normalized_status = normalize_order_status(order_status)
    if normalized_status in {"completed", "invoiced"}:
        return float(ordered_quantity), float(ordered_quantity)
    if normalized_status == "delivered":
        return float(ordered_quantity), 0.0
    return delivered_quantity, invoiced_quantity


def _infer_status_from_quantities(
    ordered_quantity: Decimal | None,
    delivered_quantity: Decimal | None,
    invoiced_quantity: Decimal | None,
    pending_delivery_quantity: Decimal | None,
    pending_invoice_quantity: Decimal | None,
) -> str | None:
    ordered_value = _non_negative(ordered_quantity)
    delivered_value = _non_negative(delivered_quantity)
    invoiced_value = _non_negative(invoiced_quantity)
    pending_delivery_value = _non_negative(pending_delivery_quantity)
    pending_invoice_value = _non_negative(pending_invoice_quantity)
    zero = Decimal("0")

    if pending_delivery_quantity is not None:
        fully_delivered = pending_delivery_value <= zero
    elif delivered_quantity is not None and ordered_value > zero:
        fully_delivered = delivered_value >= ordered_value
    else:
        fully_delivered = False

    if pending_invoice_quantity is not None:
        fully_invoiced = pending_invoice_value <= zero and (delivered_value > zero or fully_delivered)
    elif invoiced_quantity is not None and ordered_value > zero:
        fully_invoiced = invoiced_value >= ordered_value
    else:
        fully_invoiced = False

    if fully_delivered and fully_invoiced:
        return "completed"
    if invoiced_value > zero and (fully_invoiced or invoiced_value >= delivered_value > zero):
        return "invoiced"
    if delivered_value > zero or (pending_invoice_quantity is not None and pending_invoice_value > zero):
        return "delivered"
    if pending_delivery_quantity is not None and pending_delivery_value > zero:
        return "confirmed"
    if ordered_value > zero:
        return "confirmed"
    return None


def _normalize_status_text(value: str | None) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _non_negative(value: Decimal | None) -> Decimal:
    if value is None:
        return Decimal("0")
    return value if value > Decimal("0") else Decimal("0")


def _to_decimal(value: Decimal | float | int | None) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))
