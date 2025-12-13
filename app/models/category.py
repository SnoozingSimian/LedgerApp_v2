# app/models/category.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    
    # Family support 
    family_id = Column(
        Integer,
        ForeignKey("families.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    is_global = Column(Boolean, default=False)
    
    parent_category_id = Column(Integer, ForeignKey("categories.id"), index=True)
    category_type = Column(String(20), nullable=False, index=True)
    budget_classification = Column(String(20))
    icon = Column(String(50))
    color = Column(String(7))
    default_mcc_ranges = Column(Text)
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
    
    # Family relationship
    family = relationship("Family", back_populates="categories", lazy="select")
