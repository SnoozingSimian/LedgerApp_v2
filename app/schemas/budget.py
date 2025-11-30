# app/schemas/budget.py

from pydantic import BaseModel, Field, field_validator, field_serializer
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


class BudgetCategoryAllocationBase(BaseModel):
    category_id: int
    allocated_amount: Decimal = Field(..., ge=0)

    @field_validator("allocated_amount")
    @classmethod
    def validate_amount(cls, v):
        """Ensure amount has max 2 decimal places."""
        if v is not None:
            return round(v, 2)
        return v


class BudgetCategoryAllocationCreate(BudgetCategoryAllocationBase):
    pass


class BudgetCategoryAllocationUpdate(BaseModel):
    category_id: Optional[int] = None
    allocated_amount: Optional[Decimal] = None

    @field_validator("allocated_amount")
    @classmethod
    def validate_amount(cls, v):
        """Ensure amount has max 2 decimal places."""
        if v is not None:
            return round(v, 2)
        return v


class BudgetCategoryAllocationResponse(BudgetCategoryAllocationBase):
    id: int
    budget_id: int
    category_name: Optional[str] = None
    spent_amount: Optional[Decimal] = None
    remaining_amount: Optional[Decimal] = None
    utilization_percent: Optional[float] = None

    class Config:
        from_attributes = True


class BudgetBase(BaseModel):
    name: str = Field(..., max_length=100)
    period_start: date
    period_end: date
    total_budget: Optional[Decimal] = None
    needs_budget: Optional[Decimal] = None
    wants_budget: Optional[Decimal] = None
    savings_budget: Optional[Decimal] = None
    alert_threshold_percent: int = Field(default=80, ge=1, le=100)
    is_active: bool = Field(default=True)

    @field_validator("total_budget", "needs_budget", "wants_budget", "savings_budget")
    @classmethod
    def validate_amounts(cls, v):
        """Ensure amounts have max 2 decimal places."""
        if v is not None:
            return round(v, 2)
        return v

    @field_validator("period_end")
    @classmethod
    def validate_period(cls, v, info):
        """Ensure period_end is after period_start."""
        if "period_start" in info.data and v <= info.data["period_start"]:
            raise ValueError("period_end must be after period_start")
        return v


class BudgetCreate(BudgetBase):
    family_id: Optional[int] = None
    category_allocations: List[BudgetCategoryAllocationCreate] = []

    @field_validator("category_allocations")
    @classmethod
    def validate_allocations(cls, v, info):
        """Validate that category allocations don't exceed total budget."""
        if v and "total_budget" in info.data and info.data["total_budget"] is not None:
            total_allocated = sum(alloc.allocated_amount for alloc in v)
            if total_allocated > info.data["total_budget"]:
                raise ValueError(
                    f"Total category allocations ({total_allocated}) exceed total budget ({info.data['total_budget']})"
                )
        return v


class BudgetUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    total_budget: Optional[Decimal] = None
    needs_budget: Optional[Decimal] = None
    wants_budget: Optional[Decimal] = None
    savings_budget: Optional[Decimal] = None
    alert_threshold_percent: Optional[int] = Field(None, ge=1, le=100)
    is_active: Optional[bool] = None
    category_allocations: Optional[List[BudgetCategoryAllocationCreate]] = None

    @field_validator("total_budget", "needs_budget", "wants_budget", "savings_budget")
    @classmethod
    def validate_amounts(cls, v):
        """Ensure amounts have max 2 decimal places."""
        if v is not None:
            return round(v, 2)
        return v


class BudgetResponse(BudgetBase):
    id: int
    user_id: int
    family_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    category_allocations: List[BudgetCategoryAllocationResponse] = []
    total_spent: Optional[Decimal] = None
    total_remaining: Optional[Decimal] = None
    overall_utilization_percent: Optional[float] = None

    @field_serializer("period_start", "period_end")
    def serialize_date(self, value):
        return value.isoformat() if value else None

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, value):
        return value.isoformat() if value else None

    class Config:
        from_attributes = True


class BudgetListResponse(BaseModel):
    budgets: List[BudgetResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class BudgetSummary(BaseModel):
    id: int
    name: str
    period_start: date
    period_end: date
    total_budget: Optional[Decimal]
    total_spent: Optional[Decimal]
    is_active: bool
    overall_utilization_percent: Optional[float]

    @field_serializer("period_start", "period_end")
    def serialize_date(self, value):
        return value.isoformat() if value else None

    class Config:
        from_attributes = True
