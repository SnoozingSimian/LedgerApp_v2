# app/models/family.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Family(Base):
    __tablename__ = "families"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    created_by = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    members = relationship(
        "FamilyMember",
        back_populates="family",
        cascade="all, delete-orphan",
        lazy="select",
    )
    transactions = relationship("Transaction", back_populates="family", lazy="select")
    budgets = relationship("Budget", back_populates="family", lazy="select")
    assets = relationship("Asset", back_populates="family", lazy="select")
    income_streams = relationship(
        "IncomeStream", back_populates="family", lazy="select"
    )
    financial_goals = relationship(
        "FinancialGoal", back_populates="family", lazy="select"
    )
    tags = relationship("Tag", back_populates="family", lazy="select")


class FamilyMember(Base):
    __tablename__ = "family_members"

    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(
        Integer,
        ForeignKey("families.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role = Column(String(20), default="member")  # 'admin', 'member', 'viewer'
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships - use string references
    user = relationship("User", back_populates="family_memberships", lazy="select")
    family = relationship("Family", back_populates="members", lazy="select")
