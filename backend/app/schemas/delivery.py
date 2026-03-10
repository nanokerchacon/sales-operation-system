from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DeliveryItemCreate(BaseModel):
    order_item_id: int
    quantity: float


class DeliveryItemRead(BaseModel):
    id: int
    order_item_id: int
    quantity: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeliveryNoteCreate(BaseModel):
    order_id: int
    items: list[DeliveryItemCreate]


class DeliveryNoteRead(BaseModel):
    id: int
    order_id: int
    delivery_date: datetime
    created_at: datetime
    items: list[DeliveryItemRead]

    model_config = ConfigDict(from_attributes=True)
