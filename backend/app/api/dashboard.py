from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
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
from app.services.access_control import CurrentUser, require_permission
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
def operations_dashboard(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("dashboard.view")),
) -> OperationsDashboardSummary:
    return get_operations_dashboard(db, current_user.access_context)


@router.get("/order-status-summary", response_model=OrderStatusSummary)
def order_status_summary(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("dashboard.view")),
) -> OrderStatusSummary:
    return get_order_status_summary(db, current_user.access_context)


@router.get("/orders-with-incidents", response_model=list[OrderOperationalStatus])
def orders_with_incidents(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("dashboard.view")),
) -> list[OrderOperationalStatus]:
    return get_orders_with_incidents(db, current_user.access_context)


@router.get("/risk-orders", response_model=list[OrderOperationalStatus])
def risk_orders(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("dashboard.view")),
) -> list[OrderOperationalStatus]:
    return get_orders_with_incidents(db, current_user.access_context)


@router.get("/pending-invoices", response_model=list[PendingInvoiceItem])
def pending_invoices(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("dashboard.view")),
) -> list[PendingInvoiceItem]:
    return get_pending_invoices(db, current_user.access_context)


@router.get("/pending-revenue", response_model=list[PendingRevenueItem])
def pending_revenue(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("dashboard.view")),
) -> list[PendingRevenueItem]:
    return get_pending_revenue(db, current_user.access_context)


@router.get("/revenue-at-risk", response_model=list[PendingRevenueItem])
def revenue_at_risk(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("dashboard.view")),
) -> list[PendingRevenueItem]:
    return get_pending_revenue(db, current_user.access_context)


@router.get("/work-queue", response_model=list[WorkQueueItem])
def work_queue(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("dashboard.view")),
) -> list[WorkQueueItem]:
    return get_work_queue(db, current_user.access_context)


@router.get("/clients-with-incidents", response_model=list[ClientIncidentsItem])
def clients_with_incidents(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("dashboard.view")),
) -> list[ClientIncidentsItem]:
    return get_clients_with_incidents(db, current_user.access_context)


@router.get("/client-risk", response_model=list[ClientIncidentsItem])
def client_risk(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("dashboard.view")),
) -> list[ClientIncidentsItem]:
    return get_clients_with_incidents(db, current_user.access_context)


@router.get("/aging-invoices", response_model=AgingInvoicesSummary)
def aging_invoices(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("dashboard.view")),
) -> AgingInvoicesSummary:
    return get_aging_invoices(db, current_user.access_context)
