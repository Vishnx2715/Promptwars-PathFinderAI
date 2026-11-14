"""Practice Lab API: Coding problems, submissions, test execution, AI review."""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, require_student, get_current_student_profile
from app.core.rate_limit import check_rate_limit, get_client_identifier
from app.models.user import User
from app.models.profile import StudentProfile
from app.schemas.practice import (
    CodeRunRequest,
    CodeSubmitRequest,
    CodeSubmissionResponse,
    SubmissionHistoryItem,
    CodingProblemListItem,
    CodingProblemDetail,
)
from app.services.practice_service import PracticeService
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/practice", tags=["Practice Lab"])


@router.get("/problems")
async def list_problems(
    language: Optional[str] = None,
    skill_id: Optional[int] = None,
    subtopic: Optional[str] = None,
    difficulty: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    problems = await PracticeService.list_problems(
        db, profile.id, language, skill_id, subtopic, difficulty, status
    )
    return problems


@router.get("/problems/{problem_id}")
async def get_problem(
    problem_id: int,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await PracticeService.get_problem(db, profile.id, problem_id)


@router.post("/problems/{problem_id}/run")
async def run_sample_tests(
    problem_id: int,
    req: CodeRunRequest,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    results = await PracticeService.run_sample_tests(db, profile.id, problem_id, req.code, req.language)
    return {"results": results}


@router.post("/problems/{problem_id}/submit", response_model=CodeSubmissionResponse)
async def submit_solution(
    problem_id: int,
    req: CodeSubmitRequest,
    request: Request,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    # Rate limit: 5 submissions per minute per user
    identifier = get_client_identifier(request, current_user.id)
    allowed, err = check_rate_limit(identifier, "code_submit", 5, 60)
    if not allowed:
        raise HTTPException(status_code=429, detail=err)

    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    
    # If JavaScript, frontend_results will be provided in the request body
    frontend_results = getattr(req, 'frontend_results', None)
    
    return await PracticeService.submit_solution(
        db, profile.id, problem_id, req.code, req.language, frontend_results
    )


@router.get("/problems/{problem_id}/history")
async def get_submission_history(
    problem_id: int,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await PracticeService.get_submission_history(db, profile.id, problem_id)


@router.get("/problems/{problem_id}/next")
async def get_next_recommended(
    problem_id: int,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await PracticeService.get_next_recommended_problem(db, profile.id, problem_id)
