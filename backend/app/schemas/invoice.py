from datetime import datetime

from pydantic import BaseModel, ConfigDict


class InvoiceItemCreate(BaseModel):
    order_item_id: int
    quantity: float
    unit_price: float

    model_config = ConfigDict(from_attributes=True)


class InvoiceItemRead(BaseModel):
    id: int
    order_item_id: int
    quantity: float
    unit_price: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceCreate(BaseModel):
    order_id: int
    items: list[InvoiceItemCreate]

    model_config = ConfigDict(from_attributes=True)


class InvoiceRead(BaseModel):
    id: int
    order_id: int
    invoice_date: datetime
    created_at: datetime
    items: list[InvoiceItemRead]

    model_config = ConfigDict(from_attributes=True)
