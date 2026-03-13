from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.database.session import Base


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("source", "series", "order_number", name="uq_orders_source_series_number"),
    )

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    order_date = Column(DateTime, default=func.now())
    series = Column(String, index=True)
    order_number = Column(String, index=True)
    legacy_client_code = Column(String, index=True)
    client_name_snapshot = Column(String)
    notes = Column(String)
    source = Column(String, nullable=False, default="erp")
    subtotal = Column(Float)
    tax_amount = Column(Float)
    total_amount = Column(Float)
    status = Column(String, default="draft")
    created_at = Column(DateTime, default=func.now())

    items = relationship("OrderItem", back_populates="order")
    invoices = relationship("Invoice", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        UniqueConstraint("order_id", "line_number", name="uq_order_items_order_line_number"),
    )

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    line_number = Column(Integer)
    line_type = Column(String, nullable=False, default="product")
    legacy_article_code = Column(String, index=True)
    description = Column(String)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    line_amount = Column(Float)
    created_at = Column(DateTime, default=func.now())

    order = relationship("Order", back_populates="items")
