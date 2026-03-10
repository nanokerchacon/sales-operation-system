from fastapi import FastAPI
from sqlalchemy import text

from app.api.clients import router as clients_router
from app.api.deliveries import router as deliveries_router
from app.api.invoices import router as invoices_router
from app.api.orders import router as orders_router
from app.api.products import router as products_router
from app.database.session import Base, engine
from app.models.client import Client
from app.models.delivery import DeliveryItem, DeliveryNote
from app.models.invoice import Invoice, InvoiceItem
from app.models.order import Order, OrderItem
from app.models.product import Product

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
app.include_router(deliveries_router, prefix="/deliveries", tags=["deliveries"])
app.include_router(invoices_router, prefix="/invoices", tags=["invoices"])
app.include_router(orders_router, prefix="/orders", tags=["orders"])
app.include_router(products_router, prefix="/products", tags=["products"])
