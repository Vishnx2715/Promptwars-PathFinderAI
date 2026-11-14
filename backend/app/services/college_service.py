"""College Connect service — courses, assignments, announcements, academic records."""
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.college import (
    CollegeCourse, StudentCourseEnrollment, CourseSchedule,
    CollegeAssignment, AssignmentSubmission, CollegeAnnouncement,
    AcademicRecord, AcademicRiskAlert,
)
from app.models.portfolio import Campus
from app.models.notification import Notification
from app.services.notification_service import NotificationService


class CollegeService:
    # ----- Student facing -----

    @staticmethod
    async def get_enrolled_courses(db: AsyncSession, profile_id: int) -> List[Dict[str, Any]]:
        res = await db.execute(
            select(StudentCourseEnrollment)
            .options(
                selectinload(StudentCourseEnrollment.course).selectinload(CollegeCourse.schedules),
                selectinload(StudentCourseEnrollment.course).selectinload(CollegeCourse.assignments),
            )
            .where(StudentCourseEnrollment.student_profile_id == profile_id,
                   StudentCourseEnrollment.status == "active")
        )
        enrs = res.scalars().all()
        result = []
        for e in enrs:
            c = e.course
            # Pending assignments count
            pending = 0
            for a in c.assignments:
                sub_res = await db.execute(
                    select(AssignmentSubmission).where(
                        AssignmentSubmission.college_assignment_id == a.id,
                        AssignmentSubmission.student_profile_id == profile_id,
                    )
                )
                if not sub_res.scalar_one_or_none():
                    pending += 1
            result.append({
                "enrollment_id": e.id, "course_id": c.id,
                "course_code": c.course_code, "course_name": c.course_name,
                "semester": c.semester, "pending_assignments": pending,
            })
        return result

    @staticmethod
    async def get_course_detail(db: AsyncSession, profile_id: int, course_id: int) -> Dict[str, Any]:
        # Verify enrollment
        enr_res = await db.execute(
            select(StudentCourseEnrollment).where(
                StudentCourseEnrollment.student_profile_id == profile_id,
                StudentCourseEnrollment.college_course_id == course_id,
                StudentCourseEnrollment.status == "active",
            )
        )
        if not enr_res.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Not enrolled in this course.")

        c_res = await db.execute(
            select(CollegeCourse)
            .options(
                selectinload(CollegeCourse.schedules),
                selectinload(CollegeCourse.assignments),
            )
            .where(CollegeCourse.id == course_id)
        )
        c = c_res.scalar_one_or_none()
        if not c:
            raise HTTPException(status_code=404, detail="Course not found.")

        assignments = []
        for a in c.assignments:
            sub_res = await db.execute(
                select(AssignmentSubmission).where(
                    AssignmentSubmission.college_assignment_id == a.id,
                    AssignmentSubmission.student_profile_id == profile_id,
                )
            )
            sub = sub_res.scalar_one_or_none()
            assignments.append({
                "id": a.id, "title": a.title, "description": a.description,
                "due_date": a.due_date.isoformat() if a.due_date else None,
                "max_marks": a.max_marks,
                "submission_status": sub.status if sub else "pending",
                "marks": sub.marks if sub else None,
            })

        return {
            "id": c.id, "course_code": c.course_code, "course_name": c.course_name,
            "semester": c.semester, "syllabus": c.syllabus or [],
            "schedules": [
                {"week": s.week_number, "title": s.title, "topics": s.topics,
                 "lecture_url": s.lecture_recording_url}
                for s in sorted(c.schedules, key=lambda x: x.week_number)
            ],
            "assignments": sorted(assignments, key=lambda x: x["due_date"] or ""),
        }

    @staticmethod
    async def submit_assignment(
        db: AsyncSession, profile_id: int, assignment_id: int,
        submission_url: Optional[str], notes: Optional[str]
    ) -> Dict[str, Any]:
        # Check assignment exists and student is enrolled in its course
        a_res = await db.execute(select(CollegeAssignment).where(CollegeAssignment.id == assignment_id))
        a = a_res.scalar_one_or_none()
        if not a:
            raise HTTPException(status_code=404, detail="Assignment not found.")

        enr_res = await db.execute(
            select(StudentCourseEnrollment).where(
                StudentCourseEnrollment.student_profile_id == profile_id,
                StudentCourseEnrollment.college_course_id == a.college_course_id,
            )
        )
        if not enr_res.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Not enrolled in this course.")

        now = datetime.now(timezone.utc)
        late = a.due_date and now > a.due_date if a.due_date else False

        # Upsert submission
        sub_res = await db.execute(
            select(AssignmentSubmission).where(
                AssignmentSubmission.college_assignment_id == assignment_id,
                AssignmentSubmission.student_profile_id == profile_id,
            )
        )
        sub = sub_res.scalar_one_or_none()
        if sub:
            sub.submission_url = submission_url
            sub.notes = notes
            sub.status = "late" if late else "submitted"
            sub.submitted_at = now
        else:
            sub = AssignmentSubmission(
                college_assignment_id=assignment_id, student_profile_id=profile_id,
                submission_url=submission_url, notes=notes,
                status="late" if late else "submitted", submitted_at=now,
            )
            db.add(sub)

        await db.commit()
        return {"assignment_id": assignment_id, "status": sub.status, "late": late}

    @staticmethod
    async def get_announcements(db: AsyncSession, profile_id: int) -> List[Dict[str, Any]]:
        enr_res = await db.execute(
            select(StudentCourseEnrollment.college_course_id)
            .where(StudentCourseEnrollment.student_profile_id == profile_id,
                   StudentCourseEnrollment.status == "active")
        )
        course_ids = [r[0] for r in enr_res.all()]
        if not course_ids:
            return []

        # Get campus IDs from enrolled courses
        c_res = await db.execute(
            select(CollegeCourse.campus_id).where(CollegeCourse.id.in_(course_ids))
        )
        campus_ids = list({r[0] for r in c_res.all()})

        a_res = await db.execute(
            select(CollegeAnnouncement)
            .where(CollegeAnnouncement.campus_id.in_(campus_ids))
            .order_by(CollegeAnnouncement.created_at.desc())
            .limit(20)
        )
        return [
            {"id": a.id, "title": a.title, "message": a.message,
             "audience": a.audience, "created_at": a.created_at.isoformat()}
            for a in a_res.scalars().all()
        ]

    @staticmethod
    async def get_academic_records(db: AsyncSession, profile_id: int) -> List[Dict[str, Any]]:
        res = await db.execute(
            select(AcademicRecord)
            .options(selectinload(AcademicRecord.course))
            .where(AcademicRecord.student_profile_id == profile_id)
        )
        return [
            {"id": r.id, "course_name": r.course.course_name if r.course else "",
             "attendance_percentage": r.attendance_percentage,
             "internal_marks": r.internal_marks, "external_marks": r.external_marks,
             "assignment_completion_percentage": r.assignment_completion_percentage,
             "academic_status": r.academic_status}
            for r in res.scalars().all()
        ]

    @staticmethod
    async def get_risk_alerts(db: AsyncSession, profile_id: int) -> List[Dict[str, Any]]:
        res = await db.execute(
            select(AcademicRiskAlert)
            .where(AcademicRiskAlert.student_profile_id == profile_id,
                   AcademicRiskAlert.is_dismissed == False)  # noqa: E712
            .order_by(AcademicRiskAlert.created_at.desc())
        )
        return [
            {"id": a.id, "risk_type": a.risk_type, "risk_level": a.risk_level,
             "message": a.message, "recommended_action": a.recommended_action,
             "created_at": a.created_at.isoformat()}
            for a in res.scalars().all()
        ]

    # ----- Admin facing -----

    @staticmethod
    async def upsert_academic_record(
        db: AsyncSession, profile_id: int, course_id: int,
        attendance: Optional[float], internal: Optional[float],
        external: Optional[float], assignment_pct: Optional[float]
    ) -> Dict[str, Any]:
        """Admin/mentor adds or updates academic record and auto-creates risk alerts."""
        res = await db.execute(
            select(AcademicRecord).where(
                AcademicRecord.student_profile_id == profile_id,
                AcademicRecord.college_course_id == course_id,
            )
        )
        record = res.scalar_one_or_none()
        status = "good"
        if attendance is not None and attendance < 65:
            status = "critical"
        elif internal is not None and internal < 33:
            status = "critical"
        elif (attendance is not None and attendance < 75) or (internal is not None and internal < 40):
            status = "at_risk"
        elif assignment_pct is not None and assignment_pct < 50:
            status = "at_risk"

        if record:
            if attendance is not None:
                record.attendance_percentage = attendance
            if internal is not None:
                record.internal_marks = internal
            if external is not None:
                record.external_marks = external
            if assignment_pct is not None:
                record.assignment_completion_percentage = assignment_pct
            record.academic_status = status
            record.updated_at = datetime.now(timezone.utc)
        else:
            record = AcademicRecord(
                student_profile_id=profile_id, college_course_id=course_id,
                attendance_percentage=attendance, internal_marks=internal,
                external_marks=external, assignment_completion_percentage=assignment_pct,
                academic_status=status, updated_at=datetime.now(timezone.utc),
            )
            db.add(record)

        # Auto-create risk alerts
        alerts = []
        if attendance is not None and attendance < 65:
            alerts.append(("low_attendance", "critical", f"Attendance {attendance:.0f}% — below 65%.",
                           "Attend all remaining classes immediately."))
        elif attendance is not None and attendance < 75:
            alerts.append(("low_attendance", "warning", f"Attendance {attendance:.0f}% — below 75%.",
                           "Avoid missing any more classes this semester."))
        if internal is not None and internal < 33:
            alerts.append(("low_marks", "critical", f"Internal marks {internal:.0f} — below 33.",
                           "Schedule extra study sessions and seek mentor help."))
        if assignment_pct is not None and assignment_pct < 50:
            alerts.append(("missing_assignments", "warning",
                           f"Assignment completion {assignment_pct:.0f}% — below 50%.",
                           "Complete pending assignments before deadlines."))

        for risk_type, risk_level, msg, action in alerts:
            alert = AcademicRiskAlert(
                student_profile_id=profile_id, college_course_id=course_id,
                risk_type=risk_type, risk_level=risk_level,
                message=msg, recommended_action=action,
                created_at=datetime.now(timezone.utc),
            )
            db.add(alert)

        await db.commit()
        return {"profile_id": profile_id, "academic_status": status, "alerts_created": len(alerts)}
