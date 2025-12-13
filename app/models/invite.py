# app/models/invite.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class FamilyInvite(Base):
    __tablename__ = "family_invites"

    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(
        Integer,
        ForeignKey("families.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    invited_email = Column(String(255), nullable=False, index=True)
    invited_by_user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role = Column(String(20), default="member")  # 'admin', 'member', 'viewer'
    token = Column(String(255), unique=True, nullable=False, index=True)
    accepted = Column(Boolean, default=False)
    accepted_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Relationships
    family = relationship(
        "Family", back_populates="pending_invites", lazy="select"
    )
    invited_by_user = relationship(
        "User",
        foreign_keys=[invited_by_user_id],
        lazy="select",
        primaryjoin="FamilyInvite.invited_by_user_id==User.id",
    )
    accepted_by_user = relationship(
        "User",
        foreign_keys=[accepted_by_user_id],
        lazy="select",
        primaryjoin="FamilyInvite.accepted_by_user_id==User.id",
    )