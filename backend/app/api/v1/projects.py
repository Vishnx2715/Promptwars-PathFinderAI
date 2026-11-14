"""Projects API: Project submission, evaluation status, evaluation reports."""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, require_student, get_current_student_profile
from app.core.rate_limit import check_rate_limit, get_client_identifier
from app.models.user import User
from app.models.profile import StudentProfile
from app.schemas.project import (
    ProjectSubmitRequest,
    ProjectDetailResponse,
    ProjectListItem,
)
from app.services.project_evaluation_service import ProjectEvaluationService
from app.services.profile_service import ProfileService
from app.services.roadmap_service import RoadmapService

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("/submit", status_code=status.HTTP_202_ACCEPTED)
async def submit_project(
    request: Request,
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    project_type: str = Form(...),
    description: str = Form(...),
    github_url: Optional[str] = Form(None),
    live_url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    # Rate limit: 3 per hour per user
    identifier = get_client_identifier(request, current_user.id)
    allowed, err = check_rate_limit(identifier, "project_submit", 3, 3600)
    if not allowed:
        raise HTTPException(status_code=429, detail=err)

    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    submission = await ProjectEvaluationService.submit_project(
        db, profile.id, title, project_type, description, github_url, live_url, file
    )

    # Get career role name for evaluation
    career_role_name = ""
    if profile.target_role_id:
        from app.models.career import CareerRole
        from sqlalchemy import select as sa_select
        cr_res = await db.execute(sa_select(CareerRole).where(CareerRole.id == profile.target_role_id))
        cr = cr_res.scalar_one_or_none()
        career_role_name = cr.name if cr else "General"

    # Schedule background evaluation
    background_tasks.add_task(
        ProjectEvaluationService.evaluate_in_background,
        submission.id,
        profile.id,
        description,
        submission.file_path,
        github_url,
        live_url,
        project_type,
        title,
        career_role_name,
    )

    return {"message": "Project submitted for evaluation.", "id": submission.id, "status": "evaluating"}


@router.get("/")
async def list_projects(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await ProjectEvaluationService.get_student_projects(db, profile.id)


@router.get("/{project_id}")
async def get_project_detail(
    project_id: int,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await ProjectEvaluationService.get_project_detail(db, profile.id, project_id)


@router.get("/student/{profile_id}")
async def get_student_projects_mentor(
    profile_id: int,
    current_user: User = Depends(get_current_student_profile),
    db: AsyncSession = Depends(get_db)
):
    """Mentor view of student projects."""
    return await ProjectEvaluationService.get_project_for_mentor(db, profile_id)
