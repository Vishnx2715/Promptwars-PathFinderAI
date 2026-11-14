"""Section 3 interview models."""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    career_role_id: Mapped[int] = mapped_column(Integer, ForeignKey("career_roles.id", ondelete="CASCADE"), index=True, nullable=False)
    interview_type: Mapped[str] = mapped_column(String(50), nullable=False)  # technical, behavioral, project, mixed
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="created", nullable=False)
    overall_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    student_profile: Mapped["StudentProfile"] = relationship("StudentProfile")
    career_role: Mapped["CareerRole"] = relationship("CareerRole")
    questions: Mapped[List["InterviewQuestion"]] = relationship("InterviewQuestion", back_populates="session", cascade="all, delete-orphan", order_by="InterviewQuestion.order_index")


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    interview_session_id: Mapped[int] = mapped_column(Integer, ForeignKey("interview_sessions.id", ondelete="CASCADE"), index=True, nullable=False)
    question_text: Mapped[str] = mapped_column(String(2000), nullable=False)
    question_type: Mapped[str] = mapped_column(String(50), nullable=False)  # technical, behavioral, project, scenario
    skill_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("skills.id", ondelete="SET NULL"), nullable=True)
    expected_answer_points: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    session: Mapped["InterviewSession"] = relationship("InterviewSession", back_populates="questions")
    response: Mapped[Optional["InterviewResponse"]] = relationship("InterviewResponse", back_populates="question", uselist=False, cascade="all, delete-orphan")


class InterviewResponse(Base):
    __tablename__ = "interview_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    interview_question_id: Mapped[int] = mapped_column(Integer, ForeignKey("interview_questions.id", ondelete="CASCADE"), index=True, nullable=False)
    student_answer: Mapped[str] = mapped_column(String(10000), nullable=False)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    feedback: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    question: Mapped["InterviewQuestion"] = relationship("InterviewQuestion", back_populates="response")
