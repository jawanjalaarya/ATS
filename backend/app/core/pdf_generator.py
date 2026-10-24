"""Ephemeral PDF and CSV report generation (D-13, D-14, D-15, D-16).

Generates reports in-memory using BytesIO/StringIO and streams them
directly as FastAPI responses. No files are written to disk.

PDF generation uses ReportLab. CSV uses Python's built-in csv module.
Anonymous screening redaction is applied automatically when enabled (D-15).
"""

import csv
import io
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def generate_candidate_pdf(candidate_data: dict[str, Any], anonymous: bool = False) -> io.BytesIO:
    """Generate a styled PDF for a single candidate profile (D-14).

    Args:
        candidate_data: Dict with candidate fields.
        anonymous: If True, PII is redacted (D-15).

    Returns:
        BytesIO buffer containing the PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle("CandTitle", parent=styles["Heading1"], fontSize=18, spaceAfter=12)
    section_style = ParagraphStyle("Section", parent=styles["Heading2"], fontSize=13, spaceAfter=6)
    body_style = styles["Normal"]

    elements = []

    # Header
    name = candidate_data.get("name") or "Unknown"
    if anonymous:
        name = f"Candidate #{candidate_data.get('id', 0)}"

    elements.append(Paragraph(f"Candidate Profile: {name}", title_style))
    elements.append(Spacer(1, 12))

    # Contact info (redacted if anonymous)
    if not anonymous:
        contact_data = [
            ["Email", candidate_data.get("email") or "—"],
            ["Phone", candidate_data.get("phone") or "—"],
            ["Location", candidate_data.get("location") or "—"],
        ]
        contact_table = Table(contact_data, colWidths=[1.5 * inch, 4 * inch])
        contact_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(contact_table)
        elements.append(Spacer(1, 12))

    # Skills
    skills = candidate_data.get("skills") or []
    if skills:
        elements.append(Paragraph("Skills", section_style))
        elements.append(Paragraph(", ".join(skills), body_style))
        elements.append(Spacer(1, 10))

    # Experience
    experience = candidate_data.get("experience") or []
    if experience:
        elements.append(Paragraph("Experience", section_style))
        for exp in experience:
            if isinstance(exp, dict):
                title = exp.get("title", "")
                company = exp.get("company", "")
                elements.append(Paragraph(f"• {title} at {company}", body_style))
            else:
                elements.append(Paragraph(f"• {exp}", body_style))
        elements.append(Spacer(1, 10))

    # Education
    education = candidate_data.get("education") or []
    if education:
        elements.append(Paragraph("Education", section_style))
        for edu in education:
            if isinstance(edu, dict):
                degree = edu.get("degree", "")
                institution = edu.get("institution", "")
                elements.append(Paragraph(f"• {degree} — {institution}", body_style))
            else:
                elements.append(Paragraph(f"• {edu}", body_style))
        elements.append(Spacer(1, 10))

    # Status
    elements.append(Paragraph("Status", section_style))
    elements.append(Paragraph(candidate_data.get("status", "unknown"), body_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_candidates_csv(candidates: list[dict[str, Any]], anonymous: bool = False) -> io.StringIO:
    """Generate a CSV report of multiple candidates (D-14, D-15).

    Args:
        candidates: List of candidate dicts.
        anonymous: If True, PII columns are redacted.

    Returns:
        StringIO buffer containing the CSV.
    """
    buffer = io.StringIO()
    fieldnames = ["id", "name", "email", "phone", "location", "skills", "status", "created_at"]

    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()

    for c in candidates:
        row = {
            "id": c.get("id", ""),
            "name": f"Candidate #{c.get('id', 0)}" if anonymous else (c.get("name") or ""),
            "email": "" if anonymous else (c.get("email") or ""),
            "phone": "" if anonymous else (c.get("phone") or ""),
            "location": c.get("location") or "",
            "skills": ", ".join(c.get("skills") or []),
            "status": c.get("status") or "",
            "created_at": c.get("created_at") or "",
        }
        writer.writerow(row)

    buffer.seek(0)
    return buffer


def generate_job_report_pdf(job_data: dict[str, Any], applicants: list[dict[str, Any]], anonymous: bool = False) -> io.BytesIO:
    """Generate a PDF report for a job listing with its applicants (D-14).

    Args:
        job_data: Dict with job fields.
        applicants: List of candidate dicts linked to this job.
        anonymous: If True, applicant PII is redacted.

    Returns:
        BytesIO buffer containing the PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("JobTitle", parent=styles["Heading1"], fontSize=18, spaceAfter=12)
    section_style = ParagraphStyle("Section", parent=styles["Heading2"], fontSize=13, spaceAfter=6)

    elements = []

    # Job header
    elements.append(Paragraph(f"Job Report: {job_data.get('title', 'Unknown')}", title_style))
    elements.append(Spacer(1, 6))

    job_info = [
        ["Department", job_data.get("department") or "—"],
        ["Location", job_data.get("location") or "—"],
        ["Status", job_data.get("status") or "—"],
    ]
    job_table = Table(job_info, colWidths=[1.5 * inch, 4 * inch])
    job_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(job_table)
    elements.append(Spacer(1, 16))

    # Applicants section
    elements.append(Paragraph(f"Applicants ({len(applicants)})", section_style))
    elements.append(Spacer(1, 6))

    if applicants:
        table_data = [["#", "Name", "Skills", "Status"]]
        for i, a in enumerate(applicants, 1):
            name = f"Candidate #{a.get('id', 0)}" if anonymous else (a.get("name") or "—")
            skills = ", ".join((a.get("skills") or [])[:3])
            table_data.append([str(i), name, skills, a.get("status", "—")])

        t = Table(table_data, colWidths=[0.4 * inch, 2 * inch, 2.5 * inch, 1 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(t)
    else:
        elements.append(Paragraph("No applicants for this position.", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer
