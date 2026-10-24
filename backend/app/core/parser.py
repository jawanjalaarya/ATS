"""Resume text extraction and heuristic profile parsing.

Extracts text from PDF (PyMuPDF) and DOCX (python-docx) files,
then parses structured candidate profile data using regex heuristics.
"""

import re
from pathlib import Path

import fitz  # PyMuPDF
from docx import Document


# ---------------------------------------------------------------------------
# Skills normalization lexicon (lowercase variant → canonical name)
# ---------------------------------------------------------------------------

SKILLS_LEXICON: dict[str, str] = {
    "python": "Python",
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "react": "React",
    "reactjs": "React",
    "react.js": "React",
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "ml": "Machine Learning",
    "machine learning": "Machine Learning",
    "ai": "Artificial Intelligence",
    "artificial intelligence": "Artificial Intelligence",
    "aws": "AWS",
    "docker": "Docker",
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "sql": "SQL",
    "nosql": "NoSQL",
    "mongodb": "MongoDB",
    "mongo": "MongoDB",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "java": "Java",
    "c++": "C++",
    "cpp": "C++",
    "c#": "C#",
    "csharp": "C#",
    "go": "Go",
    "golang": "Go",
    "rust": "Rust",
    "ruby": "Ruby",
    "php": "PHP",
    "swift": "Swift",
    "kotlin": "Kotlin",
    "scala": "Scala",
    "html": "HTML",
    "css": "CSS",
    "sass": "Sass",
    "scss": "Sass",
    "tailwind": "Tailwind CSS",
    "tailwindcss": "Tailwind CSS",
    "tailwind css": "Tailwind CSS",
    "vue": "Vue.js",
    "vuejs": "Vue.js",
    "vue.js": "Vue.js",
    "angular": "Angular",
    "svelte": "Svelte",
    "nextjs": "Next.js",
    "next.js": "Next.js",
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "spring": "Spring",
    "graphql": "GraphQL",
    "rest": "REST",
    "git": "Git",
    "ci/cd": "CI/CD",
    "cicd": "CI/CD",
    "terraform": "Terraform",
    "linux": "Linux",
    "redis": "Redis",
    "elasticsearch": "Elasticsearch",
    "kafka": "Kafka",
    "rabbitmq": "RabbitMQ",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "scipy": "SciPy",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "keras": "Keras",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "express": "Express.js",
    "expressjs": "Express.js",
    "mysql": "MySQL",
    "sqlite": "SQLite",
    "firebase": "Firebase",
    "azure": "Azure",
    "gcp": "GCP",
    "heroku": "Heroku",
    "nginx": "Nginx",
    "apache": "Apache",
    "jenkins": "Jenkins",
    "github actions": "GitHub Actions",
    "gitlab ci": "GitLab CI",
    "ansible": "Ansible",
    "prometheus": "Prometheus",
    "grafana": "Grafana",
}


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file using PyMuPDF.

    Returns empty string on any extraction failure.
    """
    try:
        doc = fitz.open(file_path)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        return "\n".join(text_parts)
    except Exception:
        return ""


def extract_text_from_docx(file_path: str) -> str:
    """Extract text from a DOCX file using python-docx.

    Returns empty string on any extraction failure.
    """
    try:
        doc = Document(file_path)
        return "\n".join(paragraph.text for paragraph in doc.paragraphs)
    except Exception:
        return ""


def extract_text(file_path: str) -> str:
    """Dispatch to PDF or DOCX extractor based on file extension.

    Raises ValueError for unsupported file extensions.
    """
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".docx":
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file extension: {ext}")


# ---------------------------------------------------------------------------
# Skills normalization
# ---------------------------------------------------------------------------


def normalize_skills(raw_skills: list[str]) -> list[str]:
    """Normalize skills against the lexicon using case-insensitive matching.

    Unknown skills are title-cased. Results are deduplicated preserving order.
    """
    seen: set[str] = set()
    normalized: list[str] = []
    for skill in raw_skills:
        key = skill.strip().lower()
        if not key:
            continue
        canonical = SKILLS_LEXICON.get(key, skill.strip().title())
        if canonical not in seen:
            seen.add(canonical)
            normalized.append(canonical)
    return normalized


# ---------------------------------------------------------------------------
# Section extraction helpers
# ---------------------------------------------------------------------------

# Common section header patterns (case-insensitive)
_SECTION_HEADERS = [
    "SKILLS",
    "TECHNICAL SKILLS",
    "TECHNOLOGIES",
    "COMPETENCIES",
    "EDUCATION",
    "EXPERIENCE",
    "WORK EXPERIENCE",
    "PROFESSIONAL EXPERIENCE",
    "PROJECTS",
    "CERTIFICATIONS",
    "CERTIFICATES",
    "ACHIEVEMENTS",
    "AWARDS",
    "HONORS",
    "SUMMARY",
    "OBJECTIVE",
    "PROFILE",
    "CONTACT",
    "REFERENCES",
    "PUBLICATIONS",
    "LANGUAGES",
    "INTERESTS",
    "VOLUNTEER",
]

_SECTION_PATTERN = re.compile(
    r"^\s*(?:" + "|".join(re.escape(h) for h in _SECTION_HEADERS) + r")\s*:?\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def _extract_section(text: str, header_patterns: list[str]) -> list[str]:
    """Extract content between a section header and the next section header.

    Returns list of non-empty lines in the section.
    """
    # Build pattern for the target section header
    header_re = re.compile(
        r"^\s*(?:" + "|".join(re.escape(h) for h in header_patterns) + r")\s*:?\s*$",
        re.IGNORECASE | re.MULTILINE,
    )

    match = header_re.search(text)
    if not match:
        return []

    # Find start of content (after header line)
    start = match.end()

    # Find next section header
    next_section = _SECTION_PATTERN.search(text, start)
    end = next_section.start() if next_section else len(text)

    section_text = text[start:end].strip()
    if not section_text:
        return []

    # Split into lines and filter empties
    lines = [line.strip() for line in section_text.split("\n") if line.strip()]
    return lines


# ---------------------------------------------------------------------------
# Resume text parsing
# ---------------------------------------------------------------------------

# Regex patterns for contact info extraction
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(r"[\+]?[(]?[0-9]{1,4}[)]?[-\s./0-9]{7,}")
_LINKEDIN_RE = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+")
_GITHUB_RE = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[\w-]+")
_PORTFOLIO_RE = re.compile(
    r"(?:https?://)?(?:www\.)?[\w-]+\.(?:com|io|dev|me|org|net)/[\w/\-]*"
)
_LOCATION_RE = re.compile(
    r"([A-Z][a-zA-Z\s]+,\s*[A-Z][a-zA-Z\s]+)"
)


def parse_resume_text(text: str) -> dict:
    """Parse raw resume text into structured profile fields using regex heuristics.

    Returns a dict with keys: name, email, phone, location, linkedin_url,
    github_url, portfolio_url, skills, education, experience, projects,
    certifications, achievements.
    """
    if not text or not text.strip():
        return {
            "name": None,
            "email": None,
            "phone": None,
            "location": None,
            "linkedin_url": None,
            "github_url": None,
            "portfolio_url": None,
            "skills": [],
            "education": [],
            "experience": [],
            "projects": [],
            "certifications": [],
            "achievements": [],
        }

    # --- Contact information ---
    email_match = _EMAIL_RE.search(text)
    email = email_match.group(0) if email_match else None

    phone_match = _PHONE_RE.search(text)
    phone = phone_match.group(0).strip() if phone_match else None

    linkedin_match = _LINKEDIN_RE.search(text)
    linkedin_url = linkedin_match.group(0) if linkedin_match else None

    github_match = _GITHUB_RE.search(text)
    github_url = github_match.group(0) if github_match else None

    # Portfolio: exclude linkedin and github matches
    portfolio_url = None
    for m in _PORTFOLIO_RE.finditer(text):
        url = m.group(0)
        if "linkedin.com" not in url and "github.com" not in url:
            portfolio_url = url
            break

    # --- Name: first non-empty line (stripped, max 100 chars) ---
    name = None
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped:
            name = stripped[:100]
            break

    # --- Location: "City, State/Country" pattern in first 500 chars ---
    location = None
    location_match = _LOCATION_RE.search(text[:500])
    if location_match:
        location = location_match.group(1).strip()

    # --- Skills section ---
    skills_lines = _extract_section(
        text, ["SKILLS", "TECHNICAL SKILLS", "TECHNOLOGIES", "COMPETENCIES"]
    )
    raw_skills: list[str] = []
    for line in skills_lines:
        # Split by comma, pipe, bullet, or semicolon
        items = re.split(r"[,|;•·▪►▸–—\-]\s*|\s{2,}", line)
        raw_skills.extend(item.strip() for item in items if item.strip())
    skills = normalize_skills(raw_skills)

    # --- Structured sections ---
    education = _extract_section(text, ["EDUCATION"])
    experience = _extract_section(
        text, ["EXPERIENCE", "WORK EXPERIENCE", "PROFESSIONAL EXPERIENCE"]
    )
    projects = _extract_section(text, ["PROJECTS"])
    certifications = _extract_section(text, ["CERTIFICATIONS", "CERTIFICATES"])
    achievements = _extract_section(text, ["ACHIEVEMENTS", "AWARDS", "HONORS"])

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "location": location,
        "linkedin_url": linkedin_url,
        "github_url": github_url,
        "portfolio_url": portfolio_url,
        "skills": skills,
        "education": education,
        "experience": experience,
        "projects": projects,
        "certifications": certifications,
        "achievements": achievements,
    }


# ---------------------------------------------------------------------------
# Parse status determination
# ---------------------------------------------------------------------------


def determine_parse_status(parsed: dict) -> str:
    """Determine if parse result is complete or needs review.

    Returns "complete" if both name and email are present and non-empty,
    otherwise "pending_review" per D-10.
    """
    name = parsed.get("name")
    email = parsed.get("email")
    if name and email:
        return "complete"
    return "pending_review"
