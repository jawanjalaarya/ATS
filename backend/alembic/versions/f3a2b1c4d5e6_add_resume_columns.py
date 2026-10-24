"""Add resume columns and make name/email nullable for pending_review

Revision ID: f3a2b1c4d5e6
Revises: c818aac227d7
Create Date: 2026-08-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f3a2b1c4d5e6"
down_revision: Union[str, Sequence[str], None] = "c818aac227d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add resume_path and original_filename; make name/email nullable."""
    # SQLite requires batch mode for ALTER COLUMN operations
    with op.batch_alter_table("candidates", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("resume_path", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("original_filename", sa.String(), nullable=True))
        batch_op.alter_column("name", existing_type=sa.String(), nullable=True)
        batch_op.alter_column("email", existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    """Remove resume columns and restore name/email NOT NULL."""
    with op.batch_alter_table("candidates", recreate="always") as batch_op:
        batch_op.drop_column("original_filename")
        batch_op.drop_column("resume_path")
        batch_op.alter_column("name", existing_type=sa.String(), nullable=False)
        batch_op.alter_column("email", existing_type=sa.String(), nullable=False)
