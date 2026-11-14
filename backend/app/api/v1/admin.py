"""Admin API: User/mentor management, question bank, coding problem management."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, require_admin
from app.models.user import User
from app.schemas.admin import (
    QuestionCreateRequest,
    QuestionUpdateRequest,
    CodingProblemCreateRequest,
    CodingProblemUpdateRequest,
)
from app.schemas.mentor import CreateMentorRequest
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["Admin"])


# ---- Overview ----

@router.get("/overview")
async def get_overview(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    return await AdminService.get_overview(db)


# ---- User management ----

@router.get("/users")
async def list_users(
    role: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    return await AdminService.list_users(db, role)


@router.put("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    return await AdminService.toggle_user_active(db, user_id)


# ---- Mentor management ----

@router.get("/mentors")
async def list_mentors(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    return await AdminService.list_mentors(db)


@router.post("/mentors", status_code=status.HTTP_201_CREATED)
async def create_mentor(
    req: CreateMentorRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    return await AdminService.create_mentor(db, req.user_id, req.full_name, req.expertise)


@router.put("/mentors/{mentor_id}/toggle-active")
async def toggle_mentor_active(
    mentor_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    return await AdminService.deactivate_mentor(db, mentor_id)


# ---- Question bank ----

@router.get("/questions")
async def list_questions(
    skill_id: Optional[int] = None,
    subtopic: Optional[str] = None,
    difficulty: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    return await AdminService.list_questions(db, skill_id, subtopic, difficulty)


@router.post("/questions", status_code=status.HTTP_201_CREATED)
async def create_question(
    req: QuestionCreateRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    return await AdminService.create_question(db, req)


@router.put("/questions/{question_id}")
async def update_question(
    question_id: int,
    req: QuestionUpdateRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    return await AdminService.update_question(db, question_id, req)


@router.delete("/questions/{question_id}")
async def delete_question(
    question_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    return await AdminService.delete_question(db, question_id)


# ---- Coding problem management ----

@router.get("/coding-problems")
async def list_coding_problems(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    return await AdminService.list_coding_problems(db)


@router.post("/coding-problems", status_code=status.HTTP_201_CREATED)
async def create_coding_problem(
    req: CodingProblemCreateRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    return await AdminService.create_coding_problem(db, req, current_user.id)


@router.put("/coding-problems/{problem_id}")
async def update_coding_problem(
    problem_id: int,
    req: CodingProblemUpdateRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    return await AdminService.update_coding_problem(db, problem_id, req)


@router.delete("/coding-problems/{problem_id}")
async def delete_coding_problem(
    problem_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    return await AdminService.delete_coding_problem(db, problem_id)
