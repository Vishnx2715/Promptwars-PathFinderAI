"""Analytics API: Student, mentor, and admin analytics."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, require_student, require_mentor, require_admin
from app.models.user import User
from app.models.mentor import Mentor
from app.services.analytics_service import AnalyticsService
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/student")
async def get_student_analytics(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await AnalyticsService.get_student_analytics(db, profile.id)


@router.get("/mentor")
async def get_mentor_analytics(
    mentor: Mentor = Depends(require_mentor),
    db: AsyncSession = Depends(get_db)
):
    return await AnalyticsService.get_mentor_analytics(db, mentor.id)


@router.get("/admin")
async def get_admin_analytics(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    return await AnalyticsService.get_admin_analytics(db)
