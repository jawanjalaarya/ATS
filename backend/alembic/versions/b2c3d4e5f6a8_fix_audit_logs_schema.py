"""fix audit_logs table schema to match model

Revision ID: b2c3d4e5f6a8
Revises: a1b2c3d4e5f7
Create Date: 2026-08-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a8"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rebuild audit_logs table to match the AuditLog model."""
    # Recreate the table with correct schema
    # Old: id, action, entity_type, entity_id, actor, timestamp, action_metadata
    # New: id, user_id, user_email, action, resource_type, resource_id, metadata, created_at
    with op.batch_alter_table("audit_logs", recreate="always") as batch_op:
        # Drop old columns
        batch_op.drop_column("entity_type")
        batch_op.drop_column("entity_id")
        batch_op.drop_column("actor")
        batch_op.drop_column("timestamp")
        batch_op.drop_column("action_metadata")
        # Add new columns
        batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("user_email", sa.String(), nullable=False, server_default="system"))
        batch_op.add_column(sa.Column("resource_type", sa.String(), nullable=False, server_default="unknown"))
        batch_op.add_column(sa.Column("resource_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("metadata", sa.JSON(), server_default="{}"))
        batch_op.add_column(sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()))


def downgrade() -> None:
    """Restore original audit_logs schema."""
    with op.batch_alter_table("audit_logs", recreate="always") as batch_op:
        batch_op.drop_column("user_id")
        batch_op.drop_column("user_email")
        batch_op.drop_column("resource_type")
        batch_op.drop_column("resource_id")
        batch_op.drop_column("metadata")
        batch_op.drop_column("created_at")
        batch_op.add_column(sa.Column("entity_type", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("entity_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("actor", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("timestamp", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("action_metadata", sa.JSON(), nullable=True))
