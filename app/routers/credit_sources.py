from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List

from app.database import get_session
from app.models.user import User
from app.models.credit_source import CreditSource
from app.schemas.credit_source import (
    CreditSourceCreate,
    CreditSourceUpdate,
    CreditSourceResponse,
)
from app.utils.security import get_current_active_user

router = APIRouter()


@router.post(
    "",
    response_model=CreditSourceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_credit_source(
    credit_source_data: CreditSourceCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new credit source (credit card) for the current user.
    
    Automatically associates with the active family if one is set.
    """
    
    new_credit_source = CreditSource(
        **credit_source_data.model_dump(),
        user_id=current_user.id,
        family_id=current_user.active_family_id,  # Associate with active family
    )
    
    session.add(new_credit_source)
    await session.commit()
    await session.refresh(new_credit_source)
    
    return new_credit_source


@router.get("", response_model=List[CreditSourceResponse])
async def list_credit_sources(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """List all credit sources for the current user.
    
    If a family is active, only shows credit sources for that family.
    If no family is active, only shows personal credit sources (family_id=NULL).
    """
    
    conditions = [CreditSource.user_id == current_user.id]
    
    # Filter by active family
    if current_user.active_family_id:
        conditions.append(CreditSource.family_id == current_user.active_family_id)
    else:
        conditions.append(CreditSource.family_id.is_(None))
    
    result = await session.execute(
        select(CreditSource)
        .where(and_(*conditions))
        .order_by(CreditSource.card_name)
    )
    credit_sources = result.scalars().all()
    
    return credit_sources


@router.get("/active", response_model=List[CreditSourceResponse])
async def list_active_credit_sources(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """List all active credit sources for the current user.
    
    If a family is active, only shows active credit sources for that family.
    If no family is active, only shows personal active credit sources (family_id=NULL).
    """
    
    conditions = [
        CreditSource.user_id == current_user.id,
        CreditSource.is_active == True,
    ]
    
    # Filter by active family
    if current_user.active_family_id:
        conditions.append(CreditSource.family_id == current_user.active_family_id)
    else:
        conditions.append(CreditSource.family_id.is_(None))
    
    result = await session.execute(
        select(CreditSource)
        .where(and_(*conditions))
        .order_by(CreditSource.card_name)
    )
    credit_sources = result.scalars().all()
    
    return credit_sources


@router.get("/{credit_source_id}", response_model=CreditSourceResponse)
async def get_credit_source(
    credit_source_id: int,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Get a specific credit source by ID."""
    
    result = await session.execute(
        select(CreditSource).where(
            and_(
                CreditSource.id == credit_source_id,
                CreditSource.user_id == current_user.id,
            )
        )
    )
    credit_source = result.scalar_one_or_none()
    
    if not credit_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credit source not found",
        )
    
    return credit_source


@router.put("/{credit_source_id}", response_model=CreditSourceResponse)
async def update_credit_source(
    credit_source_id: int,
    credit_source_data: CreditSourceUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Update a credit source."""
    
    result = await session.execute(
        select(CreditSource).where(
            and_(
                CreditSource.id == credit_source_id,
                CreditSource.user_id == current_user.id,
            )
        )
    )
    credit_source = result.scalar_one_or_none()
    
    if not credit_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credit source not found",
        )
    
    # Update only provided fields
    update_data = credit_source_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(credit_source, field, value)
    
    await session.commit()
    await session.refresh(credit_source)
    
    return credit_source


@router.delete("/{credit_source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credit_source(
    credit_source_id: int,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Soft delete a credit source (mark as inactive)."""
    
    result = await session.execute(
        select(CreditSource).where(
            and_(
                CreditSource.id == credit_source_id,
                CreditSource.user_id == current_user.id,
            )
        )
    )
    credit_source = result.scalar_one_or_none()
    
    if not credit_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credit source not found",
        )
    
    # Soft delete by marking as inactive
    credit_source.is_active = False
    await session.commit()
    
    return None
