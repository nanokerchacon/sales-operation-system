from fastapi import FastAPI
from sqlalchemy import text

from app.database.session import engine

app = FastAPI()


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Sales Operation System API running"}


@app.get("/db-test")
def db_test() -> dict[str, str]:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {"database": "connected"}
