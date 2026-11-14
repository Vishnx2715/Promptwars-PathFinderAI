from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl


class ProjectSubmitRequest(BaseModel):
    title: str = Field(..., max_length=300)
    project_type: str = Field(..., max_length=50)  # "frontend", "backend", "full_stack", "data_analysis", "machine_learning"
    description: str = Field(..., max_length=5000)
    github_url: Optional[str] = Field(None, max_length=1000)
    live_url: Optional[str] = Field(None, max_length=1000)


class ProjectListItem(BaseModel):
    id: int
    title: str
    project_type: str
    status: str
    evaluation_score: Optional[float] = None
    submitted_at: datetime
    evaluated_at: Optional[datetime] = None


class ProjectEvaluationReport(BaseModel):
    project_title: str
    overall_score: float
    verdict: str  # "strong", "good", "needs_improvement", "weak"
    verified_skills: List[Dict[str, Any]] = []
    strengths: List[str] = []
    weaknesses: List[Dict[str, Any]] = []
    limitations: List[str] = []
    rubric_scores: List[Dict[str, Any]] = []
    security_flags: List[str] = []
    portfolio_readiness: str  # "ready", "almost_ready", "not_ready"
    next_improvements: List[str] = []
    roadmap_impact: List[Dict[str, Any]] = []
    mentor_review_required: bool = True


class ProjectDetailResponse(BaseModel):
    id: int
    title: str
    project_type: str
    description: str
    github_url: Optional[str] = None
    live_url: Optional[str] = None
    status: str
    evaluation_score: Optional[float] = None
    evaluation_report: Optional[Dict[str, Any]] = None
    submitted_at: datetime
    evaluated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MentorProjectFeedback(BaseModel):
    comment: str = Field(..., max_length=2000)
    approve: bool = True


class RubricResponse(BaseModel):
    id: int
    project_type: str
    criteria: List[Dict[str, Any]]
    total_weight: int
