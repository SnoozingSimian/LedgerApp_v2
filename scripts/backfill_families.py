# scripts/backfill_families.py
"""
Backfill script to create Personal families for all existing users
and migrate their data.

Run this after:
1. Creating FamilyInvite model
2. Adding family_id and active_family_id columns
3. Adding relationships

Usage:
    python -m scripts.backfill_families
"""
# Import models
from app.models.user import User
from app.models.family import Family, FamilyMember
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.models.asset import Asset
from app.models.credit_source import CreditSource
from app.models.income_stream import IncomeStream
from app.models.financial_goal import FinancialGoal

import asyncio
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def backfill_families():
    """Create Personal families for all users and migrate data."""

    # Get database URL
    database_url = os.getenv(
        "DATABASE_URL", "sqlite+aiosqlite:///./test.db"
    )

    # Create engine
    engine = create_async_engine(database_url, echo=False)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        logger.info("Starting family backfill...")

        # Get all users
        result = await session.execute(select(User))
        users = result.scalars().all()

        logger.info(f"Found {len(users)} users to process")

        created_count = 0

        for user in users:
            # Check if user already has families
            result = await session.execute(
                select(FamilyMember).where(
                    FamilyMember.user_id == user.id
                )
            )
            existing_members = result.scalars().all()

            if existing_members:
                logger.info(
                    f"User {user.email} already has {len(existing_members)} family(ies), skipping"
                )
                continue

            # Create Personal family
            personal_family = Family(
                name=f"Personal - {user.full_name}",
                created_by=user.id,
                created_at=user.created_at or datetime.utcnow(),
            )
            session.add(personal_family)
            await session.flush()

            # Add user as admin
            family_member = FamilyMember(
                family_id=personal_family.id,
                user_id=user.id,
                role="admin",
                joined_at=user.created_at or datetime.utcnow(),
            )
            session.add(family_member)

            # Set as active family
            user.active_family_id = personal_family.id

            # Migrate all user's data
            result = await session.execute(
                select(Transaction).where(Transaction.user_id == user.id)
            )
            transactions = result.scalars().all()
            for txn in transactions:
                txn.family_id = personal_family.id

            result = await session.execute(
                select(Budget).where(Budget.user_id == user.id)
            )
            budgets = result.scalars().all()
            for budget in budgets:
                budget.family_id = personal_family.id

            result = await session.execute(
                select(CreditSource).where(
                    CreditSource.user_id == user.id
                )
            )
            credit_sources = result.scalars().all()
            for cs in credit_sources:
                cs.family_id = personal_family.id

            result = await session.execute(
                select(Asset).where(Asset.user_id == user.id)
            )
            assets = result.scalars().all()
            for asset in assets:
                asset.family_id = personal_family.id

            result = await session.execute(
                select(IncomeStream).where(
                    IncomeStream.user_id == user.id
                )
            )
            income_streams = result.scalars().all()
            for stream in income_streams:
                stream.family_id = personal_family.id

            result = await session.execute(
                select(FinancialGoal).where(
                    FinancialGoal.user_id == user.id
                )
            )
            goals = result.scalars().all()
            for goal in goals:
                goal.family_id = personal_family.id

            created_count += 1
            logger.info(
                f"Created Personal family for {user.email} with ID {personal_family.id}"
            )

        await session.commit()

        # Verify
        result = await session.execute(
            select(Family).where(Family.created_by.in_(
                [u.id for u in users]
            ))
        )
        total_families = len(result.scalars().all())

        logger.info("✓ Backfill complete!")
        logger.info(f"  - Created families: {created_count}")
        logger.info(f"  - Total personal families: {total_families}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(backfill_families())