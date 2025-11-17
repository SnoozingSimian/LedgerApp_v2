# alembic/env.py

import os
from logging.config import fileConfig

from sqlalchemy import pool, engine_from_config
from sqlalchemy.engine import Connection

from alembic import context
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set flag so app.database knows we're in Alembic context
os.environ["ALEMBIC_CONFIG"] = "1"

# Import your Base and models
from app.database import Base

# Import all your models so Alembic can detect them
from app.models import *  # This imports everything from __init__.py

# Add other model imports as you create them
# from app.models.category import Category
# from app.models.transaction import Transaction
# etc.

# this is the Alembic Config object
config = context.config

# Convert async URL to sync URL for Alembic
database_url = os.getenv("DATABASE_URL", "")

# Handle both postgresql:// and postgresql+asyncpg:// formats
if "asyncpg" in database_url:
    sync_database_url = database_url.replace(
        "postgresql+asyncpg://", "postgresql+psycopg2://"
    )
elif database_url.startswith("postgresql://"):
    sync_database_url = database_url.replace(
        "postgresql://", "postgresql+psycopg2://", 1
    )
else:
    sync_database_url = database_url

config.set_main_option("sqlalchemy.url", sync_database_url)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for autogeneration
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
