from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, require_student
from app.models.user import User
from app.schemas.skill import GapAnalysisResponse
from app.services.profile_service import ProfileService
from app.services.gap_analysis_service import GapAnalysisService

router = APIRouter(prefix="/skills", tags=["Skills & Gap Analysis"])


@router.get("/gap-analysis", response_model=GapAnalysisResponse)
async def get_skill_gap_analysis(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await GapAnalysisService.analyze(db, profile.id)

