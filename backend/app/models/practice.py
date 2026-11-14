from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import Integer, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class CodingProblem(Base):
    __tablename__ = "coding_problems"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(5000), nullable=False)
    language: Mapped[str] = mapped_column(String(50), nullable=False)  # "javascript", "python"
    skill_id: Mapped[int] = mapped_column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), index=True, nullable=False)
    subtopic: Mapped[str] = mapped_column(String(100), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(50), default="medium", nullable=False)  # "easy", "medium", "hard"
    starter_code: Mapped[str] = mapped_column(String(5000), nullable=False)
    function_name: Mapped[str] = mapped_column(String(200), nullable=False)
    test_cases: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False)
    examples: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, default=list, nullable=True)
    constraints: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    skill: Mapped["Skill"] = relationship("Skill")
    submissions: Mapped[List["CodeSubmission"]] = relationship("CodeSubmission", back_populates="problem", cascade="all, delete-orphan")


class CodeSubmission(Base):
    __tablename__ = "code_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    coding_problem_id: Mapped[int] = mapped_column(Integer, ForeignKey("coding_problems.id", ondelete="CASCADE"), index=True, nullable=False)
    language: Mapped[str] = mapped_column(String(50), nullable=False)
    submitted_code: Mapped[str] = mapped_column(String(20000), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="error", nullable=False)  # "passed", "failed", "error", "timeout"
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    tests_passed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tests_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    runtime_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    execution_output: Mapped[Optional[str]] = mapped_column(String(10000), nullable=True)
    ai_review: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    student_profile: Mapped["StudentProfile"] = relationship("StudentProfile")
    problem: Mapped["CodingProblem"] = relationship("CodingProblem", back_populates="submissions")


class PracticeSession(Base):
    __tablename__ = "practice_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    skill_id: Mapped[int] = mapped_column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), index=True, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    problems_attempted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    problems_solved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    accuracy: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    student_profile: Mapped["StudentProfile"] = relationship("StudentProfile")
    skill: Mapped["Skill"] = relationship("Skill")
