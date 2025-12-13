# app/models/category.py - FINAL CORRECTED VERSION
# ✅ With fix for transactions relationship foreign_keys

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    
    # Family support (NEW - nullable for backwards compatibility)
    family_id = Column(
        Integer,
        ForeignKey("families.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    is_global = Column(Boolean, default=False)  # True if shared across families
    
    # Existing hierarchy support (KEEP)
    parent_category_id = Column(Integer, ForeignKey("categories.id"), index=True)
    
    # Existing category type (KEEP)
    category_type = Column(
        String(20), nullable=False, index=True
    )  # 'expense' or 'income'

    # Existing budget classification (KEEP)
    budget_classification = Column(String(20))  # 'needs', 'wants', 'savings'

    # Existing visual identifiers (KEEP)
    icon = Column(String(50))
    color = Column(String(7))

    # Existing merchant mapping (KEEP)
    default_mcc_ranges = Column(Text)  # JSON array of MCC ranges

    # Existing system vs custom (KEEP)
    is_system = Column(Boolean, default=True)
    display_order = Column(Integer)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # All existing relationships (KEEP)
    parent = relationship("Category", remote_side=[id], backref="subcategories")
    
    # ✅ FIXED: Keep foreign_keys specification (Transaction has 2 FKs to Category!)
    transactions = relationship(
        "Transaction",
        foreign_keys="Transaction.category_id",  # ← CRITICAL: Specifies which FK
        back_populates="category"
    )
    
    budget_allocations = relationship("BudgetCategory", back_populates="category")
    
    income_streams = relationship("IncomeStream", back_populates="category")
    
    # NEW relationship for family support
    family = relationship("Family", back_populates="categories", lazy="select")
