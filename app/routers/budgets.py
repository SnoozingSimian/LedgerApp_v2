from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import date
from decimal import Decimal
import logging

from app.database import get_session
from app.models.user import User
from app.models.budget import Budget, BudgetCategory
from app.models.category import Category
from app.models.transaction import Transaction
from app.schemas.budget import (
    BudgetCreate,
    BudgetUpdate,
    BudgetResponse,
    BudgetListResponse,
    BudgetSummary,
    BudgetCategoryAllocationResponse,
)
from app.utils.security import get_current_active_user

router = APIRouter()
logger = logging.getLogger(__name__)


async def calculate_budget_spending(budget: Budget, session: AsyncSession) -> dict:
    """
    Calculate spending statistics for a budget.
    Returns total spent, remaining, and utilization percentage.
    """
    # Query transactions within the budget period
    query = select(func.sum(Transaction.amount)).where(
        and_(
            Transaction.user_id == budget.user_id,
            Transaction.transaction_type == "expense",
            Transaction.t_date >= budget.period_start,
            Transaction.t_date <= budget.period_end,
        )
    )

    # Add family filter if budget is family-based
    if budget.family_id:
        query = query.where(Transaction.family_id == budget.family_id)

    result = await session.execute(query)
    total_spent = result.scalar() or Decimal("0.00")

    # Calculate remaining and utilization
    total_remaining = None
    utilization_percent = None

    if budget.total_budget:
        total_remaining = budget.total_budget - total_spent
        if budget.total_budget > 0:
            utilization_percent = float((total_spent / budget.total_budget) * 100)

    return {
        "total_spent": total_spent,
        "total_remaining": total_remaining,
        "overall_utilization_percent": utilization_percent,
    }


async def calculate_category_spending(
    budget_category: BudgetCategory, budget: Budget, session: AsyncSession
) -> dict:
    """
    Calculate spending for a specific budget category allocation.
    """
    # Query transactions for this category within budget period
    query = select(func.sum(Transaction.amount)).where(
        and_(
            Transaction.user_id == budget.user_id,
            Transaction.transaction_type == "expense",
            Transaction.category_id == budget_category.category_id,
            Transaction.t_date >= budget.period_start,
            Transaction.t_date <= budget.period_end,
        )
    )

    if budget.family_id:
        query = query.where(Transaction.family_id == budget.family_id)

    result = await session.execute(query)
    spent_amount = result.scalar() or Decimal("0.00")

    remaining_amount = budget_category.allocated_amount - spent_amount
    utilization_percent = None

    if budget_category.allocated_amount > 0:
        utilization_percent = float(
            (spent_amount / budget_category.allocated_amount) * 100
        )

    return {
        "spent_amount": spent_amount,
        "remaining_amount": remaining_amount,
        "utilization_percent": utilization_percent,
    }


@router.post("/", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
async def create_budget(
    budget_data: BudgetCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new budget with category allocations.
    If no family_id is provided, uses the active family from current user.
    """
    # Use active family if not explicitly provided
    family_id = budget_data.family_id or current_user.active_family_id
    
    # Validate that period doesn't overlap with existing active budgets
    overlap_query = select(Budget).where(
        and_(
            Budget.user_id == current_user.id,
            Budget.family_id == family_id,  # Only check within same family scope
            Budget.is_active == True,
            or_(
                and_(
                    Budget.period_start <= budget_data.period_start,
                    Budget.period_end >= budget_data.period_start,
                ),
                and_(
                    Budget.period_start <= budget_data.period_end,
                    Budget.period_end >= budget_data.period_end,
                ),
                and_(
                    Budget.period_start >= budget_data.period_start,
                    Budget.period_end <= budget_data.period_end,
                ),
            ),
        )
    )

    result = await session.execute(overlap_query)
    overlapping_budget = result.scalar_one_or_none()

    if overlapping_budget:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Budget period overlaps with existing budget '{overlapping_budget.name}'",
        )

    # Validate category IDs exist
    if budget_data.category_allocations:
        category_ids = [alloc.category_id for alloc in budget_data.category_allocations]
        result = await session.execute(
            select(Category).where(Category.id.in_(category_ids))
        )
        categories = result.scalars().all()

        if len(categories) != len(category_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more category IDs are invalid",
            )

    # Create budget
    new_budget = Budget(
        user_id=current_user.id,
        family_id=family_id,
        name=budget_data.name,
        period_start=budget_data.period_start,
        period_end=budget_data.period_end,
        total_budget=budget_data.total_budget,
        needs_budget=budget_data.needs_budget,
        wants_budget=budget_data.wants_budget,
        savings_budget=budget_data.savings_budget,
        alert_threshold_percent=budget_data.alert_threshold_percent,
        is_active=budget_data.is_active,
    )

    session.add(new_budget)
    await session.flush()  # Get the budget ID

    # Create category allocations
    for allocation in budget_data.category_allocations:
        budget_category = BudgetCategory(
            budget_id=new_budget.id,
            category_id=allocation.category_id,
            allocated_amount=allocation.allocated_amount,
        )
        session.add(budget_category)

    await session.commit()
    await session.refresh(new_budget)

    # Load relationships and calculate spending
    result = await session.execute(
        select(Budget)
        .options(
            selectinload(Budget.budget_categories).selectinload(BudgetCategory.category)
        )
        .where(Budget.id == new_budget.id)
    )
    budget = result.scalar_one()

    # Calculate spending stats
    spending_stats = await calculate_budget_spending(budget, session)

    # Build response with category details
    category_allocations = []
    for bc in budget.budget_categories:
        category_stats = await calculate_category_spending(bc, budget, session)
        category_allocations.append(
            BudgetCategoryAllocationResponse(
                id=bc.id,
                budget_id=bc.budget_id,
                category_id=bc.category_id,
                allocated_amount=bc.allocated_amount,
                category_name=bc.category.name,
                **category_stats,
            )
        )

    response_data = BudgetResponse(
        id=budget.id,
        user_id=budget.user_id,
        family_id=budget.family_id,
        name=budget.name,
        period_start=budget.period_start,
        period_end=budget.period_end,
        total_budget=budget.total_budget,
        needs_budget=budget.needs_budget,
        wants_budget=budget.wants_budget,
        savings_budget=budget.savings_budget,
        alert_threshold_percent=budget.alert_threshold_percent,
        is_active=budget.is_active,
        created_at=budget.created_at,
        updated_at=budget.updated_at,
        category_allocations=category_allocations,
        **spending_stats,
    )

    logger.info(f"Created budget '{budget.name}' for user {current_user.id}")
    return response_data


@router.get("/", response_model=BudgetListResponse)
async def list_budgets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """
    List all budgets for the current user with pagination.
    If a family is active, only shows budgets for that family.
    If no family is active, only shows personal budgets (family_id=NULL).
    """
    # Build base query
    query = select(Budget).where(Budget.user_id == current_user.id)
    
    # Filter by active family
    if current_user.active_family_id:
        query = query.where(Budget.family_id == current_user.active_family_id)
    else:
        query = query.where(Budget.family_id.is_(None))

    if is_active is not None:
        query = query.where(Budget.is_active == is_active)

    query = query.order_by(Budget.period_start.desc())

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    query = query.offset((page - 1) * page_size).limit(page_size)

    # Load budgets with relationships
    query = query.options(
        selectinload(Budget.budget_categories).selectinload(BudgetCategory.category)
    )

    result = await session.execute(query)
    budgets = result.scalars().all()

    # Build response with spending stats
    budget_responses = []
    for budget in budgets:
        spending_stats = await calculate_budget_spending(budget, session)

        category_allocations = []
        for bc in budget.budget_categories:
            category_stats = await calculate_category_spending(bc, budget, session)
            category_allocations.append(
                BudgetCategoryAllocationResponse(
                    id=bc.id,
                    budget_id=bc.budget_id,
                    category_id=bc.category_id,
                    allocated_amount=bc.allocated_amount,
                    category_name=bc.category.name,
                    **category_stats,
                )
            )

        budget_responses.append(
            BudgetResponse(
                id=budget.id,
                user_id=budget.user_id,
                family_id=budget.family_id,
                name=budget.name,
                period_start=budget.period_start,
                period_end=budget.period_end,
                total_budget=budget.total_budget,
                needs_budget=budget.needs_budget,
                wants_budget=budget.wants_budget,
                savings_budget=budget.savings_budget,
                alert_threshold_percent=budget.alert_threshold_percent,
                is_active=budget.is_active,
                created_at=budget.created_at,
                updated_at=budget.updated_at,
                category_allocations=category_allocations,
                **spending_stats,
            )
        )

    total_pages = (total + page_size - 1) // page_size

    return BudgetListResponse(
        budgets=budget_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/active", response_model=BudgetResponse)
async def get_active_budget(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get the currently active budget for the user.
    Respects active family scope.
    """
    today = date.today()
    
    conditions = [
        Budget.user_id == current_user.id,
        Budget.is_active == True,
        Budget.period_start <= today,
        Budget.period_end >= today,
    ]
    
    # Filter by active family
    if current_user.active_family_id:
        conditions.append(Budget.family_id == current_user.active_family_id)
    else:
        conditions.append(Budget.family_id.is_(None))

    query = (
        select(Budget)
        .options(
            selectinload(Budget.budget_categories).selectinload(BudgetCategory.category)
        )
        .where(and_(*conditions))
    )

    result = await session.execute(query)
    budget = result.scalar_one_or_none()

    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active budget found for current period",
        )

    # Calculate spending stats
    spending_stats = await calculate_budget_spending(budget, session)

    # Build category allocations with stats
    category_allocations = []
    for bc in budget.budget_categories:
        category_stats = await calculate_category_spending(bc, budget, session)
        category_allocations.append(
            BudgetCategoryAllocationResponse(
                id=bc.id,
                budget_id=bc.budget_id,
                category_id=bc.category_id,
                allocated_amount=bc.allocated_amount,
                category_name=bc.category.name,
                **category_stats,
            )
        )

    return BudgetResponse(
        id=budget.id,
        user_id=budget.user_id,
        family_id=budget.family_id,
        name=budget.name,
        period_start=budget.period_start,
        period_end=budget.period_end,
        total_budget=budget.total_budget,
        needs_budget=budget.needs_budget,
        wants_budget=budget.wants_budget,
        savings_budget=budget.savings_budget,
        alert_threshold_percent=budget.alert_threshold_percent,
        is_active=budget.is_active,
        created_at=budget.created_at,
        updated_at=budget.updated_at,
        category_allocations=category_allocations,
        **spending_stats,
    )


@router.get("/{budget_id}", response_model=BudgetResponse)
async def get_budget(
    budget_id: int,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get a specific budget by ID.
    """
    query = (
        select(Budget)
        .options(
            selectinload(Budget.budget_categories).selectinload(BudgetCategory.category)
        )
        .where(and_(Budget.id == budget_id, Budget.user_id == current_user.id))
    )

    result = await session.execute(query)
    budget = result.scalar_one_or_none()

    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found"
        )

    # Calculate spending stats
    spending_stats = await calculate_budget_spending(budget, session)

    # Build category allocations with stats
    category_allocations = []
    for bc in budget.budget_categories:
        category_stats = await calculate_category_spending(bc, budget, session)
        category_allocations.append(
            BudgetCategoryAllocationResponse(
                id=bc.id,
                budget_id=bc.budget_id,
                category_id=bc.category_id,
                allocated_amount=bc.allocated_amount,
                category_name=bc.category.name,
                **category_stats,
            )
        )

    return BudgetResponse(
        id=budget.id,
        user_id=budget.user_id,
        family_id=budget.family_id,
        name=budget.name,
        period_start=budget.period_start,
        period_end=budget.period_end,
        total_budget=budget.total_budget,
        needs_budget=budget.needs_budget,
        wants_budget=budget.wants_budget,
        savings_budget=budget.savings_budget,
        alert_threshold_percent=budget.alert_threshold_percent,
        is_active=budget.is_active,
        created_at=budget.created_at,
        updated_at=budget.updated_at,
        category_allocations=category_allocations,
        **spending_stats,
    )


@router.put("/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    budget_id: int,
    budget_data: BudgetUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Update an existing budget.
    """
    # Get budget
    query = select(Budget).where(
        and_(Budget.id == budget_id, Budget.user_id == current_user.id)
    )
    result = await session.execute(query)
    budget = result.scalar_one_or_none()

    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found"
        )

    # Update basic fields
    update_data = budget_data.model_dump(
        exclude_unset=True, exclude={"category_allocations"}
    )
    for field, value in update_data.items():
        setattr(budget, field, value)

    # Update category allocations if provided
    if budget_data.category_allocations is not None:
        # Delete existing allocations properly
        existing_query = select(BudgetCategory).where(
            BudgetCategory.budget_id == budget_id
        )
        existing_result = await session.execute(existing_query)
        existing_allocations = existing_result.scalars().all()

        for alloc in existing_allocations:
            await session.delete(alloc)

        # Flush to ensure deletions are processed before inserts
        await session.flush()

        # Create new allocations
        for allocation in budget_data.category_allocations:
            budget_category = BudgetCategory(
                budget_id=budget.id,
                category_id=allocation.category_id,
                allocated_amount=allocation.allocated_amount,
            )
            session.add(budget_category)

    await session.commit()

    # Reload with relationships
    result = await session.execute(
        select(Budget)
        .options(
            selectinload(Budget.budget_categories).selectinload(BudgetCategory.category)
        )
        .where(Budget.id == budget_id)
    )
    budget = result.scalar_one()

    # Calculate spending stats
    spending_stats = await calculate_budget_spending(budget, session)

    # Build category allocations with stats
    category_allocations = []
    for bc in budget.budget_categories:
        category_stats = await calculate_category_spending(bc, budget, session)
        category_allocations.append(
            BudgetCategoryAllocationResponse(
                id=bc.id,
                budget_id=bc.budget_id,
                category_id=bc.category_id,
                allocated_amount=bc.allocated_amount,
                category_name=bc.category.name,
                **category_stats,
            )
        )

    logger.info(f"Updated budget {budget_id} for user {current_user.id}")

    return BudgetResponse(
        id=budget.id,
        user_id=budget.user_id,
        family_id=budget.family_id,
        name=budget.name,
        period_start=budget.period_start,
        period_end=budget.period_end,
        total_budget=budget.total_budget,
        needs_budget=budget.needs_budget,
        wants_budget=budget.wants_budget,
        savings_budget=budget.savings_budget,
        alert_threshold_percent=budget.alert_threshold_percent,
        is_active=budget.is_active,
        created_at=budget.created_at,
        updated_at=budget.updated_at,
        category_allocations=category_allocations,
        **spending_stats,
    )


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(
    budget_id: int,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Delete a budget.
    """
    query = select(Budget).where(
        and_(Budget.id == budget_id, Budget.user_id == current_user.id)
    )
    result = await session.execute(query)
    budget = result.scalar_one_or_none()

    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found"
        )

    await session.delete(budget)
    await session.commit()

    logger.info(f"Deleted budget {budget_id} for user {current_user.id}")
    return None
