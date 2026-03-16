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


class DeliveryListItem(BaseModel):
    id: int
    order_id: int
    delivery_number: str
    client_id: int
    client_name: str
    order_number: str | None = None
    delivery_date: datetime | None = None
    created_at: datetime
    status: str
    total_amount: float
    invoice_status: str | None = None
    items: list[DeliveryItemRead]


class DeliveryDetailLine(BaseModel):
    id: int
    order_item_id: int
    product_id: int | None = None
    product_code: str | None = None
    product_name: str | None = None
    description: str
    quantity: float
    unit_label: str | None = None
    unit_price: float | None = None
    total_amount: float | None = None


class DeliveryInvoiceReference(BaseModel):
    id: int
    invoice_number: str
    invoice_date: str | None = None
    invoice_status: str | None = None
    total_amount: float | None = None


class DeliveryDetailRelations(BaseModel):
    source_order_id: int | None = None
    source_order_number: str | None = None
    source_order_status: str | None = None
    document_status: str | None = None
    linked_invoices: list[DeliveryInvoiceReference]


class DeliveryDetailResponse(BaseModel):
    id: int
    delivery_number: str
    client_id: int
    client_name: str
    order_id: int | None = None
    order_number: str | None = None
    delivery_date: datetime | None = None
    created_at: datetime
    status: str
    notes: str | None = None
    total_amount: float
    invoice_status: str | None = None
    lines: list[DeliveryDetailLine]
    relations: DeliveryDetailRelations
