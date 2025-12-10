from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class CreditSourceBase(BaseModel):
    card_name: str = Field(..., max_length=100, description="Name of the credit card")
    card_last4: Optional[str] = Field(None, max_length=4, description="Last 4 digits of card")
    card_network: Optional[str] = Field(None, max_length=20, description="Visa, Mastercard, RuPay, Amex, Other")
    credit_limit: Decimal = Field(..., gt=0, description="Credit limit amount")
    billing_day: Optional[int] = Field(None, ge=1, le=31, description="Billing cycle start day")
    due_day: Optional[int] = Field(None, ge=1, le=31, description="Payment due day")


class CreditSourceCreate(CreditSourceBase):
    pass


class CreditSourceUpdate(BaseModel):
    card_name: Optional[str] = None
    card_last4: Optional[str] = None
    card_network: Optional[str] = None
    credit_limit: Optional[Decimal] = None
    billing_day: Optional[int] = None
    due_day: Optional[int] = None
    is_active: Optional[bool] = None


class CreditSourceResponse(CreditSourceBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
