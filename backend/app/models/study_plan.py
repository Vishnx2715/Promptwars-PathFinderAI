"""Section 3 weekly study plan and career readiness report models."""
from datetime import datetime, date, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import Integer, String, Float, DateTime, Date, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class WeeklyStudyPlan(Base):
    __tablename__ = "weekly_study_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    career_role_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("career_roles.id", ondelete="SET NULL"), nullable=True)
    week_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    weekly_hours: Mapped[int] = mapped_column(Integer, default=8, nullable=False)
    planned_hours: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    completed_hours: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    plan: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    student_profile: Mapped["StudentProfile"] = relationship("StudentProfile")
    tasks: Mapped[List["StudyTask"]] = relationship("StudyTask", back_populates="plan", cascade="all, delete-orphan")


class StudyTask(Base):
    __tablename__ = "study_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    weekly_study_plan_id: Mapped[int] = mapped_column(Integer, ForeignKey("weekly_study_plans.id", ondelete="CASCADE"), index=True, nullable=False)
    roadmap_module_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("roadmap_modules.id", ondelete="SET NULL"), nullable=True)
    skill_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("skills.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # resource, practice, assessment, project, revision, college_assignment
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    day: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    plan: Mapped["WeeklyStudyPlan"] = relationship("WeeklyStudyPlan", back_populates="tasks")


class CareerReadinessReport(Base):
    __tablename__ = "career_readiness_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # career_readiness, skill_progress, assessment, project_portfolio
    file_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    report_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    student_profile: Mapped["StudentProfile"] = relationship("StudentProfile")
