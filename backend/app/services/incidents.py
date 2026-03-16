from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.delivery import DeliveryNote
from app.models.incident import Incident
from app.models.invoice import Invoice
from app.models.order import Order
from app.services.access_control import AccessContext, apply_client_scope, apply_incident_scope, require_client_access
from app.services.orders import build_delivery_number, build_order_number, get_invoice_number

INCIDENT_TYPES = {"comercial", "logistica", "documental", "facturacion", "cobro", "producto", "otro"}
INCIDENT_STATUSES = {"abierta", "en_proceso", "resuelta", "cerrada"}
INCIDENT_PRIORITIES = {"baja", "media", "alta", "critica"}


def build_incident_number(incident_id: int) -> str:
    return f"INC{incident_id:06d}"


def _normalize_value(value: str | None, allowed: set[str], fallback: str) -> str:
    normalized = (value or fallback).strip().lower().replace("á", "a").replace("í", "i")
    return normalized if normalized in allowed else fallback


def _serialize_incident_relations(db: Session, incident: Incident) -> tuple[Order | None, DeliveryNote | None, Invoice | None, Client | None]:
    order = db.query(Order).filter(Order.id == incident.order_id).first() if incident.order_id else None
    delivery = db.query(DeliveryNote).filter(DeliveryNote.id == incident.delivery_id).first() if incident.delivery_id else None
    invoice = db.query(Invoice).filter(Invoice.id == incident.invoice_id).first() if incident.invoice_id else None
    client = db.query(Client).filter(Client.id == incident.client_id).first()
    return order, delivery, invoice, client


def list_incidents_overview(db: Session, access_context: AccessContext) -> list[dict[str, object]]:
    incidents = (
        apply_incident_scope(db.query(Incident), access_context)
        .order_by(Incident.created_at.desc(), Incident.id.desc())
        .all()
    )

    rows = []
    for incident in incidents:
        order, delivery, invoice, client = _serialize_incident_relations(db, incident)
        rows.append(
            {
                "id": incident.id,
                "incident_number": incident.incident_number,
                "client_id": incident.client_id,
                "client_name": client.name if client else "",
                "order_id": incident.order_id,
                "order_number": (order.order_number or build_order_number(order.id)) if order else None,
                "delivery_id": incident.delivery_id,
                "delivery_number": build_delivery_number(delivery.id) if delivery else None,
                "invoice_id": incident.invoice_id,
                "invoice_number": get_invoice_number(invoice.id) if invoice else None,
                "type": incident.type,
                "status": incident.status,
                "priority": incident.priority,
                "title": incident.title,
                "created_at": incident.created_at,
                "resolved_at": incident.resolved_at,
            }
        )
    return rows


def get_incident_detail(db: Session, incident_id: int, access_context: AccessContext) -> dict[str, object] | None:
    incident = apply_incident_scope(db.query(Incident), access_context).filter(Incident.id == incident_id).first()
    if incident is None:
        return None

    order, delivery, invoice, client = _serialize_incident_relations(db, incident)
    return {
        "id": incident.id,
        "incident_number": incident.incident_number,
        "client_id": incident.client_id,
        "client_name": client.name if client else "",
        "order_id": incident.order_id,
        "order_number": (order.order_number or build_order_number(order.id)) if order else None,
        "delivery_id": incident.delivery_id,
        "delivery_number": build_delivery_number(delivery.id) if delivery else None,
        "invoice_id": incident.invoice_id,
        "invoice_number": get_invoice_number(invoice.id) if invoice else None,
        "type": incident.type,
        "status": incident.status,
        "priority": incident.priority,
        "title": incident.title,
        "description": incident.description,
        "resolution_notes": incident.resolution_notes,
        "created_at": incident.created_at,
        "updated_at": incident.updated_at,
        "resolved_at": incident.resolved_at,
    }


def create_incident(db: Session, access_context: AccessContext, payload: dict[str, object], created_by_user_id: int | None) -> Incident:
    client = apply_client_scope(db.query(Client), access_context).filter(Client.id == payload["client_id"]).first()
    require_client_access(access_context, client)

    order_id = payload.get("order_id")
    delivery_id = payload.get("delivery_id")
    invoice_id = payload.get("invoice_id")

    if order_id:
        order = db.query(Order).filter(Order.id == order_id, Order.client_id == client.id).first()
        if order is None:
            raise ValueError("El pedido indicado no pertenece al cliente seleccionado.")

    if delivery_id:
        delivery = db.query(DeliveryNote).join(Order, Order.id == DeliveryNote.order_id).filter(DeliveryNote.id == delivery_id, Order.client_id == client.id).first()
        if delivery is None:
            raise ValueError("El albarán indicado no pertenece al cliente seleccionado.")

    if invoice_id:
        invoice = db.query(Invoice).join(Order, Order.id == Invoice.order_id).filter(Invoice.id == invoice_id, Order.client_id == client.id).first()
        if invoice is None:
            raise ValueError("La factura indicada no pertenece al cliente seleccionado.")

    incident = Incident(
        client_id=client.id,
        order_id=order_id,
        delivery_id=delivery_id,
        invoice_id=invoice_id,
        incident_number=f"TMP-{uuid4().hex}",
        type=_normalize_value(str(payload.get("type")), INCIDENT_TYPES, "otro"),
        status="abierta",
        priority=_normalize_value(str(payload.get("priority")), INCIDENT_PRIORITIES, "media"),
        title=str(payload.get("title") or "").strip(),
        description=str(payload.get("description") or "").strip(),
        created_by_user_id=created_by_user_id,
    )
    db.add(incident)
    db.flush()
    incident.incident_number = build_incident_number(incident.id)
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


def update_incident(db: Session, access_context: AccessContext, incident_id: int, payload: dict[str, object]) -> Incident | None:
    incident = apply_incident_scope(db.query(Incident), access_context).filter(Incident.id == incident_id).first()
    if incident is None:
        return None

    if payload.get("status") is not None:
        incident.status = _normalize_value(str(payload["status"]), INCIDENT_STATUSES, incident.status)
    if payload.get("priority") is not None:
        incident.priority = _normalize_value(str(payload["priority"]), INCIDENT_PRIORITIES, incident.priority)
    if payload.get("resolution_notes") is not None:
        incident.resolution_notes = payload["resolution_notes"]
    if "resolved_at" in payload:
        incident.resolved_at = payload["resolved_at"]
    elif incident.status in {"resuelta", "cerrada"} and incident.resolved_at is None:
        from datetime import datetime
        incident.resolved_at = datetime.utcnow()

    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident
