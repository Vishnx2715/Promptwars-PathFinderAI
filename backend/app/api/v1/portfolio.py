"""Portfolio, leaderboard, skill-decay, and recommendations API."""
from typing import Optional
from fastapi import APIRouter, Depends, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_student
from app.models.user import User
from app.services.portfolio_service import PortfolioService, SkillDecayService, RecommendationService
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/portfolio", tags=["Portfolio & Leaderboard"])


@router.get("/")
async def get_portfolio(current_user: User = Depends(require_student), db: AsyncSession = Depends(get_db)):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await PortfolioService.get_or_create_portfolio(db, profile.id)


@router.put("/")
async def update_portfolio(
    body: dict,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await PortfolioService.update_portfolio(db, profile.id, body)


@router.get("/leaderboard")
async def get_leaderboard(
    campus_id: Optional[int] = Query(None),
    period_type: str = Query("weekly"),
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await PortfolioService.get_leaderboard(db, campus_id, period_type)


@router.get("/skill-decay")
async def get_skill_decay_alerts(current_user: User = Depends(require_student), db: AsyncSession = Depends(get_db)):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await SkillDecayService.get_alerts(db, profile.id)


@router.post("/skill-decay/detect")
async def detect_skill_decay(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    created = await SkillDecayService.detect_and_create_alerts(db, profile.id)
    return {"alerts_created": len(created), "skills": created}


@router.get("/recommendations")
async def get_recommendations(current_user: User = Depends(require_student), db: AsyncSession = Depends(get_db)):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await RecommendationService.get_active(db, profile.id)


@router.put("/recommendations/{rec_id}")
async def update_recommendation(
    rec_id: int, body: dict,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    status = body.get("status", "dismissed")
    return await RecommendationService.update_status(db, profile.id, rec_id, status)
