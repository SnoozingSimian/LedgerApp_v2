# app/models/category.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    parent_category_id = Column(Integer, ForeignKey("categories.id"), index=True)
    category_type = Column(
        String(20), nullable=False, index=True
    )  # 'expense' or 'income'

    # 50/30/20 budget classification
    budget_classification = Column(String(20))  # 'needs', 'wants', 'savings'

    # Visual identifiers
    icon = Column(String(50))
    color = Column(String(7))

    # Merchant mapping for auto-categorization
    default_mcc_ranges = Column(Text)  # JSON array of MCC ranges

    # System vs custom categories
    is_system = Column(Boolean, default=True)
    display_order = Column(Integer)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    parent = relationship("Category", remote_side=[id], backref="subcategories")
    transactions = relationship(
        "Transaction", back_populates="category", foreign_keys="Transaction.category_id"
    )
    budget_allocations = relationship("BudgetCategory", back_populates="category")
    income_streams = relationship("IncomeStream", back_populates="category")
