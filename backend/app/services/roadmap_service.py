import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import StudentProfile
from app.models.career import CareerRole, RoleSkillRequirement
from app.models.skill import Skill, LearnerSkill
from app.models.roadmap import LearningPath, RoadmapModule, RoadmapResource
from app.schemas.roadmap import (
    RoadmapResponse,
    RoadmapModuleResponse,
    RoadmapResourceResponse,
)
from app.services.gap_analysis_service import GapAnalysisService

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class RoadmapService:
    @staticmethod
    def load_curated_resources() -> List[Dict[str, Any]]:
        resources_path = DATA_DIR / "resources.json"
        if resources_path.exists():
            with open(resources_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    @classmethod
    async def get_active_roadmap(
        cls, db: AsyncSession, profile_id: int
    ) -> Optional[RoadmapResponse]:
        res = await db.execute(
            select(LearningPath)
            .options(
                selectinload(LearningPath.career_role),
                selectinload(LearningPath.modules).selectinload(RoadmapModule.skill),
                selectinload(LearningPath.modules).selectinload(RoadmapModule.resources),
                selectinload(LearningPath.modules).selectinload(RoadmapModule.prerequisite_module),
            )
            .where(
                LearningPath.student_profile_id == profile_id,
                LearningPath.status == "active",
            )
            .order_by(LearningPath.version.desc())
        )
        path = res.scalar_one_or_none()
        if not path:
            return None
        return cls._format_roadmap_response(path)

    @classmethod
    def _format_roadmap_response(cls, path: LearningPath) -> RoadmapResponse:
        modules_resp = []
        for mod in sorted(path.modules, key=lambda m: (m.phase, m.order_index)):
            res_resp = [
                RoadmapResourceResponse(
                    id=r.id,
                    roadmap_module_id=r.roadmap_module_id,
                    title=r.title,
                    url=r.url,
                    resource_type=r.resource_type,
                    difficulty=r.difficulty,
                    estimated_minutes=r.estimated_minutes,
                    reason=r.reason,
                    is_completed=r.is_completed,
                )
                for r in mod.resources
            ]
            modules_resp.append(
                RoadmapModuleResponse(
                    id=mod.id,
                    learning_path_id=mod.learning_path_id,
                    title=mod.title,
                    description=mod.description,
                    skill_id=mod.skill_id,
                    skill_name=mod.skill.name if mod.skill else "",
                    phase=mod.phase,
                    order_index=mod.order_index,
                    estimated_hours=mod.estimated_hours,
                    status=mod.status,
                    prerequisite_module_id=mod.prerequisite_module_id,
                    prerequisite_module_title=mod.prerequisite_module.title if mod.prerequisite_module else None,
                    min_mastery_to_unlock=mod.min_mastery_to_unlock,
                    reason=mod.reason,
                    resources=res_resp,
                )
            )

        return RoadmapResponse(
            id=path.id,
            student_profile_id=path.student_profile_id,
            career_role_id=path.career_role_id,
            career_role_name=path.career_role.name if path.career_role else "",
            version=path.version,
            status=path.status,
            readiness_score=path.readiness_score,
            replan_reason=path.replan_reason,
            modules=modules_resp,
            created_at=path.created_at,
        )

    @classmethod
    async def generate_roadmap(
        cls,
        db: AsyncSession,
        profile_id: int,
        replan_reason: Optional[str] = None
    ) -> RoadmapResponse:
        # Load profile
        res = await db.execute(
            select(StudentProfile)
            .options(
                selectinload(StudentProfile.target_role),
                selectinload(StudentProfile.learner_skills).selectinload(LearnerSkill.skill)
            )
            .where(StudentProfile.id == profile_id)
        )
        profile = res.scalar_one_or_none()
        if not profile or not profile.target_role_id:
            raise HTTPException(
                status_code=400,
                detail="A target career goal must be selected before generating a roadmap."
            )

        # Archive any currently active roadmap
        res_active = await db.execute(
            select(LearningPath).where(
                LearningPath.student_profile_id == profile_id,
                LearningPath.status == "active"
            )
        )
        for old_lp in res_active.scalars().all():
            old_lp.status = "archived"
            if not old_lp.replan_reason:
                old_lp.replan_reason = replan_reason or "Superseded by newly generated roadmap."

        # Fetch current readiness and gaps
        gap_data = await GapAnalysisService.analyze(db, profile_id, use_agent=False)

        # Get role requirements with skills
        req_res = await db.execute(
            select(RoleSkillRequirement)
            .options(
                selectinload(RoleSkillRequirement.skill),
                selectinload(RoleSkillRequirement.prerequisite_skill)
            )
            .where(RoleSkillRequirement.career_role_id == profile.target_role_id)
        )
        requirements = req_res.scalars().all()

        # Learner skill map
        learner_skills_map = {ls.skill.name: ls for ls in profile.learner_skills}

        # Load resources from disk
        all_resources = cls.load_curated_resources()

        # Build new LearningPath
        latest_version_res = await db.execute(
            select(LearningPath.version)
            .where(LearningPath.student_profile_id == profile_id)
            .order_by(LearningPath.version.desc())
        )
        latest_version = latest_version_res.scalars().first() or 0

        learning_path = LearningPath(
            student_profile_id=profile_id,
            career_role_id=profile.target_role_id,
            version=latest_version + 1,
            status="active",
            readiness_score=float(gap_data.readiness_score),
            replan_reason=replan_reason or "Initial personalized roadmap generated based on career goal.",
            created_at=datetime.now(timezone.utc)
        )
        db.add(learning_path)
        await db.flush()

        # Deterministic Prerequisite-Aware Ordering
        # Full Stack Developer Phasing:
        # Phase 1: HTML, CSS, JavaScript (available)
        # Phase 2: React (locked until JS >= 70%)
        # Phase 3: Node.js (locked until JS >= 70%), Express (locked until Node >= 70%), REST APIs (locked until Node >= 70%)
        # Phase 4: SQL (available), Git (available), Database Design (locked until SQL >= 70%)
        # Phase 5: Capstone / Full Stack Integration
        
        # Build dependency graph
        skill_req_map = {req.skill.name: req for req in requirements}
        created_modules: Dict[str, RoadmapModule] = {}

        # Define phases deterministically based on role
        phases_plan = cls._get_deterministic_phases(profile.target_role.name, requirements)

        order_counter = 1
        for phase_idx, phase_info in enumerate(phases_plan, start=1):
            for skill_name in phase_info["skills"]:
                req = skill_req_map.get(skill_name)
                if not req:
                    continue

                skill_obj = req.skill
                ls = learner_skills_map.get(skill_name)
                current_mastery = ls.mastery_percentage if ls else 0.0

                # Prerequisite checking:
                # 1. Prerequisite module from prereq skill
                prereq_skill_name = req.prerequisite_skill.name if req.prerequisite_skill else None
                prereq_module = created_modules.get(prereq_skill_name) if prereq_skill_name else None
                prereq_ls = learner_skills_map.get(prereq_skill_name) if prereq_skill_name else None
                prereq_mastery = prereq_ls.mastery_percentage if prereq_ls else 0.0

                # Determine module status
                if current_mastery >= 85.0:
                    status_val = "completed"
                    reason_val = f"Pre-requisite satisfied and skill mastery verified at {current_mastery:.0f}%."
                elif skill_name in ["HTML", "CSS", "JavaScript"]:
                    # Foundational competencies are available initially
                    status_val = "available"
                    reason_val = "Foundational web competency. Available to start."
                elif prereq_skill_name and prereq_mastery < 70.0:
                    # React & Node.js locked until JS >= 70%
                    status_val = "locked"
                    reason_val = f"Locked: Requires at least 70% mastery in {prereq_skill_name} (currently {prereq_mastery:.0f}%)."
                else:
                    # Available initially
                    status_val = "available"
                    reason_val = "Prerequisites satisfied. Ready to start."

                # Estimated hours based on weekly study hours and required level
                # Lower weekly hours scales up pacing cleanly
                hours = float(req.required_level * 6.0)

                mod = RoadmapModule(
                    learning_path_id=learning_path.id,
                    title=f"Mastering {skill_name}",
                    description=skill_obj.description or f"Comprehensive mastery of {skill_name} for {profile.target_role.name}.",
                    skill_id=skill_obj.id,
                    phase=phase_idx,
                    order_index=order_counter,
                    estimated_hours=hours,
                    status=status_val,
                    prerequisite_module_id=prereq_module.id if prereq_module else None,
                    min_mastery_to_unlock=70.0,
                    reason=reason_val,
                )
                db.add(mod)
                await db.flush()
                created_modules[skill_name] = mod
                order_counter += 1

                # Attach curated resources
                skill_resources = [r for r in all_resources if r.get("skill") == skill_name]
                for r_item in skill_resources[:6]:
                    r_obj = RoadmapResource(
                        roadmap_module_id=mod.id,
                        title=r_item["title"],
                        url=r_item["url"],
                        resource_type=r_item.get("resource_type", "documentation"),
                        difficulty=r_item.get("difficulty", "medium"),
                        estimated_minutes=r_item.get("estimated_minutes", 30),
                        reason=r_item.get("reason", "Curated study resource."),
                        is_completed=False,
                    )
                    db.add(r_obj)

        await db.commit()
        return await cls.get_active_roadmap(db, profile_id)

    @staticmethod
    def _get_deterministic_phases(role_name: str, requirements: List[RoleSkillRequirement]) -> List[Dict[str, Any]]:
        req_skill_names = {req.skill.name for req in requirements}

        if "Full Stack" in role_name:
            return [
                {
                    "title": "Phase 1: Web Foundations & Core Scripting",
                    "skills": [s for s in ["HTML", "CSS", "JavaScript"] if s in req_skill_names]
                },
                {
                    "title": "Phase 2: Frontend Engineering & Component Systems",
                    "skills": [s for s in ["React"] if s in req_skill_names]
                },
                {
                    "title": "Phase 3: Backend Runtime & RESTful Architectures",
                    "skills": [s for s in ["Node.js", "Express", "REST APIs"] if s in req_skill_names]
                },
                {
                    "title": "Phase 4: Relational Data Layer & Version Control",
                    "skills": [s for s in ["SQL", "Database Design", "Git"] if s in req_skill_names]
                }
            ]
        elif "Data Analyst" in role_name:
            return [
                {
                    "title": "Phase 1: Structured Query Language Foundations",
                    "skills": [s for s in ["SQL", "Git"] if s in req_skill_names]
                },
                {
                    "title": "Phase 2: Python Scripting for Data Analysis",
                    "skills": [s for s in ["Python"] if s in req_skill_names]
                },
                {
                    "title": "Phase 3: Data Wrangling & Manipulation",
                    "skills": [s for s in ["Pandas"] if s in req_skill_names]
                },
                {
                    "title": "Phase 4: Statistical Analysis & Business Storytelling",
                    "skills": [s for s in ["Statistics", "Data Visualization"] if s in req_skill_names]
                }
            ]
        elif "Frontend" in role_name:
            return [
                {
                    "title": "Phase 1: Semantic Markup & Modern CSS",
                    "skills": [s for s in ["HTML", "CSS"] if s in req_skill_names]
                },
                {
                    "title": "Phase 2: Advanced JavaScript Core",
                    "skills": [s for s in ["JavaScript", "Git"] if s in req_skill_names]
                },
                {
                    "title": "Phase 3: React Single Page Applications & APIs",
                    "skills": [s for s in ["React", "REST APIs"] if s in req_skill_names]
                }
            ]
        elif "Backend" in role_name:
            return [
                {
                    "title": "Phase 1: JavaScript Engine & Version Control",
                    "skills": [s for s in ["JavaScript", "Git"] if s in req_skill_names]
                },
                {
                    "title": "Phase 2: Node.js Runtime & Express Servers",
                    "skills": [s for s in ["Node.js", "Express", "REST APIs"] if s in req_skill_names]
                },
                {
                    "title": "Phase 3: Relational Persistence & Schema Modeling",
                    "skills": [s for s in ["SQL", "Database Design"] if s in req_skill_names]
                }
            ]
        else:
            # Default fallback group into 3 phases
            skills = list(req_skill_names)
            chunk_size = max(1, len(skills) // 3)
            return [
                {"title": "Phase 1: Fundamentals", "skills": skills[:chunk_size]},
                {"title": "Phase 2: Core Engineering", "skills": skills[chunk_size:chunk_size*2]},
                {"title": "Phase 3: Advanced Competencies", "skills": skills[chunk_size*2:]},
            ]

    @classmethod
    async def update_resource_completion(
        cls, db: AsyncSession, profile_id: int, resource_id: int, is_completed: bool
    ) -> RoadmapResourceResponse:
        res = await db.execute(
            select(RoadmapResource)
            .join(RoadmapModule)
            .join(LearningPath)
            .where(
                RoadmapResource.id == resource_id,
                LearningPath.student_profile_id == profile_id,
                LearningPath.status == "active",
            )
        )
        resource = res.scalar_one_or_none()
        if not resource:
            raise HTTPException(status_code=404, detail="Roadmap resource not found")

        resource.is_completed = is_completed
        await db.commit()
        await db.refresh(resource)

        return RoadmapResourceResponse(
            id=resource.id,
            roadmap_module_id=resource.roadmap_module_id,
            title=resource.title,
            url=resource.url,
            resource_type=resource.resource_type,
            difficulty=resource.difficulty,
            estimated_minutes=resource.estimated_minutes,
            reason=resource.reason,
            is_completed=resource.is_completed,
        )

    @classmethod
    async def update_module_status(
        cls, db: AsyncSession, profile_id: int, module_id: int, new_status: str
    ) -> RoadmapResponse:
        res = await db.execute(
            select(RoadmapModule)
            .options(
                selectinload(RoadmapModule.resources),
                selectinload(RoadmapModule.learning_path),
            )
            .where(
                RoadmapModule.id == module_id,
                RoadmapModule.learning_path.has(student_profile_id=profile_id, status="active"),
            )
        )
        module = res.scalar_one_or_none()
        if not module:
            raise HTTPException(status_code=404, detail="Roadmap module not found")

        # Business Rule: "Mark module complete only when all required resources are complete"
        if new_status == "completed":
            incomplete = [r for r in module.resources if not r.is_completed]
            if incomplete:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot mark module completed. {len(incomplete)} required resources are still incomplete."
                )

        module.status = new_status
        module.updated_at = datetime.now(timezone.utc)
        await db.commit()

        # If completed, evaluate unlocking downstream dependent modules
        if new_status == "completed":
            await cls.evaluate_prerequisites_and_unlock(db, module.learning_path_id, profile_id)

        return await cls.get_active_roadmap(db, profile_id)

    @classmethod
    async def evaluate_prerequisites_and_unlock(
        cls, db: AsyncSession, learning_path_id: int, profile_id: int
    ) -> None:
        # Load all modules for this learning path
        res = await db.execute(
            select(RoadmapModule)
            .options(selectinload(RoadmapModule.skill))
            .where(RoadmapModule.learning_path_id == learning_path_id)
        )
        modules = res.scalars().all()
        module_by_id = {m.id: m for m in modules}
        module_by_skill_id = {m.skill_id: m for m in modules}

        # Load learner skills
        ls_res = await db.execute(
            select(LearnerSkill).where(LearnerSkill.student_profile_id == profile_id)
        )
        learner_skills = {ls.skill_id: ls for ls in ls_res.scalars().all()}

        # Load role requirements for prerequisite relationships
        lp_res = await db.execute(select(LearningPath).where(LearningPath.id == learning_path_id))
        lp = lp_res.scalar_one_or_none()
        if not lp:
            return

        req_res = await db.execute(
            select(RoleSkillRequirement).where(RoleSkillRequirement.career_role_id == lp.career_role_id)
        )
        requirements = req_res.scalars().all()
        prereq_map = {req.skill_id: req.prerequisite_skill_id for req in requirements if req.prerequisite_skill_id}

        for m in modules:
            if m.status in ["locked", "needs_revision"]:
                # Check prerequisite module completion
                prereq_mod_ok = True
                if m.prerequisite_module_id:
                    parent_mod = module_by_id.get(m.prerequisite_module_id)
                    if not parent_mod or parent_mod.status != "completed":
                        prereq_mod_ok = False

                # Check prerequisite skill mastery >= 70%
                prereq_skill_ok = True
                parent_skill_id = prereq_map.get(m.skill_id)
                if parent_skill_id:
                    parent_ls = learner_skills.get(parent_skill_id)
                    if not parent_ls or parent_ls.mastery_percentage < 70.0:
                        prereq_skill_ok = False

                if prereq_mod_ok or prereq_skill_ok:
                    # Specific rule: React and Node.js require JS >= 70%
                    if parent_skill_id:
                        parent_ls = learner_skills.get(parent_skill_id)
                        if parent_ls and parent_ls.mastery_percentage >= 70.0:
                            m.status = "available"
                            m.reason = "Prerequisites satisfied. Module unlocked."
                    elif prereq_mod_ok and parent_mod and parent_mod.status == "completed":
                        m.status = "available"
                        m.reason = "Prerequisite module completed. Module unlocked."

        await db.commit()

