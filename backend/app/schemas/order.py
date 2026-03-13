from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OrderItemCreate(BaseModel):
    product_id: int | None = None
    line_number: int | None = None
    line_type: str | None = "product"
    legacy_article_code: str | None = None
    description: str | None = None
    quantity: float
    unit_price: float
    line_amount: float | None = None


class OrderItemRead(BaseModel):
    id: int
    product_id: int | None = None
    line_number: int | None = None
    line_type: str
    legacy_article_code: str | None = None
    description: str | None = None
    quantity: float
    unit_price: float
    line_amount: float | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    client_id: int
    order_date: datetime | None = None
    series: str | None = None
    order_number: str | None = None
    legacy_client_code: str | None = None
    client_name_snapshot: str | None = None
    notes: str | None = None
    source: str | None = None
    subtotal: float | None = None
    tax_amount: float | None = None
    total_amount: float | None = None
    status: str | None = None
    items: list[OrderItemCreate]


class OrderRead(BaseModel):
    id: int
    client_id: int
    order_date: datetime
    series: str | None = None
    order_number: str | None = None
    legacy_client_code: str | None = None
    client_name_snapshot: str | None = None
    notes: str | None = None
    source: str
    subtotal: float | None = None
    tax_amount: float | None = None
    total_amount: float | None = None
    status: str
    created_at: datetime
    items: list[OrderItemRead]

    model_config = ConfigDict(from_attributes=True)
