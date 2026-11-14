"""MentorChatAgent — context-aware career copilot using Grok (Section 3 upgrade)."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.agents.base_agent import BaseAgent


class NextBestAction(BaseModel):
    title: str = ""
    description: str = ""
    reason: str = ""
    estimated_minutes: int = 30
    action_type: str = "resource"
    reference_id: Optional[int] = None


class EvidenceItem(BaseModel):
    type: str = "roadmap"
    summary: str = ""


class ResourceItem(BaseModel):
    title: str = ""
    url: str = ""
    reason: str = ""


class MentorChatResult(BaseModel):
    answer: str
    next_best_action: NextBestAction = Field(default_factory=NextBestAction)
    evidence: List[EvidenceItem] = []
    recommended_resources: List[ResourceItem] = []
    escalate_to_mentor: bool = False
    escalation_reason: Optional[str] = None


class MentorChatAgent(BaseAgent):
    agent_name = "mentor_chat_agent"

    @classmethod
    async def run(
        cls,
        user_message: str,
        student_name: str,
        career_goal: str,
        skill_mastery: List[Dict[str, Any]],
        active_roadmap: List[Dict[str, Any]],
        recent_assessments: List[Dict[str, Any]],
        coding_practice: Dict[str, Any],
        project_evaluations: List[Dict[str, Any]],
        mentor_feedback: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        academic_risk: Optional[str] = None,
        job_match_score: Optional[float] = None,
        interview_score: Optional[float] = None,
    ) -> Dict[str, Any]:
        # Build compact context
        skill_text = "\n".join(
            f"- {s['name']}: {s['mastery']:.0f}%" for s in skill_mastery[:12]
        )
        roadmap_text = "\n".join(
            f"- {m['title']}: {m['status']}" for m in active_roadmap[:8]
        )
        history_text = ""
        if conversation_history:
            history_text = "\nConversation so far:\n" + "\n".join(
                f"{m['role'].capitalize()}: {m['content'][:100]}"
                for m in conversation_history[-8:]
            )

        system_prompt = (
            f"You are an AI career mentor for {student_name}, who targets {career_goal}. "
            f"Use their actual learner data for specific, evidence-based advice. "
            f"Always give one specific next action. "
            f"Do not reveal direct solutions to active coding problems — give hints instead. "
            f"If the question is complex or personal, suggest connecting with the human mentor."
        )
        user_prompt = (
            f"Student: {student_name}\nCareer goal: {career_goal}\n\n"
            f"Skill mastery:\n{skill_text}\n\n"
            f"Active roadmap:\n{roadmap_text}\n\n"
            f"Recent assessment avg: {recent_assessments[0].get('mastery', 0) if recent_assessments else 'N/A'}%\n"
            f"Coding: {coding_practice.get('solved', 0)} solved, {coding_practice.get('accuracy', 0)}% accuracy\n"
            f"Projects evaluated: {len(project_evaluations)}\n"
            f"Job match score: {job_match_score or 'N/A'}\n"
            f"Interview score: {interview_score or 'N/A'}\n"
            f"Academic risk: {academic_risk or 'None'}\n"
            f"{history_text}\n\n"
            f"Student question: {user_message}"
        )

        result = await cls.call_structured_output(system_prompt, user_prompt, MentorChatResult)
        if result:
            return result.model_dump()
        return cls._fallback(user_message, career_goal, skill_mastery, active_roadmap)

    @staticmethod
    def _fallback(user_message: str, career_goal: str,
                  skill_mastery: List[Dict[str, Any]],
                  active_roadmap: List[Dict[str, Any]]) -> Dict[str, Any]:
        weakest = min(skill_mastery, key=lambda s: s.get("mastery", 100)) if skill_mastery else None
        next_mod = next(
            (m for m in active_roadmap if m.get("status") in ("available", "in_progress", "needs_revision")), None
        )
        if weakest and weakest.get("mastery", 100) < 50:
            answer = f"Your weakest skill is {weakest['name']} at {weakest.get('mastery', 0):.0f}%. Focus there first."
            action = {"title": f"Revise {weakest['name']}", "description": "Complete a practice exercise.",
                      "reason": "Lowest mastery skill", "estimated_minutes": 45, "action_type": "revision", "reference_id": None}
        elif next_mod:
            answer = f"Your next step is '{next_mod['title']}' (status: {next_mod['status']})."
            action = {"title": f"Work on {next_mod['title']}", "description": "Start the resources in this module.",
                      "reason": "Next available roadmap module", "estimated_minutes": 60, "action_type": "resource", "reference_id": None}
        else:
            answer = f"Keep progressing toward {career_goal}. Take a diagnostic assessment to identify gaps."
            action = {"title": "Take a diagnostic assessment", "description": "Measure your current mastery.",
                      "reason": "No active roadmap modules", "estimated_minutes": 20, "action_type": "assessment", "reference_id": None}
        return {
            "answer": answer, "next_best_action": action,
            "evidence": [], "recommended_resources": [],
            "escalate_to_mentor": False, "escalation_reason": None
        }
