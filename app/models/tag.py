# app/models/tag.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    
    # User ownership
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    
    # Family scoping 
    family_id = Column(
        Integer, ForeignKey("families.id", ondelete="CASCADE"), index=True, nullable=True
    )
    
    # Visual styling
    color = Column(String(7))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # All existing relationships
    user = relationship("User", back_populates="tags")
    family = relationship("Family", back_populates="tags")
    transactions = relationship("TransactionTag", back_populates="tag")

    # Uniqueness constraint
    __table_args__ = (
        UniqueConstraint("name", "user_id", "family_id", name="uq_tag_name_user_family"),
    )
