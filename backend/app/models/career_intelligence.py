"""Section 3 career-intelligence models: resume, job matching, career advisor."""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, JSON, Boolean, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class ResumeUpload(Base):
    __tablename__ = "resume_uploads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)  # pdf, docx, txt
    extracted_text: Mapped[Optional[str]] = mapped_column(String(50000), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    extracted_profile: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    confirmed_skills: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    student_profile: Mapped["StudentProfile"] = relationship("StudentProfile")


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    company: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    job_description_text: Mapped[str] = mapped_column(String(20000), nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    extracted_requirements: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    student_profile: Mapped["StudentProfile"] = relationship("StudentProfile")


class JobMatch(Base):
    __tablename__ = "job_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    job_description_id: Mapped[int] = mapped_column(Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"), index=True, nullable=False)
    target_career_role_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("career_roles.id", ondelete="SET NULL"), nullable=True)
    overall_match_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    skill_match_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    experience_match_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    education_match_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    matched_skills: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    missing_skills: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    partial_skills: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    recommendations: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    student_profile: Mapped["StudentProfile"] = relationship("StudentProfile")
    job_description: Mapped["JobDescription"] = relationship("JobDescription")


class CareerRecommendation(Base):
    __tablename__ = "career_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    recommended_career_role_id: Mapped[int] = mapped_column(Integer, ForeignKey("career_roles.id", ondelete="CASCADE"), index=True, nullable=False)
    match_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    readiness_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reasons: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    transferable_skills: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    missing_skills: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    student_profile: Mapped["StudentProfile"] = relationship("StudentProfile")
    recommended_career_role: Mapped["CareerRole"] = relationship("CareerRole")
