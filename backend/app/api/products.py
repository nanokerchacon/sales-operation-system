from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductRead
from app.services.access_control import CurrentUser, require_permission


router = APIRouter()


@router.post("", response_model=ProductRead)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("products.create")),
) -> Product:
    db_product = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.get("", response_model=list[ProductRead])
def list_products(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("products.view")),
) -> list[Product]:
    return db.query(Product).all()
