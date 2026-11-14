from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    requirements: Mapped[list["RoleSkillRequirement"]] = relationship("RoleSkillRequirement", back_populates="skill", foreign_keys="RoleSkillRequirement.skill_id")
    learner_skills: Mapped[list["LearnerSkill"]] = relationship("LearnerSkill", back_populates="skill")
    assessments: Mapped[list["Assessment"]] = relationship("Assessment", back_populates="skill")


class LearnerSkill(Base):
    __tablename__ = "learner_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    skill_id: Mapped[int] = mapped_column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), index=True, nullable=False)
    self_reported_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 0-5
    verified_level: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # 0-5
    evidence_type: Mapped[str] = mapped_column(String(50), default="self_report", nullable=False)  # "self_report", "assessment", "project", "mentor"
    last_assessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    mastery_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    student_profile: Mapped["StudentProfile"] = relationship("StudentProfile", back_populates="learner_skills")
    skill: Mapped["Skill"] = relationship("Skill", back_populates="learner_skills")
