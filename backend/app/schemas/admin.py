from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AdminOverviewResponse(BaseModel):
    total_students: int = 0
    total_mentors: int = 0
    active_learning_paths: int = 0
    total_assessments_completed: int = 0
    total_coding_submissions: int = 0
    total_projects_submitted: int = 0
    average_readiness_score: float = 0.0
    at_risk_student_count: int = 0


class AdminUserItem(BaseModel):
    id: int
    email: str
    username: str
    role: str
    is_active: bool
    created_at: datetime
    profile_name: Optional[str] = None
    mentor_code: Optional[str] = None


class AdminUserListResponse(BaseModel):
    users: List[AdminUserItem]
    total: int


class QuestionCreateRequest(BaseModel):
    skill_id: int
    subtopic: str = Field(..., max_length=100)
    question_text: str = Field(..., max_length=1000)
    options: Dict[str, str]
    correct_option: str = Field(..., max_length=10)
    explanation: str = Field(..., max_length=1000)
    difficulty: str = Field("medium", max_length=50)
    marks: int = 1
    assessment_id: int


class QuestionUpdateRequest(BaseModel):
    question_text: Optional[str] = None
    options: Optional[Dict[str, str]] = None
    correct_option: Optional[str] = None
    explanation: Optional[str] = None
    difficulty: Optional[str] = None
    marks: Optional[int] = None


class CodingProblemCreateRequest(BaseModel):
    title: str = Field(..., max_length=200)
    description: str = Field(..., max_length=5000)
    language: str = Field(..., max_length=50)
    skill_id: int
    subtopic: str = Field(..., max_length=100)
    difficulty: str = Field("medium", max_length=50)
    starter_code: str = Field(..., max_length=5000)
    function_name: str = Field(..., max_length=200)
    test_cases: List[Dict[str, Any]]
    examples: List[Dict[str, Any]] = []
    constraints: Optional[str] = None


class CodingProblemUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    difficulty: Optional[str] = None
    starter_code: Optional[str] = None
    test_cases: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None
