"""Career Advisor service — compares career paths and recommends alternatives."""
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import StudentProfile
from app.models.skill import LearnerSkill
from app.models.career import CareerRole, RoleSkillRequirement
from app.models.career_intelligence import CareerRecommendation
from app.agents.career_advisor_agent import CareerAdvisorAgent


class CareerAdvisorService:
    @staticmethod
    async def get_career_recommendations(db: AsyncSession, profile_id: int) -> Dict[str, Any]:
        prof_res = await db.execute(
            select(StudentProfile)
            .options(
                selectinload(StudentProfile.learner_skills).selectinload(LearnerSkill.skill),
                selectinload(StudentProfile.target_role),
            )
            .where(StudentProfile.id == profile_id)
        )
        profile = prof_res.scalar_one_or_none()
        if not profile:
            return {"error": "Profile not found."}

        current_role = profile.target_role.name if profile.target_role else "General"
        skill_mastery = [
            {"name": ls.skill.name, "mastery": ls.mastery_percentage}
            for ls in profile.learner_skills if ls.skill
        ]

        # Readiness from active learning path
        from app.models.roadmap import LearningPath
        lp_res = await db.execute(
            select(LearningPath).where(
                LearningPath.student_profile_id == profile_id,
                LearningPath.status == "active"
            )
        )
        lp = lp_res.scalar_one_or_none()
        readiness = lp.readiness_score if lp else 0.0

        # All roles
        all_roles_res = await db.execute(select(CareerRole).where(CareerRole.is_active == True))  # noqa: E712
        all_roles = [r.name for r in all_roles_res.scalars().all()]

        result = await CareerAdvisorAgent.run(current_role, skill_mastery, all_roles, readiness)

        # Save recommendations
        for alt in result.get("alternative_careers", []):
            role_res = await db.execute(
                select(CareerRole).where(CareerRole.name == alt.get("career_role", ""))
            )
            role_obj = role_res.scalar_one_or_none()
            if role_obj:
                rec = CareerRecommendation(
                    student_profile_id=profile_id,
                    recommended_career_role_id=role_obj.id,
                    match_score=alt.get("match_score", 0.0),
                    readiness_score=alt.get("readiness_score", 0.0),
                    reasons=[alt.get("reason", "")],
                    transferable_skills=alt.get("transferable_skills", []),
                    missing_skills=alt.get("missing_skills", []),
                    created_at=datetime.now(timezone.utc),
                )
                db.add(rec)

        await db.commit()
        return result

    @staticmethod
    async def compare_careers(
        db: AsyncSession, profile_id: int,
        primary_role_id: int, alt_role_id: int
    ) -> Dict[str, Any]:
        """Side-by-side readiness comparison for two career roles."""
        prof_res = await db.execute(
            select(StudentProfile)
            .options(selectinload(StudentProfile.learner_skills).selectinload(LearnerSkill.skill))
            .where(StudentProfile.id == profile_id)
        )
        profile = prof_res.scalar_one_or_none()
        mastery_map = {
            ls.skill_id: ls.mastery_percentage
            for ls in (profile.learner_skills if profile else [])
        }

        async def _calc_readiness(role_id: int) -> Dict[str, Any]:
            req_res = await db.execute(
                select(RoleSkillRequirement)
                .options(selectinload(RoleSkillRequirement.skill))
                .where(RoleSkillRequirement.career_role_id == role_id)
            )
            reqs = req_res.scalars().all()
            if not reqs:
                return {"readiness": 0.0, "met": [], "missing": []}
            met, missing = [], []
            total_weight, earned = 0, 0
            for r in reqs:
                skill_mastery = mastery_map.get(r.skill_id, 0)
                required_mastery = (r.required_level / 5.0) * 100.0
                total_weight += r.weight
                if skill_mastery >= required_mastery * 0.7:
                    earned += r.weight
                    met.append(r.skill.name if r.skill else "")
                else:
                    missing.append(r.skill.name if r.skill else "")
            readiness = round((earned / max(total_weight, 1)) * 100.0, 1)
            return {"readiness": readiness, "met": met, "missing": missing}

        primary_data = await _calc_readiness(primary_role_id)
        alt_data = await _calc_readiness(alt_role_id)

        cr1_res = await db.execute(select(CareerRole).where(CareerRole.id == primary_role_id))
        cr1 = cr1_res.scalar_one_or_none()
        cr2_res = await db.execute(select(CareerRole).where(CareerRole.id == alt_role_id))
        cr2 = cr2_res.scalar_one_or_none()

        return {
            "primary": {"name": cr1.name if cr1 else "", **primary_data},
            "alternative": {"name": cr2.name if cr2 else "", **alt_data},
            "recommendation": cr1.name if primary_data["readiness"] >= alt_data["readiness"] else cr2.name,
        }
