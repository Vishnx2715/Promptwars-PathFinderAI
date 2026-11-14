"""AdminService: Admin dashboard, user/mentor management, question bank, coding problem management."""
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.profile import StudentProfile
from app.models.skill import Skill
from app.models.career import CareerRole
from app.models.assessment import Assessment, Question
from app.models.roadmap import LearningPath
from app.models.mentor import Mentor, MentorConnection
from app.models.practice import CodingProblem, CodeSubmission
from app.models.project import ProjectSubmission
from app.models.analytics import LearningActivity
from app.schemas.admin import (
    AdminOverviewResponse,
    AdminUserItem,
    QuestionCreateRequest,
    QuestionUpdateRequest,
    CodingProblemCreateRequest,
    CodingProblemUpdateRequest,
)
from app.services.mentor_service import MentorService


class AdminService:
    @staticmethod
    async def get_overview(db: AsyncSession) -> AdminOverviewResponse:
        # Total students
        students_res = await db.execute(
            select(func.count(User.id)).where(User.role == "student")
        )
        total_students = students_res.scalar() or 0

        # Total mentors
        mentors_res = await db.execute(
            select(func.count(Mentor.id)).where(Mentor.is_active == True)
        )
        total_mentors = mentors_res.scalar() or 0

        # Active learning paths
        lp_res = await db.execute(
            select(func.count(LearningPath.id)).where(LearningPath.status == "active")
        )
        active_paths = lp_res.scalar() or 0

        # Total assessments completed
        from app.models.assessment import AssessmentAttempt
        assess_res = await db.execute(
            select(func.count(AssessmentAttempt.id)).where(AssessmentAttempt.submitted_at != None)
        )
        assessments_completed = assess_res.scalar() or 0

        # Total coding submissions
        cs_res = await db.execute(select(func.count(CodeSubmission.id)))
        total_coding = cs_res.scalar() or 0

        # Total projects
        proj_res = await db.execute(select(func.count(ProjectSubmission.id)))
        total_projects = proj_res.scalar() or 0

        # Average readiness
        avg_res = await db.execute(
            select(func.avg(LearningPath.readiness_score)).where(LearningPath.status == "active")
        )
        avg_readiness = float(avg_res.scalar() or 0)

        # At-risk count (readiness < 40)
        at_risk_res = await db.execute(
            select(func.count(LearningPath.id)).where(
                LearningPath.status == "active",
                LearningPath.readiness_score < 40,
            )
        )
        at_risk = at_risk_res.scalar() or 0

        return AdminOverviewResponse(
            total_students=total_students,
            total_mentors=total_mentors,
            active_learning_paths=active_paths,
            total_assessments_completed=assessments_completed,
            total_coding_submissions=total_coding,
            total_projects_submitted=total_projects,
            average_readiness_score=round(avg_readiness, 1),
            at_risk_student_count=at_risk,
        )

    @staticmethod
    async def list_users(
        db: AsyncSession, role_filter: Optional[str] = None
    ) -> List[AdminUserItem]:
        query = select(User).options(selectinload(User.profile))
        if role_filter:
            query = query.where(User.role == role_filter)
        query = query.order_by(User.created_at.desc())
        res = await db.execute(query)
        users = res.scalars().all()
        result = []
        for u in users:
            # Get mentor code if applicable
            mentor_code = None
            if u.role == "mentor":
                m_res = await db.execute(select(Mentor).where(Mentor.user_id == u.id))
                m = m_res.scalar_one_or_none()
                mentor_code = m.mentor_code if m else None

            result.append(AdminUserItem(
                id=u.id,
                email=u.email,
                username=u.username,
                role=u.role,
                is_active=u.is_active,
                created_at=u.created_at,
                profile_name=u.profile.full_name if u.profile else None,
                mentor_code=mentor_code,
            ))
        return result

    @staticmethod
    async def toggle_user_active(db: AsyncSession, user_id: int) -> Dict[str, Any]:
        res = await db.execute(select(User).where(User.id == user_id))
        user = res.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.is_active = not user.is_active
        await db.commit()
        return {"id": user.id, "is_active": user.is_active}

    @staticmethod
    async def create_mentor(
        db: AsyncSession, user_id: int, full_name: str, expertise: str
    ) -> Dict[str, Any]:
        mentor = await MentorService.create_mentor(db, user_id, full_name, expertise)
        return {
            "id": mentor.id,
            "full_name": mentor.full_name,
            "expertise": mentor.expertise,
            "mentor_code": mentor.mentor_code,
        }

    @staticmethod
    async def list_mentors(db: AsyncSession) -> List[Dict[str, Any]]:
        res = await db.execute(select(Mentor).order_by(Mentor.created_at.desc()))
        mentors = res.scalars().all()
        result = []
        for m in mentors:
            count_res = await db.execute(
                select(func.count(MentorConnection.id)).where(
                    MentorConnection.mentor_id == m.id,
                    MentorConnection.status == "connected",
                )
            )
            student_count = count_res.scalar() or 0
            result.append({
                "id": m.id,
                "full_name": m.full_name,
                "expertise": m.expertise,
                "mentor_code": m.mentor_code,
                "is_active": m.is_active,
                "student_count": student_count,
                "created_at": m.created_at.isoformat(),
            })
        return result

    @staticmethod
    async def deactivate_mentor(db: AsyncSession, mentor_id: int) -> Dict[str, Any]:
        res = await db.execute(select(Mentor).where(Mentor.id == mentor_id))
        mentor = res.scalar_one_or_none()
        if not mentor:
            raise HTTPException(status_code=404, detail="Mentor not found")
        mentor.is_active = not mentor.is_active
        await db.commit()
        return {"id": mentor.id, "is_active": mentor.is_active}

    @staticmethod
    async def create_question(db: AsyncSession, req: QuestionCreateRequest) -> Dict[str, Any]:
        question = Question(
            assessment_id=req.assessment_id,
            skill_id=req.skill_id,
            subtopic=req.subtopic,
            question_text=req.question_text,
            options=req.options,
            correct_option=req.correct_option,
            explanation=req.explanation,
            difficulty=req.difficulty,
            marks=req.marks,
        )
        db.add(question)
        await db.commit()
        await db.refresh(question)
        return {"id": question.id, "message": "Question created."}

    @staticmethod
    async def update_question(db: AsyncSession, question_id: int, req: QuestionUpdateRequest) -> Dict[str, Any]:
        res = await db.execute(select(Question).where(Question.id == question_id))
        question = res.scalar_one_or_none()
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        if req.question_text is not None:
            question.question_text = req.question_text
        if req.options is not None:
            question.options = req.options
        if req.correct_option is not None:
            question.correct_option = req.correct_option
        if req.explanation is not None:
            question.explanation = req.explanation
        if req.difficulty is not None:
            question.difficulty = req.difficulty
        if req.marks is not None:
            question.marks = req.marks
        await db.commit()
        return {"id": question.id, "message": "Question updated."}

    @staticmethod
    async def delete_question(db: AsyncSession, question_id: int) -> Dict[str, Any]:
        res = await db.execute(select(Question).where(Question.id == question_id))
        question = res.scalar_one_or_none()
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        await db.delete(question)
        await db.commit()
        return {"message": "Question deleted."}

    @staticmethod
    async def list_questions(
        db: AsyncSession,
        skill_id: Optional[int] = None,
        subtopic: Optional[str] = None,
        difficulty: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        query = select(Question).options(selectinload(Question.skill))
        if skill_id:
            query = query.where(Question.skill_id == skill_id)
        if subtopic:
            query = query.where(Question.subtopic == subtopic)
        if difficulty:
            query = query.where(Question.difficulty == difficulty)
        res = await db.execute(query.order_by(Question.id.desc()))
        questions = res.scalars().all()
        return [
            {
                "id": q.id,
                "skill_name": q.skill.name if q.skill else "",
                "subtopic": q.subtopic,
                "question_text": q.question_text[:100],
                "difficulty": q.difficulty,
                "marks": q.marks,
            }
            for q in questions
        ]

    @staticmethod
    async def create_coding_problem(
        db: AsyncSession, req: CodingProblemCreateRequest, created_by: int
    ) -> Dict[str, Any]:
        problem = CodingProblem(
            title=req.title,
            description=req.description,
            language=req.language,
            skill_id=req.skill_id,
            subtopic=req.subtopic,
            difficulty=req.difficulty,
            starter_code=req.starter_code,
            function_name=req.function_name,
            test_cases=req.test_cases,
            examples=req.examples,
            constraints=req.constraints,
            created_by=created_by,
            is_active=True,
        )
        db.add(problem)
        await db.commit()
        await db.refresh(problem)
        return {"id": problem.id, "message": "Coding problem created."}

    @staticmethod
    async def update_coding_problem(
        db: AsyncSession, problem_id: int, req: CodingProblemUpdateRequest
    ) -> Dict[str, Any]:
        res = await db.execute(select(CodingProblem).where(CodingProblem.id == problem_id))
        problem = res.scalar_one_or_none()
        if not problem:
            raise HTTPException(status_code=404, detail="Coding problem not found")
        if req.title is not None:
            problem.title = req.title
        if req.description is not None:
            problem.description = req.description
        if req.difficulty is not None:
            problem.difficulty = req.difficulty
        if req.starter_code is not None:
            problem.starter_code = req.starter_code
        if req.test_cases is not None:
            problem.test_cases = req.test_cases
        if req.is_active is not None:
            problem.is_active = req.is_active
        await db.commit()
        return {"id": problem.id, "message": "Coding problem updated."}

    @staticmethod
    async def delete_coding_problem(db: AsyncSession, problem_id: int) -> Dict[str, Any]:
        res = await db.execute(select(CodingProblem).where(CodingProblem.id == problem_id))
        problem = res.scalar_one_or_none()
        if not problem:
            raise HTTPException(status_code=404, detail="Coding problem not found")
        await db.delete(problem)
        await db.commit()
        return {"message": "Coding problem deleted."}

    @staticmethod
    async def list_coding_problems(db: AsyncSession) -> List[Dict[str, Any]]:
        res = await db.execute(
            select(CodingProblem)
            .options(selectinload(CodingProblem.skill))
            .order_by(CodingProblem.id.desc())
        )
        problems = res.scalars().all()
        return [
            {
                "id": p.id,
                "title": p.title,
                "language": p.language,
                "skill_name": p.skill.name if p.skill else "",
                "subtopic": p.subtopic,
                "difficulty": p.difficulty,
                "is_active": p.is_active,
            }
            for p in problems
        ]
