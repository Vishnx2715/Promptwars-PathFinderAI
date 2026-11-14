"""Mock interview service — text-based, 5 questions per session."""
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview import InterviewSession, InterviewQuestion, InterviewResponse
from app.models.profile import StudentProfile
from app.models.skill import Skill, LearnerSkill
from app.models.career import CareerRole
from app.agents.interview_question_agent import InterviewQuestionAgent
from app.agents.interview_evaluator_agent import InterviewEvaluatorAgent
from app.services.notification_service import NotificationService


class InterviewService:
    @staticmethod
    async def create_session(
        db: AsyncSession, profile_id: int, career_role_id: int,
        interview_type: str, difficulty: str
    ) -> Dict[str, Any]:
        # Load context
        prof_res = await db.execute(
            select(StudentProfile)
            .options(selectinload(StudentProfile.learner_skills).selectinload(LearnerSkill.skill))
            .where(StudentProfile.id == profile_id)
        )
        profile = prof_res.scalar_one_or_none()
        cr_res = await db.execute(select(CareerRole).where(CareerRole.id == career_role_id))
        career_role = cr_res.scalar_one_or_none()
        if not career_role:
            raise HTTPException(status_code=404, detail="Career role not found.")

        weak = [ls.skill.name for ls in (profile.learner_skills if profile else [])
                if ls.mastery_percentage < 60 and ls.skill][:5]
        skill_names = [ls.skill.name for ls in (profile.learner_skills if profile else []) if ls.skill]

        # Generate questions
        q_data = await InterviewQuestionAgent.run(
            career_role.name, interview_type, difficulty, weak, skill_names
        )
        questions_raw = q_data.get("questions", [])[:5]

        # Create session
        session = InterviewSession(
            student_profile_id=profile_id, career_role_id=career_role_id,
            interview_type=interview_type, difficulty=difficulty, status="in_progress",
            created_at=datetime.now(timezone.utc),
        )
        db.add(session)
        await db.flush()

        # Create question records
        for i, q in enumerate(questions_raw):
            iq = InterviewQuestion(
                interview_session_id=session.id,
                question_text=q.get("question_text", ""),
                question_type=q.get("question_type", "technical"),
                expected_answer_points=q.get("expected_answer_points", []),
                difficulty=q.get("difficulty", difficulty),
                order_index=i,
            )
            db.add(iq)

        await db.commit()
        await db.refresh(session)
        return {"session_id": session.id, "title": q_data.get("interview_title", ""),
                "question_count": len(questions_raw)}

    @staticmethod
    async def get_next_question(db: AsyncSession, profile_id: int, session_id: int) -> Optional[Dict[str, Any]]:
        res = await db.execute(
            select(InterviewSession)
            .options(selectinload(InterviewSession.questions).selectinload(InterviewQuestion.response))
            .where(InterviewSession.id == session_id, InterviewSession.student_profile_id == profile_id)
        )
        session = res.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found.")
        for q in sorted(session.questions, key=lambda x: x.order_index):
            if not q.response:
                return {"question_id": q.id, "question_text": q.question_text,
                        "question_type": q.question_type, "difficulty": q.difficulty,
                        "order_index": q.order_index, "total": len(session.questions)}
        return None  # All answered

    @staticmethod
    async def submit_answer(
        db: AsyncSession, profile_id: int, session_id: int,
        question_id: int, answer: str
    ) -> Dict[str, Any]:
        # Validate ownership
        sess_res = await db.execute(
            select(InterviewSession).where(
                InterviewSession.id == session_id,
                InterviewSession.student_profile_id == profile_id,
            )
        )
        session = sess_res.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found.")

        q_res = await db.execute(
            select(InterviewQuestion)
            .options(selectinload(InterviewQuestion.response))
            .where(InterviewQuestion.id == question_id, InterviewQuestion.interview_session_id == session_id)
        )
        question = q_res.scalar_one_or_none()
        if not question:
            raise HTTPException(status_code=404, detail="Question not found.")
        if question.response:
            raise HTTPException(status_code=400, detail="Question already answered.")

        # Evaluate answer
        cr_res = await db.execute(select(CareerRole).where(CareerRole.id == session.career_role_id))
        cr = cr_res.scalar_one_or_none()
        career_role_name = cr.name if cr else "General"

        feedback = await InterviewEvaluatorAgent.run(
            question.question_text, question.expected_answer_points,
            answer, question.question_type, career_role_name
        )

        response = InterviewResponse(
            interview_question_id=question.id,
            student_answer=answer,
            score=feedback.get("score", 0.0),
            feedback=feedback,
            submitted_at=datetime.now(timezone.utc),
        )
        db.add(response)
        await db.commit()
        return {"question_id": question_id, "feedback": feedback}

    @staticmethod
    async def complete_session(db: AsyncSession, profile_id: int, session_id: int) -> Dict[str, Any]:
        res = await db.execute(
            select(InterviewSession)
            .options(selectinload(InterviewSession.questions).selectinload(InterviewQuestion.response))
            .where(InterviewSession.id == session_id, InterviewSession.student_profile_id == profile_id)
        )
        session = res.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found.")

        scores = [q.response.score for q in session.questions if q.response and q.response.score is not None]
        avg_score = sum(scores) / len(scores) if scores else 0.0

        session.overall_score = avg_score
        session.status = "completed"
        session.completed_at = datetime.now(timezone.utc)
        await db.commit()

        # Create notification
        try:
            prof_res = await db.execute(
                select(StudentProfile).where(StudentProfile.id == profile_id)
            )
            profile = prof_res.scalar_one_or_none()
            if profile:
                await NotificationService.create(
                    db, user_id=profile.user_id, title="Interview Completed",
                    message=f"Your interview session scored {avg_score:.0f}/100.",
                    notification_type="interview", reference_id=session_id,
                    reference_path=f"/career-intelligence/interview/{session_id}",
                )
        except Exception:
            pass

        q_feedbacks = []
        for q in sorted(session.questions, key=lambda x: x.order_index):
            if q.response:
                q_feedbacks.append({
                    "question": q.question_text, "score": q.response.score,
                    "feedback": q.response.feedback,
                })

        return {"session_id": session_id, "overall_score": avg_score,
                "question_feedbacks": q_feedbacks}

    @staticmethod
    async def list_sessions(db: AsyncSession, profile_id: int) -> List[Dict[str, Any]]:
        res = await db.execute(
            select(InterviewSession)
            .options(selectinload(InterviewSession.career_role))
            .where(InterviewSession.student_profile_id == profile_id)
            .order_by(InterviewSession.created_at.desc())
        )
        return [
            {"id": s.id, "career_role": s.career_role.name if s.career_role else "",
             "interview_type": s.interview_type, "difficulty": s.difficulty,
             "status": s.status, "overall_score": s.overall_score,
             "created_at": s.created_at.isoformat()}
            for s in res.scalars().all()
        ]
