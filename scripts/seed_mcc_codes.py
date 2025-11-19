# scripts/seed_mcc_codes.py

import asyncio
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.database import async_session_maker
from app.models.category import Category
from app.models.merchant_category import MerchantCategory

# A sample/representative MCCs list - expand or edit as needed!
MCC_CODES = [
    # Groceries & Food
    {
        "mcc_code": "5411",
        "description": "Grocery Stores, Supermarkets",
        "category_name": "Groceries & Food",
    },
    {
        "mcc_code": "5422",
        "description": "Meat Provisioners, Freezer and Locker",
        "category_name": "Groceries & Food",
    },
    {
        "mcc_code": "5499",
        "description": "Misc Food Stores/Convenience Stores",
        "category_name": "Groceries & Food",
    },
    # Dining
    {
        "mcc_code": "5812",
        "description": "Eating Places/Restaurants",
        "category_name": "Dining & Restaurants",
    },
    {
        "mcc_code": "5814",
        "description": "Fast Food Restaurants",
        "category_name": "Dining & Restaurants",
    },
    # Transportation
    {
        "mcc_code": "4121",
        "description": "Taxicabs and Limousines",
        "category_name": "Transportation",
    },
    {
        "mcc_code": "4111",
        "description": "Local/Suburban Passenger Transport",
        "category_name": "Transportation",
    },
    # Healthcare
    {
        "mcc_code": "5912",
        "description": "Drug Stores and Pharmacies",
        "category_name": "Healthcare & Medical",
    },
    {
        "mcc_code": "8011",
        "description": "Doctors",
        "category_name": "Healthcare & Medical",
    },
    # Shopping
    {
        "mcc_code": "5311",
        "description": "Department Stores",
        "category_name": "Shopping & Clothing",
    },
    {
        "mcc_code": "5691",
        "description": "Men's and Women's Clothing Stores",
        "category_name": "Shopping & Clothing",
    },
    # Entertainment
    {
        "mcc_code": "7832",
        "description": "Motion Picture Theatres",
        "category_name": "Entertainment",
    },
    # Utilities
    {
        "mcc_code": "4900",
        "description": "Utilities - Electric, Gas, Water",
        "category_name": "Utilities",
    },
    # Travel
    {
        "mcc_code": "7011",
        "description": "Hotels, Motels, Resorts",
        "category_name": "Travel & Vacation",
    },
    {
        "mcc_code": "4112",
        "description": "Passenger Railways",
        "category_name": "Travel & Vacation",
    },
    # Technology
    {
        "mcc_code": "5732",
        "description": "Electronics Stores",
        "category_name": "Technology & Gadgets",
    },
]


async def seed_mcc_codes():
    """Seed MCC codes into database and link to categories."""
    async with async_session_maker() as session:
        # Prepare a map for quick category lookup
        category_map = {}
        categories = await session.execute(select(Category))
        for cat in categories.scalars():
            category_map[cat.name] = cat.id

        # Check if any MCCs already exist
        existing = await session.execute(select(MerchantCategory))
        if existing.scalars().first():
            print("⚠️  Merchant categories already seeded; skipping.")
            return

        objects = []
        for item in MCC_CODES:
            cat_id = category_map.get(item["category_name"])
            if not cat_id:
                print(
                    f"Skipping: {item['mcc_code']} (category '{item['category_name']}' not found)"
                )
                continue

            objects.append(
                MerchantCategory(
                    mcc_code=item["mcc_code"],
                    description=item["description"],
                    suggested_category_id=cat_id,
                )
            )
        session.add_all(objects)
        await session.commit()
        print(f"✅ Seeded {len(objects)} merchant category codes.")


if __name__ == "__main__":
    print("🌱 Seeding merchant category codes...")
    asyncio.run(seed_mcc_codes())
