# app/routers/transactions.py

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import date

from app.database import get_session
from app.models.user import User
from app.models.transaction import Transaction, TransactionTag
from app.models.category import Category
from app.models.tag import Tag
from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransactionListResponse,
    CategoryResponse,
    TagResponse,
)
from app.utils.security import get_current_active_user

router = APIRouter()


@router.post(
    "", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED
)
async def create_transaction(
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new transaction for the current user."""

    # Verify category exists
    category_result = await session.execute(
        select(Category).where(Category.id == transaction_data.category_id)
    )
    category = category_result.scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    # Verify subcategory if provided
    if transaction_data.subcategory_id:
        subcategory_result = await session.execute(
            select(Category).where(Category.id == transaction_data.subcategory_id)
        )
        subcategory = subcategory_result.scalar_one_or_none()
        if not subcategory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Subcategory not found"
            )

    # Create transaction
    transaction_dict = transaction_data.model_dump(exclude={"tag_ids"})
    new_transaction = Transaction(**transaction_dict, user_id=current_user.id)

    session.add(new_transaction)
    await session.flush()  # Get transaction ID

    # Add tags if provided
    if transaction_data.tag_ids:
        for tag_id in transaction_data.tag_ids:
            tag_link = TransactionTag(transaction_id=new_transaction.id, tag_id=tag_id)
            session.add(tag_link)

    await session.commit()
    await session.refresh(new_transaction)

    # Load relationships for response
    result = await session.execute(
        select(Transaction)
        .where(Transaction.id == new_transaction.id)
        .options(
            selectinload(Transaction.category),
            selectinload(Transaction.subcategory),
            selectinload(Transaction.tags).selectinload(TransactionTag.tag),
        )
    )
    transaction = result.scalar_one()

    return transaction


@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    transaction_type: Optional[str] = Query(None, pattern="^(income|expense)$"),
    category_id: Optional[int] = None,
    payment_method: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """List all transactions for the current user with filters and pagination."""

    # Build query
    query = select(Transaction).where(Transaction.user_id == current_user.id)

    # Apply filters
    if start_date:
        query = query.where(Transaction.t_date >= start_date)
    if end_date:
        query = query.where(Transaction.t_date <= end_date)
    if transaction_type:
        query = query.where(Transaction.transaction_type == transaction_type)
    if category_id:
        query = query.where(Transaction.category_id == category_id)
    if payment_method:
        query = query.where(Transaction.payment_method == payment_method)
    if search:
        search_filter = or_(
            Transaction.payee.ilike(f"%{search}%"),
            Transaction.notes.ilike(f"%{search}%"),
            Transaction.merchant_type.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar()

    # Apply pagination and ordering
    query = query.order_by(desc(Transaction.t_date), desc(Transaction.id))
    query = query.offset((page - 1) * page_size).limit(page_size)

    # Load relationships
    query = query.options(
        selectinload(Transaction.category),
        selectinload(Transaction.subcategory),
        selectinload(Transaction.tags).selectinload(TransactionTag.tag),
    )

    # Execute query
    result = await session.execute(query)
    transactions = result.scalars().all()

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size

    return {
        "transactions": transactions,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Get a specific transaction by ID."""

    result = await session.execute(
        select(Transaction)
        .where(
            and_(
                Transaction.id == transaction_id, Transaction.user_id == current_user.id
            )
        )
        .options(
            selectinload(Transaction.category),
            selectinload(Transaction.subcategory),
            selectinload(Transaction.tags).selectinload(TransactionTag.tag),
        )
    )
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )

    return transaction


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Update a transaction."""

    import logging
    from datetime import date as date_type

    logger = logging.getLogger(__name__)

    try:
        body = await request.json()
        logger.info(f"Raw request body: {body}")

        # Convert date strings to date objects
        if "t_date" in body and body["t_date"]:
            try:
                body["t_date"] = date_type.fromisoformat(body["t_date"])
            except (ValueError, AttributeError):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid date format. Use YYYY-MM-DD",
                )

        if "payment_due_date" in body and body["payment_due_date"]:
            try:
                body["payment_due_date"] = date_type.fromisoformat(
                    body["payment_due_date"]
                )
            except (ValueError, AttributeError):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid payment_due_date format. Use YYYY-MM-DD",
                )

        # Manually validate
        transaction_data = TransactionUpdate(**body)
        logger.info(f"Validated data: {transaction_data.model_dump()}")

    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}",
        )

    # Get transaction
    result = await session.execute(
        select(Transaction).where(
            and_(
                Transaction.id == transaction_id, Transaction.user_id == current_user.id
            )
        )
    )
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )

    # Update fields - only update fields that are provided
    update_data = transaction_data.model_dump(exclude_unset=True, exclude={"tag_ids"})

    # Convert date strings to date objects for database
    if "t_date" in update_data and isinstance(update_data["t_date"], str):
        update_data["t_date"] = date_type.fromisoformat(update_data["t_date"])
    if "payment_due_date" in update_data and isinstance(
        update_data["payment_due_date"], str
    ):
        update_data["payment_due_date"] = date_type.fromisoformat(
            update_data["payment_due_date"]
        )

    for field, value in update_data.items():
        setattr(transaction, field, value)

    # Update tags if provided
    if transaction_data.tag_ids is not None:
        # Remove existing tags
        existing_tags_result = await session.execute(
            select(TransactionTag).where(
                TransactionTag.transaction_id == transaction_id
            )
        )
        existing_tags = existing_tags_result.scalars().all()

        for tag in existing_tags:
            await session.delete(tag)

        await session.flush()

        # Add new tags
        for tag_id in transaction_data.tag_ids:
            tag_link = TransactionTag(transaction_id=transaction_id, tag_id=tag_id)
            session.add(tag_link)

    await session.commit()

    # Reload with relationships
    result = await session.execute(
        select(Transaction)
        .where(Transaction.id == transaction_id)
        .options(
            selectinload(Transaction.category),
            selectinload(Transaction.subcategory),
            selectinload(Transaction.tags).selectinload(TransactionTag.tag),
        )
    )
    updated_transaction = result.scalar_one()

    return updated_transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete a transaction."""

    result = await session.execute(
        select(Transaction).where(
            and_(
                Transaction.id == transaction_id, Transaction.user_id == current_user.id
            )
        )
    )
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )

    await session.delete(transaction)
    await session.commit()

    return None


@router.get("/stats/summary")
async def get_transaction_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Get transaction summary statistics."""
    from sqlalchemy import func as sql_func
    from decimal import Decimal

    # Build WHERE conditions
    conditions = [Transaction.user_id == current_user.id]

    if start_date:
        conditions.append(Transaction.t_date >= start_date)
    if end_date:
        conditions.append(Transaction.t_date <= end_date)

    # Get income summary
    income_result = await session.execute(
        select(
            sql_func.coalesce(sql_func.sum(Transaction.amount), 0).label("total"),
            sql_func.count(Transaction.id).label("count"),
        ).where(and_(*conditions, Transaction.transaction_type == "income"))
    )
    income_row = income_result.first()
    total_income = float(income_row.total) if income_row else 0.0
    income_count = income_row.count if income_row else 0

    # Get expense summary
    expense_result = await session.execute(
        select(
            sql_func.coalesce(sql_func.sum(Transaction.amount), 0).label("total"),
            sql_func.count(Transaction.id).label("count"),
        ).where(and_(*conditions, Transaction.transaction_type == "expense"))
    )
    expense_row = expense_result.first()
    total_expenses = float(expense_row.total) if expense_row else 0.0
    expense_count = expense_row.count if expense_row else 0

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_savings": total_income - total_expenses,
        "income_count": income_count,
        "expense_count": expense_count,
        "total_transactions": income_count + expense_count,
    }


# Add this endpoint to app/routers/transactions.py


@router.get("/categories/list", response_model=List[CategoryResponse])
async def list_categories(
    transaction_type: Optional[str] = Query(None, pattern="^(income|expense)$"),
    session: AsyncSession = Depends(get_session),
):
    """Get all categories, optionally filtered by type."""

    query = select(Category).where(Category.is_system == True)

    if transaction_type:
        query = query.where(Category.category_type == transaction_type)

    query = query.order_by(Category.display_order)

    result = await session.execute(query)
    categories = result.scalars().all()

    return categories
