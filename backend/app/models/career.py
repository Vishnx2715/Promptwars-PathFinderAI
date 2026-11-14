from typing import Optional, List
from sqlalchemy import Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class CareerRole(Base):
    __tablename__ = "career_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    requirements: Mapped[List["RoleSkillRequirement"]] = relationship(
        "RoleSkillRequirement", back_populates="career_role", cascade="all, delete-orphan"
    )


class RoleSkillRequirement(Base):
    __tablename__ = "role_skill_requirements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    career_role_id: Mapped[int] = mapped_column(Integer, ForeignKey("career_roles.id", ondelete="CASCADE"), index=True, nullable=False)
    skill_id: Mapped[int] = mapped_column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), index=True, nullable=False)
    required_level: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    weight: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_prerequisite_for: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    prerequisite_skill_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("skills.id", ondelete="SET NULL"), index=True, nullable=True)

    career_role: Mapped["CareerRole"] = relationship("CareerRole", back_populates="requirements")
    skill: Mapped["Skill"] = relationship("Skill", foreign_keys=[skill_id], back_populates="requirements")
    prerequisite_skill: Mapped[Optional["Skill"]] = relationship("Skill", foreign_keys=[prerequisite_skill_id])
