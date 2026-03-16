from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ClientCreate(BaseModel):
    name: str
    legacy_code: str | None = None
    tax_id: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None


class ClientRead(BaseModel):
    id: int
    name: str
    legacy_code: str | None = None
    tax_id: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClientListItem(BaseModel):
    id: int
    name: str
    legacy_code: str | None = None
    tax_id: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    location: str | None = None
    order_count: int
    total_order_amount: float
    last_order_date: datetime | None = None
    created_at: datetime


class ClientSummary(BaseModel):
    order_count: int
    total_order_amount: float
    last_order_date: datetime | None = None


class ClientDetail(BaseModel):
    id: int
    name: str
    legacy_code: str | None = None
    tax_id: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    location: str | None = None
    summary: ClientSummary
    created_at: datetime


class ClientOrderHistoryItem(BaseModel):
    id: int
    order_number: str
    order_date: datetime | None = None
    status: str
    total_amount: float
    source: str


class ClientOrdersResponse(BaseModel):
    client_id: int
    orders: list[ClientOrderHistoryItem]
