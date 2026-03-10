from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ClientCreate(BaseModel):
    name: str
    tax_id: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None


class ClientRead(BaseModel):
    id: int
    name: str
    tax_id: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
