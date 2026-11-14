from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Mentor(Base):
    __tablename__ = "mentors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    expertise: Mapped[str] = mapped_column(String(500), nullable=False)
    mentor_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    user: Mapped["User"] = relationship("User")
    connections: Mapped[List["MentorConnection"]] = relationship("MentorConnection", back_populates="mentor", cascade="all, delete-orphan")
    feedback: Mapped[List["MentorFeedback"]] = relationship("MentorFeedback", back_populates="mentor", cascade="all, delete-orphan")
    doubts: Mapped[List["MentorDoubt"]] = relationship("MentorDoubt", back_populates="mentor")


class MentorConnection(Base):
    __tablename__ = "mentor_connections"
    __table_args__ = (
        # Ensure one active connection per student-mentor pair
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    mentor_id: Mapped[int] = mapped_column(Integer, ForeignKey("mentors.id", ondelete="CASCADE"), index=True, nullable=False)
    mentor_code: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="connected", nullable=False)  # "connected", "disconnected"
    connected_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    student_profile: Mapped["StudentProfile"] = relationship("StudentProfile")
    mentor: Mapped["Mentor"] = relationship("Mentor", back_populates="connections")


class MentorFeedback(Base):
    __tablename__ = "mentor_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    mentor_id: Mapped[int] = mapped_column(Integer, ForeignKey("mentors.id", ondelete="CASCADE"), index=True, nullable=False)
    roadmap_module_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("roadmap_modules.id", ondelete="SET NULL"), nullable=True)
    feedback_type: Mapped[str] = mapped_column(String(50), default="general", nullable=False)  # "general", "roadmap", "project", "assessment"
    comment: Mapped[str] = mapped_column(String(2000), nullable=False)
    recommended_action: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    student_profile: Mapped["StudentProfile"] = relationship("StudentProfile")
    mentor: Mapped["Mentor"] = relationship("Mentor", back_populates="feedback")


class MentorDoubt(Base):
    __tablename__ = "mentor_doubts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    mentor_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("mentors.id", ondelete="SET NULL"), index=True, nullable=True)
    skill_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("skills.id", ondelete="SET NULL"), nullable=True)
    roadmap_module_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("roadmap_modules.id", ondelete="SET NULL"), nullable=True)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    question: Mapped[str] = mapped_column(String(5000), nullable=False)
    attachment_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    ai_draft_answer: Mapped[Optional[str]] = mapped_column(String(5000), nullable=True)
    mentor_response: Mapped[Optional[str]] = mapped_column(String(5000), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="open", nullable=False)  # "open", "answered", "resolved"
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    answered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    student_profile: Mapped["StudentProfile"] = relationship("StudentProfile")
    mentor: Mapped[Optional["Mentor"]] = relationship("Mentor", back_populates="doubts")
    skill: Mapped[Optional["Skill"]] = relationship("Skill")
