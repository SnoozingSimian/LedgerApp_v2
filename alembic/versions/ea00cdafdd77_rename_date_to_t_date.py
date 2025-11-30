"""rename_date_to_t_date

Revision ID: ea00cdafdd77
Revises: 9380119a1fda
Create Date: 2025-11-19 13:50:30.181434

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ea00cdafdd77"
down_revision: Union[str, None] = "9380119a1fda"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Rename column
    op.alter_column("transactions", "date", new_column_name="t_date")


def downgrade():
    # Revert column name
    op.alter_column("transactions", "t_date", new_column_name="date")
