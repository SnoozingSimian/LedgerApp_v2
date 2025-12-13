# app/schemas/invite.py
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class FamilyInviteCreate(BaseModel):
    invited_email: EmailStr
    role: str = "member"


class FamilyInviteResponse(BaseModel):
    id: int
    family_id: int
    invited_email: str
    role: str
    token: str
    accepted: bool
    created_at: datetime
    accepted_at: Optional[datetime]
    expires_at: datetime

    class Config:
        from_attributes = True


class FamilyInviteAccept(BaseModel):
    token: str


class UserPendingInvite(BaseModel):
    id: int
    family_id: int
    invited_email: str
    role: str
    created_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True