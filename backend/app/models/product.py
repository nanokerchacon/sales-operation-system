from sqlalchemy import Column, DateTime, Float, Integer, String, func

from app.database.session import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    sku = Column(String, unique=True, index=True, nullable=False)
    description = Column(String)
    unit_price = Column(Float)
    created_at = Column(DateTime, default=func.now())
