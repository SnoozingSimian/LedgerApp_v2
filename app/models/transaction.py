# app/models/transaction.py

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


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    family_id = Column(
        Integer, ForeignKey("families.id", ondelete="CASCADE"), index=True
    )

    # Financial details
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="INR")

    # Classification
    transaction_type = Column(
        String(20), nullable=False, index=True
    )  # 'income' or 'expense'
    payment_method = Column(
        String(20), nullable=False, index=True
    )  # 'cash', 'credit_card', 'upi', etc.

    # Categorization
    category_id = Column(
        Integer, ForeignKey("categories.id"), nullable=False, index=True
    )
    subcategory_id = Column(Integer, ForeignKey("categories.id"), index=True)

    # Merchant details
    payee = Column(String(200))
    merchant_type = Column(String(100), index=True)
    mcc_code = Column(String(4), ForeignKey("merchant_categories.mcc_code"))

    # Transaction metadata
    t_date = Column(Date, nullable=False, index=True)
    notes = Column(Text)

    # Credit card specific
    credit_source_id = Column(Integer, ForeignKey("credit_sources.id"), index=True)
    is_paid = Column(Boolean, default=False)
    payment_due_date = Column(Date)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="transactions")
    family = relationship("Family", back_populates="transactions")
    category = relationship(
        "Category", foreign_keys=[category_id], back_populates="transactions"
    )
    subcategory = relationship("Category", foreign_keys=[subcategory_id])
    credit_source = relationship("CreditSource", back_populates="transactions")
    merchant_category = relationship("MerchantCategory", back_populates="transactions")
    tags = relationship(
        "TransactionTag", back_populates="transaction", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("amount > 0", name="positive_amount"),
        CheckConstraint(
            "transaction_type IN ('income', 'expense')", name="valid_transaction_type"
        ),
        CheckConstraint(
            "payment_method IN ('cash', 'credit_card', 'upi', 'neft', 'imps', 'rtgs', 'cheque', 'debit_card', 'other')",
            name="valid_payment_method",
        ),
        CheckConstraint(
            "(payment_method = 'credit_card' AND credit_source_id IS NOT NULL) OR (payment_method != 'credit_card')",
            name="credit_card_requires_source",
        ),
        CheckConstraint(
            "user_id IS NOT NULL OR family_id IS NOT NULL", name="transaction_owner"
        ),
    )


class TransactionTag(Base):
    __tablename__ = "transaction_tags"

    transaction_id = Column(
        Integer, ForeignKey("transactions.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id = Column(
        Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True, index=True
    )

    # Relationships
    transaction = relationship("Transaction", back_populates="tags")
    tag = relationship("Tag", back_populates="transactions")
