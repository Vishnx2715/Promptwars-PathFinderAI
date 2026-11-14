"""Weekly Study Planner API."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_student
from app.models.user import User
from app.services.study_planner_service import StudyPlannerService
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/study-plan", tags=["Weekly Study Plan"])


@router.get("/")
async def get_or_create_plan(current_user: User = Depends(require_student), db: AsyncSession = Depends(get_db)):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await StudyPlannerService.get_or_create_plan(db, profile.id)


@router.post("/generate")
async def generate_plan(current_user: User = Depends(require_student), db: AsyncSession = Depends(get_db)):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await StudyPlannerService.generate_plan(db, profile.id)


@router.put("/tasks/{task_id}/complete")
async def complete_task(
    task_id: int, current_user: User = Depends(require_student), db: AsyncSession = Depends(get_db)
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await StudyPlannerService.complete_task(db, profile.id, task_id)
