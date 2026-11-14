from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class LearningPath(Base):
    __tablename__ = "learning_paths"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    career_role_id: Mapped[int] = mapped_column(Integer, ForeignKey("career_roles.id", ondelete="CASCADE"), index=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)  # "active", "archived"
    readiness_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    replan_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    student_profile: Mapped["StudentProfile"] = relationship("StudentProfile", back_populates="learning_paths")
    career_role: Mapped["CareerRole"] = relationship("CareerRole")
    modules: Mapped[List["RoadmapModule"]] = relationship(
        "RoadmapModule", back_populates="learning_path", cascade="all, delete-orphan", order_by="RoadmapModule.order_index"
    )


class RoadmapModule(Base):
    __tablename__ = "roadmap_modules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    learning_path_id: Mapped[int] = mapped_column(Integer, ForeignKey("learning_paths.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    skill_id: Mapped[int] = mapped_column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), index=True, nullable=False)
    phase: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    estimated_hours: Mapped[float] = mapped_column(Float, default=10.0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="locked", nullable=False)  # "locked", "available", "in_progress", "completed", "needs_revision"
    prerequisite_module_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("roadmap_modules.id", ondelete="SET NULL"), index=True, nullable=True)
    min_mastery_to_unlock: Mapped[float] = mapped_column(Float, default=70.0, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    learning_path: Mapped["LearningPath"] = relationship("LearningPath", back_populates="modules")
    skill: Mapped["Skill"] = relationship("Skill")
    prerequisite_module: Mapped[Optional["RoadmapModule"]] = relationship("RoadmapModule", remote_side=[id])
    resources: Mapped[List["RoadmapResource"]] = relationship("RoadmapResource", back_populates="roadmap_module", cascade="all, delete-orphan")


class RoadmapResource(Base):
    __tablename__ = "roadmap_resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    roadmap_module_id: Mapped[int] = mapped_column(Integer, ForeignKey("roadmap_modules.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), default="documentation", nullable=False)  # "course", "documentation", "video", "exercise", "project"
    difficulty: Mapped[str] = mapped_column(String(50), default="medium", nullable=False)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    roadmap_module: Mapped["RoadmapModule"] = relationship("RoadmapModule", back_populates="resources")
