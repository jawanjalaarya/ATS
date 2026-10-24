#!/usr/bin/env python3
"""Test the list jobs endpoint."""

import requests

BASE_URL = "http://localhost:8000/api/v1"

# Step 1: Login as recruiter
print("=" * 60)
print("Testing List Jobs Endpoint")
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
    exit(1)

# Step 2: List jobs
print("\nListing all jobs...")
list_response = requests.get(
    f"{BASE_URL}/jobs/",
    cookies=cookies
)

if list_response.status_code == 200:
    data = list_response.json()
    print(f"✓ Successfully retrieved jobs!")
    print(f"  Total jobs: {data['total']}")
    print(f"  Jobs returned in this page: {len(data['items'])}")
    
    if data['items']:
        first_job = data['items'][0]
        print(f"\n  First job:")
        print(f"    ID: {first_job['id']}")
        print(f"    Title: {first_job['title']}")
        print(f"    Status: {first_job['status']}")
        print(f"    Created: {first_job['created_at']}")
        print(f"    Updated: {first_job['updated_at']}")
else:
    print(f"✗ Failed to list jobs: {list_response.status_code}")
    print(f"Response: {list_response.text}")
    exit(1)

print("\n" + "=" * 60)
print("✓ All tests passed!")
print("=" * 60)
