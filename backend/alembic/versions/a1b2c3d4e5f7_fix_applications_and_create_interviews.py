"""fix applications schema and create interviews table

Revision ID: a1b2c3d4e5f7
Revises: f3a2b1c4d5e6
Create Date: 2026-08-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f7"
down_revision: Union[str, Sequence[str], None] = "f3a2b1c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix applications table schema and create interviews table."""

    # --- Fix applications table ---
    # Rename application_date -> created_at, add updated_at, drop legacy columns
    with op.batch_alter_table("applications", recreate="always") as batch_op:
        # Keep: id, job_id, candidate_id, status
        # Rename: application_date -> created_at
        # Add: updated_at
        # Drop: match_score, notes (moved to screening_results)
        batch_op.drop_column("match_score")
        batch_op.drop_column("notes")
        batch_op.alter_column(
            "application_date",
            new_column_name="created_at",
            existing_type=sa.DateTime(),
            server_default=sa.func.now(),
        )
        batch_op.alter_column(
            "status",
            existing_type=sa.String(),
            nullable=False,
            server_default="applied",
        )
        batch_op.add_column(
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now())
        )

    # --- Create interviews table ---
    op.create_table(
        "interviews",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("application_id", sa.Integer(), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("candidate_id", sa.Integer(), sa.ForeignKey("candidates.id"), nullable=False, index=True),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("interviewer_name", sa.String(), nullable=False),
        sa.Column("interviewer_email", sa.String(), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="scheduled"),
        sa.Column("questions", sa.JSON(), server_default="[]"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    """Reverse: drop interviews table and restore applications legacy columns."""
    op.drop_table("interviews")

    with op.batch_alter_table("applications", recreate="always") as batch_op:
        batch_op.drop_column("updated_at")
        batch_op.alter_column(
            "created_at",
            new_column_name="application_date",
            existing_type=sa.DateTime(),
        )
        batch_op.add_column(sa.Column("match_score", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("notes", sa.Text(), nullable=True))
