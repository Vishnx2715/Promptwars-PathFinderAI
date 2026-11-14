from datetime import datetime, timezone
from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import StudentProfile
from app.models.skill import Skill, LearnerSkill
from app.models.career import CareerRole
from app.schemas.profile import (
    StudentProfileCreate,
    StudentProfileUpdate,
    StudentProfileResponse,
)
from app.schemas.skill import LearnerSkillCreate, LearnerSkillResponse


class ProfileService:
    @staticmethod
    async def get_profile_by_user_id(db: AsyncSession, user_id: int) -> StudentProfile:
        res = await db.execute(
            select(StudentProfile)
            .options(
                selectinload(StudentProfile.target_role),
                selectinload(StudentProfile.learner_skills).selectinload(LearnerSkill.skill)
            )
            .where(StudentProfile.user_id == user_id)
        )
        profile = res.scalar_one_or_none()
        if not profile:
            raise HTTPException(status_code=404, detail="Student profile not found")
        return profile

    @staticmethod
    def format_profile_response(profile: StudentProfile) -> StudentProfileResponse:
        skills_resp: List[LearnerSkillResponse] = []
        for ls in profile.learner_skills:
            skills_resp.append(
                LearnerSkillResponse(
                    id=ls.id,
                    skill_id=ls.skill_id,
                    skill_name=ls.skill.name if ls.skill else "",
                    category=ls.skill.category if ls.skill else "General",
                    self_reported_level=ls.self_reported_level,
                    verified_level=ls.verified_level,
                    evidence_type=ls.evidence_type,
                    mastery_percentage=ls.mastery_percentage,
                    last_assessed_at=ls.last_assessed_at,
                )
            )

        return StudentProfileResponse(
            id=profile.id,
            user_id=profile.user_id,
            full_name=profile.full_name,
            education_level=profile.education_level,
            experience_level=profile.experience_level,
            weekly_study_hours=profile.weekly_study_hours,
            learning_preference=profile.learning_preference,
            target_role_id=profile.target_role_id,
            target_role_name=profile.target_role.name if profile.target_role else None,
            career_goal_changed_at=profile.career_goal_changed_at,
            projects=profile.projects or [],
            certifications=profile.certifications or [],
            learner_skills=skills_resp,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )

    @classmethod
    async def create_or_update_onboarding(
        cls, db: AsyncSession, user_id: int, data: StudentProfileCreate
    ) -> StudentProfileResponse:
        profile = await cls.get_profile_by_user_id(db, user_id)

        profile.full_name = data.full_name
        profile.education_level = data.education_level
        profile.experience_level = data.experience_level
        profile.weekly_study_hours = data.weekly_study_hours
        profile.learning_preference = data.learning_preference

        if data.projects is not None:
            profile.projects = [p.model_dump() for p in data.projects]
        if data.certifications is not None:
            profile.certifications = [c.model_dump() for c in data.certifications]

        profile.updated_at = datetime.now(timezone.utc)

        # Handle skills if provided in onboarding
        if data.skills:
            for s_in in data.skills:
                await cls.add_or_update_skill(db, profile.id, s_in)

        await db.commit()
        db.expire_all()
        # Refetch with loaded relationships
        refreshed = await cls.get_profile_by_user_id(db, user_id)
        return cls.format_profile_response(refreshed)

    @classmethod
    async def update_profile(
        cls, db: AsyncSession, user_id: int, data: StudentProfileUpdate
    ) -> StudentProfileResponse:
        profile = await cls.get_profile_by_user_id(db, user_id)

        if data.full_name is not None:
            profile.full_name = data.full_name
        if data.education_level is not None:
            profile.education_level = data.education_level
        if data.experience_level is not None:
            profile.experience_level = data.experience_level
        if data.weekly_study_hours is not None:
            profile.weekly_study_hours = data.weekly_study_hours
        if data.learning_preference is not None:
            profile.learning_preference = data.learning_preference
        if data.projects is not None:
            profile.projects = [p.model_dump() for p in data.projects]
        if data.certifications is not None:
            profile.certifications = [c.model_dump() for c in data.certifications]

        profile.updated_at = datetime.now(timezone.utc)
        await db.commit()
        refreshed = await cls.get_profile_by_user_id(db, user_id)
        return cls.format_profile_response(refreshed)

    @classmethod
    async def add_or_update_skill(
        cls, db: AsyncSession, profile_id: int, skill_data: LearnerSkillCreate
    ) -> LearnerSkill:
        # Resolve skill
        skill_obj = None
        if skill_data.skill_id:
            res = await db.execute(select(Skill).where(Skill.id == skill_data.skill_id))
            skill_obj = res.scalar_one_or_none()
        elif skill_data.skill_name:
            res = await db.execute(select(Skill).where(Skill.name == skill_data.skill_name))
            skill_obj = res.scalar_one_or_none()

        if not skill_obj:
            raise HTTPException(status_code=404, detail="Skill not found")

        # Find if existing
        res = await db.execute(
            select(LearnerSkill).where(
                LearnerSkill.student_profile_id == profile_id,
                LearnerSkill.skill_id == skill_obj.id,
            )
        )
        learner_skill = res.scalar_one_or_none()

        mastery = (float(skill_data.level) / 5.0) * 100.0
        verified = float(skill_data.level)

        if learner_skill:
            learner_skill.self_reported_level = skill_data.level
            # Only update verified_level if it was not already higher from an assessment
            if learner_skill.evidence_type == "self_report" or learner_skill.verified_level == 0:
                learner_skill.verified_level = verified
                learner_skill.mastery_percentage = mastery
            learner_skill.updated_at = datetime.now(timezone.utc)
        else:
            learner_skill = LearnerSkill(
                student_profile_id=profile_id,
                skill_id=skill_obj.id,
                self_reported_level=skill_data.level,
                verified_level=verified,
                evidence_type="self_report",
                mastery_percentage=mastery,
            )
            db.add(learner_skill)

        await db.commit()
        return learner_skill

    @classmethod
    async def delete_skill(cls, db: AsyncSession, profile_id: int, skill_id: int) -> None:
        res = await db.execute(
            select(LearnerSkill).where(
                LearnerSkill.student_profile_id == profile_id,
                LearnerSkill.skill_id == skill_id,
            )
        )
        ls = res.scalar_one_or_none()
        if not ls:
            raise HTTPException(status_code=404, detail="Skill not found on profile")

        await db.delete(ls)
        await db.commit()
