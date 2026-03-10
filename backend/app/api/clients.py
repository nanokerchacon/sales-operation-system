from fastapi import APIRouter

from app.database.session import SessionLocal
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientRead


router = APIRouter()


@router.post("", response_model=ClientRead)
def create_client(client: ClientCreate) -> Client:
    db = SessionLocal()
    try:
        db_client = Client(**client.model_dump())
        db.add(db_client)
        db.commit()
        db.refresh(db_client)
        return db_client
    finally:
        db.close()


@router.get("", response_model=list[ClientRead])
def list_clients() -> list[Client]:
    db = SessionLocal()
    try:
        return db.query(Client).all()
    finally:
        db.close()
