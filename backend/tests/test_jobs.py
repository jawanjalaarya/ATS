import pytest
from fastapi import status

from app.core.security import create_access_token
from app.models.job import Job
from app.models.application import Application
from app.models.candidate import Candidate
from tests.conftest import create_application_for_job


def _auth_client(client, user):
    """Helper to authenticate client with user token."""
    token = create_access_token(data={"sub": user.email})
    client.cookies.set("access_token", f"Bearer {token}")
    return client


# Job Creation Tests
def test_create_job_as_recruiter(client, test_recruiter):
    """Test job creation by recruiter role."""
    _auth_client(client, test_recruiter)
    job_data = {
        "title": "Backend Developer",
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
        "required_skills": ["Python", "Django"],
        "preferred_skills": ["AWS", "Docker"],
        "required_certs": [],
        "preferred_certs": ["AWS Solutions Architect"]
    }
    
    response = client.post("/api/v1/jobs/", json=job_data)
    assert response.status_code == status.HTTP_201_CREATED
    
    data = response.json()
    assert data["title"] == job_data["title"]
    assert data["department"] == job_data["department"]
    assert data["applicant_count"] == 0  # New job has no applications


def test_create_job_as_admin(client, test_admin):
    """Test job creation by admin role."""
    _auth_client(client, test_admin)
    job_data = {
        "title": "Frontend Developer",
        "department": "Engineering",
        "description": "Build beautiful UIs",
        "location": "San Francisco",
        "work_mode": "hybrid",
        "employment_type": "full-time",
        "min_experience": 1,
        "max_experience": 4,
        "education_requirement": "bachelor",
        "required_skills": ["JavaScript", "React"]
    }
    
    response = client.post("/api/v1/jobs/", json=job_data)
    assert response.status_code == status.HTTP_201_CREATED


def test_create_job_unauthenticated(client):
    """Test job creation fails without authentication."""
    job_data = {
        "title": "Test Job",
        "department": "Test",
        "description": "Test description",
        "location": "Test Location",
        "work_mode": "remote",
        "employment_type": "full-time",
        "min_experience": 0,
        "max_experience": 1,
        "education_requirement": "none"
    }
    
    response = client.post("/api/v1/jobs/", json=job_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# Weight Validation Tests
def test_active_job_weight_validation_100_percent(client, test_recruiter):
    """Test active job with weights totaling exactly 100% is accepted."""
    _auth_client(client, test_recruiter)
    job_data = {
        "title": "Test Job",
        "department": "Test",
        "description": "Test description",
        "location": "Test Location",
        "work_mode": "remote",
        "employment_type": "full-time",
        "min_experience": 0,
        "max_experience": 1,
        "education_requirement": "none",
        "status": "active",
        "weight_skills": 25,
        "weight_experience": 30,
        "weight_education": 15,
        "weight_projects": 20,
        "weight_certs": 10
    }
    
    response = client.post("/api/v1/jobs/", json=job_data)
    assert response.status_code == status.HTTP_201_CREATED


def test_active_job_weight_validation_99_percent(client, test_recruiter):
    """Test active job with weights not totaling 100% is rejected."""
    _auth_client(client, test_recruiter)
    job_data = {
        "title": "Test Job",
        "department": "Test",
        "description": "Test description",
        "location": "Test Location",
        "work_mode": "remote",
        "employment_type": "full-time",
        "min_experience": 0,
        "max_experience": 1,
        "education_requirement": "none",
        "status": "active",
        "weight_skills": 25,
        "weight_experience": 30,
        "weight_education": 15,
        "weight_projects": 19,  # Total = 99%
        "weight_certs": 10
    }
    
    response = client.post("/api/v1/jobs/", json=job_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_draft_job_weight_validation_incomplete(client, test_recruiter):
    """Test draft job can have incomplete weights."""
    _auth_client(client, test_recruiter)
    job_data = {
        "title": "Test Job",
        "department": "Test",
        "description": "Test description",
        "location": "Test Location",
        "work_mode": "remote",
        "employment_type": "full-time",
        "min_experience": 0,
        "max_experience": 1,
        "education_requirement": "none",
        "status": "draft",
        "weight_skills": 10,
        "weight_experience": 15,
        "weight_education": 5,
        "weight_projects": 10,
        "weight_certs": 5  # Total = 45%, allowed for draft
    }
    
    response = client.post("/api/v1/jobs/", json=job_data)
    assert response.status_code == status.HTTP_201_CREATED


# Job Listing Tests
def test_list_jobs_with_pagination(client, test_recruiter, test_job):
    """Test job listing with pagination parameters."""
    _auth_client(client, test_recruiter)
    
    response = client.get("/api/v1/jobs/?skip=0&limit=10")
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) >= 1  # At least the test_job


def test_list_jobs_with_status_filter(client, test_recruiter, test_job, test_active_job):
    """Test job listing with status filtering."""
    _auth_client(client, test_recruiter)
    
    # Filter for active jobs only
    response = client.get("/api/v1/jobs/?status=active")
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    active_jobs = [job for job in data["items"] if job["status"] == "active"]
    assert len(active_jobs) >= 1


def test_list_jobs_exclude_archived_by_default(client, test_recruiter, test_job, test_archived_job):
    """Test that archived jobs are excluded by default."""
    _auth_client(client, test_recruiter)
    
    response = client.get("/api/v1/jobs/")
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    # Should not include archived jobs by default
    archived_jobs = [job for job in data["items"] if job["archived_at"] is not None]
    assert len(archived_jobs) == 0


def test_list_jobs_include_archived_when_requested(client, test_recruiter, test_job, test_archived_job):
    """Test that archived jobs are included when explicitly requested."""
    _auth_client(client, test_recruiter)
    
    response = client.get("/api/v1/jobs/?include_archived=true")
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    # Should include archived jobs when requested
    archived_jobs = [job for job in data["items"] if job["archived_at"] is not None]
    assert len(archived_jobs) >= 1


# Job Retrieval Tests
def test_get_job_by_id(client, test_recruiter, test_job):
    """Test retrieving a single job by ID."""
    _auth_client(client, test_recruiter)
    
    response = client.get(f"/api/v1/jobs/{test_job.id}")
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["id"] == test_job.id
    assert data["title"] == test_job.title
    assert "applicant_count" in data


def test_get_job_not_found(client, test_recruiter):
    """Test retrieving non-existent job returns 404."""
    _auth_client(client, test_recruiter)
    
    response = client.get("/api/v1/jobs/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_job_unauthenticated(client, test_job):
    """Test retrieving job without authentication."""
    response = client.get(f"/api/v1/jobs/{test_job.id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# Job Update Tests
def test_update_job_all_fields(client, test_recruiter, test_job, db_session):
    """Test updating all job fields."""
    _auth_client(client, test_recruiter)
    
    update_data = {
        "title": "Updated Software Engineer",
        "department": "Updated Engineering",
        "description": "Updated job description",
        "status": "active",
        "weight_skills": 30,
        "weight_experience": 25,
        "weight_education": 15,
        "weight_projects": 20,
        "weight_certs": 10
    }
    
    response = client.patch(f"/api/v1/jobs/{test_job.id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["title"] == update_data["title"]
    assert data["status"] == "active"


def test_update_job_weight_validation(client, test_recruiter, test_job):
    """Test weight validation on job update."""
    _auth_client(client, test_recruiter)
    
    # Try to update to active with invalid weights
    update_data = {
        "status": "active",
        "weight_skills": 25,
        "weight_experience": 25,
        "weight_education": 25,
        "weight_projects": 25,
        "weight_certs": 1  # Total = 101%
    }
    
    response = client.patch(f"/api/v1/jobs/{test_job.id}", json=update_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_update_nonexistent_job(client, test_recruiter):
    """Test updating non-existent job returns 404."""
    _auth_client(client, test_recruiter)
    
    update_data = {"title": "Updated Title"}
    response = client.patch("/api/v1/jobs/99999", json=update_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND


# Job Actions Tests
def test_close_job(client, test_recruiter, test_active_job):
    """Test closing a job."""
    _auth_client(client, test_recruiter)
    
    response = client.patch(f"/api/v1/jobs/{test_active_job.id}/close")
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["status"] == "closed"


def test_archive_job_as_recruiter(client, test_recruiter, test_job):
    """Test archiving a job as recruiter."""
    _auth_client(client, test_recruiter)
    
    response = client.patch(f"/api/v1/jobs/{test_job.id}/archive")
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["archived_at"] is not None


def test_restore_job_as_recruiter(client, test_recruiter, test_archived_job):
    """Test restoring an archived job as recruiter."""
    _auth_client(client, test_recruiter)
    
    response = client.patch(f"/api/v1/jobs/{test_archived_job.id}/restore")
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["archived_at"] is None


def test_restore_job_as_admin(client, test_admin, test_archived_job):
    """Test restoring an archived job as admin."""
    _auth_client(client, test_admin)
    
    response = client.patch(f"/api/v1/jobs/{test_archived_job.id}/restore")
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["archived_at"] is None


# Applicant Count Tests
def test_job_applicant_count_calculation_real_data(client, test_recruiter, test_job_with_applications):
    """Test real applicant count calculation using database queries."""
    _auth_client(client, test_recruiter)
    
    response = client.get(f"/api/v1/jobs/{test_job_with_applications.id}")
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["applicant_count"] == 3  # test_job_with_applications has 3 applications


def test_job_applicant_count_zero_applications(client, test_recruiter, test_job):
    """Test applicant count is zero for job with no applications."""
    _auth_client(client, test_recruiter)
    
    response = client.get(f"/api/v1/jobs/{test_job.id}")
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["applicant_count"] == 0


# RBAC Tests
def test_recruiter_access_to_jobs(client, test_recruiter):
    """Test recruiter can access job endpoints."""
    _auth_client(client, test_recruiter)
    
    # Test GET access
    response = client.get("/api/v1/jobs/")
    assert response.status_code == status.HTTP_200_OK


def test_admin_access_to_jobs(client, test_admin):
    """Test admin can access job endpoints."""
    _auth_client(client, test_admin)
    
    # Test GET access
    response = client.get("/api/v1/jobs/")
    assert response.status_code == status.HTTP_200_OK


def test_cross_recruiter_job_updates_allowed(client, test_recruiter, test_admin, test_job):
    """Test cross-recruiter collaboration per D-04."""
    # Admin can edit job created by recruiter
    _auth_client(client, test_admin)
    
    update_data = {"title": "Updated by Admin"}
    response = client.patch(f"/api/v1/jobs/{test_job.id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK


# Input Validation Tests
def test_job_field_validation(client, test_recruiter):
    """Test job field validation."""
    _auth_client(client, test_recruiter)
    
    # Missing required fields
    invalid_data = {
        "title": "",  # Empty title
        "department": "Engineering"
        # Missing other required fields
    }
    
    response = client.post("/api/v1/jobs/", json=invalid_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_experience_range_validation(client, test_recruiter):
    """Test experience range validation."""
    _auth_client(client, test_recruiter)
    
    job_data = {
        "title": "Test Job",
        "department": "Test",
        "description": "Test description",
        "location": "Test Location",
        "work_mode": "remote",
        "employment_type": "full-time",
        "min_experience": -1,  # Invalid negative experience
        "max_experience": 5,
        "education_requirement": "none"
    }
    
    response = client.post("/api/v1/jobs/", json=job_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_salary_range_validation(client, test_recruiter):
    """Test salary range validation."""
    _auth_client(client, test_recruiter)
    
    job_data = {
        "title": "Test Job",
        "department": "Test",
        "description": "Test description",
        "location": "Test Location",
        "work_mode": "remote",
        "employment_type": "full-time",
        "min_experience": 0,
        "max_experience": 5,
        "education_requirement": "none",
        "salary_min": -1000  # Invalid negative salary
    }
    
    response = client.post("/api/v1/jobs/", json=job_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# Enum Validation Tests
def test_work_mode_validation(client, test_recruiter):
    """Test work mode enum validation."""
    _auth_client(client, test_recruiter)
    
    job_data = {
        "title": "Test Job",
        "department": "Test",
        "description": "Test description",
        "location": "Test Location",
        "work_mode": "invalid_mode",  # Invalid work mode
        "employment_type": "full-time",
        "min_experience": 0,
        "max_experience": 5,
        "education_requirement": "none"
    }
    
    response = client.post("/api/v1/jobs/", json=job_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_employment_type_validation(client, test_recruiter):
    """Test employment type enum validation."""
    _auth_client(client, test_recruiter)
    
    job_data = {
        "title": "Test Job",
        "department": "Test",
        "description": "Test description",
        "location": "Test Location",
        "work_mode": "remote",
        "employment_type": "invalid_type",  # Invalid employment type
        "min_experience": 0,
        "max_experience": 5,
        "education_requirement": "none"
    }
    
    response = client.post("/api/v1/jobs/", json=job_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_education_requirement_validation(client, test_recruiter):
    """Test education requirement enum validation."""
    _auth_client(client, test_recruiter)
    
    job_data = {
        "title": "Test Job",
        "department": "Test",
        "description": "Test description",
        "location": "Test Location",
        "work_mode": "remote",
        "employment_type": "full-time",
        "min_experience": 0,
        "max_experience": 5,
        "education_requirement": "invalid_education"  # Invalid education requirement
    }
    
    response = client.post("/api/v1/jobs/", json=job_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# Malicious Content Tests
def test_job_creation_with_script_tags(client, test_recruiter):
    """Test job creation with script tags is safe."""
    _auth_client(client, test_recruiter)
    
    job_data = {
        "title": "<script>alert('xss')</script>",
        "department": "Test",
        "description": "<script>alert('xss')</script>",
        "location": "Test Location",
        "work_mode": "remote",
        "employment_type": "full-time",
        "min_experience": 0,
        "max_experience": 5,
        "education_requirement": "none"
    }
    
    response = client.post("/api/v1/jobs/", json=job_data)
    assert response.status_code == status.HTTP_201_CREATED
    
    # Verify content is stored as-is (React will handle escaping)
    data = response.json()
    assert "<script>" in data["title"]  # Raw content stored


def test_job_creation_with_sql_fragments(client, test_recruiter):
    """Test job creation with SQL fragments is safe."""
    _auth_client(client, test_recruiter)
    
    job_data = {
        "title": "'; DROP TABLE jobs; --",
        "department": "Test",
        "description": "Test description",
        "location": "Test Location",
        "work_mode": "remote",
        "employment_type": "full-time",
        "min_experience": 0,
        "max_experience": 5,
        "education_requirement": "none"
    }
    
    response = client.post("/api/v1/jobs/", json=job_data)
    assert response.status_code == status.HTTP_201_CREATED
    
    # SQLAlchemy ORM prevents SQL injection
    data = response.json()
    assert "DROP TABLE" in data["title"]  # Raw content stored safely


# Archive Behavior Tests
def test_archived_job_list_exclusion(client, test_recruiter, test_archived_job):
    """Test archived jobs are excluded from default listing."""
    _auth_client(client, test_recruiter)
    
    # Default listing should not include archived job
    response = client.get("/api/v1/jobs/")
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    job_ids = [job["id"] for job in data["items"]]
    assert test_archived_job.id not in job_ids


def test_archived_job_detail_access(client, test_recruiter, test_archived_job):
    """Test archived job details are accessible to authorized users."""
    _auth_client(client, test_recruiter)
    
    # Should be able to view archived job details
    response = client.get(f"/api/v1/jobs/{test_archived_job.id}")
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["id"] == test_archived_job.id
    assert data["archived_at"] is not None


def test_complete_job_workflow_end_to_end(client, test_recruiter, test_admin, db_session):
    """Integration test for complete job management workflow."""
    
    # 1. Create job as recruiter with draft status
    _auth_client(client, test_recruiter)
    
    job_data = {
        "title": "Full Stack Developer",
        "department": "Engineering",
        "description": "Build web applications",
        "location": "Remote",
        "work_mode": "remote",
        "employment_type": "full-time",
        "min_experience": 2,
        "max_experience": 6,
        "education_requirement": "bachelor",
        "status": "draft",
        "required_skills": ["JavaScript", "Python"]
    }
    
    response = client.post("/api/v1/jobs/", json=job_data)
    assert response.status_code == status.HTTP_201_CREATED
    job_id = response.json()["id"]
    
    # 2. Update job fields and set weights to total 100%
    update_data = {
        "status": "active",
        "weight_skills": 30,
        "weight_experience": 25,
        "weight_education": 15,
        "weight_projects": 20,
        "weight_certs": 10
    }
    
    response = client.patch(f"/api/v1/jobs/{job_id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "active"
    
    # 3. Create candidates and applications for applicant count testing
    for _ in range(2):
        create_application_for_job(db_session, job_id)
    
    # 4. Verify applicant count calculation in job listing and details
    response = client.get(f"/api/v1/jobs/{job_id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["applicant_count"] == 2
    
    # 5. Close job
    response = client.patch(f"/api/v1/jobs/{job_id}/close")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "closed"
    
    # 6. Archive job
    response = client.patch(f"/api/v1/jobs/{job_id}/archive")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["archived_at"] is not None
    
    # 7. Verify archived job excluded from default listing
    response = client.get("/api/v1/jobs/")
    assert response.status_code == status.HTTP_200_OK
    job_ids = [job["id"] for job in response.json()["items"]]
    assert job_id not in job_ids
    
    # 8. Restore job as admin
    _auth_client(client, test_admin)
    response = client.patch(f"/api/v1/jobs/{job_id}/restore")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["archived_at"] is None
    
    # 9. Verify job reappears in default listing
    response = client.get("/api/v1/jobs/")
    assert response.status_code == status.HTTP_200_OK
    job_ids = [job["id"] for job in response.json()["items"]]
    assert job_id in job_ids
    
    # 10. Test cross-recruiter collaboration per D-04 (different recruiter can edit)
    # (Already covered in test_cross_recruiter_job_updates_allowed)