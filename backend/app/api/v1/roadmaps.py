from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, require_student
from app.models.user import User
from app.schemas.roadmap import (
    RoadmapResponse,
    RoadmapResourceResponse,
    ModuleStatusUpdate,
    ResourceCompleteUpdate,
)
from app.services.profile_service import ProfileService
from app.services.roadmap_service import RoadmapService

router = APIRouter(prefix="/roadmap", tags=["Roadmap"])


@router.post("/generate", response_model=RoadmapResponse)
async def generate_roadmap(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await RoadmapService.generate_roadmap(db, profile.id)


@router.get("/active", response_model=Optional[RoadmapResponse])
async def get_active_roadmap(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await RoadmapService.get_active_roadmap(db, profile.id)


@router.post("/replan", response_model=RoadmapResponse)
async def replan_roadmap(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await RoadmapService.generate_roadmap(
        db, profile.id, replan_reason="User requested adaptive replan."
    )


@router.patch("/modules/{module_id}/status", response_model=RoadmapResponse)
async def update_module_status(
    module_id: int,
    data: ModuleStatusUpdate,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await RoadmapService.update_module_status(db, profile.id, module_id, data.status)


@router.patch("/resources/{resource_id}/complete", response_model=RoadmapResourceResponse)
async def update_resource_completion(
    resource_id: int,
    data: ResourceCompleteUpdate,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await RoadmapService.update_resource_completion(
        db, profile.id, resource_id, data.is_completed
    )

