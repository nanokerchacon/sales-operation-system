from fastapi import APIRouter

from app.database.session import SessionLocal
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductRead


router = APIRouter()


@router.post("", response_model=ProductRead)
def create_product(product: ProductCreate) -> Product:
    db = SessionLocal()
    try:
        db_product = Product(**product.model_dump())
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return db_product
    finally:
        db.close()


@router.get("", response_model=list[ProductRead])
def list_products() -> list[Product]:
    db = SessionLocal()
    try:
        return db.query(Product).all()
    finally:
        db.close()
