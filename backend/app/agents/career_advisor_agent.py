"""CareerAdvisorAgent — recommends career alternatives using Grok."""
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from app.agents.base_agent import BaseAgent


class PrimaryCareer(BaseModel):
    career_role: str = ""
    readiness_score: float = 0.0
    match_score: float = 0.0
    reason: str = ""


class AlternativeCareer(BaseModel):
    career_role: str = ""
    readiness_score: float = 0.0
    match_score: float = 0.0
    transferable_skills: List[str] = []
    missing_skills: List[str] = []
    estimated_weeks_to_readiness: int = 12
    reason: str = ""


class CareerAdvisorResult(BaseModel):
    primary_career: PrimaryCareer = Field(default_factory=PrimaryCareer)
    alternative_careers: List[AlternativeCareer] = []
    recommended_career: str = ""
    recommendation_reason: str = ""
    next_best_action: str = ""


class CareerAdvisorAgent(BaseAgent):
    agent_name = "career_advisor_agent"

    @classmethod
    async def run(
        cls, current_role: str, skill_mastery: List[Dict[str, Any]],
        all_roles: List[str], readiness_score: float
    ) -> Dict[str, Any]:
        skills_summary = "\n".join(
            f"- {s['name']}: {s['mastery']:.0f}%" for s in skill_mastery[:20]
        )
        system_prompt = (
            f"You are a career advisor. The student's current target role is {current_role} "
            f"with a readiness score of {readiness_score:.0f}%. "
            f"Suggest 2-3 alternative career roles from: {', '.join(all_roles)}. "
            f"Calculate readiness and match scores based on the skill mastery data. "
            f"Identify transferable skills and missing skills."
        )
        user_prompt = (
            f"Current role: {current_role}\nReadiness: {readiness_score:.0f}%\n"
            f"Skill mastery:\n{skills_summary}\n"
            f"Available roles: {', '.join(all_roles)}"
        )

        result = await cls.call_structured_output(system_prompt, user_prompt, CareerAdvisorResult)
        if result:
            return result.model_dump()
        # Deterministic fallback
        alts = [r for r in all_roles if r != current_role][:2]
        return {
            "primary_career": {"career_role": current_role, "readiness_score": readiness_score,
                               "match_score": readiness_score, "reason": "Current target role."},
            "alternative_careers": [
                {"career_role": r, "readiness_score": 0.0, "match_score": 0.0,
                 "transferable_skills": [], "missing_skills": [],
                 "estimated_weeks_to_readiness": 16, "reason": "Alternative path based on your skills."}
                for r in alts
            ],
            "recommended_career": current_role,
            "recommendation_reason": "AI analysis unavailable. Continue on current path.",
            "next_best_action": "Complete your active roadmap modules."
        }
