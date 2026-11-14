"""Resume parsing and AI evidence extraction with student confirmation."""
import io
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.career_intelligence import ResumeUpload
from app.models.profile import StudentProfile
from app.models.skill import Skill, LearnerSkill
from app.models.analytics import LearningActivity
from app.agents.resume_evidence_agent import ResumeEvidenceAgent


def _safe_filename(original: str) -> str:
    name = os.path.basename(original)
    ext = os.path.splitext(name)[1].lower()
    return f"{uuid.uuid4().hex[:12]}{ext}"


async def _extract_text(content: bytes, file_type: str) -> str:
    """Extract plain text from uploaded file bytes."""
    if file_type == "txt":
        return content.decode("utf-8", errors="ignore")[:50000]
    if file_type == "pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(content))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            return text[:50000]
        except Exception:
            return "(PDF text extraction failed)"
    if file_type == "docx":
        try:
            from docx import Document as DocxDocument
            doc = DocxDocument(io.BytesIO(content))
            text = "\n".join(p.text for p in doc.paragraphs)
            return text[:50000]
        except Exception:
            return "(DOCX text extraction failed)"
    return ""


class ResumeService:
    @staticmethod
    async def upload_resume(
        db: AsyncSession, profile_id: int, file: UploadFile
    ) -> ResumeUpload:
        filename = file.filename or "resume.txt"
        ext = os.path.splitext(filename)[1].lower().lstrip(".")
        if ext not in ("pdf", "docx", "txt"):
            raise HTTPException(status_code=400, detail="Only PDF, DOCX, and TXT resumes are accepted.")

        content = await file.read()
        if len(content) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File exceeds 5 MB limit.")

        upload_dir = Path(settings.UPLOAD_DIR) / "resumes" / str(profile_id)
        upload_dir.mkdir(parents=True, exist_ok=True)
        safe_name = _safe_filename(filename)
        file_path = upload_dir / safe_name
        file_path.write_bytes(content)

        resume = ResumeUpload(
            student_profile_id=profile_id,
            file_name=filename,
            file_path=str(file_path),
            file_type=ext,
            status="processing",
            created_at=datetime.now(timezone.utc),
        )
        db.add(resume)
        await db.commit()
        await db.refresh(resume)
        return resume

    @staticmethod
    async def process_resume(resume_id: int) -> None:
        """Background task: extract text and run AI analysis."""
        from app.db.session import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            res = await session.execute(select(ResumeUpload).where(ResumeUpload.id == resume_id))
            resume = res.scalar_one_or_none()
            if not resume:
                return
            try:
                # Read file and extract text
                file_path = Path(resume.file_path)
                if file_path.exists():
                    content = file_path.read_bytes()
                    text = await _extract_text(content, resume.file_type)
                else:
                    text = "(file not found)"

                resume.extracted_text = text

                # Load known skills and career role
                from app.models.profile import StudentProfile
                from app.models.career import CareerRole
                prof_res = await session.execute(
                    select(StudentProfile).where(StudentProfile.id == resume.student_profile_id)
                )
                profile = prof_res.scalar_one_or_none()
                career_role = "General"
                if profile and profile.target_role_id:
                    cr_res = await session.execute(
                        select(CareerRole).where(CareerRole.id == profile.target_role_id)
                    )
                    cr = cr_res.scalar_one_or_none()
                    if cr:
                        career_role = cr.name

                skill_res = await session.execute(select(Skill))
                known_skills = [s.name for s in skill_res.scalars().all()]

                # Run AI extraction
                extracted = await ResumeEvidenceAgent.run(text, career_role, known_skills)

                resume.extracted_profile = extracted
                resume.status = "processed"
                resume.processed_at = datetime.now(timezone.utc)
                await session.commit()
            except Exception as e:
                resume.status = "failed"
                resume.extracted_profile = {"error": str(e)[:200]}
                await session.commit()

    @staticmethod
    async def confirm_skills(
        db: AsyncSession, profile_id: int, resume_id: int, confirmed: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply confirmed skills to LearnerSkill, then trigger gap reanalysis."""
        res = await db.execute(
            select(ResumeUpload).where(
                ResumeUpload.id == resume_id,
                ResumeUpload.student_profile_id == profile_id,
            )
        )
        resume = res.scalar_one_or_none()
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found.")

        updated = []
        for item in confirmed:
            skill_name = item.get("skill", "").strip()
            level = max(1, min(5, int(item.get("suggested_level", 2))))
            if not skill_name:
                continue
            s_res = await db.execute(select(Skill).where(Skill.name == skill_name))
            skill = s_res.scalar_one_or_none()
            if not skill:
                continue
            mastery = (level / 5.0) * 100.0
            ls_res = await db.execute(
                select(LearnerSkill).where(
                    LearnerSkill.student_profile_id == profile_id,
                    LearnerSkill.skill_id == skill.id,
                )
            )
            ls = ls_res.scalar_one_or_none()
            if ls:
                if ls.mastery_percentage < mastery:
                    ls.mastery_percentage = mastery
                    ls.verified_level = float(level)
                    ls.evidence_type = "project"
                    ls.updated_at = datetime.now(timezone.utc)
            else:
                ls = LearnerSkill(
                    student_profile_id=profile_id, skill_id=skill.id,
                    self_reported_level=level, verified_level=float(level),
                    evidence_type="project", mastery_percentage=mastery,
                )
                db.add(ls)
            updated.append(skill_name)

        resume.confirmed_skills = confirmed
        activity = LearningActivity(
            student_profile_id=profile_id, activity_type="mentor_feedback",
            meta={"type": "resume_skills_confirmed", "skills": updated},
            created_at=datetime.now(timezone.utc),
        )
        db.add(activity)
        await db.commit()
        return {"confirmed_skills": updated, "count": len(updated)}

    @staticmethod
    async def list_resumes(db: AsyncSession, profile_id: int) -> List[Dict[str, Any]]:
        res = await db.execute(
            select(ResumeUpload).where(ResumeUpload.student_profile_id == profile_id)
            .order_by(ResumeUpload.created_at.desc())
        )
        return [
            {"id": r.id, "file_name": r.file_name, "file_type": r.file_type,
             "status": r.status, "created_at": r.created_at.isoformat(),
             "extracted_profile": r.extracted_profile}
            for r in res.scalars().all()
        ]
