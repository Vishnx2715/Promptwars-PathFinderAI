from typing import Dict, List, Any, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.profile import StudentProfile
from app.models.career import CareerRole, RoleSkillRequirement
from app.models.skill import LearnerSkill, Skill
from app.schemas.skill import GapAnalysisResponse, GapItem, StrengthItem


class GapAnalysisService:
    @staticmethod
    async def analyze(
        db: AsyncSession,
        profile_id: int,
        use_agent: bool = True
    ) -> GapAnalysisResponse:
        # Load profile with target role and learner skills
        res = await db.execute(
            select(StudentProfile)
            .options(
                selectinload(StudentProfile.target_role),
                selectinload(StudentProfile.learner_skills).selectinload(LearnerSkill.skill),
            )
            .where(StudentProfile.id == profile_id)
        )
        profile = res.scalar_one_or_none()
        if not profile:
            raise HTTPException(status_code=404, detail="Student profile not found")

        if not profile.target_role_id:
            return GapAnalysisResponse(
                readiness_score=0,
                strengths=[],
                gaps=[],
                next_best_action="Select a career target role in Career Goal to generate your skill gap analysis.",
                summary="No career goal selected yet."
            )

        # Load requirements for target role
        req_res = await db.execute(
            select(RoleSkillRequirement)
            .options(
                selectinload(RoleSkillRequirement.skill),
                selectinload(RoleSkillRequirement.prerequisite_skill)
            )
            .where(RoleSkillRequirement.career_role_id == profile.target_role_id)
        )
        requirements = req_res.scalars().all()

        if not requirements:
            return GapAnalysisResponse(
                readiness_score=0,
                strengths=[],
                gaps=[],
                next_best_action="Career role requirements are not configured yet.",
                summary="No requirements found for the selected career role."
            )

        # Build mapping of learner skills
        learner_skill_map: Dict[int, LearnerSkill] = {
            ls.skill_id: ls for ls in profile.learner_skills
        }

        # 1. Career Readiness Score Calculation
        total_weighted_required = 0
        total_weighted_effective = 0

        # Also collect skills that block others
        # Map: prerequisite_skill_id -> list of dependent skill names
        dependents_map: Dict[int, List[str]] = {}
        for req in requirements:
            if req.prerequisite_skill_id:
                dependents_map.setdefault(req.prerequisite_skill_id, []).append(req.skill.name)

        strengths: List[StrengthItem] = []
        gaps: List[GapItem] = []

        for req in requirements:
            skill = req.skill
            required_level = req.required_level
            weight = req.weight

            ls = learner_skill_map.get(skill.id)
            verified_level = ls.verified_level if ls else 0.0
            mastery = ls.mastery_percentage if ls else 0.0

            effective_level = min(verified_level, float(required_level))
            total_weighted_effective += (weight * effective_level)
            total_weighted_required += (weight * required_level)

            # Classify
            blocking_list = dependents_map.get(skill.id, [])
            is_blocking = len(blocking_list) > 0 and mastery < 70.0

            if mastery >= 85.0:
                strengths.append(
                    StrengthItem(
                        skill=skill.name,
                        mastery=round(mastery, 1),
                        reason=f"Exceeds required competency ({mastery:.0f}% verified mastery). Ready for production work."
                    )
                )
            else:
                # Determine priority
                if mastery < 30.0:
                    priority = "critical"
                    reason = f"Critical gap: {skill.name} requires level {required_level}, current mastery is {mastery:.0f}%."
                elif mastery < 60.0:
                    priority = "high"
                    reason = f"Substantial gap: {skill.name} requires level {required_level}, current mastery is {mastery:.0f}%."
                elif mastery < 85.0:
                    priority = "medium"
                    reason = f"Developing: {skill.name} is at {mastery:.0f}%, near the required level {required_level}."
                else:
                    priority = "low"
                    reason = f"{skill.name} is on track."

                if is_blocking:
                    reason += f" Blocks progress in {', '.join(blocking_list)} until >= 70% mastery is achieved."

                gaps.append(
                    GapItem(
                        skill=skill.name,
                        current_mastery=round(mastery, 1),
                        required_level=required_level,
                        priority=priority,
                        blocking_skills=blocking_list if is_blocking else [],
                        reason=reason
                    )
                )

        readiness_score = int(round((total_weighted_effective / total_weighted_required) * 100)) if total_weighted_required > 0 else 0

        # Sort gaps: critical first, then high, then medium, then low
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        gaps.sort(key=lambda g: (priority_order.get(g.priority, 4), -len(g.blocking_skills)))

        # Determine deterministic next best action
        next_action = "Continue learning modules on your roadmap."
        if gaps:
            # Check if there is a blocking gap that has an assessment
            blocking_gaps = [g for g in gaps if g.blocking_skills]
            if blocking_gaps:
                top_gap = blocking_gaps[0]
                next_action = f"Complete the diagnostic assessment for {top_gap.skill} to unblock {', '.join(top_gap.blocking_skills)}."
            else:
                top_gap = gaps[0]
                next_action = f"Focus on {top_gap.skill} (priority: {top_gap.priority}) to close your primary career gap."
        elif readiness_score >= 85:
            next_action = "Congratulations! Your career readiness score exceeds 85%. You are ready for mock interviews and portfolio capstones."

        summary = (
            f"You are currently at {readiness_score}% career readiness for {profile.target_role.name}. "
            f"You have {len(strengths)} confirmed strengths and {len(gaps)} identified skill gaps to bridge."
        )

        deterministic_result = GapAnalysisResponse(
            readiness_score=readiness_score,
            strengths=strengths,
            gaps=gaps,
            next_best_action=next_action,
            summary=summary
        )

        # If agent is enabled, invoke GapAnalystAgent with fallback
        if use_agent:
            try:
                from app.agents.gap_analyst_agent import GapAnalystAgent
                agent_result = await GapAnalystAgent.run(
                    profile=profile,
                    requirements=requirements,
                    fallback=deterministic_result
                )
                return agent_result
            except Exception:
                return deterministic_result

        return deterministic_result

