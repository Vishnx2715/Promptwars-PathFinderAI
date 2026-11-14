"""AI Mentor Chat API — upgraded with full Section 3 learner context."""
from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_student
from app.core.rate_limit import check_rate_limit, get_client_identifier
from app.models.user import User
from app.models.profile import StudentProfile
from app.models.skill import LearnerSkill
from app.models.roadmap import LearningPath, RoadmapModule
from app.models.assessment import AssessmentAttempt
from app.models.practice import CodeSubmission, PracticeSession
from app.models.project import ProjectSubmission
from app.models.mentor import MentorFeedback
from app.models.career_intelligence import JobMatch
from app.models.interview import InterviewSession
from app.models.college import AcademicRiskAlert, StudentCourseEnrollment
from app.services.profile_service import ProfileService
from app.agents.mentor_chat_agent import MentorChatAgent

router = APIRouter(prefix="/mentor-chat", tags=["AI Mentor Chat"])


class ChatMessage(BaseModel):
    message: str = Field(..., max_length=2000)
    history: Optional[List[Dict[str, str]]] = Field(default_factory=list)


@router.post("/chat")
async def mentor_chat(
    req: ChatMessage,
    request: Request,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    identifier = get_client_identifier(request, current_user.id)
    allowed, err = check_rate_limit(identifier, "mentor_chat", 10, 300)
    if not allowed:
        raise HTTPException(status_code=429, detail=err)

    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    career_goal = profile.target_role.name if profile.target_role else "Not selected"

    # Skill mastery
    skill_mastery = [
        {"name": ls.skill.name if ls.skill else "", "mastery": ls.mastery_percentage}
        for ls in profile.learner_skills
    ]

    # Active roadmap
    lp_res = await db.execute(
        select(LearningPath)
        .options(selectinload(LearningPath.modules).selectinload(RoadmapModule.skill))
        .where(LearningPath.student_profile_id == profile.id, LearningPath.status == "active")
    )
    lp = lp_res.scalar_one_or_none()
    active_roadmap = []
    if lp:
        for m in sorted(lp.modules, key=lambda x: (x.phase, x.order_index)):
            active_roadmap.append({
                "title": m.title, "status": m.status,
                "skill_name": m.skill.name if m.skill else "",
            })

    # Recent assessments
    a_res = await db.execute(
        select(AssessmentAttempt)
        .options(selectinload(AssessmentAttempt.assessment))
        .where(AssessmentAttempt.student_profile_id == profile.id,
               AssessmentAttempt.submitted_at != None)
        .order_by(AssessmentAttempt.submitted_at.desc()).limit(5)
    )
    recent_assessments = [
        {"title": a.assessment.title if a.assessment else "", "mastery": a.mastery_percentage}
        for a in a_res.scalars().all()
    ]

    # Coding practice
    cs_res = await db.execute(
        select(
            func.count(CodeSubmission.id).label("total"),
            func.sum(func.case((CodeSubmission.status == "passed", 1), else_=0)).label("solved"),
        ).where(CodeSubmission.student_profile_id == profile.id)
    )
    from sqlalchemy import case as sa_case
    cs_res2 = await db.execute(
        select(
            func.count(CodeSubmission.id).label("total"),
            func.sum(sa_case((CodeSubmission.status == "passed", 1), else_=0)).label("solved"),
        ).where(CodeSubmission.student_profile_id == profile.id)
    )
    row = cs_res2.one()
    coding_practice = {
        "solved": int(row.solved or 0), "total": int(row.total or 0),
        "accuracy": round(((row.solved or 0) / max(row.total or 1, 1)) * 100, 1),
    }

    # Projects
    p_res = await db.execute(
        select(ProjectSubmission)
        .where(ProjectSubmission.student_profile_id == profile.id,
               ProjectSubmission.status == "evaluated").limit(5)
    )
    project_evals = [{"title": p.title, "score": p.evaluation_score} for p in p_res.scalars().all()]

    # Mentor feedback
    fb_res = await db.execute(
        select(MentorFeedback).where(MentorFeedback.student_profile_id == profile.id).limit(5)
    )
    mentor_feedback = [{"comment": f.comment, "type": f.feedback_type} for f in fb_res.scalars().all()]

    # Latest job match
    jm_res = await db.execute(
        select(JobMatch).where(JobMatch.student_profile_id == profile.id)
        .order_by(JobMatch.created_at.desc()).limit(1)
    )
    jm = jm_res.scalar_one_or_none()
    job_match_score = jm.overall_match_score if jm else None

    # Latest interview score
    iv_res = await db.execute(
        select(InterviewSession).where(
            InterviewSession.student_profile_id == profile.id,
            InterviewSession.status == "completed",
        ).order_by(InterviewSession.completed_at.desc()).limit(1)
    )
    iv = iv_res.scalar_one_or_none()
    interview_score = iv.overall_score if iv else None

    # Academic risk
    ar_res = await db.execute(
        select(AcademicRiskAlert).where(
            AcademicRiskAlert.student_profile_id == profile.id,
            AcademicRiskAlert.is_dismissed == False,
        ).order_by(AcademicRiskAlert.created_at.desc()).limit(1)
    )
    ar = ar_res.scalar_one_or_none()
    academic_risk = ar.message if ar else None

    result = await MentorChatAgent.run(
        user_message=req.message,
        student_name=profile.full_name,
        career_goal=career_goal,
        skill_mastery=skill_mastery,
        active_roadmap=active_roadmap,
        recent_assessments=recent_assessments,
        coding_practice=coding_practice,
        project_evaluations=project_evals,
        mentor_feedback=mentor_feedback,
        conversation_history=(req.history or [])[-10:],
        academic_risk=academic_risk,
        job_match_score=job_match_score,
        interview_score=interview_score,
    )

    return {
        "answer": result.get("answer", ""),
        "next_best_action": result.get("next_best_action", {}),
        "evidence": result.get("evidence", []),
        "recommended_resources": result.get("recommended_resources", []),
        "escalate_to_mentor": result.get("escalate_to_mentor", False),
        "escalation_reason": result.get("escalation_reason"),
    }
