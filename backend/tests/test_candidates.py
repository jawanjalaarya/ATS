"""Integration tests for the candidates API (/api/v1/candidates).

Tests cover: upload (success + validation errors), list, get, update,
delete with file cleanup, authenticated download, unauthenticated rejection,
and pending_review → complete auto-promotion.
"""

import io
import os
import struct
import tempfile
from unittest.mock import patch

import pytest
from fastapi import status

from app.core.security import create_access_token
from app.models.candidate import Candidate


def _auth_client(client, user):
    """Helper to authenticate client with user token."""
    token = create_access_token(data={"sub": user.email})
    client.cookies.set("access_token", f"Bearer {token}")
    return client


# --- Minimal valid PDF bytes for testing ---
def _minimal_pdf_bytes() -> bytes:
    """Create minimal valid PDF content that PyMuPDF can open."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R >>\nendobj\n"
        b"4 0 obj\n<< /Length 44 >>\nstream\n"
        b"BT /F1 12 Tf 100 700 Td (John Doe) Tj ET\n"
        b"endstream\nendobj\n"
        b"xref\n0 5\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"0000000210 00000 n \n"
        b"trailer\n<< /Size 5 /Root 1 0 R >>\n"
        b"startxref\n306\n%%EOF\n"
    )


def _rich_pdf_bytes() -> bytes:
    """Create a PDF with parseable resume content (name + email)."""
    # We'll create a real PDF with text that the parser can extract
    content = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        b"4 0 obj\n<< /Length 150 >>\nstream\n"
        b"BT\n/F1 12 Tf\n100 700 Td\n"
        b"(Jane Smith) Tj\n0 -20 Td\n"
        b"(jane.smith@example.com) Tj\n0 -20 Td\n"
        b"(555-123-4567) Tj\n"
        b"ET\n"
        b"endstream\nendobj\n"
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        b"xref\n0 6\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"0000000266 00000 n \n"
        b"0000000470 00000 n \n"
        b"trailer\n<< /Size 6 /Root 1 0 R >>\n"
        b"startxref\n550\n%%EOF\n"
    )
    return content


# --- Test Fixtures ---

@pytest.fixture
def resume_dir(tmp_path):
    """Monkeypatch RESUME_DIR to use a temp directory."""
    resume_path = tmp_path / "resumes"
    resume_path.mkdir()
    with patch("app.api.v1.candidates.RESUME_DIR", str(resume_path)):
        yield str(resume_path)


# --- Upload Success ---

def test_upload_resume_pdf_success(client, test_recruiter, resume_dir, db_session):
    """Upload a valid PDF file and verify 201 response with candidate fields."""
    _auth_client(client, test_recruiter)

    # Mock extract_text and parse_resume_text to return structured data
    # (avoids needing real PDF rendering and schema mismatch with raw text)
    parsed_data = {
        "name": "Jane Smith",
        "email": "jane.smith@example.com",
        "phone": "555-123-4567",
        "location": "San Francisco, CA",
        "linkedin_url": None,
        "github_url": None,
        "portfolio_url": None,
        "skills": ["Python", "JavaScript", "React"],
        "education": [],
        "experience": [],
        "projects": [],
        "certifications": [],
        "achievements": [],
    }

    with patch("app.api.v1.candidates.extract_text", return_value="Jane Smith\njane.smith@example.com"):
        with patch("app.api.v1.candidates.parse_resume_text", return_value=parsed_data):
            response = client.post(
                "/api/v1/candidates/upload",
                files={"file": ("resume.pdf", _minimal_pdf_bytes(), "application/pdf")},
            )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Jane Smith"
    assert data["email"] == "jane.smith@example.com"
    assert data["status"] == "complete"
    assert data["original_filename"] == "resume.pdf"
    assert "id" in data


# --- Upload Validation ---

def test_upload_validation_invalid_extension(client, test_recruiter, resume_dir):
    """Upload a .txt file is rejected with 422."""
    _auth_client(client, test_recruiter)

    response = client.post(
        "/api/v1/candidates/upload",
        files={"file": ("notes.txt", b"hello world", "text/plain")},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Only PDF and DOCX files are accepted" in response.json()["detail"]


def test_upload_validation_file_too_large(client, test_recruiter, resume_dir):
    """Upload exceeding 10MB is rejected."""
    _auth_client(client, test_recruiter)

    large_content = b"%PDF-1.4\n" + (b"x" * (10 * 1024 * 1024 + 1))

    response = client.post(
        "/api/v1/candidates/upload",
        files={"file": ("big.pdf", large_content, "application/pdf")},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "exceeds 10 MB limit" in response.json()["detail"]


def test_upload_validation_empty_file(client, test_recruiter, resume_dir):
    """Upload 0-byte file is rejected."""
    _auth_client(client, test_recruiter)

    response = client.post(
        "/api/v1/candidates/upload",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "damaged" in response.json()["detail"]


def test_upload_validation_wrong_mime(client, test_recruiter, resume_dir):
    """Upload with .pdf extension but non-PDF content is rejected."""
    _auth_client(client, test_recruiter)

    # Content doesn't start with %PDF magic
    response = client.post(
        "/api/v1/candidates/upload",
        files={"file": ("fake.pdf", b"This is not a PDF file at all", "application/pdf")},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_upload_validation_mime_mismatch(client, test_recruiter, resume_dir):
    """Upload with wrong MIME type is rejected."""
    _auth_client(client, test_recruiter)

    response = client.post(
        "/api/v1/candidates/upload",
        files={"file": ("resume.pdf", _minimal_pdf_bytes(), "text/plain")},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_upload_valid_pdf_with_generic_browser_mime(client, test_recruiter, resume_dir):
    """Valid PDFs uploaded by browsers as octet-stream should still be accepted."""
    _auth_client(client, test_recruiter)

    parsed_data = {
        "name": "Browser Upload User",
        "email": "browser@example.com",
        "phone": None,
        "location": None,
        "linkedin_url": None,
        "github_url": None,
        "portfolio_url": None,
        "skills": ["Python"],
        "education": [],
        "experience": [],
        "projects": [],
        "certifications": [],
        "achievements": [],
    }

    with patch("app.api.v1.candidates.extract_text", return_value="Browser Upload User\nbrowser@example.com"):
        with patch("app.api.v1.candidates.parse_resume_text", return_value=parsed_data):
            response = client.post(
                "/api/v1/candidates/upload",
                files={"file": ("resume.pdf", _minimal_pdf_bytes(), "application/octet-stream")},
            )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["email"] == "browser@example.com"


# --- Batch Upload ---

def test_upload_batch_mixed_results(client, test_recruiter, resume_dir, db_session):
    """Batch upload processes all files and reports per-file status."""
    _auth_client(client, test_recruiter)

    parsed_data = {
        "name": "Batch User",
        "email": "batch@example.com",
        "phone": None,
        "location": None,
        "linkedin_url": None,
        "github_url": None,
        "portfolio_url": None,
        "skills": ["Python"],
        "education": [],
        "experience": [],
        "projects": [],
        "certifications": [],
        "achievements": [],
    }

    with patch("app.api.v1.candidates.extract_text", return_value="Batch User\nbatch@example.com"):
        with patch("app.api.v1.candidates.parse_resume_text", return_value=parsed_data):
            response = client.post(
                "/api/v1/candidates/upload-batch",
                files=[
                    ("files", ("good.pdf", _minimal_pdf_bytes(), "application/pdf")),
                    ("files", ("bad.txt", b"plain text", "text/plain")),
                ],
            )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["results"]) == 2
    assert data["results"][0]["status"] == "success"
    assert data["results"][1]["status"] == "error"


# --- List Candidates ---

def test_list_candidates(client, test_recruiter, db_session):
    """List candidates returns items and total."""
    _auth_client(client, test_recruiter)

    # Create a candidate directly in DB
    candidate = Candidate(
        name="List Test",
        email="list@example.com",
        status="complete",
    )
    db_session.add(candidate)
    db_session.commit()

    response = client.get("/api/v1/candidates/")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1
    emails = [c["email"] for c in data["items"]]
    assert "list@example.com" in emails


# --- Get Single Candidate ---

def test_get_candidate_by_id(client, test_recruiter, db_session):
    """Get candidate by ID returns full response."""
    _auth_client(client, test_recruiter)

    candidate = Candidate(
        name="Get Test",
        email="get@example.com",
        phone="555-0000",
        skills=["Python", "React"],
        status="complete",
    )
    db_session.add(candidate)
    db_session.commit()
    db_session.refresh(candidate)

    response = client.get(f"/api/v1/candidates/{candidate.id}")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["id"] == candidate.id
    assert data["name"] == "Get Test"
    assert data["email"] == "get@example.com"
    assert data["skills"] == ["Python", "React"]


def test_get_candidate_not_found(client, test_recruiter):
    """Get non-existent candidate returns 404."""
    _auth_client(client, test_recruiter)

    response = client.get("/api/v1/candidates/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


# --- Update Candidate ---

def test_update_candidate_pending_review(client, test_recruiter, db_session):
    """PATCH with name+email on pending_review candidate promotes to complete."""
    _auth_client(client, test_recruiter)

    candidate = Candidate(
        name=None,
        email=None,
        status="pending_review",
    )
    db_session.add(candidate)
    db_session.commit()
    db_session.refresh(candidate)

    response = client.patch(
        f"/api/v1/candidates/{candidate.id}",
        json={"name": "John Doe", "email": "john@test.com"},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "John Doe"
    assert data["email"] == "john@test.com"
    assert data["status"] == "complete"


def test_update_candidate_partial(client, test_recruiter, db_session):
    """PATCH with only name does not promote if email still missing."""
    _auth_client(client, test_recruiter)

    candidate = Candidate(
        name=None,
        email=None,
        status="pending_review",
    )
    db_session.add(candidate)
    db_session.commit()
    db_session.refresh(candidate)

    response = client.patch(
        f"/api/v1/candidates/{candidate.id}",
        json={"name": "Jane Doe"},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Jane Doe"
    assert data["status"] == "pending_review"  # Not promoted without email


# --- Delete Candidate ---

def test_delete_candidate_removes_file(client, test_recruiter, db_session, tmp_path):
    """DELETE removes the physical resume file from disk."""
    _auth_client(client, test_recruiter)

    # Create a temp file simulating a resume
    resume_file = tmp_path / "test_resume.pdf"
    resume_file.write_bytes(b"fake pdf content")
    assert resume_file.exists()

    candidate = Candidate(
        name="Delete Test",
        email="delete@example.com",
        resume_path=str(resume_file),
        original_filename="resume.pdf",
        status="complete",
    )
    db_session.add(candidate)
    db_session.commit()
    db_session.refresh(candidate)

    response = client.delete(f"/api/v1/candidates/{candidate.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify file was removed
    assert not resume_file.exists()

    # Verify candidate gone from DB
    assert db_session.query(Candidate).filter(Candidate.id == candidate.id).first() is None


# --- Download Resume ---

def test_download_resume_authenticated(client, test_recruiter, db_session, tmp_path):
    """Authenticated download returns file with correct content-disposition."""
    _auth_client(client, test_recruiter)

    # Create a temp resume file
    resume_file = tmp_path / "download_test.pdf"
    pdf_content = b"%PDF-1.4 test content for download"
    resume_file.write_bytes(pdf_content)

    candidate = Candidate(
        name="Download Test",
        email="download@example.com",
        resume_path=str(resume_file),
        original_filename="my_resume.pdf",
        status="complete",
    )
    db_session.add(candidate)
    db_session.commit()
    db_session.refresh(candidate)

    response = client.get(f"/api/v1/candidates/{candidate.id}/resume")
    assert response.status_code == status.HTTP_200_OK
    assert pdf_content in response.content
    assert "my_resume.pdf" in response.headers.get("content-disposition", "")


def test_download_resume_unauthenticated(client, db_session, tmp_path):
    """Unauthenticated download is rejected."""
    # Create a candidate with a resume (no auth cookie set)
    resume_file = tmp_path / "unauth_test.pdf"
    resume_file.write_bytes(b"%PDF-1.4 content")

    candidate = Candidate(
        name="Unauth Test",
        email="unauth@example.com",
        resume_path=str(resume_file),
        original_filename="secret.pdf",
        status="complete",
    )
    db_session.add(candidate)
    db_session.commit()
    db_session.refresh(candidate)

    # No auth cookie set
    response = client.get(f"/api/v1/candidates/{candidate.id}/resume")
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


def test_download_resume_no_file(client, test_recruiter, db_session):
    """Download for candidate with no resume returns 404."""
    _auth_client(client, test_recruiter)

    candidate = Candidate(
        name="No Resume",
        email="noresume@example.com",
        resume_path=None,
        status="complete",
    )
    db_session.add(candidate)
    db_session.commit()
    db_session.refresh(candidate)

    response = client.get(f"/api/v1/candidates/{candidate.id}/resume")
    assert response.status_code == status.HTTP_404_NOT_FOUND


# --- Failed Parse Flow ---

def test_failed_parse_flow(client, test_recruiter, resume_dir, db_session):
    """Upload valid PDF with empty extracted text returns 422."""
    _auth_client(client, test_recruiter)

    # Mock extract_text returning empty (simulates unparseable PDF)
    with patch("app.api.v1.candidates.extract_text", return_value=""):
        response = client.post(
            "/api/v1/candidates/upload",
            files={"file": ("bad_content.pdf", _minimal_pdf_bytes(), "application/pdf")},
        )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "damaged" in response.json()["detail"]


# --- Duplicate Email Handling (D-15) ---

def test_duplicate_email_updates_existing(client, test_recruiter, resume_dir, db_session):
    """Upload with duplicate email updates existing candidate."""
    _auth_client(client, test_recruiter)

    # Create existing candidate
    existing = Candidate(
        name="Old Name",
        email="dupe@example.com",
        skills=["Java"],
        status="complete",
    )
    db_session.add(existing)
    db_session.commit()
    db_session.refresh(existing)
    existing_id = existing.id

    parsed_data = {
        "name": "New Name",
        "email": "dupe@example.com",
        "phone": "555-999-0000",
        "location": None,
        "linkedin_url": None,
        "github_url": None,
        "portfolio_url": None,
        "skills": ["Python", "React"],
        "education": [],
        "experience": [],
        "projects": [],
        "certifications": [],
        "achievements": [],
    }

    with patch("app.api.v1.candidates.extract_text", return_value="New Name\ndupe@example.com"):
        with patch("app.api.v1.candidates.parse_resume_text", return_value=parsed_data):
            response = client.post(
                "/api/v1/candidates/upload",
                files={"file": ("updated.pdf", _minimal_pdf_bytes(), "application/pdf")},
            )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["id"] == existing_id  # Same candidate updated
    assert data["email"] == "dupe@example.com"
    assert "Python" in data["skills"]
