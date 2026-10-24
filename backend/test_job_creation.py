#!/usr/bin/env python3
"""Quick test to verify job creation works."""

import json
from app.core.security import create_access_token
from app.models.user import User
from app.core.database import SessionLocal

# Create a test token
token = create_access_token(data={"sub": "recruiter@example.com"})

# Minimal job data (draft status, should not require weights to sum to 100)
job_data = {
    "title": "Test Backend Developer",
    "department": "Engineering",
    "description": "Build robust backend systems",
    "location": "Remote",
    "work_mode": "remote",
    "employment_type": "full-time",
    "min_experience": 2,
    "max_experience": 5,
    "education_requirement": "bachelor",
    "salary_min": 70000,
    "salary_max": 100000,
    "status": "draft",
}

print("Job data to send:")
print(json.dumps(job_data, indent=2))

# Test importing and validating with Pydantic
from app.schemas.job import JobCreate

try:
    validated = JobCreate(**job_data)
    print("\n✓ Validation passed!")
    print(f"Validated data:\n{validated.model_dump(mode='json')}")
except Exception as e:
    print(f"\n✗ Validation failed: {e}")
