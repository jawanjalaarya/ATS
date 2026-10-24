"""create system_settings table

Revision ID: c3d4e5f6a7b9
Revises: b2c3d4e5f6a8
Create Date: 2026-08-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b9"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create system_settings table and seed default values."""
    op.create_table(
        "system_settings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("key", sa.String(), unique=True, nullable=False, index=True),
        sa.Column("value", sa.String(), nullable=False, server_default=""),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Seed the anonymous_screening default
    conn = op.get_bind()
    conn.execute(
        sa.text("INSERT INTO system_settings (key, value) VALUES ('anonymous_screening', 'false')")
    )


def downgrade() -> None:
    """Drop system_settings table."""
    op.drop_table("system_settings")
