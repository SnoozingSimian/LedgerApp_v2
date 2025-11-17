# app/database.py

import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Base class for models (this is what Alembic needs)
Base = declarative_base()

# Only create async engine if not running in Alembic context
if not os.getenv("ALEMBIC_CONFIG"):
    # Ensure we're using asyncpg driver for async operations
    if DATABASE_URL.startswith("postgresql://") and "asyncpg" not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

    # Remove any parameters that asyncpg doesn't support
    # Keep only the base URL and add ssl=true if needed
    if "?" in DATABASE_URL:
        base_url = DATABASE_URL.split("?")[0]
        DATABASE_URL = base_url

    # Create async engine with explicit connect_args for asyncpg
    engine = create_async_engine(
        DATABASE_URL,
        echo=True,  # Set to False in production
        future=True,
        pool_size=20,
        max_overflow=0,
        connect_args={
            "ssl": "require",  # Neon requires SSL
            "server_settings": {"application_name": "LedgerApp_v2"},
        },
    )

    # Create async session factory
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    # Dependency to get database session
    async def get_session() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_maker() as session:
            try:
                yield session
            finally:
                await session.close()

else:
    # Running in Alembic context - don't create async engine
    engine = None
    async_session_maker = None

    async def get_session():
        raise RuntimeError("Cannot use async session in Alembic migration context")
