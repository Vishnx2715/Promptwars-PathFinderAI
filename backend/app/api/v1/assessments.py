from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_db, require_student
from app.models.user import User
from app.models.assessment import AssessmentAttempt
from app.schemas.assessment import (
    AssessmentStartResponse,
    AssessmentSubmitRequest,
    AssessmentResultResponse,
)
from app.services.profile_service import ProfileService
from app.services.assessment_service import AssessmentService

router = APIRouter(prefix="/assessments", tags=["Assessments"])


@router.get("/")
async def list_assessments(
    assessment_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all assessments, optionally filtered by type."""
    from app.models.assessment import Assessment
    from sqlalchemy.orm import selectinload
    query = select(Assessment).options(selectinload(Assessment.skill))
    if assessment_type:
        query = query.where(Assessment.assessment_type == assessment_type)
    res = await db.execute(query.order_by(Assessment.id))
    assessments = res.scalars().all()
    return [
        {
            "id": a.id,
            "title": a.title,
            "skill_id": a.skill_id,
            "skill_name": a.skill.name if a.skill else "",
            "assessment_type": a.assessment_type,
            "total_questions": a.total_questions,
        }
        for a in assessments
    ]


@router.get("/skill/{skill_id}")
async def get_assessment_for_skill(
    skill_id: int,
    db: AsyncSession = Depends(get_db)
):
    assessment = await AssessmentService.get_assessment_by_skill(db, skill_id)
    return {
        "id": assessment.id,
        "title": assessment.title,
        "skill_id": assessment.skill_id,
        "skill_name": assessment.skill.name if assessment.skill else "",
        "assessment_type": assessment.assessment_type,
        "total_questions": assessment.total_questions,
    }


@router.post("/{assessment_id}/start", response_model=AssessmentStartResponse)
async def start_assessment(
    assessment_id: int,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await AssessmentService.start_assessment(db, profile.id, assessment_id)


@router.post("/attempts/{attempt_id}/submit", response_model=AssessmentResultResponse)
async def submit_assessment_attempt(
    attempt_id: int,
    submission: AssessmentSubmitRequest,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await AssessmentService.submit_assessment(db, profile.id, attempt_id, submission)


@router.get("/attempts/{attempt_id}/result", response_model=AssessmentResultResponse)
async def get_assessment_result(
    attempt_id: int,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await AssessmentService.get_attempt_result(db, profile.id, attempt_id)


@router.get("/history")
async def get_assessment_history(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    """Get all assessment attempts for the current student."""
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    res = await db.execute(
        select(AssessmentAttempt)
        .where(
            AssessmentAttempt.student_profile_id == profile.id,
            AssessmentAttempt.submitted_at != None,
        )
        .order_by(AssessmentAttempt.submitted_at.desc())
    )
    attempts = res.scalars().all()
    return [
        {
            "attempt_id": a.id,
            "assessment_id": a.assessment_id,
            "score": a.score,
            "max_score": a.max_score,
            "mastery_percentage": a.mastery_percentage,
            "submitted_at": a.submitted_at.isoformat() if a.submitted_at else None,
        }
        for a in attempts
    ]
