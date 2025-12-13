# app/models/financial_goal.py

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Numeric,
    Date,
    Text,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class FinancialGoal(Base):
    __tablename__ = "financial_goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    family_id = Column(
        Integer,
        ForeignKey("families.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    goal_name = Column(String(200), nullable=False)
    goal_type = Column(String(50))

    target_amount = Column(Numeric(15, 2), nullable=False)
    current_amount = Column(Numeric(15, 2), default=0)

    target_date = Column(Date)

    priority = Column(String(20))  # 'high', 'medium', 'low'
    status = Column(String(20), default="in_progress", index=True)

    notes = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="financial_goals")
    family = relationship("Family", back_populates="financial_goals", lazy="select")

    # Constraints
    __table_args__ = (
        CheckConstraint("target_amount > 0", name="positive_target_amount"),
        CheckConstraint(
            "goal_type IN ('emergency_fund', 'retirement', 'house', 'education', 'vacation', 'debt_payoff', 'other') OR goal_type IS NULL",
            name="valid_goal_type",
        ),
        CheckConstraint(
            "priority IN ('high', 'medium', 'low') OR priority IS NULL",
            name="valid_priority",
        ),
        CheckConstraint(
            "status IN ('in_progress', 'completed', 'paused', 'cancelled')",
            name="valid_status",
        ),
        CheckConstraint(
            "user_id IS NOT NULL OR family_id IS NOT NULL", name="goal_owner"
        ),
    )
