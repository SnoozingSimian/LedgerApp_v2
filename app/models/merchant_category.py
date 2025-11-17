# app/models/merchant_category.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class MerchantCategory(Base):
    __tablename__ = "merchant_categories"

    id = Column(Integer, primary_key=True, index=True)
    mcc_code = Column(String(4), unique=True, nullable=False, index=True)
    description = Column(String(200), nullable=False)
    category_range = Column(String(50))  # e.g., "Retail Outlet Services"
    suggested_category_id = Column(Integer, ForeignKey("categories.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    suggested_category = relationship("Category")
    transactions = relationship("Transaction", back_populates="merchant_category")
