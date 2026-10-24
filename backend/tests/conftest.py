import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.job import Job  # noqa: F401 — required for Base.metadata FK resolution
from app.models.candidate import Candidate  # noqa: F401 — required for Application FK resolution
from app.models.application import Application  # noqa: F401 — required for Base.metadata registration
from app.core.security import get_password_hash
from datetime import datetime

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    # Create tables
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop tables after test
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def test_admin(db_session):
    user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("password123"),
        role="admin",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def test_recruiter(db_session):
    user = User(
        email="recruiter@example.com",
        hashed_password=get_password_hash("password123"),
        role="recruiter",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def test_job(db_session):
    """Creates a sample job with valid fields, default weights, and skills/certs."""
    job = Job(
        title="Software Engineer",
        department="Engineering",
        description="Develop and maintain software applications",
        location="San Francisco, CA",
        work_mode="hybrid",
        employment_type="full-time",
        min_experience=2,
        max_experience=5,
        education_requirement="bachelor",
        salary_min=80000,
        salary_max=120000,
        # Default weights (20% each)
        weight_skills=20,
        weight_experience=20,
        weight_education=20,
        weight_projects=20,
        weight_certs=20,
        # JSON skills/certs
        required_skills=["Python", "JavaScript"],
        preferred_skills=["React", "FastAPI"],
        required_certs=["AWS Certified Developer"],
        preferred_certs=["Docker Certification"],
        status="draft"
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job

@pytest.fixture(scope="function")
def test_active_job(db_session):
    """Creates a job with status='active' and weights totaling 100%."""
    job = Job(
        title="Product Manager",
        department="Product",
        description="Lead product development and strategy",
        location="Remote",
        work_mode="remote",
        employment_type="full-time",
        min_experience=3,
        max_experience=7,
        education_requirement="master",
        # Weights totaling 100%
        weight_skills=25,
        weight_experience=30,
        weight_education=15,
        weight_projects=20,
        weight_certs=10,
        required_skills=["Product Strategy", "Analytics"],
        preferred_skills=["SQL", "Data Analysis"],
        required_certs=[],
        preferred_certs=["PMP"],
        status="active"
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job

@pytest.fixture(scope="function")
def test_archived_job(db_session):
    """Creates a job with archived_at timestamp set."""
    job = Job(
        title="UX Designer",
        department="Design",
        description="Design user interfaces and experiences",
        location="New York, NY",
        work_mode="on-site",
        employment_type="full-time",
        min_experience=1,
        max_experience=4,
        education_requirement="bachelor",
        weight_skills=20,
        weight_experience=20,
        weight_education=20,
        weight_projects=20,
        weight_certs=20,
        required_skills=["Figma", "Adobe Creative Suite"],
        preferred_skills=["Sketch", "InVision"],
        required_certs=[],
        preferred_certs=["Adobe Certified Expert"],
        status="closed",
        archived_at=datetime.utcnow()
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job

def create_application_for_job(db_session, job_id, candidate_id=None):
    """Helper function to create application records linking jobs and candidates."""
    if candidate_id is None:
        # Create a minimal candidate first
        candidate = Candidate()
        db_session.add(candidate)
        db_session.commit()
        db_session.refresh(candidate)
        candidate_id = candidate.id
    
    application = Application(
        job_id=job_id,
        candidate_id=candidate_id
    )
    db_session.add(application)
    db_session.commit()
    db_session.refresh(application)
    return application

@pytest.fixture(scope="function")
def test_job_with_applications(db_session):
    """Creates job with associated applications for applicant count testing."""
    job = Job(
        title="Data Scientist",
        department="Analytics",
        description="Analyze data and build ML models",
        location="Boston, MA",
        work_mode="hybrid",
        employment_type="full-time",
        min_experience=2,
        max_experience=6,
        education_requirement="bachelor",
        weight_skills=20,
        weight_experience=20,
        weight_education=20,
        weight_projects=20,
        weight_certs=20,
        required_skills=["Python", "SQL", "Machine Learning"],
        preferred_skills=["TensorFlow", "PyTorch"],
        required_certs=[],
        preferred_certs=["AWS Machine Learning"],
        status="active"
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    
    # Create 3 applications for this job
    for _ in range(3):
        create_application_for_job(db_session, job.id)
    
    return job
