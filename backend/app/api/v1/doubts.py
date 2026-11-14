"""Doubts API: Student-mentor doubt portal."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, require_student, require_mentor
from app.models.user import User
from app.models.mentor import Mentor
from app.schemas.mentor import DoubtSubmitRequest, DoubtAnswerRequest
from app.services.doubt_service import DoubtService
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/doubts", tags=["Doubts"])


# ---- Student endpoints ----

@router.post("/submit")
async def submit_doubt(
    req: DoubtSubmitRequest,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await DoubtService.submit_doubt(db, profile.id, req)


@router.get("/")
async def get_my_doubts(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await DoubtService.get_student_doubts(db, profile.id)


@router.put("/{doubt_id}/resolve")
async def resolve_doubt(
    doubt_id: int,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await DoubtService.resolve_doubt(db, profile.id, doubt_id)


# ---- Mentor endpoints ----

@router.get("/mentor")
async def get_mentor_doubts(
    mentor: Mentor = Depends(require_mentor),
    db: AsyncSession = Depends(get_db)
):
    return await DoubtService.get_mentor_doubts(db, mentor.id)


@router.put("/{doubt_id}/answer")
async def answer_doubt(
    doubt_id: int,
    req: DoubtAnswerRequest,
    mentor: Mentor = Depends(require_mentor),
    db: AsyncSession = Depends(get_db)
):
    return await DoubtService.answer_doubt(db, mentor.id, doubt_id, req)
