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


class OrderListItem(BaseModel):
    id: int
    order_number: str
    client_id: int
    client_name: str
    order_date: datetime | None = None
    status: str
    total_amount: float
    delivery_status: str | None = None
    invoice_status: str | None = None


class OrderDetailLine(BaseModel):
    id: int
    line_number: int | None = None
    product_id: int | None = None
    product_code: str | None = None
    product_name: str | None = None
    description: str
    quantity: float
    unit_price: float
    total_amount: float


class OrderRelationReference(BaseModel):
    id: int
    document_number: str
    document_date: str | None = None
    status: str | None = None
    total_amount: float | None = None


class OrderDetailTraceability(BaseModel):
    logistics_status: str
    delivery_status: str | None = None
    invoice_status: str | None = None
    deliveries: list[OrderRelationReference]
    invoices: list[OrderRelationReference]


class OrderDetailResponse(BaseModel):
    id: int
    order_number: str
    client_id: int
    client_name: str
    order_date: datetime | None = None
    status: str
    client_reference: str | None = None
    notes: str | None = None
    subtotal: float | None = None
    tax_amount: float | None = None
    total_amount: float
    lines: list[OrderDetailLine]
    traceability: OrderDetailTraceability
