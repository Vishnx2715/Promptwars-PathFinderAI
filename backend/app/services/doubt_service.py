"""DoubtService: Student-mentor doubt portal with AI-drafted answers."""
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import StudentProfile
from app.models.skill import Skill, LearnerSkill
from app.models.roadmap import RoadmapModule
from app.models.mentor import MentorDoubt, MentorConnection
from app.models.analytics import LearningActivity
from app.agents.mentor_assistant_agent import MentorAssistantAgent
from app.schemas.mentor import (
    DoubtSubmitRequest,
    DoubtResponse,
    DoubtAnswerRequest,
)
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class DoubtService:
    @staticmethod
    def _load_resources() -> List[Dict[str, Any]]:
        path = DATA_DIR / "resources.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    @staticmethod
    async def submit_doubt(
        db: AsyncSession, profile_id: int, req: DoubtSubmitRequest
    ) -> DoubtResponse:
        # Get skill name and mastery
        skill_name = "General"
        skill_mastery = 0.0
        if req.skill_id:
            skill_res = await db.execute(select(Skill).where(Skill.id == req.skill_id))
            skill = skill_res.scalar_one_or_none()
            if skill:
                skill_name = skill.name
                ls_res = await db.execute(
                    select(LearnerSkill).where(
                        LearnerSkill.student_profile_id == profile_id,
                        LearnerSkill.skill_id == req.skill_id,
                    )
                )
                ls = ls_res.scalar_one_or_none()
                skill_mastery = ls.mastery_percentage if ls else 0.0

        # Get roadmap module title
        module_title = None
        if req.roadmap_module_id:
            mod_res = await db.execute(select(RoadmapModule).where(RoadmapModule.id == req.roadmap_module_id))
            mod = mod_res.scalar_one_or_none()
            if mod:
                module_title = mod.title

        # Find connected mentor
        conn_res = await db.execute(
            select(MentorConnection).where(
                MentorConnection.student_profile_id == profile_id,
                MentorConnection.status == "connected",
            )
        )
        conn = conn_res.scalar_one_or_none()
        mentor_id = conn.mentor_id if conn else None

        # Get relevant resources
        all_resources = DoubtService._load_resources()
        relevant = [r for r in all_resources if skill_name.lower() in r.get("title", "").lower() or r.get("skill") == skill_name]
        if not relevant:
            relevant = all_resources[:5]

        # AI draft answer
        ai_result = await MentorAssistantAgent.run(
            student_question=req.question,
            subject=req.subject,
            skill_name=skill_name,
            skill_mastery=skill_mastery,
            roadmap_module_title=module_title,
            relevant_resources=relevant,
        )

        doubt = MentorDoubt(
            student_profile_id=profile_id,
            mentor_id=mentor_id,
            skill_id=req.skill_id,
            roadmap_module_id=req.roadmap_module_id,
            subject=req.subject,
            question=req.question,
            ai_draft_answer=ai_result.get("draft_answer", ""),
            status="open",
            created_at=datetime.now(timezone.utc),
        )
        db.add(doubt)

        # Log activity
        activity = LearningActivity(
            student_profile_id=profile_id,
            activity_type="mentor_feedback",
            reference_id=None,
            meta={"type": "doubt_submitted", "subject": req.subject},
            created_at=datetime.now(timezone.utc),
        )
        db.add(activity)
        await db.commit()
        await db.refresh(doubt)

        return DoubtResponse(
            id=doubt.id,
            student_profile_id=doubt.student_profile_id,
            mentor_id=doubt.mentor_id,
            skill_id=doubt.skill_id,
            subject=doubt.subject,
            question=doubt.question,
            ai_draft_answer=doubt.ai_draft_answer,
            mentor_response=doubt.mentor_response,
            status=doubt.status,
            created_at=doubt.created_at,
            answered_at=doubt.answered_at,
        )

    @staticmethod
    async def get_student_doubts(db: AsyncSession, profile_id: int) -> List[Dict[str, Any]]:
        res = await db.execute(
            select(MentorDoubt)
            .where(MentorDoubt.student_profile_id == profile_id)
            .order_by(MentorDoubt.created_at.desc())
        )
        doubts = res.scalars().all()
        return [
            {
                "id": d.id,
                "subject": d.subject,
                "question": d.question,
                "ai_draft_answer": d.ai_draft_answer,
                "mentor_response": d.mentor_response,
                "status": d.status,
                "created_at": d.created_at.isoformat(),
                "answered_at": d.answered_at.isoformat() if d.answered_at else None,
            }
            for d in doubts
        ]

    @staticmethod
    async def get_mentor_doubts(db: AsyncSession, mentor_id: int) -> List[Dict[str, Any]]:
        res = await db.execute(
            select(MentorDoubt)
            .options(selectinload(MentorDoubt.student_profile))
            .where(MentorDoubt.mentor_id == mentor_id)
            .order_by(MentorDoubt.created_at.desc())
        )
        doubts = res.scalars().all()
        return [
            {
                "id": d.id,
                "student_name": d.student_profile.full_name if d.student_profile else "",
                "student_profile_id": d.student_profile_id,
                "subject": d.subject,
                "question": d.question,
                "ai_draft_answer": d.ai_draft_answer,
                "mentor_response": d.mentor_response,
                "status": d.status,
                "created_at": d.created_at.isoformat(),
                "answered_at": d.answered_at.isoformat() if d.answered_at else None,
            }
            for d in doubts
        ]

    @staticmethod
    async def answer_doubt(
        db: AsyncSession, mentor_id: int, doubt_id: int, req: DoubtAnswerRequest
    ) -> Dict[str, Any]:
        res = await db.execute(
            select(MentorDoubt).where(
                MentorDoubt.id == doubt_id,
                MentorDoubt.mentor_id == mentor_id,
            )
        )
        doubt = res.scalar_one_or_none()
        if not doubt:
            raise HTTPException(status_code=404, detail="Doubt not found or not assigned to you.")

        doubt.mentor_response = req.mentor_response
        doubt.status = req.status
        doubt.answered_at = datetime.now(timezone.utc)
        await db.commit()

        return {
            "id": doubt.id,
            "status": doubt.status,
            "mentor_response": doubt.mentor_response,
            "answered_at": doubt.answered_at.isoformat(),
        }

    @staticmethod
    async def resolve_doubt(db: AsyncSession, profile_id: int, doubt_id: int) -> Dict[str, Any]:
        res = await db.execute(
            select(MentorDoubt).where(
                MentorDoubt.id == doubt_id,
                MentorDoubt.student_profile_id == profile_id,
            )
        )
        doubt = res.scalar_one_or_none()
        if not doubt:
            raise HTTPException(status_code=404, detail="Doubt not found.")

        doubt.status = "resolved"
        await db.commit()
        return {"id": doubt.id, "status": "resolved"}
