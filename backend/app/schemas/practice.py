from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TestCasePublic(BaseModel):
    """Visible test case shown to student."""
    id: int
    input: str
    expected_output: str
    explanation: Optional[str] = None


class CodingProblemListItem(BaseModel):
    id: int
    title: str
    language: str
    skill_id: int
    skill_name: str
    subtopic: str
    difficulty: str
    is_solved: bool = False
    is_attempted: bool = False
    acceptance_rate: float = 0.0
    total_submissions: int = 0


class CodingProblemDetail(BaseModel):
    id: int
    title: str
    description: str
    language: str
    skill_id: int
    skill_name: str
    subtopic: str
    difficulty: str
    starter_code: str
    function_name: str
    examples: List[Dict[str, Any]] = []
    constraints: Optional[str] = None
    visible_test_cases: List[Dict[str, Any]] = []


class CodeRunRequest(BaseModel):
    code: str = Field(..., max_length=10000)
    language: str = Field(..., max_length=50)
    problem_id: int


class TestResultItem(BaseModel):
    name: str
    passed: bool
    expected: str
    actual: str
    is_hidden: bool = False


class CodeSubmitRequest(BaseModel):
    code: str = Field(..., max_length=10000)
    language: str = Field(..., max_length=50)
    problem_id: int


class CodeSubmissionResponse(BaseModel):
    id: int
    coding_problem_id: int
    language: str
    status: str
    score: float
    tests_passed: int
    tests_total: int
    runtime_ms: Optional[int] = None
    ai_review: Optional[Dict[str, Any]] = None
    submitted_at: datetime
    test_results: List[TestResultItem] = []
    mastery_change: Optional[float] = None
    mentor_alert: bool = False

    class Config:
        from_attributes = True


class SubmissionHistoryItem(BaseModel):
    id: int
    status: str
    score: float
    tests_passed: int
    tests_total: int
    submitted_at: datetime


class PracticeProblemFilter(BaseModel):
    language: Optional[str] = None
    skill_id: Optional[int] = None
    subtopic: Optional[str] = None
    difficulty: Optional[str] = None
    status: Optional[str] = None  # "unsolved", "solved", "attempted"


class NextProblemRecommendation(BaseModel):
    title: str
    reason: str
