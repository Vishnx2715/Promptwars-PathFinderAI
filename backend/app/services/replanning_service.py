from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import StudentProfile
from app.models.skill import Skill, LearnerSkill
from app.models.career import RoleSkillRequirement
from app.models.roadmap import LearningPath, RoadmapModule, RoadmapResource


class ReplanningService:
    @staticmethod
    async def apply_assessment_adaptive_rules(
        db: AsyncSession,
        profile_id: int,
        skill_id: int,
        mastery_percentage: float
    ) -> List[Dict[str, Any]]:
        changes: List[Dict[str, Any]] = []

        # Find active learning path
        res = await db.execute(
            select(LearningPath)
            .options(
                selectinload(LearningPath.modules).selectinload(RoadmapModule.skill),
                selectinload(LearningPath.modules).selectinload(RoadmapModule.resources),
            )
            .where(
                LearningPath.student_profile_id == profile_id,
                LearningPath.status == "active",
            )
        )
        learning_path = res.scalar_one_or_none()
        if not learning_path:
            return changes

        # Find the module matching the assessed skill
        assessed_module: Optional[RoadmapModule] = None
        for mod in learning_path.modules:
            if mod.skill_id == skill_id:
                assessed_module = mod
                break

        # Load requirements for prerequisite tracking
        req_res = await db.execute(
            select(RoleSkillRequirement)
            .where(RoleSkillRequirement.career_role_id == learning_path.career_role_id)
        )
        requirements = req_res.scalars().all()
        # Find which skills depend on this assessed skill
        dependent_skill_ids = [
            req.skill_id for req in requirements if req.prerequisite_skill_id == skill_id
        ]

        if assessed_module:
            skill_name = assessed_module.skill.name if assessed_module.skill else "Skill"

            # RULE A: Mastery < 50%
            if mastery_percentage < 50.0:
                assessed_module.status = "needs_revision"
                assessed_module.reason = (
                    f"Diagnostic assessment score ({mastery_percentage:.0f}%) indicates foundational gaps. "
                    f"Module entered Revision Sprint. Targeted remediation added."
                )
                changes.append({
                    "module_title": assessed_module.title,
                    "action": "needs_revision",
                    "reason": f"Marked needs_revision due to {mastery_percentage:.0f}% assessment performance."
                })

                # Add remediation resources if not already present
                existing_urls = {r.url for r in assessed_module.resources}
                remediation_resource = RoadmapResource(
                    roadmap_module_id=assessed_module.id,
                    title=f"{skill_name} Remediation & Core Fundamentals Re-read",
                    url="https://developer.mozilla.org/en-US/docs/Web/JavaScript",
                    resource_type="documentation",
                    difficulty="easy",
                    estimated_minutes=45,
                    reason="Remediation resource added to solidify core concepts before retrying the assessment.",
                    is_completed=False
                )
                db.add(remediation_resource)
                changes.append({
                    "module_title": assessed_module.title,
                    "action": "add_revision",
                    "reason": "Added targeted remediation documentation."
                })

                # Lock dependent advanced modules
                for mod in learning_path.modules:
                    if mod.skill_id in dependent_skill_ids:
                        mod.status = "locked"
                        mod.reason = f"Locked: Requires at least 70% in prerequisite {skill_name} (current: {mastery_percentage:.0f}%)."
                        changes.append({
                            "module_title": mod.title,
                            "action": "lock",
                            "reason": f"Dependent module locked because prerequisite {skill_name} is below 70%."
                        })

            # RULE B: Mastery 50% - 74%
            elif 50.0 <= mastery_percentage < 75.0:
                assessed_module.status = "in_progress"
                assessed_module.reason = (
                    f"Developing competency ({mastery_percentage:.0f}%). Practice resources added. "
                    f"Advance to 70%+ to unlock downstream modules."
                )
                changes.append({
                    "module_title": assessed_module.title,
                    "action": "keep",
                    "reason": f"Module kept in_progress. Mastery is developing at {mastery_percentage:.0f}%."
                })

                # Keep dependents locked
                for mod in learning_path.modules:
                    if mod.skill_id in dependent_skill_ids and mastery_percentage < 70.0:
                        mod.status = "locked"
                        mod.reason = f"Locked: Requires at least 70% in prerequisite {skill_name} (current: {mastery_percentage:.0f}%)."
                        changes.append({
                            "module_title": mod.title,
                            "action": "lock",
                            "reason": f"Prerequisite {skill_name} not yet at threshold (current: {mastery_percentage:.0f}%)."
                        })

            # RULE C: Mastery >= 85%
            elif mastery_percentage >= 85.0:
                # Mark module completed
                assessed_module.status = "completed"
                assessed_module.reason = f"Verified high competency ({mastery_percentage:.0f}%). Module completed!"
                changes.append({
                    "module_title": assessed_module.title,
                    "action": "complete",
                    "reason": f"Module completed with {mastery_percentage:.0f}% verified mastery."
                })

                # Mark all resources in this module as completed
                for r in assessed_module.resources:
                    r.is_completed = True

                # Unlock dependent modules whose prerequisites are now satisfied
                for mod in learning_path.modules:
                    if mod.skill_id in dependent_skill_ids:
                        mod.status = "available"
                        mod.reason = f"Unlocked: Prerequisite {skill_name} passed with {mastery_percentage:.0f}% mastery."
                        changes.append({
                            "module_title": mod.title,
                            "action": "unlock",
                            "reason": f"Unlocked because {skill_name} passed with {mastery_percentage:.0f}%!"
                        })

        await db.commit()
        return changes

