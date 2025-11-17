# app/models/asset.py

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
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    family_id = Column(
        Integer, ForeignKey("families.id", ondelete="CASCADE"), index=True
    )

    # Asset classification
    asset_type = Column(String(50), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    symbol_isin = Column(String(50))

    # Valuation
    quantity = Column(Numeric(18, 4), nullable=False)
    purchase_price = Column(Numeric(12, 2), nullable=False)
    current_price = Column(Numeric(12, 2))

    # Dates
    purchase_date = Column(Date, nullable=False)
    maturity_date = Column(Date)

    # Additional details
    interest_rate = Column(Numeric(5, 2))
    annual_return_percent = Column(Numeric(5, 2))
    risk_level = Column(String(20))  # 'low', 'medium', 'high'

    notes = Column(Text)

    # Metadata
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="assets")
    family = relationship("Family", back_populates="assets")
    valuations = relationship(
        "AssetValuation", back_populates="asset", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("quantity > 0", name="positive_quantity"),
        CheckConstraint(
            "asset_type IN ('stock', 'mutual_fund', 'fixed_deposit', 'sip', 'gold', 'real_estate', 'ppf', 'nps', 'bond', 'etf', 'cryptocurrency', 'commodities', 'other')",
            name="valid_asset_type",
        ),
        CheckConstraint(
            "risk_level IN ('low', 'medium', 'high') OR risk_level IS NULL",
            name="valid_risk_level",
        ),
        CheckConstraint(
            "user_id IS NOT NULL OR family_id IS NOT NULL", name="asset_owner"
        ),
    )


class AssetValuation(Base):
    __tablename__ = "asset_valuations"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(
        Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False
    )
    valuation_date = Column(Date, nullable=False)
    price_per_unit = Column(Numeric(12, 2), nullable=False)
    total_value = Column(Numeric(15, 2), nullable=False)
    source = Column(String(50))  # 'manual', 'api', 'estimated'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    asset = relationship("Asset", back_populates="valuations")

    # Constraints
    __table_args__ = (
        UniqueConstraint("asset_id", "valuation_date", name="uq_asset_valuation_date"),
    )
