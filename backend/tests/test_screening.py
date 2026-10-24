"""
Unit tests for the Screening Engine dimension scorers.
The semantic scorer is mocked to avoid loading the 120MB model in unit tests.
"""
from unittest.mock import MagicMock, patch

import pytest

from app.core.screening import (
    ScreeningEngine,
    _extract_years,
    _highest_education_rank,
    normalize_skill,
    normalize_skills,
    score_certifications,
    score_education,
    score_experience,
    score_projects,
    score_skills,
)


# ---------------------------------------------------------------------------
# Skills normalization
# ---------------------------------------------------------------------------


class TestNormalizeSkill:
    def test_normalizes_case_insensitive(self):
        """Normalization must be case-insensitive."""
        assert normalize_skill("Python").lower() == normalize_skill("python").lower()

    def test_passthrough_unknown(self):
        """Unknown skills should pass through unchanged and not raise."""
        result = normalize_skill("some-obscure-tool-xyz")
        assert result  # non-empty
        assert "obscure" in result.lower() or result == "some-obscure-tool-xyz"

    def test_normalizes_known_synonym(self):
        """Synonyms in the lexicon should map to a canonical value."""
        # 'javascript' is in lexicon — should return canonical form
        result = normalize_skill("javascript")
        assert result  # non-empty, recognized


class TestNormalizeSkills:
    def test_deduplicates_same_canonical(self):
        """Same normalized canonical must appear only once."""
        result = normalize_skills(["python", "Python", "PYTHON"])
        # All map to same canonical — should deduplicate
        assert len(result) == 1

    def test_returns_list(self):
        """Always returns a list."""
        result = normalize_skills([])
        assert isinstance(result, list)
        assert len(result) == 0


# ---------------------------------------------------------------------------
# Skills scoring
# ---------------------------------------------------------------------------


class TestScoreSkills:
    def test_full_required_match_scores_100(self):
        score, breakdown = score_skills(
            candidate_skills=["Python", "Docker"],
            required_skills=["Python", "Docker"],
            preferred_skills=[],
        )
        assert score == 100.0
        # Breakdown stores normalized forms; check case-insensitively
        matched_lower = [s.lower() for s in breakdown["required_matched"]]
        assert "docker" in matched_lower
        assert breakdown["required_missing"] == []

    def test_partial_required_match(self):
        score, breakdown = score_skills(
            candidate_skills=["Python"],
            required_skills=["Python", "Docker"],
            preferred_skills=[],
        )
        assert score == 50.0
        # Breakdown stores normalized forms; check case-insensitively
        missing_lower = [s.lower() for s in breakdown["required_missing"]]
        assert "docker" in missing_lower

    def test_80_20_weighting_with_preferred(self):
        # 100% required (Python matched), 0% preferred (Docker missing) → 0.8*100 + 0.2*0 = 80
        score, _ = score_skills(
            candidate_skills=["Python"],
            required_skills=["Python"],
            preferred_skills=["Docker"],
        )
        assert score == 80.0

    def test_no_required_only_preferred(self):
        score, _ = score_skills(
            candidate_skills=["Docker"],
            required_skills=[],
            preferred_skills=["Docker"],
        )
        assert score == 100.0

    def test_case_insensitive_matching(self):
        score, _ = score_skills(
            candidate_skills=["python"],
            required_skills=["Python"],
            preferred_skills=[],
        )
        assert score == 100.0

    def test_no_skills_both_sides_scores_100(self):
        score, _ = score_skills(
            candidate_skills=[],
            required_skills=[],
            preferred_skills=[],
        )
        assert score == 100.0

    def test_score_bounded_0_to_100(self):
        score, _ = score_skills(
            candidate_skills=[],
            required_skills=["Python", "Docker", "Kubernetes"],
            preferred_skills=["React"],
        )
        assert 0 <= score <= 100


# ---------------------------------------------------------------------------
# Experience scoring
# ---------------------------------------------------------------------------


class TestExtractYears:
    def test_extracts_years_from_string(self):
        years = _extract_years(["3 years experience in Python"])
        assert years == pytest.approx(3.0, abs=0.5)

    def test_extracts_year_range(self):
        years = _extract_years(["Software Engineer 2020-2023"])
        assert years == pytest.approx(3.0, abs=0.5)

    def test_empty_experience_returns_zero(self):
        assert _extract_years([]) == 0.0

    def test_extracts_months(self):
        years = _extract_years(["6 months internship"])
        assert years == pytest.approx(0.5, abs=0.1)


class TestScoreExperience:
    def test_meets_minimum_scores_100(self):
        score, breakdown = score_experience(["5 years at Acme"], min_exp=3, max_exp=10)
        assert score == 100.0
        assert breakdown["meets_minimum"] is True

    def test_below_minimum_proportional(self):
        # 1 year / 4 years required = 25%
        score, _ = score_experience(["1 year at Startup"], min_exp=4, max_exp=10)
        assert score == pytest.approx(25.0, abs=5.0)

    def test_zero_minimum_always_100(self):
        score, _ = score_experience([], min_exp=0, max_exp=5)
        assert score == 100.0

    def test_no_penalty_for_over_experience(self):
        # 15 years, max is 7 — no penalty
        score, _ = score_experience(["15 years"], min_exp=3, max_exp=7)
        assert score == 100.0

    def test_score_bounded_0_to_100(self):
        score, _ = score_experience([], min_exp=10, max_exp=20)
        assert 0 <= score <= 100


# ---------------------------------------------------------------------------
# Education scoring
# ---------------------------------------------------------------------------


class TestHighestEducationRank:
    def test_extracts_bachelor(self):
        rank = _highest_education_rank(["Bachelor of Science in Computer Science"])
        assert rank == 3

    def test_extracts_phd(self):
        rank = _highest_education_rank(["PhD in Machine Learning"])
        assert rank == 5

    def test_extracts_master(self):
        rank = _highest_education_rank(["Master of Science"])
        assert rank == 4

    def test_empty_returns_zero(self):
        assert _highest_education_rank([]) == 0


class TestScoreEducation:
    def test_meets_requirement_scores_100(self):
        score, breakdown = score_education(
            ["Master of Science in CS"],
            required_education="Bachelor",
        )
        assert score == 100.0
        assert breakdown["meets_requirement"] is True

    def test_exceeds_requirement_scores_100(self):
        score, _ = score_education(["PhD"], required_education="Master")
        assert score == 100.0

    def test_below_requirement_proportional(self):
        # High School (rank 1) vs Master (rank 4) → 25%
        score, _ = score_education(
            ["High School Diploma"],
            required_education="Master",
        )
        assert score == pytest.approx(25.0, abs=5.0)

    def test_no_requirement_scores_100(self):
        score, _ = score_education([], required_education="")
        assert score == 100.0

    def test_score_bounded_0_to_100(self):
        score, _ = score_education([], required_education="PhD")
        assert 0 <= score <= 100


# ---------------------------------------------------------------------------
# Certifications scoring
# ---------------------------------------------------------------------------


class TestScoreCertifications:
    def test_no_job_certs_omits_dimension(self):
        score, breakdown, has_certs = score_certifications([], [], [])
        assert has_certs is False
        assert breakdown.get("omitted") is True

    def test_full_required_match_scores_100(self):
        score, _, has_certs = score_certifications(
            candidate_certs=["AWS Certified"],
            required_certs=["AWS Certified"],
            preferred_certs=[],
        )
        assert has_certs is True
        assert score == 100.0

    def test_partial_required_match(self):
        score, breakdown, has_certs = score_certifications(
            candidate_certs=["AWS Certified"],
            required_certs=["AWS Certified", "Google Cloud"],
            preferred_certs=[],
        )
        assert has_certs is True
        assert score == pytest.approx(50.0, abs=1.0)
        assert "Google Cloud" in breakdown["required_missing"]

    def test_no_candidate_certs_scores_0(self):
        score, _, _ = score_certifications(
            candidate_certs=[],
            required_certs=["AWS Certified"],
            preferred_certs=[],
        )
        assert score == 0.0

    def test_only_preferred_no_required(self):
        score, _, has_certs = score_certifications(
            candidate_certs=["PMP"],
            required_certs=[],
            preferred_certs=["PMP"],
        )
        assert has_certs is True
        assert score == 100.0


# ---------------------------------------------------------------------------
# Projects scoring
# ---------------------------------------------------------------------------


class TestScoreProjects:
    def test_keyword_match_in_projects(self):
        score, breakdown = score_projects(
            candidate_projects=["Built a Python Django REST API with Docker"],
            required_skills=["Python", "Docker"],
        )
        assert score == 100.0
        assert "Python" in breakdown["matched_keywords"] or "Docker" in breakdown["matched_keywords"]

    def test_no_match_scores_zero(self):
        score, _ = score_projects(
            candidate_projects=["Built iOS apps with Swift"],
            required_skills=["Python", "Docker"],
        )
        assert score == 0.0

    def test_no_required_skills_scores_100(self):
        score, _ = score_projects(["Some project"], required_skills=[])
        assert score == 100.0

    def test_partial_keyword_match(self):
        score, _ = score_projects(
            candidate_projects=["Python web app"],
            required_skills=["Python", "Docker"],
        )
        assert score == 50.0

    def test_score_bounded_0_to_100(self):
        score, _ = score_projects([], required_skills=["Python"])
        assert 0 <= score <= 100


# ---------------------------------------------------------------------------
# ScreeningEngine integration (semantic mocked)
# ---------------------------------------------------------------------------


class TestScreeningEngine:
    def _make_candidate(self, **kwargs):
        c = MagicMock()
        c.skills = kwargs.get("skills", ["Python"])
        c.experience = kwargs.get("experience", ["3 years"])
        c.education = kwargs.get("education", ["Bachelor of Science"])
        c.projects = kwargs.get("projects", ["Built a Python app"])
        c.certifications = kwargs.get("certifications", [])
        return c

    def _make_job(self, **kwargs):
        j = MagicMock()
        j.required_skills = kwargs.get("required_skills", ["Python"])
        j.preferred_skills = kwargs.get("preferred_skills", [])
        j.required_certs = kwargs.get("required_certs", [])
        j.preferred_certs = kwargs.get("preferred_certs", [])
        j.min_experience = kwargs.get("min_experience", 2)
        j.max_experience = kwargs.get("max_experience", 10)
        j.education_requirement = kwargs.get("education_requirement", "Bachelor")
        j.weight_skills = 20
        j.weight_experience = 20
        j.weight_education = 20
        j.weight_projects = 20
        j.weight_certs = 20
        j.title = "Software Engineer"
        j.department = "Engineering"
        j.description = "Python development role"
        return j

    @patch("app.core.screening.cosine_similarity", return_value=[[0.6]])
    @patch("app.core.screening._get_model")
    def test_screen_returns_all_keys(self, mock_model, mock_cosine):
        mock_model.return_value.encode.return_value = [[0.5, 0.5], [0.5, 0.5]]
        engine = ScreeningEngine()
        result = engine.screen(self._make_candidate(), self._make_job())

        assert "overall_score" in result
        assert "skills_score" in result
        assert "experience_score" in result
        assert "education_score" in result
        assert "projects_score" in result
        assert "semantic_score" in result
        assert "explanation" in result

    @patch("app.core.screening.cosine_similarity", return_value=[[0.6]])
    @patch("app.core.screening._get_model")
    def test_screen_overall_score_bounded_0_to_100(self, mock_model, mock_cosine):
        mock_model.return_value.encode.return_value = [[0.5, 0.5], [0.5, 0.5]]
        engine = ScreeningEngine()
        result = engine.screen(self._make_candidate(), self._make_job())
        assert 0 <= result["overall_score"] <= 100

    @patch("app.core.screening.cosine_similarity", return_value=[[0.6]])
    @patch("app.core.screening._get_model")
    def test_cert_dimension_none_when_no_job_certs(self, mock_model, mock_cosine):
        mock_model.return_value.encode.return_value = [[0.5, 0.5], [0.5, 0.5]]
        engine = ScreeningEngine()
        job = self._make_job(required_certs=[], preferred_certs=[])
        result = engine.screen(self._make_candidate(), job)
        # certification_score should be None when job has no certs (omit-fallback)
        assert result["certification_score"] is None

    @patch("app.core.screening.cosine_similarity", return_value=[[0.6]])
    @patch("app.core.screening._get_model")
    def test_explanation_contains_all_dimensions(self, mock_model, mock_cosine):
        mock_model.return_value.encode.return_value = [[0.5, 0.5], [0.5, 0.5]]
        engine = ScreeningEngine()
        result = engine.screen(self._make_candidate(), self._make_job())
        explanation = result["explanation"]
        assert "skills" in explanation
        assert "experience" in explanation
        assert "education" in explanation
        assert "projects" in explanation
        assert "certifications" in explanation
        assert "semantic" in explanation

    @patch("app.core.screening.cosine_similarity", return_value=[[0.3]])
    @patch("app.core.screening._get_model")
    def test_low_cosine_maps_to_zero_semantic(self, mock_model, mock_cosine):
        """Cosine of 0.3 (SIM_LOW) should map to semantic_score = 0."""
        mock_model.return_value.encode.return_value = [[0.5, 0.5], [0.5, 0.5]]
        engine = ScreeningEngine()
        result = engine.screen(self._make_candidate(), self._make_job())
        assert result["semantic_score"] == pytest.approx(0.0, abs=1.0)

    @patch("app.core.screening.cosine_similarity", return_value=[[0.8]])
    @patch("app.core.screening._get_model")
    def test_high_cosine_maps_to_100_semantic(self, mock_model, mock_cosine):
        """Cosine of 0.8 (SIM_HIGH) should map to semantic_score = 100."""
        mock_model.return_value.encode.return_value = [[0.5, 0.5], [0.5, 0.5]]
        engine = ScreeningEngine()
        result = engine.screen(self._make_candidate(), self._make_job())
        assert result["semantic_score"] == pytest.approx(100.0, abs=1.0)
