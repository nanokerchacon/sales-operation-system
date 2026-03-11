from pydantic import BaseModel


class OrderStatusSummaryLabels(BaseModel):
    ok: str
    pending_delivery: str
    pending_invoice: str
    invoice_over_delivery: str


class OrderStatusSummary(BaseModel):
    ok: int
    pending_delivery: int
    pending_invoice: int
    invoice_over_delivery: int
    labels_es: OrderStatusSummaryLabels


class OperationsDashboardLabels(BaseModel):
    total_orders: str
    orders_with_issues: str
    orders_without_issues: str
    total_pending_delivery_quantity: str
    total_pending_invoice_quantity: str
    pending_delivery_orders: str
    pending_invoice_orders: str
    invoice_over_delivery_orders: str


class OperationsDashboardSummary(BaseModel):
    total_orders: int
    orders_with_issues: int
    orders_without_issues: int
    total_pending_delivery_quantity: float
    total_pending_invoice_quantity: float
    pending_delivery_orders: int
    pending_invoice_orders: int
    invoice_over_delivery_orders: int
    labels_es: OperationsDashboardLabels
    orders_with_risk: int
    orders_without_risk: int
    delivered_not_invoiced_orders: int
    partially_invoiced_orders: int
    invoiced_over_delivered_orders: int


class OrderOperationalStatus(BaseModel):
    order_id: int
    order_number: str
    client_id: int
    client_name: str
    order_status: str
    status: str
    status_es: str
    ordered_quantity: float
    delivered_quantity: float
    invoiced_quantity: float
    pending_delivery_quantity: float
    pending_invoice_quantity: float
    has_issue: bool
    risk_status: str
    risk_status_es: str
    has_risk: bool


class PendingInvoiceItem(BaseModel):
    order_id: int
    order_number: str
    client_id: int
    client_name: str
    order_status: str
    status: str
    status_es: str
    ordered_quantity: float
    delivered_quantity: float
    invoiced_quantity: float
    pending_invoice_quantity: float
    amount_pending_invoice: float
    risk_status: str
    risk_status_es: str


class PendingRevenueItem(BaseModel):
    order_id: int
    order_number: str
    client_id: int
    client_name: str
    order_status: str
    status: str
    status_es: str
    delivered_quantity: float
    invoiced_quantity: float
    pending_invoice_quantity: float
    amount_pending_invoice: float
    days_since_last_delivery: int
    priority_level: str
    priority_level_es: str
    risk_level: str
    risk_level_es: str
    risk_status: str
    risk_status_es: str


class WorkQueueItem(BaseModel):
    order_id: int
    order_number: str
    client_id: int
    client_name: str
    order_status: str
    delivered_quantity: float
    invoiced_quantity: float
    pending_delivery_quantity: float
    pending_invoice_quantity: float
    status: str
    status_es: str
    priority: str
    priority_es: str
    amount_pending_invoice: float
    days_since_last_delivery: int
    priority_level: str
    priority_level_es: str


class ClientIncidentsItem(BaseModel):
    client_id: int
    client_name: str
    total_orders: int
    orders_with_issues: int
    total_pending_invoice_quantity: float
    total_pending_invoice_amount: float
    highest_priority_level: str
    highest_priority_level_es: str
    orders_with_risk: int
    highest_risk_level: str
    highest_risk_level_es: str


class AgingLabels(BaseModel):
    bucket_0_3_days: str
    bucket_4_7_days: str
    bucket_8_15_days: str
    bucket_over_15_days: str
    total_pending_invoice_amount: str


class AgingInvoicesSummary(BaseModel):
    bucket_0_3_days: float
    bucket_4_7_days: float
    bucket_8_15_days: float
    bucket_over_15_days: float
    total_pending_invoice_amount: float
    labels_es: AgingLabels
