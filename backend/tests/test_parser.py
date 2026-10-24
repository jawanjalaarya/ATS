"""Unit tests for the resume parser module.

Pure function tests — no database fixtures needed.
"""

import pytest

from app.core.parser import (
    determine_parse_status,
    extract_text,
    normalize_skills,
    parse_resume_text,
)
from app.schemas.candidate import CandidateResponse


# ---------------------------------------------------------------------------
# parse_resume_text tests
# ---------------------------------------------------------------------------


class TestParseResumeTextExtraction:
    """Tests for individual field extraction from resume text."""

    def test_parse_resume_text_extracts_email(self):
        text = "John Doe\njohn.doe@example.com\n+1 555-123-4567"
        parsed = parse_resume_text(text)
        assert parsed["email"] == "john.doe@example.com"

    def test_parse_resume_text_extracts_phone(self):
        text = "John Doe\njohn@example.com\n+1 (555) 123-4567"
        parsed = parse_resume_text(text)
        assert "555" in parsed["phone"]

    def test_parse_resume_text_extracts_linkedin(self):
        text = "John Doe\njohn@test.com\nlinkedin.com/in/johndoe\n"
        parsed = parse_resume_text(text)
        assert "linkedin.com/in/johndoe" in parsed["linkedin_url"]

    def test_parse_resume_text_extracts_github(self):
        text = "John Doe\njohn@test.com\ngithub.com/johndoe\n"
        parsed = parse_resume_text(text)
        assert "github.com/johndoe" in parsed["github_url"]

    def test_parse_resume_text_extracts_name(self):
        text = "John Doe\njohn@example.com\nSoftware Engineer"
        parsed = parse_resume_text(text)
        assert parsed["name"] == "John Doe"

    def test_parse_resume_text_extracts_skills_section(self):
        text = (
            "John Doe\njohn@example.com\n\n"
            "SKILLS\n"
            "Python, JavaScript, React, Docker\n\n"
            "EXPERIENCE\n"
            "Software Engineer at Acme Corp"
        )
        parsed = parse_resume_text(text)
        assert "Python" in parsed["skills"]
        assert "JavaScript" in parsed["skills"]
        assert "React" in parsed["skills"]
        assert "Docker" in parsed["skills"]


# ---------------------------------------------------------------------------
# normalize_skills tests
# ---------------------------------------------------------------------------


class TestNormalizeSkills:
    """Tests for skill normalization logic."""

    def test_normalize_skills_canonical(self):
        result = normalize_skills(["python", "js", "reactjs"])
        assert "Python" in result
        assert "JavaScript" in result
        assert "React" in result

    def test_normalize_skills_deduplicates(self):
        result = normalize_skills(["python", "Python", "PYTHON"])
        assert result == ["Python"]

    def test_normalize_skills_unknown_capitalized(self):
        result = normalize_skills(["some-obscure-tool"])
        # Should be title-cased since not in lexicon
        assert len(result) == 1
        assert result[0] == "Some-Obscure-Tool"


# ---------------------------------------------------------------------------
# determine_parse_status tests
# ---------------------------------------------------------------------------


class TestDetermineParseStatus:
    """Tests for parse status determination."""

    def test_determine_parse_status_complete(self):
        parsed = {"name": "John Doe", "email": "john@example.com"}
        assert determine_parse_status(parsed) == "complete"

    def test_determine_parse_status_pending_review_no_email(self):
        parsed = {"name": "John Doe", "email": None}
        assert determine_parse_status(parsed) == "pending_review"

    def test_determine_parse_status_pending_review_no_name(self):
        parsed = {"name": None, "email": "john@example.com"}
        assert determine_parse_status(parsed) == "pending_review"

    def test_candidate_response_coerces_string_section_lists(self):
        candidate = {
            "id": 1,
            "name": "Jane Doe",
            "email": "jane@example.com",
            "phone": None,
            "location": None,
            "linkedin_url": None,
            "github_url": None,
            "portfolio_url": None,
            "skills": ["Python"],
            "education": ["B.Tech in Computer Science"],
            "experience": ["Software Engineer at Acme"],
            "projects": ["Resume Parser"],
            "certifications": [],
            "achievements": [],
            "resume_path": None,
            "original_filename": None,
            "status": "complete",
            "created_at": None,
            "updated_at": None,
        }

        resp = CandidateResponse.model_validate(candidate)
        assert resp.education[0]["text"] == "B.Tech in Computer Science"
        assert resp.experience[0]["text"] == "Software Engineer at Acme"
        assert resp.projects[0]["text"] == "Resume Parser"


# ---------------------------------------------------------------------------
# extract_text tests
# ---------------------------------------------------------------------------


class TestExtractText:
    """Tests for the extract_text dispatcher."""

    def test_extract_text_raises_for_unsupported(self):
        with pytest.raises(ValueError, match="Unsupported file extension"):
            extract_text("resume.txt")
