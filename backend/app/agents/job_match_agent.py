"""JobMatchAgent — analyses job description fit using Grok."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.agents.base_agent import BaseAgent


class MatchedSkill(BaseModel):
    skill: str
    evidence: str = ""
    match_type: str = "exact"
    confidence: str = "medium"


class MissingSkill(BaseModel):
    skill: str
    importance: str = "medium"
    evidence_in_jd: str = ""
    recommended_action: str = ""


class PartialSkill(BaseModel):
    skill: str
    current_evidence: str = ""
    gap: str = ""
    recommended_action: str = ""


class LearningPlanItem(BaseModel):
    title: str
    skill: str
    estimated_hours: int = 10
    resources: List[Dict[str, str]] = []
    practical_task: str = ""


class InterviewPrep(BaseModel):
    question: str
    skill: str
    reason: str = ""


class JobMatchResult(BaseModel):
    job_title: str = ""
    overall_match_score: float = 0.0
    skill_match_score: float = 0.0
    experience_match_score: Optional[float] = None
    education_match_score: Optional[float] = None
    matched_skills: List[MatchedSkill] = []
    missing_skills: List[MissingSkill] = []
    partial_skills: List[PartialSkill] = []
    resume_improvements: List[str] = []
    learning_plan: List[LearningPlanItem] = []
    interview_preparation: List[InterviewPrep] = []
    summary: str = ""


class JobMatchAgent(BaseAgent):
    agent_name = "job_match_agent"

    @classmethod
    async def run(
        cls, jd_text: str, job_title: str, skill_mastery: List[Dict[str, Any]],
        career_role: str, known_skills: List[str]
    ) -> Dict[str, Any]:
        skills_summary = "\n".join(
            f"- {s['name']}: {s['mastery']:.0f}% mastery" for s in skill_mastery[:20]
        )
        system_prompt = (
            f"You are a career advisor. Analyse the student's fit for the job description. "
            f"Use skill names from: {', '.join(known_skills[:30])}. "
            f"Calculate overall_match_score deterministically from matched vs total required skills. "
            f"skill_match_score = matched_skills / (matched + missing + partial) * 100. "
            f"Target career role: {career_role}."
        )
        user_prompt = (
            f"Job title: {job_title}\nJob description:\n{jd_text[:5000]}\n\n"
            f"Student skill mastery:\n{skills_summary}"
        )

        result = await cls.call_structured_output(system_prompt, user_prompt, JobMatchResult)
        if result:
            return result.model_dump()
        return cls._fallback(job_title, skill_mastery)

    @staticmethod
    def _fallback(job_title: str, skill_mastery: List[Dict[str, Any]]) -> Dict[str, Any]:
        strong = [s for s in skill_mastery if s.get("mastery", 0) >= 70]
        return {
            "job_title": job_title,
            "overall_match_score": round(len(strong) / max(len(skill_mastery), 1) * 100, 1),
            "skill_match_score": round(len(strong) / max(len(skill_mastery), 1) * 100, 1),
            "experience_match_score": None, "education_match_score": None,
            "matched_skills": [{"skill": s["name"], "evidence": "Platform verified",
                                 "match_type": "exact", "confidence": "high"}
                               for s in strong[:5]],
            "missing_skills": [], "partial_skills": [],
            "resume_improvements": ["Add quantified achievements to your project descriptions."],
            "learning_plan": [], "interview_preparation": [],
            "summary": "AI analysis unavailable. Deterministic match based on verified skill mastery."
        }
