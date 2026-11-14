"""ResumeEvidenceAgent — extracts skills/projects from resume text using Grok."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.agents.base_agent import BaseAgent


class ExtractedSkill(BaseModel):
    skill: str
    evidence: str
    confidence: str = "medium"
    suggested_level: int = 2
    evidence_type: str = "resume"


class ExtractedProject(BaseModel):
    title: str
    description: str
    skills: List[str] = []
    evidence_strength: str = "medium"


class ExtractedCertification(BaseModel):
    title: str
    issuer: str
    skills: List[str] = []


class ATSIssue(BaseModel):
    issue: str
    severity: str = "medium"
    recommendation: str


class ATSReadiness(BaseModel):
    score: int = 50
    issues: List[ATSIssue] = []


class CareerAlignment(BaseModel):
    career_role: str = ""
    alignment_score: int = 50
    reason: str = ""


class ResumeExtractionResult(BaseModel):
    extracted_skills: List[ExtractedSkill] = []
    projects: List[ExtractedProject] = []
    certifications: List[ExtractedCertification] = []
    ats_readiness: ATSReadiness = Field(default_factory=ATSReadiness)
    missing_information: List[str] = []
    recommendations: List[str] = []
    career_alignment: CareerAlignment = Field(default_factory=CareerAlignment)


class ResumeEvidenceAgent(BaseAgent):
    agent_name = "resume_evidence_agent"

    @classmethod
    async def run(cls, resume_text: str, career_role: str, known_skills: List[str]) -> Dict[str, Any]:
        system_prompt = (
            f"You are an expert resume analyst for a career-readiness platform. "
            f"Extract skills, projects, and certifications from the resume below. "
            f"Map skill names to this known taxonomy where possible: {', '.join(known_skills[:30])}. "
            f"The student's target career role is {career_role}. "
            f"Do NOT invent skills not supported by text evidence. "
            f"If confidence is low, reflect that in the confidence field."
        )
        user_prompt = f"Resume text:\n{resume_text[:8000]}"

        result = await cls.call_structured_output(system_prompt, user_prompt, ResumeExtractionResult)
        if result:
            return result.model_dump()
        return cls._fallback(career_role)

    @staticmethod
    def _fallback(career_role: str) -> Dict[str, Any]:
        return {
            "extracted_skills": [],
            "projects": [],
            "certifications": [],
            "ats_readiness": {
                "score": 50,
                "issues": [
                    {"issue": "Could not auto-analyse resume", "severity": "low",
                     "recommendation": "Review manually with your mentor."}
                ]
            },
            "missing_information": ["AI analysis unavailable — please review manually."],
            "recommendations": ["Ensure your resume includes a skills section and quantified project descriptions."],
            "career_alignment": {"career_role": career_role, "alignment_score": 0,
                                 "reason": "AI unavailable for alignment analysis."}
        }
