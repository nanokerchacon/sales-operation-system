from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, func
from sqlalchemy.orm import relationship

from app.database.session import Base


class DeliveryNote(Base):
    __tablename__ = "delivery_notes"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    delivery_date = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())

    items = relationship("DeliveryItem", back_populates="delivery_note")


class DeliveryItem(Base):
    __tablename__ = "delivery_items"

    id = Column(Integer, primary_key=True, index=True)
    delivery_note_id = Column(Integer, ForeignKey("delivery_notes.id"), nullable=False)
    order_item_id = Column(Integer, ForeignKey("order_items.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    created_at = Column(DateTime, default=func.now())

    delivery_note = relationship("DeliveryNote", back_populates="items")
