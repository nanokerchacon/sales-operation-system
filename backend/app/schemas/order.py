from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: float
    unit_price: float


class OrderItemRead(BaseModel):
    id: int
    product_id: int
    quantity: float
    unit_price: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    client_id: int
    status: str | None = None
    items: list[OrderItemCreate]


class OrderRead(BaseModel):
    id: int
    client_id: int
    order_date: datetime
    status: str
    created_at: datetime
    items: list[OrderItemRead]

    model_config = ConfigDict(from_attributes=True)
