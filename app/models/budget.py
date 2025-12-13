# app/models/budget.py

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Numeric,
    Date,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    family_id = Column(
        Integer,
        ForeignKey("families.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    family_id = Column(
        Integer, ForeignKey("families.id", ondelete="CASCADE"), index=True
    )

    name = Column(String(100), nullable=False)
    period_start = Column(Date, nullable=False, index=True)
    period_end = Column(Date, nullable=False, index=True)

    # Overall limits
    total_budget = Column(Numeric(12, 2))

    # 50/30/20 allocations (optional)
    needs_budget = Column(Numeric(12, 2))
    wants_budget = Column(Numeric(12, 2))
    savings_budget = Column(Numeric(12, 2))

    # Alert thresholds
    alert_threshold_percent = Column(Integer, default=80)

    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="budgets")
    family = relationship("Family", back_populates="budgets", lazy="select")
    budget_categories = relationship(
        "BudgetCategory", back_populates="budget", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("period_end > period_start", name="valid_period"),
        CheckConstraint(
            "alert_threshold_percent BETWEEN 1 AND 100", name="valid_threshold"
        ),
        CheckConstraint(
            "user_id IS NOT NULL OR family_id IS NOT NULL", name="budget_owner"
        ),
    )


class BudgetCategory(Base):
    __tablename__ = "budget_categories"

    id = Column(Integer, primary_key=True, index=True)
    budget_id = Column(
        Integer, ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False
    )
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    allocated_amount = Column(Numeric(12, 2), nullable=False)

    # Relationships
    budget = relationship("Budget", back_populates="budget_categories")
    category = relationship("Category", back_populates="budget_allocations")

    # Constraints
    __table_args__ = (
        UniqueConstraint("budget_id", "category_id", name="uq_budget_category"),
        CheckConstraint("allocated_amount >= 0", name="non_negative_allocation"),
    )
