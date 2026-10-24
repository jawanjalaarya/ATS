"""update_jobs_table_structure

Revision ID: 87b87810107b
Revises: a7ff2f5279a2
Create Date: 2026-08-12 21:30:20.110254

"""
from typing import Sequence, Union
import json

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '87b87810107b'
down_revision: Union[str, Sequence[str], None] = 'a7ff2f5279a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Update jobs table structure with individual weight columns and data backfill."""
    # Step 1: Add new columns
    op.add_column('jobs', sa.Column('weight_skills', sa.Integer(), nullable=False, server_default='20'))
    op.add_column('jobs', sa.Column('weight_experience', sa.Integer(), nullable=False, server_default='20'))
    op.add_column('jobs', sa.Column('weight_education', sa.Integer(), nullable=False, server_default='20'))
    op.add_column('jobs', sa.Column('weight_projects', sa.Integer(), nullable=False, server_default='20'))
    op.add_column('jobs', sa.Column('weight_certs', sa.Integer(), nullable=False, server_default='20'))
    op.add_column('jobs', sa.Column('salary_min', sa.Integer(), nullable=True))
    op.add_column('jobs', sa.Column('salary_max', sa.Integer(), nullable=True))
    op.add_column('jobs', sa.Column('archived_at', sa.DateTime(), nullable=True))
    op.add_column('jobs', sa.Column('education_requirement', sa.String(), nullable=False, server_default='none'))
    op.add_column('jobs', sa.Column('required_certs', sa.JSON(), nullable=False, server_default="'[]'"))
    op.add_column('jobs', sa.Column('preferred_certs', sa.JSON(), nullable=False, server_default="'[]'"))

    # Step 2: Backfill existing data
    connection = op.get_bind()
    
    # Update status 'open' to 'active' to match new enum
    connection.execute(text("UPDATE jobs SET status = 'active' WHERE status = 'open'"))
    
    # Backfill data based on existing columns
    result = connection.execute(text("""
        SELECT id, screening_weights, required_education, salary_range, certifications 
        FROM jobs
    """))
    
    jobs = result.fetchall()
    print(f"Backfilling {len(jobs)} existing job records...")
    
    for job in jobs:
        job_id = job[0]
        screening_weights = job[1]
        required_education = job[2]
        salary_range = job[3]
        certifications = job[4]
        
        # Parse screening_weights
        weights = {'skills': 20, 'experience': 20, 'education': 20, 'projects': 20, 'certifications': 20}
        if screening_weights:
            try:
                if isinstance(screening_weights, str):
                    weights_data = json.loads(screening_weights)
                else:
                    weights_data = screening_weights
                    
                if isinstance(weights_data, dict):
                    weights.update({
                        'skills': weights_data.get('skills', 20),
                        'experience': weights_data.get('experience', 20),
                        'education': weights_data.get('education', 20),
                        'projects': weights_data.get('projects', 20),
                        'certifications': weights_data.get('certifications', 20)
                    })
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Map education
        edu_mapping = {
            'high_school': 'high_school',
            'associate': 'associate', 
            'bachelor': 'bachelor',
            'master': 'master',
            'phd': 'phd'
        }
        education_req = edu_mapping.get(required_education, 'none')
        
        # Parse salary range
        salary_min, salary_max = None, None
        if salary_range and isinstance(salary_range, str):
            import re
            match = re.search(r'(\d+)(?:,?\d+)*\s*-\s*(\d+)(?:,?\d+)*', salary_range)
            if match:
                try:
                    salary_min = int(match.group(1).replace(',', ''))
                    salary_max = int(match.group(2).replace(',', ''))
                except ValueError:
                    pass
        
        # Handle certifications -> required_certs
        required_certs_val = '[]'
        if certifications:
            try:
                if isinstance(certifications, str):
                    # Validate it's valid JSON
                    json.loads(certifications)
                    required_certs_val = certifications
                else:
                    required_certs_val = json.dumps(certifications)
            except (json.JSONDecodeError, TypeError):
                required_certs_val = '[]'
        
        # Update with backfilled data
        connection.execute(text("""
            UPDATE jobs 
            SET weight_skills = :weight_skills,
                weight_experience = :weight_experience,
                weight_education = :weight_education,
                weight_projects = :weight_projects,
                weight_certs = :weight_certs,
                education_requirement = :education_requirement,
                salary_min = :salary_min,
                salary_max = :salary_max,
                required_certs = :required_certs
            WHERE id = :job_id
        """), {
            'job_id': job_id,
            'weight_skills': weights['skills'],
            'weight_experience': weights['experience'],
            'weight_education': weights['education'],
            'weight_projects': weights['projects'],
            'weight_certs': weights['certifications'],
            'education_requirement': education_req,
            'salary_min': salary_min,
            'salary_max': salary_max,
            'required_certs': required_certs_val
        })
    
    print(f"Backfill completed for {len(jobs)} jobs")
    print("Migration completed successfully")


def downgrade() -> None:
    """Downgrade to original structure."""
    # Remove new columns
    op.drop_column('jobs', 'weight_skills')
    op.drop_column('jobs', 'weight_experience')
    op.drop_column('jobs', 'weight_education')
    op.drop_column('jobs', 'weight_projects')
    op.drop_column('jobs', 'weight_certs')
    op.drop_column('jobs', 'salary_min')
    op.drop_column('jobs', 'salary_max')
    op.drop_column('jobs', 'archived_at')
    op.drop_column('jobs', 'education_requirement')
    op.drop_column('jobs', 'required_certs')
    op.drop_column('jobs', 'preferred_certs')
    
    # Restore original status values
    connection = op.get_bind()
    connection.execute(text("UPDATE jobs SET status = 'open' WHERE status = 'active'"))
