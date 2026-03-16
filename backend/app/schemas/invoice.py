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
    source_folder: str | None = None
    invoice_type: str | None = None
    invoice_status: str | None = None
    items: list[InvoiceItemCreate]

    model_config = ConfigDict(from_attributes=True)


class InvoiceRead(BaseModel):
    id: int
    order_id: int
    source_folder: str | None = None
    invoice_type: str
    invoice_status: str
    invoice_date: datetime
    created_at: datetime
    items: list[InvoiceItemRead]

    model_config = ConfigDict(from_attributes=True)


class InvoiceListItem(BaseModel):
    id: int
    invoice_number: str
    client_id: int
    client_name: str
    order_id: int | None = None
    order_number: str | None = None
    delivery_id: int | None = None
    delivery_number: str | None = None
    invoice_date: datetime | None = None
    status: str
    total_amount: float
    due_date: datetime | None = None
    payment_status: str | None = None
    invoice_type: str | None = None
    source_folder: str | None = None


class InvoiceDetailLine(BaseModel):
    id: int
    order_item_id: int
    product_id: int | None = None
    product_code: str | None = None
    product_name: str | None = None
    description: str
    quantity: float
    unit_price: float
    total_amount: float


class InvoiceRelatedDelivery(BaseModel):
    id: int
    delivery_number: str
    delivery_date: str | None = None


class InvoiceDetailRelations(BaseModel):
    client_id: int | None = None
    client_name: str | None = None
    source_order_id: int | None = None
    source_order_number: str | None = None
    primary_delivery_id: int | None = None
    primary_delivery_number: str | None = None
    linked_deliveries: list[InvoiceRelatedDelivery]
    document_status: str | None = None
    payment_status: str | None = None
    payments_placeholder: str | None = None


class InvoiceEconomicSummary(BaseModel):
    taxable_base: float | None = None
    tax_amount: float | None = None
    total_amount: float
    payment_status: str | None = None
    due_date: datetime | None = None


class InvoiceDetailResponse(BaseModel):
    id: int
    invoice_number: str
    client_id: int
    client_name: str
    order_id: int | None = None
    order_number: str | None = None
    delivery_id: int | None = None
    delivery_number: str | None = None
    invoice_date: datetime | None = None
    status: str
    due_date: datetime | None = None
    payment_status: str | None = None
    notes: str | None = None
    invoice_type: str | None = None
    source_folder: str | None = None
    total_amount: float
    lines: list[InvoiceDetailLine]
    summary: InvoiceEconomicSummary
    relations: InvoiceDetailRelations
