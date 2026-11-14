from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class LearningActivity(Base):
    __tablename__ = "learning_activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    activity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # "resource_completed", "assessment_completed", "coding_problem_attempted",
    # "project_submitted", "roadmap_replanned", "mentor_feedback"
    reference_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    meta: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    student_profile: Mapped["StudentProfile"] = relationship("StudentProfile")
