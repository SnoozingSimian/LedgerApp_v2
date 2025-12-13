# app/models/user.py

from sqlalchemy import Column, Integer, String, DateTime, Boolean, CheckConstraint, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255))
    full_name = Column(String(100), nullable=False)

    # Google OAuth fields
    google_id = Column(String(255), unique=True, index=True)
    google_refresh_token = Column(String)

    # Settings
    default_currency = Column(String(3), default="INR")
    send_email_reports = Column(Boolean, default=True)

    # Active family (for cross-device persistence)
    active_family_id = Column(Integer, ForeignKey("families.id", ondelete="SET NULL"), nullable=True, index=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))

    # Relationships
    active_family = relationship(
        "Family",
        foreign_keys=[active_family_id],
        primaryjoin="User.active_family_id==Family.id",
        uselist=False,
        lazy="select",
    )
    
    family_memberships = relationship(
        "FamilyMember",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )
    
    transactions = relationship(
        "Transaction",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )
    
    credit_sources = relationship(
        "CreditSource",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )
    
    budgets = relationship(
        "Budget", back_populates="user", cascade="all, delete-orphan", lazy="select"
    )
    
    assets = relationship(
        "Asset", back_populates="user", cascade="all, delete-orphan", lazy="select"
    )
    
    income_streams = relationship(
        "IncomeStream",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )
    
    financial_goals = relationship(
        "FinancialGoal",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )
    
    tags = relationship(
        "Tag", back_populates="user", cascade="all, delete-orphan", lazy="select"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "password_hash IS NOT NULL OR google_id IS NOT NULL",
            name="auth_method_check",
        ),
    )