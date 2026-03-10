from fastapi import FastAPI
from sqlalchemy import text

from app.api.clients import router as clients_router
from app.database.session import Base, engine
from app.models.client import Client

app = FastAPI()


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Sales Operation System API running"}


@app.get("/db-test")
def db_test() -> dict[str, str]:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {"database": "connected"}


app.include_router(clients_router, prefix="/clients", tags=["clients"])
