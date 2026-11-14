"""Career Intelligence API: resume, job match, career advisor."""
from typing import Optional
from fastapi import APIRouter, Depends, BackgroundTasks, UploadFile, File, Form, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_student, get_db
from app.core.rate_limit import check_rate_limit, get_client_identifier
from app.models.user import User
from app.services.resume_service import ResumeService
from app.services.job_matching_service import JobMatchingService
from app.services.career_advisor_service import CareerAdvisorService
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/career-intelligence", tags=["Career Intelligence"])


# ---- Resume ----

@router.post("/resume/upload")
async def upload_resume(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    identifier = get_client_identifier(request, current_user.id)
    allowed, err = check_rate_limit(identifier, "resume_upload", 3, 3600)
    if not allowed:
        raise HTTPException(status_code=429, detail=err)

    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    resume = await ResumeService.upload_resume(db, profile.id, file)
    background_tasks.add_task(ResumeService.process_resume, resume.id)
    return {"resume_id": resume.id, "status": "processing", "file_name": resume.file_name}


@router.get("/resume/list")
async def list_resumes(current_user: User = Depends(require_student), db: AsyncSession = Depends(get_db)):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await ResumeService.list_resumes(db, profile.id)


@router.post("/resume/{resume_id}/confirm")
async def confirm_resume_skills(
    resume_id: int,
    body: dict,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """body = {"confirmed": [{skill, suggested_level}, ...]}"""
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    confirmed = body.get("confirmed", [])
    return await ResumeService.confirm_skills(db, profile.id, resume_id, confirmed)


# ---- Job Match ----

@router.post("/job-match/analyze")
async def analyze_job(
    request: Request,
    body: dict,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    identifier = get_client_identifier(request, current_user.id)
    allowed, err = check_rate_limit(identifier, "job_analyze", 5, 3600)
    if not allowed:
        raise HTTPException(status_code=429, detail=err)

    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await JobMatchingService.analyze_job(
        db, profile.id,
        title=body.get("title", "Job"),
        company=body.get("company"),
        jd_text=body.get("job_description_text", ""),
        source_url=body.get("source_url"),
    )


@router.get("/job-match/history")
async def job_match_history(current_user: User = Depends(require_student), db: AsyncSession = Depends(get_db)):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await JobMatchingService.get_match_history(db, profile.id)


@router.get("/job-match/{match_id}")
async def get_job_match(match_id: int, current_user: User = Depends(require_student), db: AsyncSession = Depends(get_db)):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await JobMatchingService.get_match(db, profile.id, match_id)


# ---- Career Advisor ----

@router.get("/career-advisor")
async def get_career_recommendations(current_user: User = Depends(require_student), db: AsyncSession = Depends(get_db)):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await CareerAdvisorService.get_career_recommendations(db, profile.id)


@router.get("/career-advisor/compare")
async def compare_careers(
    primary_role_id: int, alt_role_id: int,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await CareerAdvisorService.compare_careers(db, profile.id, primary_role_id, alt_role_id)
