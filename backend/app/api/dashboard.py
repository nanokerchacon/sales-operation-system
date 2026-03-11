from fastapi import APIRouter

from app.database.session import SessionLocal
from app.schemas.dashboard import (
    AgingInvoicesSummary,
    ClientIncidentsItem,
    OperationsDashboardSummary,
    OrderOperationalStatus,
    OrderStatusSummary,
    PendingInvoiceItem,
    PendingRevenueItem,
    WorkQueueItem,
)
from app.services.dashboard import (
    get_aging_invoices,
    get_clients_with_incidents,
    get_operations_dashboard,
    get_order_status_summary,
    get_orders_with_incidents,
    get_pending_invoices,
    get_pending_revenue,
    get_work_queue,
)


router = APIRouter()


@router.get("/operations", response_model=OperationsDashboardSummary)
def operations_dashboard() -> OperationsDashboardSummary:
    db = SessionLocal()
    try:
        return get_operations_dashboard(db)
    finally:
        db.close()


@router.get("/order-status-summary", response_model=OrderStatusSummary)
def order_status_summary() -> OrderStatusSummary:
    db = SessionLocal()
    try:
        return get_order_status_summary(db)
    finally:
        db.close()


@router.get("/orders-with-incidents", response_model=list[OrderOperationalStatus])
def orders_with_incidents() -> list[OrderOperationalStatus]:
    db = SessionLocal()
    try:
        return get_orders_with_incidents(db)
    finally:
        db.close()


@router.get("/risk-orders", response_model=list[OrderOperationalStatus])
def risk_orders() -> list[OrderOperationalStatus]:
    db = SessionLocal()
    try:
        return get_orders_with_incidents(db)
    finally:
        db.close()


@router.get("/pending-invoices", response_model=list[PendingInvoiceItem])
def pending_invoices() -> list[PendingInvoiceItem]:
    db = SessionLocal()
    try:
        return get_pending_invoices(db)
    finally:
        db.close()


@router.get("/pending-revenue", response_model=list[PendingRevenueItem])
def pending_revenue() -> list[PendingRevenueItem]:
    db = SessionLocal()
    try:
        return get_pending_revenue(db)
    finally:
        db.close()


@router.get("/revenue-at-risk", response_model=list[PendingRevenueItem])
def revenue_at_risk() -> list[PendingRevenueItem]:
    db = SessionLocal()
    try:
        return get_pending_revenue(db)
    finally:
        db.close()


@router.get("/work-queue", response_model=list[WorkQueueItem])
def work_queue() -> list[WorkQueueItem]:
    db = SessionLocal()
    try:
        return get_work_queue(db)
    finally:
        db.close()


@router.get("/clients-with-incidents", response_model=list[ClientIncidentsItem])
def clients_with_incidents() -> list[ClientIncidentsItem]:
    db = SessionLocal()
    try:
        return get_clients_with_incidents(db)
    finally:
        db.close()


@router.get("/client-risk", response_model=list[ClientIncidentsItem])
def client_risk() -> list[ClientIncidentsItem]:
    db = SessionLocal()
    try:
        return get_clients_with_incidents(db)
    finally:
        db.close()


@router.get("/aging-invoices", response_model=AgingInvoicesSummary)
def aging_invoices() -> AgingInvoicesSummary:
    db = SessionLocal()
    try:
        return get_aging_invoices(db)
    finally:
        db.close()
