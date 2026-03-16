from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func

from app.database.session import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True, index=True)
    delivery_id = Column(Integer, ForeignKey("delivery_notes.id"), nullable=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True, index=True)
    incident_number = Column(String, nullable=False, unique=True, index=True)
    type = Column(String, nullable=False, default="otro")
    status = Column(String, nullable=False, default="abierta")
    priority = Column(String, nullable=False, default="media")
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    resolution_notes = Column(Text, nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_to_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    resolved_at = Column(DateTime, nullable=True)
