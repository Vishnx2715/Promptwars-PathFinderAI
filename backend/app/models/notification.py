"""Section 3 notification and recommendation models."""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    message: Mapped[str] = mapped_column(String(1000), nullable=False)
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # assessment, roadmap, mentor, project, interview, college, system
    reference_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reference_path: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user: Mapped["User"] = relationship("User")


class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    recommendation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # next_action, resource, career, project, interview, revision, college
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(String(2000), nullable=False)
    reason: Mapped[str] = mapped_column(String(1000), nullable=False)
    evidence: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    action_path: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    estimated_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    student_profile: Mapped["StudentProfile"] = relationship("StudentProfile")
