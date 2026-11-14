"""InterviewEvaluatorAgent — scores student interview answer using Grok."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.agents.base_agent import BaseAgent


class SkillImpact(BaseModel):
    skill: str = ""
    mastery_change: float = 0.0
    reason: str = ""


class InterviewEvalResult(BaseModel):
    score: float = 0.0
    verdict: str = "needs_improvement"
    strengths: List[str] = []
    weaknesses: List[str] = []
    missing_points: List[str] = []
    improved_answer: str = ""
    skill_impact: SkillImpact = Field(default_factory=SkillImpact)
    follow_up_question: Optional[str] = None


class InterviewEvaluatorAgent(BaseAgent):
    agent_name = "interview_evaluator_agent"

    @classmethod
    async def run(
        cls, question_text: str, expected_points: List[str],
        student_answer: str, skill: str, career_role: str
    ) -> Dict[str, Any]:
        rubric = (
            "Rubric: Technical accuracy 30%, Relevance 25%, Clarity 20%, "
            "Completeness 15%, Communication 10%."
        )
        system_prompt = (
            f"You are an expert {career_role} interview evaluator. "
            f"Score the student's answer on a 0-100 scale. {rubric} "
            f"Provide constructive feedback. Do NOT reveal the full expected answer. "
            f"Only increase mastery if the answer demonstrates clear competency (score >= 75)."
        )
        user_prompt = (
            f"Question: {question_text}\n"
            f"Expected answer points: {', '.join(expected_points)}\n"
            f"Student answer: {student_answer[:3000]}\n"
            f"Skill: {skill}"
        )

        result = await cls.call_structured_output(system_prompt, user_prompt, InterviewEvalResult)
        if result:
            return result.model_dump()
        # Deterministic fallback: self-evaluation checklist
        covered = sum(1 for p in expected_points if p.lower()[:20] in student_answer.lower())
        score = round((covered / max(len(expected_points), 1)) * 60, 1)
        return {
            "score": score,
            "verdict": "good" if score >= 60 else "needs_improvement",
            "strengths": ["Answer submitted."],
            "weaknesses": ["AI feedback unavailable — review expected points below."],
            "missing_points": [p for p in expected_points if p.lower()[:20] not in student_answer.lower()],
            "improved_answer": "Review the expected answer points and strengthen your response.",
            "skill_impact": {"skill": skill, "mastery_change": 0.0, "reason": "AI unavailable"},
            "follow_up_question": None
        }
