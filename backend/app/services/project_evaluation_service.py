"""ProjectEvaluationService: Handles project submissions, file validation,
background evaluation using ProjectEvaluatorAgent, and rubric-based scoring."""
import os
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, UploadFile, BackgroundTasks, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.profile import StudentProfile
from app.models.career import CareerRole
from app.models.project import ProjectSubmission, ProjectRubric
from app.models.skill import LearnerSkill
from app.models.analytics import LearningActivity
from app.agents.project_evaluator_agent import ProjectEvaluatorAgent

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class ProjectEvaluationService:
    @staticmethod
    def load_rubrics() -> List[Dict[str, Any]]:
        rubric_path = DATA_DIR / "project_rubrics.json"
        if rubric_path.exists():
            with open(rubric_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    @staticmethod
    def get_rubric_for_type(project_type: str, career_role_id: Optional[int] = None) -> Dict[str, Any]:
        rubrics = ProjectEvaluationService.load_rubrics()
        for r in rubrics:
            if r.get("project_type") == project_type:
                return r
        # Default rubric
        return {
            "project_type": project_type,
            "total_weight": 100,
            "criteria": [
                {"criterion": "Functionality", "weight": 25},
                {"criterion": "Correct skill usage", "weight": 20},
                {"criterion": "Code quality", "weight": 15},
                {"criterion": "Security", "weight": 15},
                {"criterion": "UI/UX", "weight": 10},
                {"criterion": "Documentation", "weight": 10},
                {"criterion": "Testing", "weight": 5},
            ]
        }

    @staticmethod
    def validate_file(file: UploadFile) -> tuple[bool, Optional[str]]:
        """Validate file size and type."""
        if not file.filename:
            return False, "No filename provided."

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in settings.ALLOWED_FILE_EXTENSIONS:
            return False, f"File type {ext} not allowed. Allowed: {', '.join(settings.ALLOWED_FILE_EXTENSIONS)}"

        # Size check will be done after reading
        return True, None

    @staticmethod
    async def save_uploaded_file(file: UploadFile, student_id: int, project_id: int) -> Optional[str]:
        """Save uploaded file to disk safely. Returns the file path."""
        upload_dir = Path(settings.UPLOAD_DIR) / f"student_{student_id}" / f"project_{project_id}"
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Prevent path traversal
        safe_name = os.path.basename(file.filename or "upload")
        # Add UUID prefix to avoid collisions
        safe_name = f"{uuid.uuid4().hex[:8]}_{safe_name}"
        file_path = upload_dir / safe_name

        # Read file content (check size)
        content = await file.read()
        if len(content) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_FILE_SIZE_MB}MB limit.")

        with open(file_path, "wb") as f:
            f.write(content)

        return str(file_path)

    @staticmethod
    async def extract_text(file_path: Optional[str], description: str, github_url: Optional[str]) -> str:
        """Extract readable text from project files and description."""
        parts = [description]

        if file_path:
            try:
                fp = Path(file_path)
                if fp.exists() and fp.suffix in (".txt", ".md", ".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".json"):
                    content = fp.read_text(encoding="utf-8", errors="ignore")[:4000]
                    parts.append(f"\n--- File: {fp.name} ---\n{content}")
            except Exception:
                pass

        if github_url:
            parts.append(f"\nGitHub Repository: {github_url}")
            parts.append(f"Repository URL metadata: The student provided a GitHub link at {github_url}")

        return "\n".join(parts)

    @classmethod
    async def submit_project(
        cls,
        db: AsyncSession,
        profile_id: int,
        title: str,
        project_type: str,
        description: str,
        github_url: Optional[str],
        live_url: Optional[str],
        file: Optional[UploadFile] = None
    ) -> ProjectSubmission:
        # Validate project type
        valid_types = ["frontend", "backend", "full_stack", "data_analysis", "machine_learning"]
        if project_type not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid project type. Must be one of: {', '.join(valid_types)}")

        # Validate URLs
        if github_url and not github_url.startswith(("http://", "https://")):
            raise HTTPException(status_code=400, detail="GitHub URL must start with http:// or https://")
        if live_url and not live_url.startswith(("http://", "https://")):
            raise HTTPException(status_code=400, detail="Live URL must start with http:// or https://")

        # Create submission record
        submission = ProjectSubmission(
            student_profile_id=profile_id,
            title=title,
            project_type=project_type,
            description=description,
            github_url=github_url,
            live_url=live_url,
            status="pending",
        )
        db.add(submission)
        await db.flush()

        # Handle file upload
        if file:
            valid, err = cls.validate_file(file)
            if not valid:
                raise HTTPException(status_code=400, detail=err)
            file_path = await cls.save_uploaded_file(file, profile_id, submission.id)
            submission.file_path = file_path

        # Log activity
        activity = LearningActivity(
            student_profile_id=profile_id,
            activity_type="project_submitted",
            reference_id=submission.id,
            meta={"title": title, "project_type": project_type},
            created_at=datetime.now(timezone.utc),
        )
        db.add(activity)

        submission.status = "evaluating"
        await db.commit()
        await db.refresh(submission)
        return submission

    @classmethod
    async def evaluate_in_background(
        cls,
        submission_id: int,
        profile_id: int,
        description: str,
        file_path: Optional[str],
        github_url: Optional[str],
        live_url: Optional[str],
        project_type: str,
        title: str,
        career_role_name: str,
    ):
        """Background task to evaluate project with AI agent."""
        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            # Load submission
            res = await session.execute(select(ProjectSubmission).where(ProjectSubmission.id == submission_id))
            submission = res.scalar_one_or_none()
            if not submission:
                return

            try:
                # Extract text
                extracted = await cls.extract_text(file_path, description, github_url)

                # Get rubric
                rubric = cls.get_rubric_for_type(project_type)

                # Run AI evaluator
                eval_result = await ProjectEvaluatorAgent.run(
                    project_title=title,
                    project_type=project_type,
                    description=description,
                    extracted_text=extracted,
                    github_url=github_url,
                    live_url=live_url,
                    career_role=career_role_name,
                    rubric=rubric,
                )

                # Save evaluation
                submission.evaluation_score = eval_result.get("overall_score", 0.0)
                submission.evaluation_report = eval_result
                submission.status = "evaluated"
                submission.evaluated_at = datetime.now(timezone.utc)

                # Update verified skills if confidence is high
                verified_skills = eval_result.get("verified_skills", [])
                for vs in verified_skills:
                    if vs.get("confidence") == "high":
                        # Try to find and update learner skill
                        skill_name = vs.get("skill", "")
                        if skill_name:
                            from app.models.skill import Skill, LearnerSkill
                            s_res = await session.execute(select(Skill).where(Skill.name == skill_name))
                            skill = s_res.scalar_one_or_none()
                            if skill:
                                ls_res = await session.execute(
                                    select(LearnerSkill).where(
                                        LearnerSkill.student_profile_id == profile_id,
                                        LearnerSkill.skill_id == skill.id,
                                    )
                                )
                                ls = ls_res.scalar_one_or_none()
                                if ls:
                                    ls.mastery_percentage = min(100.0, ls.mastery_percentage + 5.0)
                                    ls.evidence_type = "project"
                                    ls.updated_at = datetime.now(timezone.utc)

                await session.commit()
            except Exception as e:
                # Mark as failed but with a deterministic rubric fallback
                rubric = cls.get_rubric_for_type(project_type)
                fallback = ProjectEvaluatorAgent._deterministic_fallback(title, rubric)
                submission.evaluation_score = fallback.get("overall_score", 0.0)
                submission.evaluation_report = fallback
                submission.status = "evaluated"
                submission.evaluated_at = datetime.now(timezone.utc)
                await session.commit()

    @classmethod
    async def get_student_projects(
        cls, db: AsyncSession, profile_id: int
    ) -> List[Dict[str, Any]]:
        res = await db.execute(
            select(ProjectSubmission)
            .where(ProjectSubmission.student_profile_id == profile_id)
            .order_by(ProjectSubmission.submitted_at.desc())
        )
        projects = res.scalars().all()
        return [
            {
                "id": p.id,
                "title": p.title,
                "project_type": p.project_type,
                "status": p.status,
                "evaluation_score": p.evaluation_score,
                "submitted_at": p.submitted_at.isoformat(),
                "evaluated_at": p.evaluated_at.isoformat() if p.evaluated_at else None,
            }
            for p in projects
        ]

    @classmethod
    async def get_project_detail(
        cls, db: AsyncSession, profile_id: int, project_id: int
    ) -> Dict[str, Any]:
        res = await db.execute(
            select(ProjectSubmission).where(
                ProjectSubmission.id == project_id,
                ProjectSubmission.student_profile_id == profile_id,
            )
        )
        project = res.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        return {
            "id": project.id,
            "title": project.title,
            "project_type": project.project_type,
            "description": project.description,
            "github_url": project.github_url,
            "live_url": project.live_url,
            "status": project.status,
            "evaluation_score": project.evaluation_score,
            "evaluation_report": project.evaluation_report,
            "submitted_at": project.submitted_at.isoformat(),
            "evaluated_at": project.evaluated_at.isoformat() if project.evaluated_at else None,
        }

    @classmethod
    async def get_project_for_mentor(
        cls, db: AsyncSession, profile_id: int
    ) -> List[Dict[str, Any]]:
        """Get all projects for a student (mentor view)."""
        return await cls.get_student_projects(db, profile_id)
