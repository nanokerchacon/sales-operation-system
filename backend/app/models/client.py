from sqlalchemy import Column, DateTime, Integer, String, func

from app.database.session import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    tax_id = Column(String, unique=True, index=True)
    address = Column(String)
    phone = Column(String)
    email = Column(String)
    created_at = Column(DateTime, default=func.now())
