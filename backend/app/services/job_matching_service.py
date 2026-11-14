"""Job description matching service."""
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.career_intelligence import JobDescription, JobMatch
from app.models.profile import StudentProfile
from app.models.skill import Skill, LearnerSkill
from app.models.career import CareerRole
from app.agents.job_match_agent import JobMatchAgent


class JobMatchingService:
    @staticmethod
    async def analyze_job(
        db: AsyncSession, profile_id: int, title: str, company: Optional[str],
        jd_text: str, source_url: Optional[str]
    ) -> Dict[str, Any]:
        # Save JD
        jd = JobDescription(
            student_profile_id=profile_id, title=title, company=company,
            job_description_text=jd_text, source_url=source_url,
            created_at=datetime.now(timezone.utc),
        )
        db.add(jd)
        await db.flush()

        # Load profile context
        prof_res = await db.execute(
            select(StudentProfile)
            .options(
                selectinload(StudentProfile.learner_skills).selectinload(LearnerSkill.skill),
                selectinload(StudentProfile.target_role),
            )
            .where(StudentProfile.id == profile_id)
        )
        profile = prof_res.scalar_one_or_none()
        career_role = profile.target_role.name if profile and profile.target_role else "General"

        skill_mastery = [
            {"name": ls.skill.name, "mastery": ls.mastery_percentage}
            for ls in (profile.learner_skills if profile else [])
        ]

        # Load known skills
        s_res = await db.execute(select(Skill))
        known_skills = [s.name for s in s_res.scalars().all()]

        # Run AI match
        match_result = await JobMatchAgent.run(jd_text, title, skill_mastery, career_role, known_skills)

        # Save match
        match = JobMatch(
            student_profile_id=profile_id,
            job_description_id=jd.id,
            overall_match_score=match_result.get("overall_match_score", 0.0),
            skill_match_score=match_result.get("skill_match_score", 0.0),
            experience_match_score=match_result.get("experience_match_score"),
            education_match_score=match_result.get("education_match_score"),
            matched_skills=match_result.get("matched_skills", []),
            missing_skills=match_result.get("missing_skills", []),
            partial_skills=match_result.get("partial_skills", []),
            recommendations=match_result,
            created_at=datetime.now(timezone.utc),
        )
        db.add(match)
        await db.commit()
        return {"match_id": match.id, "jd_id": jd.id, **match_result}

    @staticmethod
    async def get_match_history(db: AsyncSession, profile_id: int) -> List[Dict[str, Any]]:
        res = await db.execute(
            select(JobMatch)
            .options(selectinload(JobMatch.job_description))
            .where(JobMatch.student_profile_id == profile_id)
            .order_by(JobMatch.created_at.desc())
        )
        return [
            {"id": m.id, "job_title": m.job_description.title if m.job_description else "",
             "company": m.job_description.company if m.job_description else "",
             "overall_match_score": m.overall_match_score,
             "skill_match_score": m.skill_match_score,
             "created_at": m.created_at.isoformat()}
            for m in res.scalars().all()
        ]

    @staticmethod
    async def get_match(db: AsyncSession, profile_id: int, match_id: int) -> Dict[str, Any]:
        res = await db.execute(
            select(JobMatch)
            .options(selectinload(JobMatch.job_description))
            .where(JobMatch.id == match_id, JobMatch.student_profile_id == profile_id)
        )
        match = res.scalar_one_or_none()
        if not match:
            raise HTTPException(status_code=404, detail="Job match not found.")
        return {
            "id": match.id,
            "job_title": match.job_description.title if match.job_description else "",
            "company": match.job_description.company if match.job_description else "",
            "overall_match_score": match.overall_match_score,
            "skill_match_score": match.skill_match_score,
            "matched_skills": match.matched_skills,
            "missing_skills": match.missing_skills,
            "partial_skills": match.partial_skills,
            "recommendations": match.recommendations,
            "created_at": match.created_at.isoformat(),
        }
