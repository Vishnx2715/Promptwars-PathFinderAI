"""InterviewQuestionAgent — generates 5 interview questions using Grok."""
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from app.agents.base_agent import BaseAgent


class IQQuestion(BaseModel):
    question_text: str
    question_type: str = "technical"
    skill: str = ""
    difficulty: str = "medium"
    expected_answer_points: List[str] = []
    reason: str = ""


class InterviewQuestionsResult(BaseModel):
    interview_title: str = ""
    questions: List[IQQuestion] = []


# Fallback questions per type
_FALLBACK: Dict[str, List[Dict[str, Any]]] = {
    "technical": [
        {"question_text": "Explain the difference between synchronous and asynchronous programming.",
         "question_type": "technical", "skill": "JavaScript", "difficulty": "medium",
         "expected_answer_points": ["Sync blocks execution", "Async uses callbacks/promises/async-await", "Event loop"],
         "reason": "Core concept for JS roles"},
        {"question_text": "What is a RESTful API and what are its key constraints?",
         "question_type": "technical", "skill": "REST APIs", "difficulty": "medium",
         "expected_answer_points": ["Stateless", "Client-server", "HTTP verbs", "Resource URLs"],
         "reason": "Essential for backend/full-stack"},
        {"question_text": "Describe your approach to debugging a production issue.",
         "question_type": "behavioral", "skill": "Problem Solving", "difficulty": "medium",
         "expected_answer_points": ["Reproduce", "Isolate", "Fix", "Test", "Monitor"],
         "reason": "Assesses problem-solving"},
        {"question_text": "Walk me through a project you built from scratch.",
         "question_type": "project", "skill": "General", "difficulty": "easy",
         "expected_answer_points": ["Problem statement", "Architecture", "Challenges", "Outcome"],
         "reason": "Project communication"},
        {"question_text": "How do you ensure code quality in a team setting?",
         "question_type": "behavioral", "skill": "Git", "difficulty": "medium",
         "expected_answer_points": ["Code review", "Tests", "Linting", "Documentation"],
         "reason": "Team collaboration"},
    ]
}


class InterviewQuestionAgent(BaseAgent):
    agent_name = "interview_question_agent"

    @classmethod
    async def run(
        cls, career_role: str, interview_type: str, difficulty: str,
        weak_areas: List[str], skill_names: List[str]
    ) -> Dict[str, Any]:
        system_prompt = (
            f"You are an interview coach. Generate exactly 5 interview questions for a "
            f"{career_role} candidate at {difficulty} level. "
            f"Interview type: {interview_type}. "
            f"Focus on weak areas: {', '.join(weak_areas[:5]) or 'general competency'}. "
            f"Relevant skills: {', '.join(skill_names[:15])}. "
            f"Mix question types. Each question must include 3-5 expected answer points."
        )
        user_prompt = (
            f"Generate 5 {interview_type} interview questions for a {career_role} role "
            f"at {difficulty} difficulty. Focus on: {', '.join(weak_areas[:3]) or 'core skills'}."
        )

        result = await cls.call_structured_output(system_prompt, user_prompt, InterviewQuestionsResult)
        if result and len(result.questions) >= 3:
            return result.model_dump()
        # Fallback
        fallback_qs = _FALLBACK.get("technical", [])
        return {
            "interview_title": f"{career_role} — {interview_type} Interview ({difficulty})",
            "questions": fallback_qs[:5]
        }
