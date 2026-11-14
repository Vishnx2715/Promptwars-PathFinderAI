"""Mentors API: Mentor codes, student connections, mentor dashboard, mentee details, feedback."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import (
    get_db, require_student, require_mentor, require_admin,
    get_current_user, get_mentor_for_user
)
from app.core.rate_limit import check_rate_limit, get_client_identifier
from app.models.user import User
from app.models.mentor import Mentor
from app.schemas.mentor import (
    MentorConnectRequest,
    MentorConnectResponse,
    MentorFeedbackRequest,
    MentorFeedbackResponse,
    AssignAssessmentRequest,
    CreateMentorRequest,
)
from app.services.mentor_service import MentorService
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/mentors", tags=["Mentors"])


# ---- Student endpoints ----

@router.post("/connect", response_model=MentorConnectResponse)
async def connect_to_mentor(
    req: MentorConnectRequest,
    request: Request,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    # Rate limit: 10 attempts per 5 min per IP
    identifier = get_client_identifier(request, current_user.id)
    allowed, err = check_rate_limit(identifier, "mentor_code_validate", 10, 300)
    if not allowed:
        raise HTTPException(status_code=429, detail=err)

    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await MentorService.connect_student(db, profile.id, req.mentor_code)


@router.get("/connections")
async def get_my_connections(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await MentorService.get_student_connections(db, profile.id)


@router.delete("/connections/{connection_id}")
async def disconnect_mentor(
    connection_id: int,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    await MentorService.disconnect_mentor(db, profile.id, connection_id)
    return {"message": "Disconnected from mentor."}


@router.get("/feedback")
async def get_my_feedback(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await MentorService.get_student_feedback(db, profile.id)


# ---- Mentor endpoints ----

@router.get("/profile")
async def get_mentor_profile(
    current_user: User = Depends(get_current_user),
    mentor: Mentor = Depends(require_mentor),
    db: AsyncSession = Depends(get_db)
):
    return await MentorService.get_mentor_profile(db, current_user.id)


@router.get("/dashboard")
async def mentor_dashboard(
    mentor: Mentor = Depends(require_mentor),
    db: AsyncSession = Depends(get_db)
):
    overview = await MentorService.get_mentor_dashboard_overview(db, mentor.id)
    mentees = await MentorService.get_mentees(db, mentor.id)
    return {"overview": overview, "mentees": [m.model_dump() for m in mentees]}


@router.get("/mentees")
async def get_mentees(
    mentor: Mentor = Depends(require_mentor),
    db: AsyncSession = Depends(get_db)
):
    mentees = await MentorService.get_mentees(db, mentor.id)
    return [m.model_dump() for m in mentees]


@router.get("/mentees/{profile_id}")
async def get_mentee_detail(
    profile_id: int,
    mentor: Mentor = Depends(require_mentor),
    db: AsyncSession = Depends(get_db)
):
    return await MentorService.get_mentee_detail(db, mentor.id, profile_id)


@router.post("/feedback", response_model=MentorFeedbackResponse)
async def add_mentor_feedback(
    req: MentorFeedbackRequest,
    mentor: Mentor = Depends(require_mentor),
    db: AsyncSession = Depends(get_db)
):
    return await MentorService.add_feedback(db, mentor.id, req)


@router.post("/assign-assessment")
async def assign_assessment(
    req: AssignAssessmentRequest,
    mentor: Mentor = Depends(require_mentor),
    db: AsyncSession = Depends(get_db)
):
    return await MentorService.assign_assessment(db, mentor.id, req)


@router.post("/regenerate-code")
async def regenerate_mentor_code(
    mentor: Mentor = Depends(require_mentor),
    db: AsyncSession = Depends(get_db)
):
    new_code = await MentorService.regenerate_code(db, mentor.id)
    return {"mentor_code": new_code}


# ---- Admin endpoints for mentor management ----

@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_mentor(
    req: CreateMentorRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    return await MentorService.create_mentor(db, req.user_id, req.full_name, req.expertise)
