from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    education_level: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    experience_level: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    weekly_study_hours: Mapped[int] = mapped_column(Integer, default=8, nullable=False)
    learning_preference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    target_role_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("career_roles.id", ondelete="SET NULL"), index=True, nullable=True)
    career_goal_changed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    projects: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, default=list, nullable=True)
    certifications: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, default=list, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="profile")
    target_role: Mapped[Optional["CareerRole"]] = relationship("CareerRole")
    learner_skills: Mapped[List["LearnerSkill"]] = relationship("LearnerSkill", back_populates="student_profile", cascade="all, delete-orphan")
    assessment_attempts: Mapped[List["AssessmentAttempt"]] = relationship("AssessmentAttempt", back_populates="student_profile", cascade="all, delete-orphan")
    learning_paths: Mapped[List["LearningPath"]] = relationship("LearningPath", back_populates="student_profile", cascade="all, delete-orphan")
