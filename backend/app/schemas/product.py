from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProductCreate(BaseModel):
    name: str
    sku: str
    description: str | None = None
    unit_price: float | None = None


class ProductRead(BaseModel):
    id: int
    name: str
    sku: str
    description: str | None = None
    unit_price: float | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
