from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user, require_student
from app.models.user import User
from app.schemas.profile import (
    StudentProfileCreate,
    StudentProfileUpdate,
    StudentProfileResponse,
)
from app.schemas.skill import LearnerSkillCreate
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.post("", response_model=StudentProfileResponse, status_code=status.HTTP_200_OK)
async def create_or_update_profile(
    data: StudentProfileCreate,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await ProfileService.create_or_update_onboarding(db, current_user.id, data)


@router.get("/me", response_model=StudentProfileResponse)
async def get_my_profile(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return ProfileService.format_profile_response(profile)


@router.put("/me", response_model=StudentProfileResponse)
async def update_my_profile(
    data: StudentProfileUpdate,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await ProfileService.update_profile(db, current_user.id, data)


@router.post("/skills", status_code=status.HTTP_200_OK)
async def add_or_update_skill(
    data: LearnerSkillCreate,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    await ProfileService.add_or_update_skill(db, profile.id, data)
    refreshed = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return ProfileService.format_profile_response(refreshed)


@router.delete("/skills/{skill_id}", status_code=status.HTTP_200_OK)
async def delete_skill(
    skill_id: int,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    await ProfileService.delete_skill(db, profile.id, skill_id)
    refreshed = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return ProfileService.format_profile_response(refreshed)
