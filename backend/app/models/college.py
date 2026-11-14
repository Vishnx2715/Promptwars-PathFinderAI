"""Section 3 college-connect models."""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import Integer, String, Float, DateTime, Date, ForeignKey, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class CollegeCourse(Base):
    __tablename__ = "college_courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    campus_id: Mapped[int] = mapped_column(Integer, ForeignKey("campuses.id", ondelete="CASCADE"), index=True, nullable=False)
    course_code: Mapped[str] = mapped_column(String(50), nullable=False)
    course_name: Mapped[str] = mapped_column(String(300), nullable=False)
    semester: Mapped[str] = mapped_column(String(50), nullable=False)
    syllabus: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    campus: Mapped["Campus"] = relationship("Campus", back_populates="courses")
    enrollments: Mapped[List["StudentCourseEnrollment"]] = relationship("StudentCourseEnrollment", back_populates="course", cascade="all, delete-orphan")
    schedules: Mapped[List["CourseSchedule"]] = relationship("CourseSchedule", back_populates="course", cascade="all, delete-orphan")
    assignments: Mapped[List["CollegeAssignment"]] = relationship("CollegeAssignment", back_populates="course", cascade="all, delete-orphan")


class StudentCourseEnrollment(Base):
    __tablename__ = "student_course_enrollments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    college_course_id: Mapped[int] = mapped_column(Integer, ForeignKey("college_courses.id", ondelete="CASCADE"), index=True, nullable=False)
    enrolled_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)

    student_profile: Mapped["StudentProfile"] = relationship("StudentProfile")
    course: Mapped["CollegeCourse"] = relationship("CollegeCourse", back_populates="enrollments")


class CourseSchedule(Base):
    __tablename__ = "course_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    college_course_id: Mapped[int] = mapped_column(Integer, ForeignKey("college_courses.id", ondelete="CASCADE"), index=True, nullable=False)
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    topics: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    learning_objectives: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    related_skill_ids: Mapped[Optional[List[int]]] = mapped_column(JSON, nullable=True)
    lecture_recording_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    course: Mapped["CollegeCourse"] = relationship("CollegeCourse", back_populates="schedules")


class CollegeAssignment(Base):
    __tablename__ = "college_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    college_course_id: Mapped[int] = mapped_column(Integer, ForeignKey("college_courses.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(String(2000), nullable=False)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    max_marks: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    related_skill_ids: Mapped[Optional[List[int]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    course: Mapped["CollegeCourse"] = relationship("CollegeCourse", back_populates="assignments")
    submissions: Mapped[List["AssignmentSubmission"]] = relationship("AssignmentSubmission", back_populates="assignment", cascade="all, delete-orphan")


class AssignmentSubmission(Base):
    __tablename__ = "assignment_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    college_assignment_id: Mapped[int] = mapped_column(Integer, ForeignKey("college_assignments.id", ondelete="CASCADE"), index=True, nullable=False)
    student_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    submission_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    marks: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    graded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    assignment: Mapped["CollegeAssignment"] = relationship("CollegeAssignment", back_populates="submissions")
    student_profile: Mapped["StudentProfile"] = relationship("StudentProfile")


class CollegeAnnouncement(Base):
    __tablename__ = "college_announcements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    campus_id: Mapped[int] = mapped_column(Integer, ForeignKey("campuses.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    message: Mapped[str] = mapped_column(String(3000), nullable=False)
    audience: Mapped[str] = mapped_column(String(50), default="all", nullable=False)
    related_course_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("college_courses.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    campus: Mapped["Campus"] = relationship("Campus")


class AcademicRecord(Base):
    __tablename__ = "academic_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    college_course_id: Mapped[int] = mapped_column(Integer, ForeignKey("college_courses.id", ondelete="CASCADE"), index=True, nullable=False)
    attendance_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    internal_marks: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    external_marks: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    assignment_completion_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    academic_status: Mapped[str] = mapped_column(String(20), default="good", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    student_profile: Mapped["StudentProfile"] = relationship("StudentProfile")
    course: Mapped["CollegeCourse"] = relationship("CollegeCourse")


class AcademicRiskAlert(Base):
    __tablename__ = "academic_risk_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    college_course_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("college_courses.id", ondelete="SET NULL"), nullable=True)
    risk_type: Mapped[str] = mapped_column(String(50), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(String(1000), nullable=False)
    recommended_action: Mapped[str] = mapped_column(String(500), nullable=False)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    student_profile: Mapped["StudentProfile"] = relationship("StudentProfile")
