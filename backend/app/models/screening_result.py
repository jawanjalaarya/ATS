from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON
from sqlalchemy.sql import func

from app.core.database import Base


class ScreeningResult(Base):
    """Maps the existing screening_results table from initial migration.

    Stores per-dimension scores and structured explanation JSON
    for each application (candidate-job pair).
    """

    __tablename__ = "screening_results"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(
        Integer,
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    overall_score = Column(Float, nullable=True)
    skills_score = Column(Float, nullable=True)
    experience_score = Column(Float, nullable=True)
    education_score = Column(Float, nullable=True)
    projects_score = Column(Float, nullable=True)
    certification_score = Column(Float, nullable=True)
    semantic_score = Column(Float, nullable=True)
    explanation = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
