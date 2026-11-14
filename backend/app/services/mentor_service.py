"""MentorService: Mentor codes, student connections, mentor dashboard, mentee analytics, feedback."""
import random
import string
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.profile import StudentProfile
from app.models.skill import Skill, LearnerSkill
from app.models.career import CareerRole
from app.models.roadmap import LearningPath, RoadmapModule, RoadmapResource
from app.models.assessment import AssessmentAttempt
from app.models.mentor import Mentor, MentorConnection, MentorFeedback, MentorDoubt
from app.models.practice import CodeSubmission, PracticeSession
from app.models.project import ProjectSubmission
from app.models.analytics import LearningActivity
from app.schemas.mentor import (
    MentorProfileResponse,
    MentorConnectResponse,
    MenteeSummary,
    MenteeDetailResponse,
    MentorFeedbackRequest,
    MentorFeedbackResponse,
    AssignAssessmentRequest,
)

# Characters for mentor codes (exclude 0, O, 1, I)
CODE_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


class MentorService:
    @staticmethod
    def generate_mentor_code() -> str:
        """Generate a unique mentor code: PF-MENTOR-XXXXXXXX"""
        code = ''.join(random.choices(CODE_CHARS, k=8))
        return f"PF-MENTOR-{code}"

    @staticmethod
    async def create_mentor(
        db: AsyncSession, user_id: int, full_name: str, expertise: str
    ) -> Mentor:
        # Update user role to mentor
        res = await db.execute(select(User).where(User.id == user_id))
        user = res.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if user.role == "mentor":
            # Already a mentor — return existing
            m_res = await db.execute(select(Mentor).where(Mentor.user_id == user_id))
            existing = m_res.scalar_one_or_none()
            if existing:
                return existing
        user.role = "mentor"

        # Generate unique code
        code = MentorService.generate_mentor_code()
        # Ensure uniqueness
        while True:
            check = await db.execute(select(Mentor).where(Mentor.mentor_code == code))
            if not check.scalar_one_or_none():
                break
            code = MentorService.generate_mentor_code()

        mentor = Mentor(
            user_id=user_id,
            full_name=full_name,
            expertise=expertise,
            mentor_code=code,
            is_active=True,
        )
        db.add(mentor)
        await db.commit()
        await db.refresh(mentor)
        return mentor

    @staticmethod
    async def get_mentor_profile(db: AsyncSession, user_id: int) -> MentorProfileResponse:
        res = await db.execute(select(Mentor).where(Mentor.user_id == user_id))
        mentor = res.scalar_one_or_none()
        if not mentor:
            raise HTTPException(status_code=404, detail="Mentor profile not found")

        count_res = await db.execute(
            select(func.count(MentorConnection.id)).where(
                MentorConnection.mentor_id == mentor.id,
                MentorConnection.status == "connected",
            )
        )
        count = count_res.scalar() or 0

        return MentorProfileResponse(
            id=mentor.id,
            full_name=mentor.full_name,
            expertise=mentor.expertise,
            mentor_code=mentor.mentor_code,
            is_active=mentor.is_active,
            connected_students=count,
        )

    @staticmethod
    async def connect_student(
        db: AsyncSession, profile_id: int, mentor_code: str
    ) -> MentorConnectResponse:
        # Find mentor by code
        res = await db.execute(
            select(Mentor).where(Mentor.mentor_code == mentor_code.strip().upper(), Mentor.is_active == True)
        )
        mentor = res.scalar_one_or_none()
        if not mentor:
            raise HTTPException(status_code=404, detail="Invalid or inactive mentor code.")

        # Check if already connected
        existing_res = await db.execute(
            select(MentorConnection).where(
                MentorConnection.student_profile_id == profile_id,
                MentorConnection.mentor_id == mentor.id,
                MentorConnection.status == "connected",
            )
        )
        existing = existing_res.scalar_one_or_none()
        if existing:
            return MentorConnectResponse(
                connected=True,
                mentor_name=mentor.full_name,
                mentor_expertise=mentor.expertise,
                status="already_connected",
            )

        # Disconnect from any previous mentor
        old_res = await db.execute(
            select(MentorConnection).where(
                MentorConnection.student_profile_id == profile_id,
                MentorConnection.status == "connected",
            )
        )
        for old in old_res.scalars().all():
            old.status = "disconnected"

        # Create new connection
        conn = MentorConnection(
            student_profile_id=profile_id,
            mentor_id=mentor.id,
            mentor_code=mentor.mentor_code,
            status="connected",
            connected_at=datetime.now(timezone.utc),
        )
        db.add(conn)

        # Log activity
        activity = LearningActivity(
            student_profile_id=profile_id,
            activity_type="mentor_feedback",
            reference_id=mentor.id,
            meta={"type": "mentor_connected", "mentor_name": mentor.full_name},
            created_at=datetime.now(timezone.utc),
        )
        db.add(activity)
        await db.commit()

        return MentorConnectResponse(
            connected=True,
            mentor_name=mentor.full_name,
            mentor_expertise=mentor.expertise,
            status="connected",
        )

    @staticmethod
    async def get_student_connections(db: AsyncSession, profile_id: int) -> List[Dict[str, Any]]:
        res = await db.execute(
            select(MentorConnection)
            .options(selectinload(MentorConnection.mentor))
            .where(MentorConnection.student_profile_id == profile_id)
            .order_by(MentorConnection.connected_at.desc())
        )
        conns = res.scalars().all()
        return [
            {
                "id": c.id,
                "mentor_name": c.mentor.full_name if c.mentor else "",
                "mentor_expertise": c.mentor.expertise if c.mentor else "",
                "status": c.status,
                "connected_at": c.connected_at.isoformat() if c.connected_at else None,
            }
            for c in conns
        ]

    @staticmethod
    async def disconnect_mentor(db: AsyncSession, profile_id: int, connection_id: int) -> None:
        res = await db.execute(
            select(MentorConnection).where(
                MentorConnection.id == connection_id,
                MentorConnection.student_profile_id == profile_id,
            )
        )
        conn = res.scalar_one_or_none()
        if not conn:
            raise HTTPException(status_code=404, detail="Connection not found")
        conn.status = "disconnected"
        await db.commit()

    @staticmethod
    async def get_mentees(db: AsyncSession, mentor_id: int) -> List[MenteeSummary]:
        res = await db.execute(
            select(MentorConnection)
            .options(
                selectinload(MentorConnection.student_profile).selectinload(StudentProfile.target_role),
            )
            .where(
                MentorConnection.mentor_id == mentor_id,
                MentorConnection.status == "connected",
            )
        )
        conns = res.scalars().all()
        mentees = []
        for c in conns:
            profile = c.student_profile
            if not profile:
                continue
            # Get readiness from active learning path
            lp_res = await db.execute(
                select(LearningPath).where(
                    LearningPath.student_profile_id == profile.id,
                    LearningPath.status == "active",
                )
            )
            lp = lp_res.scalar_one_or_none()
            readiness = lp.readiness_score if lp else 0.0

            # Roadmap progress
            mod_res = await db.execute(
                select(RoadmapModule).where(RoadmapModule.learning_path_id == lp.id) if lp else select(RoadmapModule).where(False)
            )
            modules = mod_res.scalars().all()
            total_mods = len(modules)
            completed = sum(1 for m in modules if m.status == "completed")
            progress_pct = round((completed / max(total_mods, 1)) * 100, 1) if total_mods else 0.0

            # Last activity
            act_res = await db.execute(
                select(LearningActivity)
                .where(LearningActivity.student_profile_id == profile.id)
                .order_by(LearningActivity.created_at.desc())
                .limit(1)
            )
            last_activity = act_res.scalar_one_or_none()
            last_active = last_activity.created_at if last_activity else profile.created_at

            # Pending doubts
            doubt_res = await db.execute(
                select(func.count(MentorDoubt.id)).where(
                    MentorDoubt.student_profile_id == profile.id,
                    MentorDoubt.status == "open",
                )
            )
            pending_doubts = doubt_res.scalar() or 0

            # Pending project reviews
            proj_res = await db.execute(
                select(func.count(ProjectSubmission.id)).where(
                    ProjectSubmission.student_profile_id == profile.id,
                    ProjectSubmission.status == "evaluated",
                )
            )
            pending_reviews = proj_res.scalar() or 0

            # Risk level
            risk = MentorService._calculate_risk(readiness, profile.id, last_active)

            mentees.append(MenteeSummary(
                profile_id=profile.id,
                student_name=profile.full_name,
                career_goal=profile.target_role.name if profile.target_role else None,
                readiness_score=round(readiness, 1),
                roadmap_progress_pct=progress_pct,
                last_active=last_active,
                risk_level=risk,
                pending_doubts=pending_doubts,
                pending_project_reviews=pending_reviews,
            ))
        return mentees

    @staticmethod
    def _calculate_risk(readiness: float, profile_id: int, last_active) -> str:
        now = datetime.now(timezone.utc)
        if last_active:
            if isinstance(last_active, str):
                last_active = datetime.fromisoformat(last_active)
            # Handle offset-naive datetimes from SQLite
            if last_active.tzinfo is None:
                last_active = last_active.replace(tzinfo=timezone.utc)
            days_inactive = (now - last_active).days
            if days_inactive >= 5:
                return "high"
        if readiness < 40:
            return "high"
        if readiness < 60:
            return "medium"
        return "low"

    @staticmethod
    async def get_mentee_detail(
        db: AsyncSession, mentor_id: int, profile_id: int
    ) -> MenteeDetailResponse:
        # Verify connection
        conn_res = await db.execute(
            select(MentorConnection).where(
                MentorConnection.mentor_id == mentor_id,
                MentorConnection.student_profile_id == profile_id,
                MentorConnection.status == "connected",
            )
        )
        if not conn_res.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="This student is not connected to you.")

        # Load profile with relationships
        prof_res = await db.execute(
            select(StudentProfile)
            .options(
                selectinload(StudentProfile.target_role),
                selectinload(StudentProfile.learner_skills).selectinload(LearnerSkill.skill),
            )
            .where(StudentProfile.id == profile_id)
        )
        profile = prof_res.scalar_one_or_none()
        if not profile:
            raise HTTPException(status_code=404, detail="Student profile not found")

        # Roadmap
        lp_res = await db.execute(
            select(LearningPath)
            .options(
                selectinload(LearningPath.modules).selectinload(RoadmapModule.skill),
                selectinload(LearningPath.modules).selectinload(RoadmapModule.resources),
            )
            .where(LearningPath.student_profile_id == profile_id, LearningPath.status == "active")
        )
        lp = lp_res.scalar_one_or_none()
        roadmap_modules = []
        if lp:
            for m in sorted(lp.modules, key=lambda m: (m.phase, m.order_index)):
                roadmap_modules.append({
                    "id": m.id,
                    "title": m.title,
                    "status": m.status,
                    "skill_name": m.skill.name if m.skill else "",
                    "phase": m.phase,
                    "reason": m.reason,
                })

        # Learner skills
        learner_skills = [
            {
                "skill_name": ls.skill.name if ls.skill else "",
                "mastery": ls.mastery_percentage,
                "verified_level": ls.verified_level,
                "evidence_type": ls.evidence_type,
            }
            for ls in profile.learner_skills
        ]

        # Assessment history
        assess_res = await db.execute(
            select(AssessmentAttempt)
            .options(selectinload(AssessmentAttempt.assessment).selectinload(Assessment.skill))
            .where(AssessmentAttempt.student_profile_id == profile_id)
            .order_by(AssessmentAttempt.submitted_at.desc())
            .limit(10)
        )
        assessment_history = [
            {
                "id": a.id,
                "title": a.assessment.title if a.assessment else "",
                "skill": a.assessment.skill.name if a.assessment and a.assessment.skill else "",
                "mastery": a.mastery_percentage,
                "submitted_at": a.submitted_at.isoformat() if a.submitted_at else None,
            }
            for a in assess_res.scalars().all()
        ]

        # Coding stats
        cs_res = await db.execute(
            select(
                func.count(CodeSubmission.id).label("total"),
                func.sum(func.case((CodeSubmission.status == "passed", 1), else_=0)).label("solved"),
                func.avg(CodeSubmission.score).label("avg_score"),
            ).where(CodeSubmission.student_profile_id == profile_id)
        )
        cs_stats = cs_res.one()
        coding_stats = {
            "total_submissions": cs_stats.total or 0,
            "solved": cs_stats.solved or 0,
            "accuracy": round(float(cs_stats.avg_score or 0), 1),
        }

        # Project submissions
        proj_res = await db.execute(
            select(ProjectSubmission)
            .where(ProjectSubmission.student_profile_id == profile_id)
            .order_by(ProjectSubmission.submitted_at.desc())
            .limit(10)
        )
        project_submissions = [
            {
                "id": p.id,
                "title": p.title,
                "status": p.status,
                "score": p.evaluation_score,
                "submitted_at": p.submitted_at.isoformat(),
            }
            for p in proj_res.scalars().all()
        ]

        # Weak areas
        weak_areas = [
            ls.skill.name for ls in profile.learner_skills
            if ls.mastery_percentage < 50
        ]

        # AI insight
        readiness = lp.readiness_score if lp else 0.0
        risk = MentorService._calculate_risk(readiness, profile_id, datetime.now(timezone.utc))
        ai_insight = {
            "student_name": profile.full_name,
            "readiness_score": round(readiness, 1),
            "risk_level": risk,
            "primary_blocker": weak_areas[0] if weak_areas else "No major blockers identified.",
            "weak_areas": weak_areas[:5],
            "strengths": [ls.skill.name for ls in profile.learner_skills if ls.mastery_percentage >= 75][:5],
            "recommended_mentor_action": "Focus on " + (weak_areas[0] if weak_areas else "current roadmap") + " and assign targeted practice.",
            "ai_summary": f"{profile.full_name} has a readiness score of {readiness:.0f}% with {len(weak_areas)} weak areas."
        }

        return MenteeDetailResponse(
            profile_id=profile.id,
            student_name=profile.full_name,
            career_goal=profile.target_role.name if profile.target_role else None,
            readiness_score=round(readiness, 1),
            roadmap_modules=roadmap_modules,
            learner_skills=learner_skills,
            assessment_history=assessment_history,
            coding_stats=coding_stats,
            project_submissions=project_submissions,
            weak_areas=weak_areas,
            ai_insight=ai_insight,
        )

    @staticmethod
    async def add_feedback(
        db: AsyncSession, mentor_id: int, req: MentorFeedbackRequest
    ) -> MentorFeedbackResponse:
        # Verify connection
        conn_res = await db.execute(
            select(MentorConnection).where(
                MentorConnection.mentor_id == mentor_id,
                MentorConnection.student_profile_id == req.student_profile_id,
                MentorConnection.status == "connected",
            )
        )
        if not conn_res.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="This student is not connected to you.")

        feedback = MentorFeedback(
            student_profile_id=req.student_profile_id,
            mentor_id=mentor_id,
            roadmap_module_id=req.roadmap_module_id,
            feedback_type=req.feedback_type,
            comment=req.comment,
            recommended_action=req.recommended_action,
            created_at=datetime.now(timezone.utc),
        )
        db.add(feedback)

        # Log activity
        activity = LearningActivity(
            student_profile_id=req.student_profile_id,
            activity_type="mentor_feedback",
            reference_id=mentor_id,
            meta={"type": "feedback", "feedback_type": req.feedback_type, "comment": req.comment[:200]},
            created_at=datetime.now(timezone.utc),
        )
        db.add(activity)
        await db.commit()
        await db.refresh(feedback)

        return MentorFeedbackResponse(
            id=feedback.id,
            student_profile_id=feedback.student_profile_id,
            mentor_id=feedback.mentor_id,
            feedback_type=feedback.feedback_type,
            comment=feedback.comment,
            recommended_action=feedback.recommended_action,
            created_at=feedback.created_at,
        )

    @staticmethod
    async def get_student_feedback(db: AsyncSession, profile_id: int) -> List[Dict[str, Any]]:
        res = await db.execute(
            select(MentorFeedback)
            .where(MentorFeedback.student_profile_id == profile_id)
            .order_by(MentorFeedback.created_at.desc())
        )
        feedbacks = res.scalars().all()
        return [
            {
                "id": f.id,
                "mentor_id": f.mentor_id,
                "feedback_type": f.feedback_type,
                "comment": f.comment,
                "recommended_action": f.recommended_action,
                "created_at": f.created_at.isoformat(),
            }
            for f in feedbacks
        ]

    @staticmethod
    async def assign_assessment(
        db: AsyncSession, mentor_id: int, req: AssignAssessmentRequest
    ) -> Dict[str, Any]:
        """Mentor assigns a revision assessment to a student."""
        # Verify connection
        conn_res = await db.execute(
            select(MentorConnection).where(
                MentorConnection.mentor_id == mentor_id,
                MentorConnection.student_profile_id == req.student_profile_id,
                MentorConnection.status == "connected",
            )
        )
        if not conn_res.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="This student is not connected to you.")

        # Create a mentor-assigned activity for the student to see
        activity = LearningActivity(
            student_profile_id=req.student_profile_id,
            activity_type="mentor_feedback",
            reference_id=req.skill_id,
            meta={
                "type": "assigned_assessment",
                "skill_id": req.skill_id,
                "mentor_id": mentor_id,
                "message": "Your mentor has assigned a revision assessment. Please complete it.",
            },
            created_at=datetime.now(timezone.utc),
        )
        db.add(activity)
        await db.commit()

        return {"message": "Assessment assigned successfully.", "skill_id": req.skill_id}

    @staticmethod
    async def regenerate_code(db: AsyncSession, mentor_id: int) -> str:
        """Generate a new unique mentor code for the given mentor."""
        new_code = MentorService.generate_mentor_code()
        while True:
            check = await db.execute(select(Mentor).where(Mentor.mentor_code == new_code))
            if not check.scalar_one_or_none():
                break
            new_code = MentorService.generate_mentor_code()

        res = await db.execute(select(Mentor).where(Mentor.id == mentor_id))
        mentor = res.scalar_one_or_none()
        if not mentor:
            raise HTTPException(status_code=404, detail="Mentor not found")

        mentor.mentor_code = new_code
        await db.commit()
        return new_code

    @staticmethod
    async def get_mentor_dashboard_overview(db: AsyncSession, mentor_id: int) -> Dict[str, Any]:
        mentees = await MentorService.get_mentees(db, mentor_id)
        at_risk = sum(1 for m in mentees if m.risk_level == "high")
        avg_readiness = round(sum(m.readiness_score for m in mentees) / max(len(mentees), 1), 1)

        # Doubt count
        doubt_res = await db.execute(
            select(func.count(MentorDoubt.id)).where(
                MentorDoubt.mentor_id == mentor_id,
                MentorDoubt.status.in_(["open", "answered"]),
            )
        )
        pending_doubts = doubt_res.scalar() or 0

        return {
            "mentee_count": len(mentees),
            "at_risk_count": at_risk,
            "average_readiness": avg_readiness,
            "pending_doubts": pending_doubts,
        }
