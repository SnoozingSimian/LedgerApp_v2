# app/routers/categories.py

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_session
from app.models.user import User
from app.models.category import Category
from app.utils.security import get_current_active_user

router = APIRouter()


@router.get("/categories")
async def list_categories(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """List all categories for dropdowns."""
    query = select(Category).order_by(Category.name)
    result = await session.execute(query)
    categories = result.scalars().all()

    return [
        {
            "id": cat.id,
            "name": cat.name,
            "category_type": cat.category_type,
            "icon": cat.icon,
            "color": cat.color,
        }
        for cat in categories
    ]
