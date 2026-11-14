from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class RoadmapResourceResponse(BaseModel):
    id: int
    roadmap_module_id: int
    title: str
    url: str
    resource_type: str  # "course", "documentation", "video", "exercise", "project"
    difficulty: str
    estimated_minutes: int
    reason: str
    is_completed: bool

    class Config:
        from_attributes = True


class RoadmapModuleResponse(BaseModel):
    id: int
    learning_path_id: int
    title: str
    description: str
    skill_id: int
    skill_name: str
    phase: int
    order_index: int
    estimated_hours: float
    status: str  # "locked", "available", "in_progress", "completed", "needs_revision"
    prerequisite_module_id: Optional[int] = None
    prerequisite_module_title: Optional[str] = None
    min_mastery_to_unlock: float
    reason: Optional[str] = None
    resources: List[RoadmapResourceResponse] = []

    class Config:
        from_attributes = True


class RoadmapResponse(BaseModel):
    id: int
    student_profile_id: int
    career_role_id: int
    career_role_name: str
    version: int
    status: str
    readiness_score: float
    replan_reason: Optional[str] = None
    modules: List[RoadmapModuleResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


class ModuleStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(locked|available|in_progress|completed|needs_revision)$")


class ResourceCompleteUpdate(BaseModel):
    is_completed: bool
