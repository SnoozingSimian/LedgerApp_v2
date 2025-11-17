# scripts/seed_categories.py

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.database import async_session_maker
from app.models.category import Category


# 25 comprehensive expense categories + 6 income categories
CATEGORIES = [
    # ========== EXPENSE CATEGORIES - NEEDS (50%) ==========
    {
        "name": "Housing",
        "category_type": "expense",
        "budget_classification": "needs",
        "icon": "🏠",
        "color": "#FF6B6B",
        "display_order": 1,
        "is_system": True,
    },
    {
        "name": "Utilities",
        "category_type": "expense",
        "budget_classification": "needs",
        "icon": "💡",
        "color": "#FFA07A",
        "display_order": 2,
        "is_system": True,
    },
    {
        "name": "Groceries & Food",
        "category_type": "expense",
        "budget_classification": "needs",
        "icon": "🛒",
        "color": "#4ECDC4",
        "display_order": 3,
        "is_system": True,
    },
    {
        "name": "Transportation",
        "category_type": "expense",
        "budget_classification": "needs",
        "icon": "🚗",
        "color": "#45B7D1",
        "display_order": 4,
        "is_system": True,
    },
    {
        "name": "Healthcare & Medical",
        "category_type": "expense",
        "budget_classification": "needs",
        "icon": "⚕️",
        "color": "#98D8C8",
        "display_order": 5,
        "is_system": True,
    },
    {
        "name": "Insurance",
        "category_type": "expense",
        "budget_classification": "needs",
        "icon": "🛡️",
        "color": "#A8D8EA",
        "display_order": 6,
        "is_system": True,
    },
    {
        "name": "Debt Payments & EMIs",
        "category_type": "expense",
        "budget_classification": "needs",
        "icon": "💳",
        "color": "#FFD93D",
        "display_order": 7,
        "is_system": True,
    },
    {
        "name": "Childcare & Education",
        "category_type": "expense",
        "budget_classification": "needs",
        "icon": "👶",
        "color": "#FCBAD3",
        "display_order": 8,
        "is_system": True,
    },
    # ========== EXPENSE CATEGORIES - WANTS (30%) ==========
    {
        "name": "Dining & Restaurants",
        "category_type": "expense",
        "budget_classification": "wants",
        "icon": "🍽️",
        "color": "#F38181",
        "display_order": 9,
        "is_system": True,
    },
    {
        "name": "Entertainment",
        "category_type": "expense",
        "budget_classification": "wants",
        "icon": "🎬",
        "color": "#AA96DA",
        "display_order": 10,
        "is_system": True,
    },
    {
        "name": "Shopping & Clothing",
        "category_type": "expense",
        "budget_classification": "wants",
        "icon": "🛍️",
        "color": "#FFB6C1",
        "display_order": 11,
        "is_system": True,
    },
    {
        "name": "Personal Care & Beauty",
        "category_type": "expense",
        "budget_classification": "wants",
        "icon": "💅",
        "color": "#C3AED6",
        "display_order": 12,
        "is_system": True,
    },
    {
        "name": "Subscriptions",
        "category_type": "expense",
        "budget_classification": "wants",
        "icon": "📱",
        "color": "#B8E6B8",
        "display_order": 13,
        "is_system": True,
    },
    {
        "name": "Travel & Vacation",
        "category_type": "expense",
        "budget_classification": "wants",
        "icon": "✈️",
        "color": "#4D96FF",
        "display_order": 14,
        "is_system": True,
    },
    {
        "name": "Hobbies & Recreation",
        "category_type": "expense",
        "budget_classification": "wants",
        "icon": "🎨",
        "color": "#DDA0DD",
        "display_order": 15,
        "is_system": True,
    },
    {
        "name": "Gifts & Donations",
        "category_type": "expense",
        "budget_classification": "wants",
        "icon": "🎁",
        "color": "#FF6B9D",
        "display_order": 16,
        "is_system": True,
    },
    {
        "name": "Pet Care",
        "category_type": "expense",
        "budget_classification": "wants",
        "icon": "🐾",
        "color": "#87CEEB",
        "display_order": 17,
        "is_system": True,
    },
    # ========== EXPENSE CATEGORIES - SAVINGS (20%) ==========
    {
        "name": "Investments",
        "category_type": "expense",
        "budget_classification": "savings",
        "icon": "📈",
        "color": "#6BCB77",
        "display_order": 18,
        "is_system": True,
    },
    {
        "name": "Emergency Fund",
        "category_type": "expense",
        "budget_classification": "savings",
        "icon": "🏦",
        "color": "#27AE60",
        "display_order": 19,
        "is_system": True,
    },
    {
        "name": "Retirement Savings",
        "category_type": "expense",
        "budget_classification": "savings",
        "icon": "👴",
        "color": "#2ECC71",
        "display_order": 20,
        "is_system": True,
    },
    # ========== EXPENSE CATEGORIES - MISCELLANEOUS ==========
    {
        "name": "Professional Services",
        "category_type": "expense",
        "budget_classification": "needs",
        "icon": "💼",
        "color": "#8E44AD",
        "display_order": 21,
        "is_system": True,
    },
    {
        "name": "Technology & Gadgets",
        "category_type": "expense",
        "budget_classification": "wants",
        "icon": "💻",
        "color": "#3498DB",
        "display_order": 22,
        "is_system": True,
    },
    {
        "name": "Home Maintenance",
        "category_type": "expense",
        "budget_classification": "needs",
        "icon": "🔧",
        "color": "#E67E22",
        "display_order": 23,
        "is_system": True,
    },
    {
        "name": "Taxes",
        "category_type": "expense",
        "budget_classification": "needs",
        "icon": "📋",
        "color": "#95A5A6",
        "display_order": 24,
        "is_system": True,
    },
    {
        "name": "Miscellaneous",
        "category_type": "expense",
        "budget_classification": "needs",
        "icon": "📦",
        "color": "#BDC3C7",
        "display_order": 25,
        "is_system": True,
    },
    # ========== INCOME CATEGORIES ==========
    {
        "name": "Salary & Wages",
        "category_type": "income",
        "budget_classification": None,
        "icon": "💼",
        "color": "#27AE60",
        "display_order": 101,
        "is_system": True,
    },
    {
        "name": "Freelance & Business Income",
        "category_type": "income",
        "budget_classification": None,
        "icon": "🚀",
        "color": "#2ECC71",
        "display_order": 102,
        "is_system": True,
    },
    {
        "name": "Investment Returns",
        "category_type": "income",
        "budget_classification": None,
        "icon": "📊",
        "color": "#16A085",
        "display_order": 103,
        "is_system": True,
    },
    {
        "name": "Rental Income",
        "category_type": "income",
        "budget_classification": None,
        "icon": "🏘️",
        "color": "#1ABC9C",
        "display_order": 104,
        "is_system": True,
    },
    {
        "name": "Gifts Received",
        "category_type": "income",
        "budget_classification": None,
        "icon": "🎉",
        "color": "#3498DB",
        "display_order": 105,
        "is_system": True,
    },
    {
        "name": "Other Income",
        "category_type": "income",
        "budget_classification": None,
        "icon": "💵",
        "color": "#9B59B6",
        "display_order": 106,
        "is_system": True,
    },
]


async def seed_categories():
    """Seed system categories into the database."""
    async with async_session_maker() as session:
        # Check if categories already exist
        result = await session.execute(select(Category))
        existing_categories = result.scalars().all()

        if existing_categories:
            print(
                f"⚠️  Categories already seeded ({len(existing_categories)} existing). Skipping."
            )
            return

        # Insert categories
        categories = [Category(**cat_data) for cat_data in CATEGORIES]
        session.add_all(categories)

        await session.commit()
        print(f"✅ Successfully seeded {len(CATEGORIES)} categories!")

        # Display summary
        expense_count = sum(1 for c in CATEGORIES if c["category_type"] == "expense")
        income_count = sum(1 for c in CATEGORIES if c["category_type"] == "income")
        print(f"   - {expense_count} expense categories")
        print(f"   - {income_count} income categories")


if __name__ == "__main__":
    print("🌱 Seeding categories...")
    asyncio.run(seed_categories())
