from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_student
from app.models.user import User
from app.models.profile import StudentProfile
from app.models.career import CareerRole, RoleSkillRequirement
from app.models.roadmap import LearningPath
from app.schemas.career import (
    CareerRoleResponse,
    RoleSkillRequirementResponse,
    CareerGoalSelect,
)
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/careers", tags=["Careers"])


@router.get("", response_model=List[CareerRoleResponse])
async def list_career_roles(db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(CareerRole)
        .where(CareerRole.is_active == True)
        .options(
            selectinload(CareerRole.requirements).selectinload(RoleSkillRequirement.skill),
            selectinload(CareerRole.requirements).selectinload(RoleSkillRequirement.prerequisite_skill),
        )
    )
    roles = res.scalars().all()

    result = []
    for r in roles:
        req_list = []
        for req in r.requirements:
            req_list.append(
                RoleSkillRequirementResponse(
                    id=req.id,
                    career_role_id=req.career_role_id,
                    skill_id=req.skill_id,
                    skill_name=req.skill.name if req.skill else "",
                    category=req.skill.category if req.skill else "",
                    required_level=req.required_level,
                    weight=req.weight,
                    is_prerequisite_for=req.is_prerequisite_for,
                    prerequisite_skill_id=req.prerequisite_skill_id,
                    prerequisite_skill_name=req.prerequisite_skill.name if req.prerequisite_skill else None,
                )
            )
        result.append(
            CareerRoleResponse(
                id=r.id,
                name=r.name,
                description=r.description,
                is_active=r.is_active,
                requirements=req_list,
            )
        )
    return result


@router.get("/{career_role_id}/requirements", response_model=List[RoleSkillRequirementResponse])
async def get_career_requirements(career_role_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(RoleSkillRequirement)
        .where(RoleSkillRequirement.career_role_id == career_role_id)
        .options(
            selectinload(RoleSkillRequirement.skill),
            selectinload(RoleSkillRequirement.prerequisite_skill),
        )
    )
    requirements = res.scalars().all()
    if not requirements:
        # Check if role exists
        role_res = await db.execute(select(CareerRole).where(CareerRole.id == career_role_id))
        if not role_res.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Career role not found")

    return [
        RoleSkillRequirementResponse(
            id=req.id,
            career_role_id=req.career_role_id,
            skill_id=req.skill_id,
            skill_name=req.skill.name if req.skill else "",
            category=req.skill.category if req.skill else "",
            required_level=req.required_level,
            weight=req.weight,
            is_prerequisite_for=req.is_prerequisite_for,
            prerequisite_skill_id=req.prerequisite_skill_id,
            prerequisite_skill_name=req.prerequisite_skill.name if req.prerequisite_skill else None,
        )
        for req in requirements
    ]


@router.post("/select", status_code=status.HTTP_200_OK)
async def select_career_role(
    data: CareerGoalSelect,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)

    # Validate target career role
    res = await db.execute(select(CareerRole).where(CareerRole.id == data.career_role_id))
    role = res.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Target career role not found")

    # If career goal changed
    if profile.target_role_id != role.id:
        old_role_res = await db.execute(select(CareerRole).where(CareerRole.id == profile.target_role_id)) if profile.target_role_id else None
        old_role_name = old_role_res.scalar_one_or_none().name if old_role_res else "None"
        
        profile.target_role_id = role.id
        profile.career_goal_changed_at = datetime.now(timezone.utc)

        # Archive any active learning paths
        replan_msg = f"Career goal changed from {old_role_name} to {role.name}. Transferable skills preserved."
        await db.execute(
            update(LearningPath)
            .where(
                LearningPath.student_profile_id == profile.id,
                LearningPath.status == "active",
            )
            .values(
                status="archived",
                replan_reason=replan_msg,
            )
        )
        await db.commit()

    refreshed = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return ProfileService.format_profile_response(refreshed)
