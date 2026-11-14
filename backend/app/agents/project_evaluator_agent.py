"""ProjectEvaluatorAgent: Evaluates student projects against a rubric using OpenAI Structured Outputs.
Falls back to rubric-based deterministic checklist on AI failure."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.agents.base_agent import BaseAgent


class VerifiedSkill(BaseModel):
    skill: str
    evidence: str
    confidence: str = "medium"  # "high", "medium", "low"


class ProjectWeakness(BaseModel):
    area: str
    issue: str
    severity: str = "medium"  # "critical", "high", "medium", "low"
    improvement: str


class RubricScore(BaseModel):
    criterion: str
    score: float
    max_score: float
    feedback: str


class RoadmapImpact(BaseModel):
    skill: str
    action: str  # "verify", "improve", "no_change"
    reason: str


class ProjectEvaluationResult(BaseModel):
    project_title: str
    overall_score: float = 0.0
    verdict: str = "needs_improvement"  # "strong", "good", "needs_improvement", "weak"
    verified_skills: List[VerifiedSkill] = []
    strengths: List[str] = []
    weaknesses: List[ProjectWeakness] = []
    limitations: List[str] = []
    rubric_scores: List[RubricScore] = []
    security_flags: List[str] = []
    portfolio_readiness: str = "not_ready"  # "ready", "almost_ready", "not_ready"
    next_improvements: List[str] = []
    roadmap_impact: List[RoadmapImpact] = []
    mentor_review_required: bool = True


class ProjectEvaluatorAgent(BaseAgent):
    @classmethod
    async def run(
        cls,
        project_title: str,
        project_type: str,
        description: str,
        extracted_text: str,
        github_url: Optional[str],
        live_url: Optional[str],
        career_role: str,
        rubric: Dict[str, Any]
    ) -> Dict[str, Any]:
        rubric_text = "\n".join(
            f"- {c.get('criterion', '')}: weight {c.get('weight', 0)}" 
            for c in rubric.get("criteria", [])
        )

        system_prompt = f"""You are a senior technical project evaluator.
Evaluate this {project_type} project submitted for the role of {career_role}.
Score each rubric criterion from 0 to its weight. The overall score is the sum of criterion scores.
The overall score must NOT exceed the total weight ({rubric.get('total_weight', 100)}).
Clearly state limitations if code cannot be executed or repositories are inaccessible.
Do not claim a project is fully verified unless sufficient evidence exists.
Be thorough but fair."""

        user_prompt = f"""Project Title: {project_title}
Type: {project_type}
Target Career Role: {career_role}

Description:
{description[:2000]}

Extracted Code / README Text:
{extracted_text[:4000]}

GitHub URL: {github_url or 'Not provided'}
Live URL: {live_url or 'Not provided'}

Rubric Criteria (criterion: weight):
{rubric_text}

Evaluate the project against each rubric criterion. Provide strengths, weaknesses, limitations, and next improvements."""

        result = await cls.call_structured_output(system_prompt, user_prompt, ProjectEvaluationResult)
        if result:
            # Validate overall score within rubric range
            max_score = float(rubric.get("total_weight", 100))
            if result.overall_score > max_score:
                result.overall_score = max_score
            return result.model_dump()
        return cls._deterministic_fallback(project_title, rubric)

    @staticmethod
    def _deterministic_fallback(project_title: str, rubric: Dict[str, Any]) -> Dict[str, Any]:
        criteria = rubric.get("criteria", [])
        rubric_scores = [
            {
                "criterion": c.get("criterion", ""),
                "score": 0.0,
                "max_score": float(c.get("weight", 0)),
                "feedback": "Manual review required. AI evaluation unavailable."
            }
            for c in criteria
        ]
        return {
            "project_title": project_title,
            "overall_score": 0.0,
            "verdict": "needs_improvement",
            "verified_skills": [],
            "strengths": [],
            "weaknesses": [],
            "limitations": ["AI evaluation unavailable. Manual mentor review required."],
            "rubric_scores": rubric_scores,
            "security_flags": [],
            "portfolio_readiness": "not_ready",
            "next_improvements": ["Review rubric criteria and ensure each is addressed.", "Add comprehensive documentation."],
            "roadmap_impact": [],
            "mentor_review_required": True,
        }
