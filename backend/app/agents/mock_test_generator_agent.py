"""MockTestGeneratorAgent: Generates practice test questions for a weak topic.
Validates AI output before saving. Falls back to existing question bank."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.agents.base_agent import BaseAgent


class GeneratedQuestion(BaseModel):
    subtopic: str
    question_text: str
    options: Dict[str, str]
    correct_option: str
    explanation: str
    difficulty: str = "medium"
    marks: int = 1


class MockTestResult(BaseModel):
    title: str
    skill_name: str
    questions: List[GeneratedQuestion]


class MockTestGeneratorAgent(BaseAgent):
    @classmethod
    async def run(
        cls,
        skill_name: str,
        weak_subtopics: List[str],
        existing_questions: List[Dict[str, Any]],
        difficulty: str = "medium"
    ) -> Optional[Dict[str, Any]]:
        system_prompt = f"""You are an assessment generator for a learning platform.
Generate 5-8 practice questions for {skill_name}, focusing on these weak subtopics: {', '.join(weak_subtopics)}.
Each question must have 4 options (A, B, C, D), a correct answer, and an explanation.
The questions should be at {difficulty} difficulty.
Do NOT reuse existing questions."""

        existing_text = "\n".join(f"- {q['question_text'][:80]}" for q in existing_questions[:10])
        user_prompt = f"""Skill: {skill_name}
Weak Subtopics: {', '.join(weak_subtopics)}
Difficulty: {difficulty}

Existing questions to avoid duplicating:
{existing_text}

Generate 5-8 new practice questions."""

        result = await cls.call_structured_output(system_prompt, user_prompt, MockTestResult)
        if result and result.questions:
            return result.model_dump()
        return None  # Signal fallback to existing questions
