"""ReportSummaryAgent — generates a concise narrative for career readiness reports."""
from typing import Dict, Any
from pydantic import BaseModel
from app.agents.base_agent import BaseAgent


class ReportNarrative(BaseModel):
    executive_summary: str = ""
    key_strengths: str = ""
    critical_gaps: str = ""
    recommended_next_steps: str = ""


class ReportSummaryAgent(BaseAgent):
    agent_name = "report_summary_agent"

    @classmethod
    async def run(cls, report_data: Dict[str, Any]) -> Dict[str, Any]:
        system_prompt = (
            "You are a career coach writing a concise, professional report narrative. "
            "Write a 2-3 sentence executive summary, one sentence on strengths, "
            "one sentence on critical gaps, and one sentence on next steps. "
            "Be specific and use the student's actual data."
        )
        user_prompt = (
            f"Student: {report_data.get('student_name', 'Student')}\n"
            f"Career goal: {report_data.get('career_role', 'Unknown')}\n"
            f"Readiness score: {report_data.get('readiness_score', 0)}%\n"
            f"Strengths: {', '.join(report_data.get('strengths', [])[:5])}\n"
            f"Critical gaps: {', '.join(report_data.get('gaps', [])[:5])}\n"
            f"Assessment avg: {report_data.get('assessment_avg', 0)}%\n"
            f"Projects evaluated: {report_data.get('projects_count', 0)}"
        )

        result = await cls.call_structured_output(system_prompt, user_prompt, ReportNarrative)
        if result:
            return result.model_dump()
        name = report_data.get("student_name", "Student")
        role = report_data.get("career_role", "target role")
        score = report_data.get("readiness_score", 0)
        return {
            "executive_summary": (
                f"{name} is currently at {score:.0f}% readiness for the {role} role. "
                f"Continued practice and assessment completion will accelerate progress."
            ),
            "key_strengths": f"Strongest areas: {', '.join(report_data.get('strengths', ['to be determined'])[:3])}.",
            "critical_gaps": f"Focus areas: {', '.join(report_data.get('gaps', ['core skills'])[:3])}.",
            "recommended_next_steps": "Complete active roadmap modules and take diagnostic assessments.",
        }
