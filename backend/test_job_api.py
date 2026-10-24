#!/usr/bin/env python3
"""Comprehensive test for job creation via API."""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

# Step 1: Login as recruiter
print("=" * 60)
print("Step 1: Logging in as recruiter")
print("=" * 60)

login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"email": "recruiter@example.com", "password": "recruiter123"},
    cookies={}
)

if login_response.status_code == 200:
    print("✓ Login successful")
    cookies = login_response.cookies
else:
    print(f"✗ Login failed: {login_response.status_code}")
    print(login_response.text)
    exit(1)

# Step 2: Create a draft job
print("\n" + "=" * 60)
print("Step 2: Creating a DRAFT job (weights don't need to sum to 100%)")
print("=" * 60)

draft_job_data = {
    "title": "Backend Engineer - Draft",
    "department": "Engineering",
    "description": "Build robust backend systems with Python and FastAPI",
    "location": "Remote",
    "work_mode": "remote",
    "employment_type": "full-time",
    "min_experience": 2,
    "max_experience": 5,
    "education_requirement": "bachelor",
    "status": "draft",
    # Note: salary fields are optional - let's not send them
    # Default weights: 20% each (totals 100%, but that's fine for draft)
}

print(f"\nSending draft job data:\n{json.dumps(draft_job_data, indent=2)}")

draft_response = requests.post(
    f"{BASE_URL}/jobs/",
    json=draft_job_data,
    cookies=cookies
)

if draft_response.status_code in [200, 201]:
    draft_job = draft_response.json()
    print(f"\n✓ Draft job created successfully!")
    print(f"  Job ID: {draft_job['id']}")
    print(f"  Title: {draft_job['title']}")
    print(f"  Status: {draft_job['status']}")
    print(f"  Weights - Skills: {draft_job['weight_skills']}, Experience: {draft_job['weight_experience']}, "
          f"Education: {draft_job['weight_education']}, Projects: {draft_job['weight_projects']}, "
          f"Certs: {draft_job['weight_certs']}")
else:
    print(f"✗ Draft job creation failed: {draft_response.status_code}")
    print(f"Response: {draft_response.text}")
    exit(1)

# Step 3: Create an active job with proper weights
print("\n" + "=" * 60)
print("Step 3: Creating an ACTIVE job (weights MUST sum to 100%)")
print("=" * 60)

active_job_data = {
    "title": "Frontend Engineer - Active",
    "department": "Engineering",
    "description": "Build beautiful and responsive user interfaces with React and TypeScript",
    "location": "San Francisco, CA",
    "work_mode": "hybrid",
    "employment_type": "full-time",
    "min_experience": 1,
    "max_experience": 4,
    "education_requirement": "bachelor",
    "salary_min": 80000,
    "salary_max": 130000,
    "status": "active",
    "weight_skills": 30,
    "weight_experience": 25,
    "weight_education": 15,
    "weight_projects": 20,
    "weight_certs": 10,  # Total: 100%
    "required_skills": ["JavaScript", "React", "TypeScript"],
    "preferred_skills": ["Vue.js", "GraphQL"],
    "required_certs": [],
    "preferred_certs": ["AWS Solutions Architect"]
}

print(f"\nSending active job data:\n{json.dumps(active_job_data, indent=2)}")

active_response = requests.post(
    f"{BASE_URL}/jobs/",
    json=active_job_data,
    cookies=cookies
)

if active_response.status_code in [200, 201]:
    active_job = active_response.json()
    print(f"\n✓ Active job created successfully!")
    print(f"  Job ID: {active_job['id']}")
    print(f"  Title: {active_job['title']}")
    print(f"  Status: {active_job['status']}")
    print(f"  Salary: ${active_job['salary_min']:,} - ${active_job['salary_max']:,}")
    print(f"  Weights total: {active_job['weight_skills'] + active_job['weight_experience'] + active_job['weight_education'] + active_job['weight_projects'] + active_job['weight_certs']}%")
else:
    print(f"✗ Active job creation failed: {active_response.status_code}")
    print(f"Response: {active_response.text}")
    exit(1)

# Step 4: Try to create an active job with invalid weights
print("\n" + "=" * 60)
print("Step 4: Attempting INVALID active job (weights don't sum to 100%)")
print("=" * 60)

invalid_job_data = {
    "title": "Invalid Active Job",
    "department": "Engineering",
    "description": "This should fail",
    "location": "Remote",
    "work_mode": "remote",
    "employment_type": "full-time",
    "min_experience": 0,
    "max_experience": 1,
    "education_requirement": "none",
    "status": "active",
    "weight_skills": 25,
    "weight_experience": 25,
    "weight_education": 25,
    "weight_projects": 20,
    "weight_certs": 5,  # Total: 100% - actually this is valid! Let me make it invalid
}

invalid_job_data["weight_certs"] = 4  # Now total is 99%

print(f"\nSending invalid job data (weights sum to 99%):")
invalid_response = requests.post(
    f"{BASE_URL}/jobs/",
    json=invalid_job_data,
    cookies=cookies
)

if invalid_response.status_code == 422:
    error_data = invalid_response.json()
    print(f"✓ Correctly rejected! Error: {error_data.get('detail', error_data)}")
elif invalid_response.status_code in [200, 201]:
    print(f"✗ ERROR: Should have rejected but succeeded!")
    print(f"Response: {invalid_response.json()}")
else:
    print(f"? Unexpected status code: {invalid_response.status_code}")
    print(f"Response: {invalid_response.text}")

print("\n" + "=" * 60)
print("All tests completed!")
print("=" * 60)
