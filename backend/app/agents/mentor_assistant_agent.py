"""MentorAssistantAgent: Drafts initial answers to student doubts using learner context.
Must not reveal complete solutions. Falls back to guidance-based hint."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.agents.base_agent import BaseAgent


class MentorAssistantResult(BaseModel):
    draft_answer: str
    confidence: str = "medium"  # "high", "medium", "low"
    suggests_mentor: bool = False
    reason: str = ""


class MentorAssistantAgent(BaseAgent):
    @classmethod
    async def run(
        cls,
        student_question: str,
        subject: str,
        skill_name: str,
        skill_mastery: float,
        roadmap_module_title: Optional[str],
        relevant_resources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        system_prompt = """You are a teaching assistant for a learning platform.
Draft a helpful but guided answer to the student's doubt.
Do NOT reveal complete solutions to coding problems.
Encourage understanding by providing hints, explanations, and pointing to resources.
If the doubt is complex or requires personalized guidance, suggest connecting with the mentor."""

        user_prompt = f"""Student Question: {student_question}
Subject: {subject}
Skill: {skill_name} (Current mastery: {skill_mastery}%)
Related Roadmap Module: {roadmap_module_title or 'None'}

Relevant Resources:
{chr(10).join(f"- {r.get('title', '')}: {r.get('url', '')}" for r in relevant_resources[:5])}

Draft a guided answer that helps the student understand the concept without giving away complete solutions."""

        result = await cls.call_structured_output(system_prompt, user_prompt, MentorAssistantResult)
        if result:
            return result.model_dump()
        return cls._deterministic_fallback(student_question, subject, skill_name, skill_mastery, relevant_resources)

    @staticmethod
    def _deterministic_fallback(
        student_question: str,
        subject: str,
        skill_name: str,
        skill_mastery: float,
        relevant_resources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        resources_text = ""
        if relevant_resources:
            resources_text = "\n\nHere are some resources that may help:\n" + "\n".join(
                f"- {r.get('title', '')}: {r.get('url', '')}" for r in relevant_resources[:3]
            )
        return {
            "draft_answer": f"Your question about {subject} ({skill_name}) is a great one. "
            f"Let me break down the concept: try to identify the core pattern in the problem, "
            f"then think about edge cases.{resources_text}\n\n"
            f"If you need more detailed guidance, consider reaching out to your mentor for a 1:1 session.",
            "confidence": "medium",
            "suggests_mentor": False,
            "reason": "AI unavailable; generated guided hint with resource pointers.",
        }
