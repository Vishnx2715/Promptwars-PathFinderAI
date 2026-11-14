"""Interview Studio API."""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_student
from app.core.rate_limit import check_rate_limit, get_client_identifier
from app.models.user import User
from app.services.interview_service import InterviewService
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/interviews", tags=["Interview Studio"])


class StartInterviewRequest(BaseModel):
    career_role_id: int
    interview_type: str = "technical"
    difficulty: str = "medium"


class SubmitAnswerRequest(BaseModel):
    question_id: int
    answer: str


@router.post("/start")
async def start_interview(
    request: Request,
    body: StartInterviewRequest,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    identifier = get_client_identifier(request, current_user.id)
    allowed, err = check_rate_limit(identifier, "interview_start", 3, 3600)
    if not allowed:
        raise HTTPException(status_code=429, detail=err)
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await InterviewService.create_session(
        db, profile.id, body.career_role_id, body.interview_type, body.difficulty
    )


@router.get("/{session_id}/next")
async def get_next_question(
    session_id: int, current_user: User = Depends(require_student), db: AsyncSession = Depends(get_db)
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    q = await InterviewService.get_next_question(db, profile.id, session_id)
    if q is None:
        return {"done": True}
    return q


@router.post("/{session_id}/answer")
async def submit_answer(
    session_id: int,
    body: SubmitAnswerRequest,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await InterviewService.submit_answer(db, profile.id, session_id, body.question_id, body.answer)


@router.post("/{session_id}/complete")
async def complete_interview(
    session_id: int, current_user: User = Depends(require_student), db: AsyncSession = Depends(get_db)
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await InterviewService.complete_session(db, profile.id, session_id)


@router.get("/")
async def list_interviews(current_user: User = Depends(require_student), db: AsyncSession = Depends(get_db)):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await InterviewService.list_sessions(db, profile.id)
