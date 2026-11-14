from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class ProjectSubmission(Base):
    __tablename__ = "project_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    project_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "frontend", "backend", "full_stack", "data_analysis", "machine_learning"
    description: Mapped[str] = mapped_column(String(5000), nullable=False)
    github_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    live_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)  # "pending", "evaluating", "evaluated", "failed"
    evaluation_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    evaluation_report: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    evaluated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    student_profile: Mapped["StudentProfile"] = relationship("StudentProfile")


class ProjectRubric(Base):
    __tablename__ = "project_rubrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_type: Mapped[str] = mapped_column(String(50), nullable=False)
    career_role_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("career_roles.id", ondelete="SET NULL"), nullable=True)
    criteria: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False)
    total_weight: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
