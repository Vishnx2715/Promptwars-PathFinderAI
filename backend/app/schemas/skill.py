from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class SkillBase(BaseModel):
    name: str
    category: str
    description: Optional[str] = None


class SkillCreate(SkillBase):
    pass


class SkillResponse(SkillBase):
    id: int

    class Config:
        from_attributes = True


class LearnerSkillCreate(BaseModel):
    skill_id: Optional[int] = None
    skill_name: Optional[str] = None
    level: int = Field(..., ge=0, le=5)


class LearnerSkillResponse(BaseModel):
    id: int
    skill_id: int
    skill_name: str
    category: str
    self_reported_level: int
    verified_level: float
    evidence_type: str
    mastery_percentage: float
    last_assessed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StrengthItem(BaseModel):
    skill: str
    mastery: float
    reason: str


class GapItem(BaseModel):
    skill: str
    current_mastery: float
    required_level: int
    priority: str  # "critical" | "high" | "medium" | "low"
    blocking_skills: List[str] = []
    reason: str


class GapAnalysisResponse(BaseModel):
    readiness_score: int
    strengths: List[StrengthItem]
    gaps: List[GapItem]
    next_best_action: str
    summary: str
