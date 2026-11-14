"""College Connect API."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, require_student, require_admin
from app.models.user import User
from app.models.portfolio import Campus
from app.models.college import (
    CollegeCourse, StudentCourseEnrollment, CourseSchedule,
    CollegeAssignment, CollegeAnnouncement,
)
from app.services.college_service import CollegeService
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/college", tags=["College Connect"])


class SubmitAssignmentRequest(BaseModel):
    assignment_id: int
    submission_url: Optional[str] = None
    notes: Optional[str] = None


class AcademicRecordUpdate(BaseModel):
    profile_id: int
    course_id: int
    attendance_percentage: Optional[float] = None
    internal_marks: Optional[float] = None
    external_marks: Optional[float] = None
    assignment_completion_percentage: Optional[float] = None


class EnrollRequest(BaseModel):
    course_id: int


# ----- Student endpoints -----

@router.get("/courses")
async def get_enrolled_courses(current_user: User = Depends(require_student), db: AsyncSession = Depends(get_db)):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await CollegeService.get_enrolled_courses(db, profile.id)


@router.get("/courses/{course_id}")
async def get_course_detail(
    course_id: int, current_user: User = Depends(require_student), db: AsyncSession = Depends(get_db)
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await CollegeService.get_course_detail(db, profile.id, course_id)


@router.post("/enroll")
async def enroll_in_course(
    body: EnrollRequest, current_user: User = Depends(require_student), db: AsyncSession = Depends(get_db)
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    # Check course exists
    c_res = await db.execute(select(CollegeCourse).where(CollegeCourse.id == body.course_id))
    course = c_res.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")
    # Upsert enrollment
    from sqlalchemy.ext.asyncio import AsyncSession
    enr_res = await db.execute(
        select(StudentCourseEnrollment).where(
            StudentCourseEnrollment.student_profile_id == profile.id,
            StudentCourseEnrollment.college_course_id == body.course_id,
        )
    )
    enr = enr_res.scalar_one_or_none()
    if not enr:
        from datetime import datetime, timezone
        enr = StudentCourseEnrollment(
            student_profile_id=profile.id, college_course_id=body.course_id,
            enrolled_at=datetime.now(timezone.utc), status="active",
        )
        db.add(enr)
        await db.commit()
    return {"message": "Enrolled successfully.", "course_name": course.course_name}


@router.post("/assignments/submit")
async def submit_assignment(
    body: SubmitAssignmentRequest,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await CollegeService.submit_assignment(db, profile.id, body.assignment_id, body.submission_url, body.notes)


@router.get("/announcements")
async def get_announcements(current_user: User = Depends(require_student), db: AsyncSession = Depends(get_db)):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await CollegeService.get_announcements(db, profile.id)


@router.get("/academic-records")
async def get_academic_records(current_user: User = Depends(require_student), db: AsyncSession = Depends(get_db)):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await CollegeService.get_academic_records(db, profile.id)


@router.get("/risk-alerts")
async def get_risk_alerts(current_user: User = Depends(require_student), db: AsyncSession = Depends(get_db)):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await CollegeService.get_risk_alerts(db, profile.id)


# ----- Admin / Mentor endpoints -----

@router.post("/admin/academic-record")
async def upsert_academic_record(
    body: AcademicRecordUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await CollegeService.upsert_academic_record(
        db, body.profile_id, body.course_id,
        body.attendance_percentage, body.internal_marks,
        body.external_marks, body.assignment_completion_percentage,
    )


@router.get("/admin/campuses")
async def list_campuses(current_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Campus))
    return [{"id": c.id, "name": c.name, "code": c.code} for c in res.scalars().all()]


@router.get("/admin/courses")
async def list_all_courses(current_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(CollegeCourse))
    return [
        {"id": c.id, "course_code": c.course_code, "course_name": c.course_name, "semester": c.semester}
        for c in res.scalars().all()
    ]
