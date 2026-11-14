"""Section 3 portfolio, leaderboard, and skill-decay models."""
from datetime import datetime, date, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import Integer, String, Float, DateTime, Date, ForeignKey, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class PortfolioProfile(Base):
    __tablename__ = "portfolio_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    github_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    leetcode_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    hackerrank_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    problems_solved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    portfolio_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    show_in_leaderboard: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_activity_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    student_profile: Mapped["StudentProfile"] = relationship("StudentProfile")


class SkillDecayAlert(Base):
    __tablename__ = "skill_decay_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    skill_id: Mapped[int] = mapped_column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), index=True, nullable=False)
    last_practiced_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    days_since_practice: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    previous_mastery: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    current_mastery: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    alert_level: Mapped[str] = mapped_column(String(20), default="info", nullable=False)  # info, warning, critical
    recommended_action: Mapped[str] = mapped_column(String(500), nullable=False)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    student_profile: Mapped["StudentProfile"] = relationship("StudentProfile")
    skill: Mapped["Skill"] = relationship("Skill")


class Campus(Base):
    __tablename__ = "campuses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    courses: Mapped[List["CollegeCourse"]] = relationship("CollegeCourse", back_populates="campus", cascade="all, delete-orphan")


class LeaderboardEntry(Base):
    __tablename__ = "leaderboard_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    campus_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("campuses.id", ondelete="SET NULL"), index=True, nullable=True)
    period_type: Mapped[str] = mapped_column(String(20), nullable=False)  # weekly, monthly, all_time
    period_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    period_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    practice_points: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    assessment_points: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    project_points: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    consistency_points: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_points: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    student_profile: Mapped["StudentProfile"] = relationship("StudentProfile")
    campus: Mapped[Optional["Campus"]] = relationship("Campus")
