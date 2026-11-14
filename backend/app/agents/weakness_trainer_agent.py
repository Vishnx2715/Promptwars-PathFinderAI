"""WeaknessTrainerAgent: Identifies weak areas from assessment results and builds a remediation plan.
Falls back to rule-based remediation from resources.json on AI failure."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.agents.base_agent import BaseAgent


class WeakArea(BaseModel):
    skill: str
    subtopic: str
    mastery: float
    priority: str = "medium"  # "high", "medium", "low"
    evidence: str
    recommended_action: str


class Strength(BaseModel):
    skill: str
    subtopic: str
    mastery: float


class TrainingPlanItem(BaseModel):
    title: str
    duration_minutes: int = 30
    resources: List[Dict[str, str]] = []
    practice_task: str = ""
    follow_up_assessment: str = ""


class RoadmapImpactItem(BaseModel):
    module_title: str
    action: str  # "lock", "unlock", "needs_revision", "keep"
    reason: str


class WeaknessTrainerResult(BaseModel):
    overall_mastery: float = 0.0
    status: str = "remediate"  # "remediate", "reinforce", "advance"
    weak_areas: List[WeakArea] = []
    strengths: List[Strength] = []
    training_plan: List[TrainingPlanItem] = []
    roadmap_impact: List[RoadmapImpactItem] = []
    next_best_action: str = ""


class WeaknessTrainerAgent(BaseAgent):
    @classmethod
    async def run(
        cls,
        assessment_title: str,
        skill_name: str,
        mastery: float,
        subtopic_results: List[Dict[str, Any]],
        incorrect_answers: List[Dict[str, Any]],
        learner_skill_history: List[Dict[str, Any]],
        current_roadmap: List[Dict[str, Any]],
        fallback_resources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        system_prompt = f"""You are an adaptive learning specialist.
Analyze a student's assessment results for "{skill_name}" and build a targeted remediation plan.
The deterministic mastery calculation is the source of truth — you may NOT invent mastery scores.
You can only select and explain resources, and suggest training tasks.
Determine if status should be remediate (<50%), reinforce (50-74%), or advance (>=85%)."""

        user_prompt = f"""Assessment: {assessment_title}
Skill: {skill_name}
Overall Mastery: {mastery}%

Subtopic Results:
{chr(10).join(f"- {s['subtopic']}: {s['correct']}/{s['total']} correct" for s in subtopic_results)}

Incorrect Answers:
{chr(10).join(f"- {a['subtopic']}: selected {a['selected']}, correct {a['correct']}" for a in incorrect_answers)}

Current Roadmap Modules:
{chr(10).join(f"- {m['title']}: {m['status']}" for m in current_roadmap)}

Available Resources:
{chr(10).join(f"- {r.get('title', '')}: {r.get('url', '')}" for r in fallback_resources[:10])}

Build a training plan with specific resources and practice tasks for the weak areas."""

        result = await cls.call_structured_output(system_prompt, user_prompt, WeaknessTrainerResult)
        if result:
            return result.model_dump()
        return cls._deterministic_fallback(mastery, skill_name, subtopic_results, incorrect_answers, fallback_resources, current_roadmap)

    @staticmethod
    def _deterministic_fallback(
        mastery: float,
        skill_name: str,
        subtopic_results: List[Dict[str, Any]],
        incorrect_answers: List[Dict[str, Any]],
        fallback_resources: List[Dict[str, Any]],
        current_roadmap: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        if mastery < 50:
            status = "remediate"
            next_action = f"Complete the {skill_name} revision sprint. Your mastery is {mastery:.0f}%."
        elif mastery < 75:
            status = "reinforce"
            next_action = f"Practice more {skill_name} exercises to reach 75%+ mastery."
        elif mastery >= 85:
            status = "advance"
            next_action = f"Excellent! Proceed to the next roadmap module."
        else:
            status = "reinforce"
            next_action = f"Continue practicing {skill_name}."

        weak = [
            {
                "skill": skill_name,
                "subtopic": s["subtopic"],
                "mastery": round((s["correct"] / max(s["total"], 1)) * 100, 1),
                "priority": "high" if s["correct"] == 0 else "medium",
                "evidence": f"{s['correct']}/{s['total']} correct on {s['subtopic']}",
                "recommended_action": f"Review {s['subtopic']} fundamentals and retry."
            }
            for s in subtopic_results if s["correct"] < s["total"]
        ]

        # Build training plan from fallback resources
        training_plan = []
        relevant = [r for r in fallback_resources if r.get("skill") == skill_name or skill_name.lower() in r.get("title", "").lower()]
        if not relevant:
            relevant = fallback_resources[:5]
        
        for r in relevant[:4]:
            training_plan.append({
                "title": f"Review: {r.get('title', skill_name)}",
                "duration_minutes": r.get("estimated_minutes", 30),
                "resources": [{"title": r.get("title", ""), "url": r.get("url", ""), "type": r.get("resource_type", "documentation")}],
                "practice_task": f"Complete the {r.get('title', skill_name)} exercise and attempt a practice problem.",
                "follow_up_assessment": f"Retake the {skill_name} diagnostic to verify improvement."
            })

        roadmap_impact = []
        for mod in current_roadmap:
            if mod.get("skill_name") == skill_name:
                if mastery < 50:
                    roadmap_impact.append({"module_title": mod["title"], "action": "needs_revision", "reason": f"Mastery below 50% ({mastery:.0f}%)."})
                elif mastery < 75:
                    roadmap_impact.append({"module_title": mod["title"], "action": "keep", "reason": f"Mastery developing ({mastery:.0f}%)."})
                elif mastery >= 85:
                    roadmap_impact.append({"module_title": mod["title"], "action": "unlock", "reason": f"Mastery verified ({mastery:.0f}%)."})

        return {
            "overall_mastery": mastery,
            "status": status,
            "weak_areas": weak,
            "strengths": [
                {"skill": skill_name, "subtopic": s["subtopic"], "mastery": round((s["correct"] / max(s["total"], 1)) * 100, 1)}
                for s in subtopic_results if s["correct"] == s["total"]
            ],
            "training_plan": training_plan,
            "roadmap_impact": roadmap_impact,
            "next_best_action": next_action,
        }
