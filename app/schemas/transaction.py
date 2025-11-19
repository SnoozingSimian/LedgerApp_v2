# app/schemas/transaction.py

from pydantic import BaseModel, Field, field_serializer, field_validator
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


class TransactionBase(BaseModel):
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="INR", max_length=3)
    transaction_type: str = Field(..., pattern="^(income|expense)$")
    payment_method: str
    category_id: int
    subcategory_id: Optional[int] = None
    payee: Optional[str] = Field(None, max_length=200)
    merchant_type: Optional[str] = Field(None, max_length=100)
    t_date: date
    notes: Optional[str] = None
    credit_source_id: Optional[int] = None
    is_paid: bool = Field(default=False)
    payment_due_date: Optional[date] = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        """Ensure amount has max 2 decimal places."""
        if v is not None:
            return round(v, 2)
        return v

    @field_validator("payment_method")
    @classmethod
    def validate_payment_method(cls, v):
        valid_methods = [
            "cash",
            "credit_card",
            "upi",
            "neft",
            "imps",
            "rtgs",
            "cheque",
            "debit_card",
            "other",
        ]
        if v not in valid_methods:
            raise ValueError(f"payment_method must be one of {valid_methods}")
        return v


class TransactionCreate(TransactionBase):
    tag_ids: Optional[List[int]] = []


# SIMPLIFIED: Just use strings for dates
class TransactionUpdate(BaseModel):
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    transaction_type: Optional[str] = None
    payment_method: Optional[str] = None
    category_id: Optional[int] = None
    subcategory_id: Optional[int] = None
    payee: Optional[str] = None
    merchant_type: Optional[str] = None
    t_date: Optional[date] = None  # Simple string, no validation
    notes: Optional[str] = None
    credit_source_id: Optional[int] = None
    is_paid: Optional[bool] = None
    payment_due_date: Optional[date] = None  # Simple string, no validation
    tag_ids: Optional[List[int]] = None

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, v):
        """Ensure amount has max 2 decimal places."""
        if v is not None and v != "":
            return round(float(v), 2)
        return v

    @field_validator("payment_method", mode="before")
    @classmethod
    def validate_payment_method(cls, v):
        if v is not None and v != "":
            valid_methods = [
                "cash",
                "credit_card",
                "upi",
                "neft",
                "imps",
                "rtgs",
                "cheque",
                "debit_card",
                "other",
            ]
            if v not in valid_methods:
                raise ValueError(f"payment_method must be one of {valid_methods}")
        return v


class CategoryResponse(BaseModel):
    id: int
    name: str
    category_type: str
    icon: Optional[str] = None
    color: Optional[str] = None

    class Config:
        from_attributes = True


class TagResponse(BaseModel):
    id: int
    name: str
    color: Optional[str] = None

    class Config:
        from_attributes = True


class TransactionResponse(TransactionBase):
    id: int
    user_id: int
    family_id: Optional[int] = None
    category: CategoryResponse
    subcategory: Optional[CategoryResponse] = None
    tags: List[TagResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    @field_serializer("t_date", "payment_due_date")
    def serialize_date(self, value):
        return value.isoformat() if value else None

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, value):
        return value.isoformat() if value else None

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    transactions: List[TransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TransactionFilters(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    transaction_type: Optional[str] = None
    category_id: Optional[int] = None
    payment_method: Optional[str] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    search: Optional[str] = None
