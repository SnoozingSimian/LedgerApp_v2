# app/models/credit_source.py

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Numeric,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class CreditSource(Base):
    __tablename__ = "credit_sources"

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

    card_name = Column(String(100), nullable=False)
    card_last4 = Column(String(4))
    card_network = Column(String(20))  # 'Visa', 'Mastercard', 'RuPay', 'Amex', 'Other'

    credit_limit = Column(Numeric(12, 2), nullable=False)
    billing_day = Column(Integer)
    due_day = Column(Integer)

    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="credit_sources")
    family = relationship("Family", back_populates="credit_sources", lazy="select")
    transactions = relationship("Transaction", back_populates="credit_source")

    # Constraints
    __table_args__ = (
        CheckConstraint("credit_limit > 0", name="positive_credit_limit"),
        CheckConstraint("billing_day BETWEEN 1 AND 31", name="valid_billing_day"),
        CheckConstraint("due_day BETWEEN 1 AND 31", name="valid_due_day"),
    )
