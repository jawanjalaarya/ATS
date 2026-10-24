"""remove_legacy_job_columns

Revision ID: ad81c3c9b483
Revises: 87b87810107b
Create Date: 2026-08-12 21:36:44.080480

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ad81c3c9b483'
down_revision: Union[str, Sequence[str], None] = '87b87810107b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove legacy columns after successful backfill migration."""
    # Verify backfill completed successfully before dropping legacy columns
    conn = op.get_bind()
    
    # Check that new columns are populated for all rows
    result = conn.execute(sa.text("""
        SELECT COUNT(*) FROM jobs 
        WHERE weight_skills IS NULL OR weight_experience IS NULL OR weight_education IS NULL 
        OR weight_projects IS NULL OR weight_certs IS NULL OR education_requirement IS NULL
    """))
    
    if result.scalar() > 0:
        raise Exception("Cannot drop legacy columns: new columns contain NULL values")
    
    # Use batch_alter_table for SQLite compatibility
    with op.batch_alter_table('jobs', recreate='always') as batch_op:
        # Drop the four legacy columns that have been superseded
        batch_op.drop_column('screening_weights')
        batch_op.drop_column('certifications') 
        batch_op.drop_column('required_education')
        batch_op.drop_column('salary_range')


def downgrade() -> None:
    """Recreate legacy columns (lossy downgrade - data will be NULL)."""
    with op.batch_alter_table('jobs', recreate='always') as batch_op:
        # Recreate the legacy columns with NULL values (lossy but structurally valid)
        batch_op.add_column(sa.Column('screening_weights', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('certifications', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('required_education', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('salary_range', sa.String(), nullable=True))
