from pydantic import BaseModel


class OrderTraceabilityHeader(BaseModel):
    id: int
    order_number: str
    client_name: str
    order_date: str | None
    status: str
    invoice_document_status: str
    invoice_document_status_es: str


class OrderTraceabilitySummary(BaseModel):
    total_ordered_quantity: float
    total_delivered_quantity: float
    total_invoiced_quantity: float
    total_issued_quantity: float
    total_pending_acceptance_quantity: float
    pending_delivery_quantity: float
    pending_invoice_quantity: float
    status: str
    invoice_document_status: str
    invoice_document_status_es: str


class OrderTraceabilityItem(BaseModel):
    order_item_id: int
    product_code: str
    description: str
    ordered_quantity: float
    delivered_quantity: float
    invoiced_quantity: float
    pending_delivery_quantity: float
    pending_invoice_quantity: float
    status: str


class OrderTraceabilityDelivery(BaseModel):
    id: int
    delivery_number: str
    delivery_date: str | None


class OrderTraceabilityInvoice(BaseModel):
    id: int
    invoice_number: str
    invoice_date: str | None
    total_amount: float
    invoice_type: str
    invoice_status: str
    source_folder: str | None


class OrderTraceabilityResponse(BaseModel):
    order: OrderTraceabilityHeader
    summary: OrderTraceabilitySummary
    items: list[OrderTraceabilityItem]
    deliveries: list[OrderTraceabilityDelivery]
    invoices: list[OrderTraceabilityInvoice]
