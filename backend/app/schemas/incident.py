from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class IncidentCreate(BaseModel):
    client_id: int
    order_id: int | None = None
    delivery_id: int | None = None
    invoice_id: int | None = None
    type: str
    priority: str
    title: str
    description: str


class IncidentDraftGenerateRequest(BaseModel):
    text: str = Field(..., min_length=1)


class IncidentDraftGenerateResponse(BaseModel):
    title: str
    description: str
    type: Literal["documental", "logistica", "facturacion"]
    priority: Literal["baja", "media", "alta"]


class IncidentUpdate(BaseModel):
    status: str | None = None
    priority: str | None = None
    resolution_notes: str | None = None
    resolved_at: datetime | None = None


class IncidentListItem(BaseModel):
    id: int
    incident_number: str
    client_id: int
    client_name: str
    order_id: int | None = None
    order_number: str | None = None
    delivery_id: int | None = None
    delivery_number: str | None = None
    invoice_id: int | None = None
    invoice_number: str | None = None
    type: str
    status: str
    priority: str
    title: str
    created_at: datetime
    resolved_at: datetime | None = None


class IncidentDetailResponse(BaseModel):
    id: int
    incident_number: str
    client_id: int
    client_name: str
    order_id: int | None = None
    order_number: str | None = None
    delivery_id: int | None = None
    delivery_number: str | None = None
    invoice_id: int | None = None
    invoice_number: str | None = None
    type: str
    status: str
    priority: str
    title: str
    description: str
    resolution_notes: str | None = None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None = None


class IncidentRead(IncidentDetailResponse):
    pass
