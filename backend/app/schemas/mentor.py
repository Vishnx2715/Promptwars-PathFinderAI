from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class MentorConnectRequest(BaseModel):
    mentor_code: str = Field(..., max_length=50)


class MentorConnectResponse(BaseModel):
    connected: bool
    mentor_name: str
    mentor_expertise: str
    status: str


class MentorConnectionListItem(BaseModel):
    id: int
    mentor_name: str
    mentor_expertise: str
    status: str
    connected_at: datetime


class MentorProfileResponse(BaseModel):
    id: int
    full_name: str
    expertise: str
    mentor_code: str
    is_active: bool
    connected_students: int = 0


class MenteeSummary(BaseModel):
    profile_id: int
    student_name: str
    career_goal: Optional[str] = None
    readiness_score: float = 0.0
    roadmap_progress_pct: float = 0.0
    last_active: Optional[datetime] = None
    risk_level: str = "low"  # "low", "medium", "high"
    pending_doubts: int = 0
    pending_project_reviews: int = 0


class MenteeDetailResponse(BaseModel):
    profile_id: int
    student_name: str
    career_goal: Optional[str] = None
    readiness_score: float = 0.0
    roadmap_modules: List[Dict[str, Any]] = []
    learner_skills: List[Dict[str, Any]] = []
    assessment_history: List[Dict[str, Any]] = []
    coding_stats: Dict[str, Any] = {}
    project_submissions: List[Dict[str, Any]] = []
    weak_areas: List[str] = []
    ai_insight: Optional[Dict[str, Any]] = None


class MentorFeedbackRequest(BaseModel):
    student_profile_id: int
    feedback_type: str = Field("general", max_length=50)  # "general", "roadmap", "project", "assessment"
    comment: str = Field(..., max_length=2000)
    recommended_action: Optional[str] = Field(None, max_length=1000)
    roadmap_module_id: Optional[int] = None


class MentorFeedbackResponse(BaseModel):
    id: int
    student_profile_id: int
    mentor_id: int
    feedback_type: str
    comment: str
    recommended_action: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AssignAssessmentRequest(BaseModel):
    student_profile_id: int
    skill_id: int


class DoubtSubmitRequest(BaseModel):
    subject: str = Field(..., max_length=200)
    question: str = Field(..., max_length=5000)
    skill_id: Optional[int] = None
    roadmap_module_id: Optional[int] = None


class DoubtResponse(BaseModel):
    id: int
    student_profile_id: int
    mentor_id: Optional[int] = None
    skill_id: Optional[int] = None
    subject: str
    question: str
    ai_draft_answer: Optional[str] = None
    mentor_response: Optional[str] = None
    status: str
    created_at: datetime
    answered_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DoubtAnswerRequest(BaseModel):
    mentor_response: str = Field(..., max_length=5000)
    status: str = Field("answered", max_length=50)  # "answered" or "resolved"


class CreateMentorRequest(BaseModel):
    user_id: int
    full_name: str = Field(..., max_length=255)
    expertise: str = Field(..., max_length=500)


class RegenerateCodeRequest(BaseModel):
    mentor_id: int
