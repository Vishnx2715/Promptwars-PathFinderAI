"""StudyPlannerAgent — generates a weekly study plan using Grok."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.agents.base_agent import BaseAgent


class PlanTask(BaseModel):
    title: str
    description: str
    skill: str = ""
    task_type: str = "resource"
    estimated_minutes: int = 30
    day: str = "Monday"
    reason: str = ""


class StudyPlanResult(BaseModel):
    week_start_date: str = ""
    weekly_hours: int = 8
    planned_hours: float = 0.0
    focus_skills: List[str] = []
    tasks: List[PlanTask] = []
    weekly_objective: str = ""
    milestone: str = ""
    risk_alert: Optional[str] = None


class StudyPlannerAgent(BaseAgent):
    agent_name = "study_planner_agent"

    @classmethod
    async def run(
        cls, week_start: str, weekly_hours: int, weak_areas: List[str],
        roadmap_modules: List[Dict[str, Any]], career_role: str,
        upcoming_assignments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        total_minutes = weekly_hours * 60
        modules_text = "\n".join(
            f"- {m['title']} ({m['status']})" for m in roadmap_modules[:10]
        )
        assignments_text = "\n".join(
            f"- {a['title']} (due: {a['due']})" for a in upcoming_assignments[:5]
        ) if upcoming_assignments else "None"

        system_prompt = (
            f"Create a realistic weekly study plan for a {career_role} student. "
            f"Total available time: {total_minutes} minutes ({weekly_hours} hours). "
            f"Do not exceed this limit. "
            f"Prioritise: 1) critical gaps, 2) revision, 3) prerequisites, 4) roadmap, "
            f"5) college assignments, 6) projects. "
            f"Each task must have a day of the week."
        )
        user_prompt = (
            f"Week starting: {week_start}\n"
            f"Weekly hours: {weekly_hours}\n"
            f"Weak areas: {', '.join(weak_areas[:5]) or 'None identified'}\n"
            f"Active roadmap modules:\n{modules_text}\n"
            f"Upcoming college assignments:\n{assignments_text}"
        )

        result = await cls.call_structured_output(system_prompt, user_prompt, StudyPlanResult)
        if result:
            return result.model_dump()
        return cls._fallback(week_start, weekly_hours, weak_areas, roadmap_modules)

    @staticmethod
    def _fallback(week_start: str, weekly_hours: int, weak_areas: List[str],
                  roadmap_modules: List[Dict[str, Any]]) -> Dict[str, Any]:
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        tasks = []
        for i, wa in enumerate(weak_areas[:3]):
            tasks.append({
                "title": f"Revise {wa}",
                "description": f"Complete a practice exercise on {wa} to strengthen mastery.",
                "skill": wa, "task_type": "revision",
                "estimated_minutes": 45, "day": days[i % 5], "reason": "Weak area identified."
            })
        for m in roadmap_modules[:2]:
            if m.get("status") in ("available", "in_progress"):
                tasks.append({
                    "title": f"Study: {m['title']}",
                    "description": f"Work through the resources in {m['title']}.",
                    "skill": m.get("skill_name", ""), "task_type": "resource",
                    "estimated_minutes": 60, "day": days[len(tasks) % 5], "reason": "Next roadmap step."
                })
        total_min = sum(t["estimated_minutes"] for t in tasks)
        return {
            "week_start_date": week_start,
            "weekly_hours": weekly_hours,
            "planned_hours": round(total_min / 60, 1),
            "focus_skills": weak_areas[:3],
            "tasks": tasks,
            "weekly_objective": f"Strengthen weak areas and progress on {roadmap_modules[0]['title'] if roadmap_modules else 'roadmap'}.",
            "milestone": "Complete at least 2 revision tasks.",
            "risk_alert": None
        }
