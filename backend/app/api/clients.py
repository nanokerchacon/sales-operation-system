from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientDetail, ClientListItem, ClientOrdersResponse, ClientRead
from app.services.access_control import CurrentUser, require_permission
from app.services.clients import get_client_detail, get_client_orders, list_clients_overview


router = APIRouter()


@router.post("", response_model=ClientRead)
def create_client(
    client: ClientCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("clients.create")),
) -> Client:
    db_client = Client(**client.model_dump())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client


@router.get("", response_model=list[ClientListItem])
def list_clients(
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("clients.view")),
) -> list[dict[str, object]]:
    return list_clients_overview(db, current_user.access_context, q)


@router.get("/{client_id}", response_model=ClientDetail)
def client_detail(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("clients.view")),
) -> dict[str, object]:
    return get_client_detail(db, current_user.access_context, client_id)


@router.get("/{client_id}/orders", response_model=ClientOrdersResponse)
def client_orders(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("orders.view")),
) -> dict[str, object]:
    return get_client_orders(db, current_user.access_context, client_id)
