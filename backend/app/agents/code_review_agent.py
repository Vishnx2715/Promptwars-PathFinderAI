"""CodeReviewAgent: Reviews student code submissions using OpenAI Structured Outputs.
Returns test-result-grounded feedback with fallback to deterministic checklist."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.agents.base_agent import BaseAgent


class CodeIssue(BaseModel):
    type: str = Field(description="logic, syntax, performance, security, or style")
    title: str
    explanation: str
    suggested_fix: str


class Complexity(BaseModel):
    time: str = ""
    space: str = ""


class SkillUpdate(BaseModel):
    skill: str = ""
    subtopic: str = ""
    mastery_change: float = 0.0
    reason: str = ""


class NextProblemRecommendation(BaseModel):
    title: str = ""
    reason: str = ""


class CodeReviewResult(BaseModel):
    verdict: str = Field(description="correct, partially_correct, incorrect, or error")
    tests_passed: int = 0
    tests_total: int = 0
    strengths: List[str] = []
    issues: List[CodeIssue] = []
    complexity: Complexity = Field(default_factory=Complexity)
    skill_update: Optional[SkillUpdate] = None
    next_problem_recommendation: Optional[NextProblemRecommendation] = None
    mentor_alert_required: bool = False
    mentor_alert_reason: Optional[str] = None


class CodeReviewAgent(BaseAgent):
    @classmethod
    async def run(
        cls,
        problem_title: str,
        problem_description: str,
        student_code: str,
        test_results: List[Dict[str, Any]],
        language: str,
        skill_name: str,
        subtopic: str,
        previous_attempts: int,
        tests_passed: int,
        tests_total: int
    ) -> Dict[str, Any]:
        system_prompt = f"""You are a senior code reviewer for a learning platform.
Review the student's {language} code submission for the problem "{problem_title}".
The deterministic test results are the source of truth: {tests_passed}/{tests_total} passed.
You must NOT override the pass/fail status from tests. Only explain, suggest, and enrich.
If the student failed the same subtopic 3+ times, set mentor_alert_required to true."""

        user_prompt = f"""Problem: {problem_title}
Skill: {skill_name} / Subtopic: {subtopic}
Previous attempts on this problem: {previous_attempts}

Test Results:
{chr(10).join(f"- {t['name']}: {'PASS' if t['passed'] else 'FAIL'} (expected: {t['expected']}, actual: {t['actual']})" for t in test_results)}

Student Code:
```{language}
{student_code}
```

Provide a structured code review. Include strengths, issues, complexity analysis, and next problem recommendation.
If {previous_attempts} >= 3 and tests_failed > 0, set mentor_alert_required=true."""

        result = await cls.call_structured_output(system_prompt, user_prompt, CodeReviewResult)
        if result:
            return result.model_dump()
        return cls._deterministic_fallback(tests_passed, tests_total, previous_attempts)

    @staticmethod
    def _deterministic_fallback(tests_passed: int, tests_total: int, previous_attempts: int) -> Dict[str, Any]:
        all_passed = tests_passed == tests_total
        some_passed = tests_passed > 0
        return {
            "verdict": "correct" if all_passed else ("partially_correct" if some_passed else "incorrect"),
            "tests_passed": tests_passed,
            "tests_total": tests_total,
            "strengths": ["Code submitted successfully."] if some_passed else [],
            "issues": [
                {
                    "type": "logic",
                    "title": "Failing test cases",
                    "explanation": f"{tests_total - tests_passed} of {tests_total} tests failed. Review the logic against the problem description.",
                    "suggested_fix": "Check edge cases and ensure output format matches expectations."
                }
            ] if not all_passed else [],
            "complexity": {"time": "O(n)", "space": "O(1)"},
            "skill_update": None,
            "next_problem_recommendation": {
                "title": "Try a different problem in this topic",
                "reason": "Continue practicing to build mastery."
            },
            "mentor_alert_required": previous_attempts >= 3 and not all_passed,
            "mentor_alert_reason": f"Student failed {previous_attempts} times on this subtopic." if previous_attempts >= 3 else None,
        }
