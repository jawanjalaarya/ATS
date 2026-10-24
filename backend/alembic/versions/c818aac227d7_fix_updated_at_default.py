"""fix_updated_at_default

Revision ID: c818aac227d7
Revises: ad81c3c9b483
Create Date: 2026-08-12 21:57:12.620729

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c818aac227d7'
down_revision: Union[str, Sequence[str], None] = 'ad81c3c9b483'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add server_default to updated_at column."""
    # SQLite doesn't support ALTER COLUMN, so we need to use batch operations
    with op.batch_alter_table('jobs', recreate='always') as batch_op:
        batch_op.alter_column(
            'updated_at',
            existing_type=sa.DateTime(),
            server_default=sa.func.now(),
            existing_nullable=True
        )


def downgrade() -> None:
    """Remove server_default from updated_at column."""
    # Remove server default
    with op.batch_alter_table('jobs', recreate='always') as batch_op:
        batch_op.alter_column(
            'updated_at',
            existing_type=sa.DateTime(),
            server_default=None,
            existing_nullable=True
        )
