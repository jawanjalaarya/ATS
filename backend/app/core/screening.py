"""
Screening Engine for computing candidate-job match scores.

All scoring is deterministic and runs entirely on local libraries (SCR-05).
The sentence-transformers model is lazy-loaded once on first use (D-05, D-06).
"""
import json
import os
from functools import lru_cache
from typing import Any

from sklearn.metrics.pairwise import cosine_similarity  # scikit-learn


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
EDUCATION_RANK = {
    "high school": 1,
    "associate": 2,
    "bachelor": 3,
    "master": 4,
    "phd": 5,
    "doctorate": 5,
}

# Semantic min-max scaling bounds (D-08): cosine [0.3, 0.8] → [0, 100]
SIM_LOW = 0.3
SIM_HIGH = 0.8

# Lexicon path relative to this file
_LEXICON_PATH = os.path.join(os.path.dirname(__file__), "skills_lexicon.json")


# ---------------------------------------------------------------------------
# Lexicon helpers
# ---------------------------------------------------------------------------
@lru_cache(maxsize=1)
def _load_lexicon() -> dict[str, str]:
    """
    Load skills_lexicon.json and build a flat synonym→canonical mapping.
    The JSON is structured as {canonical: [synonym, ...]} where each key is
    a canonical skill name and values are synonym lists.
    Returns a flat {lowercase_synonym: canonical} dict.
    """
    with open(_LEXICON_PATH, encoding="utf-8") as f:
        raw: dict[str, list[str]] = json.load(f)

    mapping: dict[str, str] = {}
    for canonical, synonyms in raw.items():
        # Include the canonical form itself
        mapping[canonical.lower()] = canonical
        for syn in synonyms:
            mapping[syn.lower()] = canonical
    return mapping


def normalize_skill(skill: str) -> str:
    """Normalize a single skill string using the lexicon (D-01, D-03)."""
    lexicon = _load_lexicon()
    cleaned = skill.strip().lower()
    return lexicon.get(cleaned, skill.strip())


def normalize_skills(skills: list[str]) -> list[str]:
    """Normalize a list of skill strings; deduplicate preserving first occurrence."""
    seen: set[str] = set()
    result: list[str] = []
    for s in skills:
        normalized = normalize_skill(s)
        key = normalized.lower()
        if key not in seen:
            seen.add(key)
            result.append(normalized)
    return result


# ---------------------------------------------------------------------------
# Sentence-Transformers model (lazy load, cached)
# ---------------------------------------------------------------------------
@lru_cache(maxsize=1)
def _get_model():  # type: ignore[return]
    """Lazy-load all-MiniLM-L6-v2 once. Cached for subsequent calls (D-05, D-06)."""
    from sentence_transformers import SentenceTransformer  # noqa: PLC0415

    return SentenceTransformer("all-MiniLM-L6-v2")


# ---------------------------------------------------------------------------
# Dimension scorers
# ---------------------------------------------------------------------------

def score_skills(
    candidate_skills: list[str],
    required_skills: list[str],
    preferred_skills: list[str],
) -> tuple[float, dict[str, Any]]:
    """
    Score skills dimension using 80/20 required/preferred weighting (D-04).
    Returns (score 0-100, breakdown dict).
    """
    cand_norm = set(normalize_skill(s).lower() for s in candidate_skills)
    req_norm = [normalize_skill(s) for s in required_skills]
    pref_norm = [normalize_skill(s) for s in preferred_skills]

    req_matched = [s for s in req_norm if s.lower() in cand_norm]
    req_missing = [s for s in req_norm if s.lower() not in cand_norm]
    pref_matched = [s for s in pref_norm if s.lower() in cand_norm]
    pref_missing = [s for s in pref_norm if s.lower() not in cand_norm]

    req_score = (len(req_matched) / len(req_norm) * 100) if req_norm else 100.0
    pref_score = (len(pref_matched) / len(pref_norm) * 100) if pref_norm else 100.0

    # 80% required, 20% preferred (D-04)
    if req_norm and pref_norm:
        score = req_score * 0.8 + pref_score * 0.2
    elif req_norm:
        score = req_score
    else:
        score = pref_score

    return round(score, 2), {
        "required_matched": req_matched,
        "required_missing": req_missing,
        "preferred_matched": pref_matched,
        "preferred_missing": pref_missing,
    }


def score_experience(
    candidate_experience: list[Any],
    min_exp: int,
    max_exp: int,
) -> tuple[float, dict[str, Any]]:
    """
    Threshold scoring for experience years (D-09).
    Meeting or exceeding minimum → 100. Below minimum → proportional.
    Over maximum → no penalty.
    """
    total_years = _extract_years(candidate_experience)

    if total_years >= min_exp:
        score = 100.0
    elif min_exp == 0:
        score = 100.0
    else:
        score = round((total_years / min_exp) * 100, 2)

    score = max(0.0, min(100.0, score))

    return score, {
        "candidate_years": total_years,
        "required_min": min_exp,
        "required_max": max_exp,
        "meets_minimum": total_years >= min_exp,
    }


def _extract_years(experience: list[Any]) -> float:
    """
    Heuristically extract total years of experience from the parsed experience list.
    Each entry can be a string or dict. Looks for patterns like
    '2 years', '6 months', '2020-2023'.
    """
    import re  # noqa: PLC0415
    import datetime  # noqa: PLC0415

    total_months = 0.0
    for entry in experience:
        text = entry if isinstance(entry, str) else str(entry)

        year_match = re.search(r"(\d+(?:\.\d+)?)\s*year", text, re.IGNORECASE)
        month_match = re.search(r"(\d+)\s*month", text, re.IGNORECASE)
        range_match = re.search(
            r"(20\d{2})\s*[-\u2013]\s*(20\d{2}|present|current)", text, re.IGNORECASE
        )

        if year_match:
            total_months += float(year_match.group(1)) * 12
            if month_match:
                total_months += int(month_match.group(1))
        elif month_match:
            total_months += int(month_match.group(1))
        elif range_match:
            start = int(range_match.group(1))
            end_str = range_match.group(2).lower()
            end = (
                datetime.date.today().year
                if end_str in ("present", "current")
                else int(end_str)
            )
            total_months += max(0, (end - start)) * 12

    return round(total_months / 12, 1)


def score_education(
    candidate_education: list[Any],
    required_education: str,
) -> tuple[float, dict[str, Any]]:
    """
    Ordinal degree ranking 1-5 (D-10). Meeting or exceeding → 100.
    Below requirement → partial score scaled by rank difference.
    """
    req_rank = _education_rank(required_education)
    cand_rank = _highest_education_rank(candidate_education)

    if req_rank == 0:
        score = 100.0
    elif cand_rank >= req_rank:
        score = 100.0
    else:
        score = round((cand_rank / req_rank) * 100, 2)

    score = max(0.0, min(100.0, score))

    return score, {
        "required_level": required_education,
        "candidate_level": _rank_to_label(cand_rank),
        "meets_requirement": cand_rank >= req_rank,
    }


def _education_rank(level: str) -> int:
    if not level:
        return 0
    cleaned = level.strip().lower()
    for key, rank in EDUCATION_RANK.items():
        if key in cleaned:
            return rank
    return 0


def _highest_education_rank(education: list[Any]) -> int:
    highest = 0
    for entry in education:
        text = entry if isinstance(entry, str) else str(entry)
        for key, rank in EDUCATION_RANK.items():
            if key in text.lower() and rank > highest:
                highest = rank
    return highest


def _rank_to_label(rank: int) -> str:
    mapping = {
        0: "Unknown",
        1: "High School",
        2: "Associate",
        3: "Bachelor",
        4: "Master",
        5: "PhD",
    }
    return mapping.get(rank, "Unknown")


def score_certifications(
    candidate_certs: list[str],
    required_certs: list[str],
    preferred_certs: list[str],
) -> tuple[float, dict[str, Any], bool]:
    """
    Score certifications with omit-fallback (D-11).
    If the job has no certs at all → returns (0, {}, has_certs=False)
    to signal weight redistribution.
    Otherwise: 80/20 required/preferred weighting.
    """
    has_certs = bool(required_certs or preferred_certs)

    if not has_certs:
        return 0.0, {"omitted": True, "reason": "Job has no certification requirements"}, False

    cand_norm = set(c.strip().lower() for c in candidate_certs)
    req_norm = [c.strip() for c in required_certs]
    pref_norm = [c.strip() for c in preferred_certs]

    req_matched = [c for c in req_norm if c.lower() in cand_norm]
    req_missing = [c for c in req_norm if c.lower() not in cand_norm]
    pref_matched = [c for c in pref_norm if c.lower() in cand_norm]
    pref_missing = [c for c in pref_norm if c.lower() not in cand_norm]

    req_score = (len(req_matched) / len(req_norm) * 100) if req_norm else 100.0
    pref_score = (len(pref_matched) / len(pref_norm) * 100) if pref_norm else 100.0

    if req_norm and pref_norm:
        score = req_score * 0.8 + pref_score * 0.2
    elif req_norm:
        score = req_score
    else:
        score = pref_score

    return round(score, 2), {
        "required_matched": req_matched,
        "required_missing": req_missing,
        "preferred_matched": pref_matched,
        "preferred_missing": pref_missing,
    }, True


def score_projects(
    candidate_projects: list[Any],
    required_skills: list[str],
) -> tuple[float, dict[str, Any]]:
    """
    Score projects by keyword overlap with required skills/terms (D-12).
    """
    if not required_skills:
        return 100.0, {"matched_keywords": [], "missing_keywords": [], "total_keywords": 0}

    project_text = " ".join(
        entry if isinstance(entry, str) else str(entry)
        for entry in candidate_projects
    ).lower()

    matched = []
    for skill in required_skills:
        normalized = normalize_skill(skill).lower()
        if normalized in project_text or skill.lower() in project_text:
            matched.append(skill)

    score = round((len(matched) / len(required_skills)) * 100, 2)
    return score, {
        "matched_keywords": matched,
        "missing_keywords": [s for s in required_skills if s not in matched],
        "total_keywords": len(required_skills),
    }


def score_semantic(
    candidate_text: str,
    job_text: str,
) -> tuple[float, dict[str, Any]]:
    """
    Compute semantic similarity using all-MiniLM-L6-v2 (D-05).
    Min-max scale cosine similarity from [0.3, 0.8] → [0, 100] (D-08).
    """
    model = _get_model()
    embeddings = model.encode([candidate_text, job_text])
    raw_cosine = float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])

    # Min-max scaling (D-08)
    scaled = (raw_cosine - SIM_LOW) / (SIM_HIGH - SIM_LOW) * 100
    score = round(max(0.0, min(100.0, scaled)), 2)

    return score, {
        "raw_cosine": round(raw_cosine, 4),
        "scaled_score": score,
    }


# ---------------------------------------------------------------------------
# Text builders for semantic comparison (D-07)
# ---------------------------------------------------------------------------

def build_job_text(job: Any) -> str:
    """Build job comparison text from title, department, description, skills (D-07)."""
    parts = [
        getattr(job, "title", "") or "",
        getattr(job, "department", "") or "",
        getattr(job, "description", "") or "",
    ]
    req_skills = getattr(job, "required_skills", []) or []
    pref_skills = getattr(job, "preferred_skills", []) or []
    parts.append(" ".join(req_skills + pref_skills))
    return " ".join(p for p in parts if p)


def build_candidate_text(candidate: Any) -> str:
    """Build candidate comparison text from skills, experience, projects (D-07)."""
    skills = getattr(candidate, "skills", []) or []
    experience = getattr(candidate, "experience", []) or []
    projects = getattr(candidate, "projects", []) or []

    exp_text = " ".join(e if isinstance(e, str) else str(e) for e in experience)
    proj_text = " ".join(p if isinstance(p, str) else str(p) for p in projects)
    skills_text = " ".join(skills)

    return f"{skills_text} {exp_text} {proj_text}".strip()


# ---------------------------------------------------------------------------
# Main ScreeningEngine
# ---------------------------------------------------------------------------

class ScreeningEngine:
    """
    Computes explainable match scores for a candidate-job pair.

    All scoring is deterministic and entirely local (SCR-05).
    Call screen(candidate, job) to get a full breakdown dict.
    """

    def screen(self, candidate: Any, job: Any) -> dict[str, Any]:
        """
        Run all scoring dimensions and return a structured result dict.

        Returns:
            {
              "overall_score": float,
              "skills_score": float,
              "experience_score": float,
              "education_score": float,
              "projects_score": float,
              "certification_score": float | None,
              "semantic_score": float,
              "explanation": { ... dimension breakdowns ... }
            }
        """
        # Extract job weights (all default to 20 if missing)
        w_skills = getattr(job, "weight_skills", 20) or 20
        w_exp = getattr(job, "weight_experience", 20) or 20
        w_edu = getattr(job, "weight_education", 20) or 20
        w_proj = getattr(job, "weight_projects", 20) or 20
        w_cert = getattr(job, "weight_certs", 20) or 20

        # Compute all dimension scores
        skills_score, skills_breakdown = score_skills(
            candidate_skills=getattr(candidate, "skills", []) or [],
            required_skills=getattr(job, "required_skills", []) or [],
            preferred_skills=getattr(job, "preferred_skills", []) or [],
        )

        exp_score, exp_breakdown = score_experience(
            candidate_experience=getattr(candidate, "experience", []) or [],
            min_exp=getattr(job, "min_experience", 0) or 0,
            max_exp=getattr(job, "max_experience", 99) or 99,
        )

        edu_score, edu_breakdown = score_education(
            candidate_education=getattr(candidate, "education", []) or [],
            required_education=getattr(job, "education_requirement", "") or "",
        )

        proj_score, proj_breakdown = score_projects(
            candidate_projects=getattr(candidate, "projects", []) or [],
            required_skills=getattr(job, "required_skills", []) or [],
        )

        cert_score, cert_breakdown, has_certs = score_certifications(
            candidate_certs=getattr(candidate, "certifications", []) or [],
            required_certs=getattr(job, "required_certs", []) or [],
            preferred_certs=getattr(job, "preferred_certs", []) or [],
        )

        semantic_score, semantic_breakdown = score_semantic(
            candidate_text=build_candidate_text(candidate),
            job_text=build_job_text(job),
        )

        # Compute overall weighted score (D-11: omit cert weight if no certs)
        if has_certs:
            total_weight = w_skills + w_exp + w_edu + w_proj + w_cert
            raw_overall = (
                skills_score * w_skills
                + exp_score * w_exp
                + edu_score * w_edu
                + proj_score * w_proj
                + cert_score * w_cert
            ) / total_weight if total_weight > 0 else 0.0
        else:
            # Redistribute cert weight to other dimensions equally (D-11)
            total_weight = w_skills + w_exp + w_edu + w_proj
            raw_overall = (
                skills_score * w_skills
                + exp_score * w_exp
                + edu_score * w_edu
                + proj_score * w_proj
            ) / total_weight if total_weight > 0 else 0.0

        # Blend semantic: 80% weighted dimensional, 20% semantic signal
        overall_score = round(raw_overall * 0.8 + semantic_score * 0.2, 2)

        return {
            "overall_score": overall_score,
            "skills_score": skills_score,
            "experience_score": exp_score,
            "education_score": edu_score,
            "projects_score": proj_score,
            "certification_score": cert_score if has_certs else None,
            "semantic_score": semantic_score,
            "explanation": {
                "skills": skills_breakdown,
                "experience": exp_breakdown,
                "education": edu_breakdown,
                "projects": proj_breakdown,
                "certifications": cert_breakdown,
                "semantic": semantic_breakdown,
            },
        }
