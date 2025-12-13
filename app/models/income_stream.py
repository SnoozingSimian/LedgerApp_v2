# app/models/income_stream.py

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Numeric,
    Date,
    Text,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class IncomeStream(Base):
    __tablename__ = "income_streams"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    family_id = Column(
        Integer,
        ForeignKey("families.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    source = Column(String(200), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="INR")

    frequency = Column(String(20), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)

    # Tax details (optional)
    is_taxable = Column(Boolean, default=True)
    tax_rate = Column(Numeric(5, 2))

    is_active = Column(Boolean, default=True, index=True)
    notes = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="income_streams")
    family = relationship("Family", back_populates="income_streams", lazy="select")
    category = relationship("Category", back_populates="income_streams")

    # Constraints
    __table_args__ = (
        CheckConstraint("amount > 0", name="positive_income_amount"),
        CheckConstraint(
            "frequency IN ('monthly', 'quarterly', 'yearly', 'one-time', 'weekly', 'bi-weekly', 'daily')",
            name="valid_frequency",
        ),
        CheckConstraint(
            "user_id IS NOT NULL OR family_id IS NOT NULL", name="income_owner"
        ),
    )
